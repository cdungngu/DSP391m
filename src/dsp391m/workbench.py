"""Prepare real-source review packets; publish only explicit human review decisions."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .catalog import Catalog, candidates
from .contracts import EvidenceRecord
from .paths import snapshot_dir
from .releases import digest, publish, read_release, source_manifest, verify_sources


def prepare(snap: Path, out: Path) -> dict:
    if out.exists():
        raise FileExistsError("Choose a new packet directory; existing packets are immutable")
    source_files = {name: snap / name for name in ("drugs.parquet", "drug_names.parquet",
                                                   "manifest.json")}
    section_path = snap / "dailymed_sections.parquet"
    if section_path.exists():
        source_files[section_path.name] = section_path
    manifest = source_manifest(source_files, {"snapshot": snap.name, "purpose": "human_review"})
    catalog = candidates(snap)
    drafts = []
    if section_path.exists():
        for row in pd.read_parquet(section_path).to_dict("records"):
            record = EvidenceRecord(
                evidence_id=row["chunk_id"], evidence_type="drug_label",
                subjects=(row["stitch_id"],),
                source_url="https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=" + row["setid"],
                source_record_id=row["setid"], source_version=str(row["spl_version"]),
                source_text=row["text"], statement_vi="", conditions=(),
                review_status="pending", reviewer="", reviewed_at="",
                relation="unreviewed_label_section")
            drafts.append({"record": asdict(record), "content_hash": record.content_hash,
                           "section": row["section"], "title": row["title"]})
    # Verify sources again before publication so a concurrent refresh fails closed.
    verify_sources(manifest)
    out.mkdir(parents=True)
    publish(out / "sources.json", manifest)
    publish(out / "catalog_candidates.json", catalog)
    publish(out / "evidence_candidates.json", {"schema_version": 1, "source_manifest": manifest,
                                              "records": drafts})
    guide = {"schema_version": 1, "status": "pending_human_review",
             "catalog_instructions": "Select ingredients; explicitly review aliases/products; use catalog import-decisions.",
             "evidence_instructions": "Review original source/version and applicability; provide subjects, Vietnamese statement and all conditions.",
             "gold_case_fields": ["case_id", "ingredient_ids", "canonical_pairs", "split", "source_snapshot"],
             "annotation_fields": ["case_id", "claim_id", "annotator", "supported",
                                   "contradicted", "insufficient", "citation_correct", "overclaim", "rationale"],
             "counts": {"catalog_candidates": len(catalog["ingredients"]),
                        "evidence_candidates": len(drafts), "approved": 0}}
    publish(out / "review_instructions.json", guide)
    return guide["counts"]


def publish_corpus(catalog_path: Path, draft_path: Path, decisions_path: Path, out: Path) -> dict:
    catalog_doc, _ = read_release(catalog_path)
    catalog = Catalog(catalog_doc)
    draft, _ = read_release(draft_path)
    verify_sources(draft["source_manifest"])
    by_id = {r["record"]["evidence_id"]: r for r in draft["records"]}
    decisions = json.loads(decisions_path.read_text())
    approved, seen = [], set()
    for decision in decisions:
        ident = decision["evidence_id"]
        if ident in seen or ident not in by_id:
            raise ValueError("Duplicate or unknown evidence decision")
        seen.add(ident)
        candidate = by_id[ident]
        if decision["content_hash"] != candidate["content_hash"]:
            raise ValueError("Evidence review source has changed")
        if decision.get("review_status") not in {"approved", "rejected", "pending"}:
            raise ValueError("Invalid review decision")
        if decision["review_status"] != "approved":
            continue
        if not decision.get("rationale"):
            raise ValueError("Review rationale is required")
        fields = ("subjects", "statement_vi", "conditions", "review_status", "reviewer", "reviewed_at")
        record = EvidenceRecord.from_dict({**candidate["record"],
                                          **{k: decision[k] for k in fields},
                                          "relation": "interaction_statement"})
        if len(record.subjects) != 2 or not set(record.subjects) <= catalog.items.keys():
            raise ValueError("Consumer evidence requires two approved ingredients")
        if not set(candidate["record"]["subjects"]) <= set(record.subjects):
            raise ValueError("Statement must retain the original source drug")
        approved.append(asdict(record))
    payload = {"schema_version": 1, "catalog_version": catalog.version,
               "snapshot_hash": digest(draft["source_manifest"]), "source_manifest": draft["source_manifest"],
               "evidence": approved, "review_decisions": decisions}
    publish(out, payload)
    return {"approved_pair_statements": len(approved), "catalog_ingredients": len(catalog.items)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--snapshot-dir", type=Path, default=snapshot_dir())
    prep.add_argument("--out", type=Path, required=True)
    pub = sub.add_parser("publish-corpus")
    pub.add_argument("--catalog", type=Path, required=True)
    pub.add_argument("--drafts", type=Path, required=True)
    pub.add_argument("--decisions", type=Path, required=True)
    pub.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.command == "prepare":
        result = prepare(args.snapshot_dir, args.out)
    else:
        result = publish_corpus(args.catalog, args.drafts, args.decisions, args.out)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
