"""Offline consumer template path; only reviewed, source-backed statements are publishable."""
import argparse
import json
from dataclasses import asdict, replace
from itertools import combinations
from pathlib import Path

from .catalog import Catalog
from .contracts import Claim, EvidenceRecord, RunContext, consumer_claim
from .releases import digest, read_release, verify_sources


def verify(claim: Claim, records: dict[str, EvidenceRecord]) -> Claim:
    """Conservative verifier: exact reviewed statement only; free text is not auto-approved."""
    if len(claim.evidence_ids) != 1 or claim.evidence_ids[0] not in records:
        return replace(claim, support_status="insufficient", reason_codes=("citation_missing",))
    e = records[claim.evidence_ids[0]]
    reasons = []
    if e.review_status != "approved":
        reasons.append("unreviewed_semantics")
    if e.evidence_type not in {"drug_label", "curated_statement"} or e.relation != "interaction_statement":
        reasons.append("scope_overreach")
    if len(e.subjects) != 2 or set(claim.subjects) != set(e.subjects):
        reasons.append("wrong_subject")
    if claim.text_vi != e.statement_vi:
        reasons.append("unverified_semantics")
    if claim.conditions != e.conditions:
        reasons.append("condition_dropped")
    return replace(claim, support_status="insufficient" if reasons else "supported",
                   reason_codes=tuple(reasons))


def run_review(tokens: list[str], catalog: Catalog, corpus: dict, snapshot_hash: str) -> dict:
    if corpus.get("schema_version") != 1 or corpus.get("catalog_version") != catalog.version:
        raise ValueError("Corpus/catalog version mismatch")
    context = RunContext("consumer_review", "evidence", snapshot_hash, catalog.version,
                         digest(corpus), digest({"renderer": "reviewed_template_v1", "verifier": 1}))
    resolution = catalog.resolve_all(tokens)
    result = {"schema_version": 1, "context": asdict(context), "input_resolution": resolution,
              "execution_status": "needs_resolution", "pair_results": [], "claims": [],
              "missing_data": [], "coverage": {}}
    if not resolution["ready"]:
        return result  # never review a silently reduced subset of the prescription
    evidence = [EvidenceRecord.from_dict(row) for row in corpus["evidence"]]
    records = {e.evidence_id: e for e in evidence}
    if len(records) != len(evidence):
        raise ValueError("Duplicate evidence IDs")
    if any(not set(e.subjects) <= catalog.items.keys() for e in evidence):
        raise ValueError("Evidence contains unapproved or unknown ingredients")
    for pair in combinations(resolution["ingredient_ids"], 2):
        published = []
        for e in evidence:
            if set(e.subjects) != set(pair):
                continue
            claim = verify(Claim("claim:" + e.content_hash, pair, e.statement_vi,
                                 (e.evidence_id,), e.conditions), records)
            if claim.support_status == "supported":
                published.append(consumer_claim(claim, records))
        result["claims"].extend(published)
        result["pair_results"].append({"ingredients": list(pair),
                                       "evidence_status": "supported" if published else "insufficient",
                                       "prediction_status": "not_requested"})
        if not published:
            result["missing_data"].append({"scope": "pair", "ingredients": list(pair),
                                           "reason": "no_reviewed_pair_statement"})
    result["coverage"] = {"pairs_total": len(result["pair_results"]),
                          "pairs_with_supported_claims": sum(p["evidence_status"] == "supported"
                                                            for p in result["pair_results"])}
    result["execution_status"] = "completed"
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("drugs", nargs="+")
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--corpus", type=Path, required=True)
    args = p.parse_args()
    catalog_doc, _ = read_release(args.catalog)
    corpus, _ = read_release(args.corpus)
    verify_sources(corpus["source_manifest"])
    result = run_review(args.drugs, Catalog(catalog_doc), corpus, corpus["snapshot_hash"])
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
