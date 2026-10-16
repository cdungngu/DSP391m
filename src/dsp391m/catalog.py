"""Reviewed catalog with explicit candidate export/import. No automatic approvals."""
import argparse
import difflib
import json
import unicodedata
from pathlib import Path

import pandas as pd

from .paths import snapshot_dir
from .releases import digest, publish, read_release


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def candidates(snap: Path) -> dict:
    names = pd.read_parquet(snap / "drug_names.parquet")
    drugs = pd.read_parquet(snap / "drugs.parquet")
    source_hash = digest({"names": digest((snap / "drug_names.parquet").read_bytes().hex()),
                          "drugs": digest((snap / "drugs.parquet").read_bytes().hex())})
    combo = set(drugs.loc[drugs["in_combo"], "stitch_id"])
    rows = []
    for d in names.itertuples(index=False):
        if d.stitch_id not in combo:
            continue
        rows.append({"ingredient_id": d.stitch_id, "display_name_vi": d.display_name,
                     "aliases": sorted(set([d.display_name, *d.synonyms])),
                     "source_ids": {"stitch_id": d.stitch_id},
                     "source_hash": source_hash, "review_status": "pending",
                     "reviewer": "", "reviewed_at": "", "rationale": "",
                     "review_source": "", "products": []})
    return {"schema_version": 1, "source_hash": source_hash, "ingredients": rows}


def apply_decisions(candidate_doc: dict, decisions: list[dict]) -> dict:
    by_id = {r["ingredient_id"]: dict(r) for r in candidate_doc["ingredients"]}
    seen = set()
    for decision in decisions:
        ident = decision["ingredient_id"]
        if ident in seen or ident not in by_id:
            raise ValueError(f"Duplicate/unknown ingredient decision: {ident}")
        seen.add(ident)
        if decision.get("source_hash") != candidate_doc["source_hash"]:
            raise ValueError("Review was made against a different source snapshot")
        if decision.get("review_status") not in {"approved", "rejected", "pending"}:
            raise ValueError("Invalid decision")
        if not all(decision.get(k) for k in ("reviewer", "reviewed_at", "rationale", "review_source")):
            raise ValueError("Review provenance is required")
        if not isinstance(decision.get("aliases"), list) or not decision.get("display_name_vi"):
            raise ValueError("Explicit reviewed aliases and display name are required")
        allowed = {"display_name_vi", "aliases", "review_status", "reviewer", "reviewed_at",
                   "rationale", "review_source", "products"}
        by_id[ident].update({k: v for k, v in decision.items() if k in allowed})
    output = {**candidate_doc, "ingredients": list(by_id.values())}
    Catalog(output)  # validate before publication
    return output


class Catalog:
    def __init__(self, doc: dict):
        if doc.get("schema_version") != 1:
            raise ValueError("Unsupported catalog schema")
        self.version = digest(doc)
        self.items, self.aliases = {}, {}
        all_ids = [r["ingredient_id"] for r in doc["ingredients"]]
        if len(set(all_ids)) != len(all_ids):
            raise ValueError("Duplicate ingredient ID")
        for row in doc["ingredients"]:
            if row["review_status"] != "approved":
                continue
            if not all(row.get(k) for k in ("reviewer", "reviewed_at", "rationale", "review_source",
                                           "display_name_vi")):
                raise ValueError("Approved catalog item is missing review provenance")
            if row.get("source_hash") != doc["source_hash"]:
                raise ValueError("Catalog item source mismatch")
            ident = row["ingredient_id"]
            self.items[ident] = row
            for alias in [ident, row["display_name_vi"], *row["aliases"]]:
                if not isinstance(alias, str) or not normalize(alias):
                    raise ValueError("Empty or non-string alias")
                self.aliases.setdefault(normalize(alias), set()).add(ident)
        self.products = {}
        for row in self.items.values():
            for product in row.get("products", []):
                pid = product["product_id"]
                if pid in self.items or pid in self.products:
                    raise ValueError("Duplicate product ID")
                if not all(product.get(k) for k in ("brand", "country", "route", "formulation",
                                                    "source_url", "ingredient_ids")):
                    raise ValueError("Incomplete reviewed product")
                if not set(product["ingredient_ids"]) <= self.items.keys():
                    raise ValueError("Product contains an unapproved ingredient")
                self.products[pid] = product
                for alias in [pid, product["brand"]]:
                    self.aliases.setdefault(normalize(alias), set()).add(pid)

    def resolve(self, token: str) -> dict:
        hits = sorted(self.aliases.get(normalize(token), set()))
        if len(hits) != 1:
            close = difflib.get_close_matches(normalize(token), list(self.aliases), n=3, cutoff=0.7)
            return {"input": token, "status": "ambiguous" if hits else "not_found",
                    "candidates": hits or sorted({x for a in close for x in self.aliases[a]})}
        ident = hits[0]
        product = self.products.get(ident)
        return {"input": token, "status": "resolved", "catalog_id": ident,
                "ingredient_ids": sorted(set(product["ingredient_ids"])) if product else [ident],
                "route": product["route"] if product else None}

    def resolve_all(self, tokens: list[str]) -> dict:
        resolved = [self.resolve(t) for t in tokens]
        ids = sorted({i for r in resolved if r["status"] == "resolved" for i in r["ingredient_ids"]})
        ready = bool(tokens) and all(r["status"] == "resolved" for r in resolved) and 2 <= len(ids) <= 5
        counts = {}
        for r in resolved:
            for i in r.get("ingredient_ids", []):
                counts[i] = counts.get(i, 0) + 1
        return {"inputs": resolved, "ingredient_ids": ids, "ready": ready,
                "duplicates": sorted(i for i, n in counts.items() if n > 1),
                "reason": None if ready else "resolve_all_inputs_and_select_2_to_5_ingredients"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("--snapshot-dir", type=Path, default=snapshot_dir())
    export.add_argument("--out", type=Path, required=True)
    review = sub.add_parser("import-decisions")
    review.add_argument("--candidates", type=Path, required=True)
    review.add_argument("--decisions", type=Path, required=True)
    review.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.command == "export":
        doc = candidates(args.snapshot_dir)
    else:
        doc, _ = read_release(args.candidates)
        doc = apply_decisions(doc, json.loads(args.decisions.read_text()))
    version = publish(args.out, doc)
    print(json.dumps({"path": str(args.out), "version": version,
                      "total": len(doc["ingredients"]), "approved": len(Catalog(doc).items)}))


if __name__ == "__main__":
    main()
