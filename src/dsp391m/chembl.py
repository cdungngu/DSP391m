"""GĐ3 (phần ChEMBL): ánh xạ thuốc → ChEMBL, cơ chế có chiều tác động, và bổ sung tên thuốc.

Chạy: python -m dsp391m.chembl [--snapshot-dir DIR] [--offline]

1. Khớp InChIKey đầy đủ (theo lô). Thuốc chưa khớp thì khớp theo khối connectivity (14 ký tự đầu của
   InChIKey: bỏ qua lập thể và trạng thái proton), ưu tiên phân tử đã được duyệt (max_phase cao), có tên.
   Mọi khớp theo connectivity có needs_review = True (có thể nhầm đồng phân lập thể hoặc muối).
2. Quy về phân tử cha (molecule_hierarchy.parent_chembl_id), vì cơ chế thường được ghi ở phân tử cha.
3. Lấy cơ chế (action_type, mechanism_of_action, target, tài liệu tham chiếu) và gene symbol của target;
   nối sang gene Entrez của Decagon qua symbol.
4. Bổ sung tên cho thuốc chưa có tên từ PubChem (name_source pending/none → "chembl"), thêm tên ChEMBL
   vào synonym của mọi thuốc đã khớp.

Đầu ra trong snapshot: chembl_map.parquet, chembl_mechanisms.parquet, chembl_report.json; cập nhật
drug_names.parquet và names_report.json. Cache phản hồi trong data/external/chembl/.
Dữ liệu ChEMBL theo giấy phép CC BY-SA 3.0.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from . import names as names_mod
from .http import batch_key, cached, request
from .manifest import utc_now, write_json
from .paths import EXTERNAL_DIR, snapshot_dir

BASE = "https://www.ebi.ac.uk/chembl/api/data"
CACHE = EXTERNAL_DIR / "chembl"
BATCH = 40
PAUSE = 0.5


def _get_all(endpoint: str, params: dict, list_key: str, offline: bool) -> list[dict]:
    """GET có phân trang; mỗi trang cache riêng theo endpoint và tham số."""
    out, offset = [], 0
    while True:
        p = {**params, "limit": 1000, "offset": offset}
        key = batch_key([endpoint, json.dumps(p, sort_keys=True)])

        def fetch(p=p):
            r = request("GET", f"{BASE}/{endpoint}.json", params=p)
            r.raise_for_status()
            return r.json()

        page = cached(CACHE / endpoint / f"{key}.json", fetch, offline, PAUSE)["data"]
        out += page.get(list_key, [])
        meta = page.get("page_meta", {})
        if not meta.get("next"):
            return out
        offset += meta["limit"]


def _by_ids(endpoint: str, field: str, ids: list[str], list_key: str, offline: bool, only: str | None = None) -> list[dict]:
    rows = []
    ids = sorted(set(ids))
    for i in range(0, len(ids), BATCH):
        params = {f"{field}__in": ",".join(ids[i:i + BATCH])}
        if only:
            params["only"] = only
        rows += _get_all(endpoint, params, list_key, offline)
    return rows


def _phase(m: dict) -> float:
    try:
        return float(m.get("max_phase") or -1)
    except (TypeError, ValueError):
        return -1.0


def _parent(m: dict) -> str:
    return (m.get("molecule_hierarchy") or {}).get("parent_chembl_id") or m["molecule_chembl_id"]


def map_drugs(structures: pd.DataFrame, offline: bool = False) -> pd.DataFrame:
    only = "molecule_chembl_id,pref_name,max_phase,molecule_hierarchy,molecule_structures"
    keys = structures["inchikey"].dropna().tolist()
    exact: dict[str, list[dict]] = {}
    for m in _by_ids("molecule", "molecule_structures__standard_inchi_key", keys, "molecules", offline, only):
        k = (m.get("molecule_structures") or {}).get("standard_inchi_key")
        exact.setdefault(k, []).append(m)

    rows = []
    for d in structures.itertuples(index=False):
        cands, match = exact.get(d.inchikey, []), "exact"
        if not cands and isinstance(d.inchikey, str):
            match = "connectivity"
            cands = _get_all("molecule", {"molecule_structures__standard_inchi_key__startswith": d.inchikey[:14],
                                          "only": only}, "molecules", offline)
        if not cands:
            rows.append({"drug_idx": d.drug_idx, "stitch_id": d.stitch_id, "match_type": "none",
                         "matched_chembl_id": None, "parent_chembl_id": None, "n_candidates": 0})
            continue
        best = max(cands, key=lambda m: (_phase(m), m.get("pref_name") is not None, -int(m["molecule_chembl_id"][6:])))
        rows.append({"drug_idx": d.drug_idx, "stitch_id": d.stitch_id, "match_type": match,
                     "matched_chembl_id": best["molecule_chembl_id"], "parent_chembl_id": _parent(best),
                     "n_candidates": len(cands)})
    return pd.DataFrame(rows)


def parent_info(parent_ids: list[str], offline: bool = False) -> pd.DataFrame:
    mols = _by_ids("molecule", "molecule_chembl_id", parent_ids, "molecules", offline,
                   "molecule_chembl_id,pref_name,max_phase,molecule_synonyms")
    return pd.DataFrame([{
        "parent_chembl_id": m["molecule_chembl_id"], "pref_name": m.get("pref_name"), "max_phase": _phase(m),
        "chembl_synonyms": sorted({s["molecule_synonym"] for s in m.get("molecule_synonyms") or []
                                   if names_mod.is_name_like(s.get("molecule_synonym"))}),
    } for m in mols], columns=["parent_chembl_id", "pref_name", "max_phase", "chembl_synonyms"])


def mechanisms(parent_ids: list[str], gene_names: pd.DataFrame, offline: bool = False) -> pd.DataFrame:
    mecs = _by_ids("mechanism", "molecule_chembl_id", parent_ids, "mechanisms", offline)
    target_ids = [m["target_chembl_id"] for m in mecs if m.get("target_chembl_id")]
    targets = {t["target_chembl_id"]: t for t in _by_ids(
        "target", "target_chembl_id", target_ids, "targets", offline,
        "target_chembl_id,pref_name,target_type,organism,target_components")}
    symbol_to_gene = {}
    for g in gene_names.dropna(subset=["symbol"]).itertuples(index=False):
        symbol_to_gene.setdefault(g.symbol.upper(), int(g.gene_id))
    rows = []
    for m in mecs:
        t = targets.get(m.get("target_chembl_id"), {})
        symbols = sorted({s["component_synonym"].upper() for c in t.get("target_components") or []
                          for s in c.get("target_component_synonyms") or [] if s.get("syn_type") == "GENE_SYMBOL"})
        rows.append({
            "parent_chembl_id": m["molecule_chembl_id"], "mec_id": m.get("mec_id"),
            "action_type": m.get("action_type"), "mechanism_of_action": m.get("mechanism_of_action"),
            "direct_interaction": m.get("direct_interaction"),
            "target_chembl_id": m.get("target_chembl_id"), "target_name": t.get("pref_name"),
            "target_type": t.get("target_type"), "organism": t.get("organism"),
            "gene_symbols": symbols,
            "decagon_gene_ids": sorted({symbol_to_gene[s] for s in symbols if s in symbol_to_gene}),
            "refs": [r.get("ref_url") or f"{r.get('ref_type')}:{r.get('ref_id')}" for r in m.get("mechanism_refs") or []],
        })
    return pd.DataFrame(rows)


def update_names(names: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """Thêm tên ChEMBL vào synonym; thuốc chưa có tên (pending/none) lấy pref_name làm tên hiển thị."""
    m = mapping.set_index("drug_idx")
    names = names.copy()
    for i, row in names.iterrows():
        if row["drug_idx"] not in m.index or pd.isna(m.at[row["drug_idx"], "pref_name"]):
            continue
        info = m.loc[row["drug_idx"]]
        pref = str(info["pref_name"]).lower()
        extra = [pref] + [s.lower() for s in info["chembl_synonyms"]]
        names.at[i, "synonyms"] = list(dict.fromkeys([*row["synonyms"], *extra]))[:names_mod.MAX_SYNONYMS * 2]
        if row["name_source"] in ("pending", "none"):
            names.at[i, "display_name"] = pref
            names.at[i, "name_source"] = "chembl"
            names.at[i, "needs_review"] = info["match_type"] != "exact"
    return names


def run(snap: Path | None = None, offline: bool = False) -> dict:
    snap = snap or snapshot_dir()
    structures = pd.read_parquet(snap / "drug_structures.parquet")
    drugs = pd.read_parquet(snap / "drugs.parquet")
    gene_names = pd.read_parquet(snap / "gene_names.parquet")

    mapping = map_drugs(structures, offline)
    parents = mapping["parent_chembl_id"].dropna().tolist()
    mapping = mapping.merge(parent_info(parents, offline), on="parent_chembl_id", how="left")
    mapping["chembl_synonyms"] = mapping["chembl_synonyms"].apply(lambda v: v if isinstance(v, list) else [])
    mapping.to_parquet(snap / "chembl_map.parquet", index=False)

    mec = mechanisms(parents, gene_names, offline)
    mec = mapping[["drug_idx", "parent_chembl_id"]].dropna().merge(mec, on="parent_chembl_id")
    mec.to_parquet(snap / "chembl_mechanisms.parquet", index=False)

    names = update_names(pd.read_parquet(snap / "drug_names.parquet"), mapping)
    names.to_parquet(snap / "drug_names.parquet", index=False)
    names_mod.write_report(snap, names, gene_names)

    combo = drugs[drugs["in_combo"]]
    has_mec = set(mec["drug_idx"])
    has_dt = set(drugs.loc[drugs["n_targets"] > 0, "drug_idx"])
    human = mec[mec["organism"] == "Homo sapiens"]
    decagon_targets = pd.read_parquet(snap / "drug_targets.parquet").groupby("drug_idx")["gene_id"].apply(set)
    overlap = sum(bool(set(g) & decagon_targets.get(d, set()))
                  for d, g in human.groupby("drug_idx")["decagon_gene_ids"].sum().items())
    report = {
        "created_at": utc_now(), "source": BASE, "license": "CC BY-SA 3.0",
        "combo_drugs": len(combo),
        "match_type_counts": mapping["match_type"].value_counts().to_dict(),
        "mapped_with_pref_name": int(mapping["pref_name"].notna().sum()),
        "drugs_with_mechanism": len(has_mec),
        "drugs_with_mechanism_but_no_decagon_targets": len(has_mec - has_dt),
        "drugs_with_neither": len(set(combo["drug_idx"]) - has_mec - has_dt),
        "drugs_with_human_mechanism_overlapping_decagon_targets": int(overlap),
        "mechanism_rows": len(mec),
        "action_type_counts": mec["action_type"].value_counts().to_dict(),
        "target_type_counts": mec["target_type"].value_counts().to_dict(),
        "needs_review": mapping.loc[mapping["match_type"] == "connectivity",
                                    ["stitch_id", "matched_chembl_id", "parent_chembl_id", "pref_name"]]
        .to_dict("records"),
        "unmapped": mapping.loc[mapping["match_type"] == "none", "stitch_id"].tolist(),
    }
    write_json(snap / "chembl_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    parser.add_argument("--offline", action="store_true", help="chỉ dùng cache, không gọi ChEMBL")
    args = parser.parse_args()
    r = run(args.snapshot_dir, args.offline)
    print(f"khớp ChEMBL: {r['match_type_counts']}; có pref_name: {r['mapped_with_pref_name']}")
    print(f"có cơ chế: {r['drugs_with_mechanism']}/{r['combo_drugs']} thuốc ({r['mechanism_rows']} dòng); "
          f"có cơ chế nhưng không có target Decagon: {r['drugs_with_mechanism_but_no_decagon_targets']}; "
          f"không có cả hai: {r['drugs_with_neither']}")
    print(f"action_type: {r['action_type_counts']}")


if __name__ == "__main__":
    main()
