"""ETL chỉ đọc: ba CSV Decagon gốc -> bảng Parquet chuẩn hóa + manifest.

Chạy: python -m dsp391m.etl [--raw-dir DIR] [--out-dir DIR]

Bảng đầu ra (khóa nội bộ ổn định, sắp theo ID gốc):
- drugs:        drug_idx, stitch_id, pubchem_cid, in_combo, n_targets
- effects:      effect_idx, effect_cui, effect_name, n_rows
- pair_labels:  drug_a, drug_b (drug_a < drug_b), effect_idx  -- cặp không thứ tự
- drug_targets: drug_idx, gene_id
- ppi:          gene_a, gene_b (gene_a < gene_b)

ETL không lọc nhãn theo tần suất và không chia tập: các bước đó thuộc GĐ1b,
sau khi giao thức đánh giá (plan mục 5.1) được chốt.
"""
import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .manifest import git_commit, sha256, utc_now, write_json
from .paths import RAW_DIR, snapshot_dir

RAW_FILES = {
    "combo": "bio-decagon-combo.csv",
    "targets": "bio-decagon-targets.csv",
    "ppi": "bio-decagon-ppi.csv",
}
TABLES = ("drugs", "effects", "pair_labels", "drug_targets", "ppi")


def read_raw(raw_dir: Path) -> dict[str, pd.DataFrame]:
    combo = pd.read_csv(raw_dir / RAW_FILES["combo"], dtype="category")
    combo.columns = ["stitch_1", "stitch_2", "effect_cui", "effect_name"]
    targets = pd.read_csv(raw_dir / RAW_FILES["targets"], dtype={0: str, 1: np.int64})
    targets.columns = ["stitch_id", "gene_id"]
    ppi = pd.read_csv(raw_dir / RAW_FILES["ppi"], dtype=np.int64)
    ppi.columns = ["gene_1", "gene_2"]
    return {"combo": combo, "targets": targets, "ppi": ppi}


def stitch_to_pubchem_cid(stitch_id: str) -> int:
    """`CID000002173` -> 2173. Đây là giả định của Decagon; mapping cấu trúc kiểm tra lại từng trường hợp."""
    if not stitch_id.startswith("CID"):
        raise ValueError(f"STITCH ID không đúng định dạng: {stitch_id!r}")
    return int(stitch_id[3:])


def build_tables(raw: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict]:
    combo, targets, ppi = raw["combo"], raw["targets"], raw["ppi"]
    stats: dict = {}

    combo_drugs = set(combo["stitch_1"].astype(str)) | set(combo["stitch_2"].astype(str))
    target_drugs = set(targets["stitch_id"])
    drug_ids = sorted(combo_drugs | target_drugs)
    drug_index = pd.Index(drug_ids)

    effect_cuis = sorted(combo["effect_cui"].astype(str).unique())
    effect_index = pd.Index(effect_cuis)

    # Cặp không thứ tự: drug_a < drug_b theo drug_idx.
    a = drug_index.get_indexer(combo["stitch_1"].astype(str)).astype(np.int32)
    b = drug_index.get_indexer(combo["stitch_2"].astype(str)).astype(np.int32)
    e = effect_index.get_indexer(combo["effect_cui"].astype(str)).astype(np.int16)
    stats["combo_self_rows_dropped"] = int((a == b).sum())
    keep = a != b
    pair_labels = pd.DataFrame(
        {"drug_a": np.minimum(a, b)[keep], "drug_b": np.maximum(a, b)[keep], "effect_idx": e[keep]}
    )
    before = len(pair_labels)
    pair_labels = pair_labels.drop_duplicates().sort_values(["drug_a", "drug_b", "effect_idx"])
    stats["combo_duplicate_or_reverse_rows_dropped"] = before - len(pair_labels)
    pair_labels = pair_labels.reset_index(drop=True)

    names = combo[["effect_cui", "effect_name"]].drop_duplicates().astype(str)
    stats["effects_with_multiple_names"] = int(names["effect_cui"].duplicated().sum())
    names = names.drop_duplicates("effect_cui").set_index("effect_cui")["effect_name"]
    effects = pd.DataFrame({"effect_idx": np.arange(len(effect_cuis), dtype=np.int16), "effect_cui": effect_cuis})
    effects["effect_name"] = effects["effect_cui"].map(names)
    effects["n_rows"] = np.bincount(pair_labels["effect_idx"], minlength=len(effect_cuis)).astype(np.int64)

    drug_targets = pd.DataFrame(
        {"drug_idx": drug_index.get_indexer(targets["stitch_id"]).astype(np.int32), "gene_id": targets["gene_id"]}
    )
    before = len(drug_targets)
    drug_targets = drug_targets.drop_duplicates().sort_values(["drug_idx", "gene_id"]).reset_index(drop=True)
    stats["target_duplicate_rows_dropped"] = before - len(drug_targets)

    g1, g2 = ppi["gene_1"].to_numpy(), ppi["gene_2"].to_numpy()
    stats["ppi_self_rows_dropped"] = int((g1 == g2).sum())
    keep = g1 != g2
    ppi_out = pd.DataFrame({"gene_a": np.minimum(g1, g2)[keep], "gene_b": np.maximum(g1, g2)[keep]})
    before = len(ppi_out)
    ppi_out = ppi_out.drop_duplicates().sort_values(["gene_a", "gene_b"]).reset_index(drop=True)
    stats["ppi_duplicate_or_reverse_rows_dropped"] = before - len(ppi_out)

    drugs = pd.DataFrame({"drug_idx": np.arange(len(drug_ids), dtype=np.int32), "stitch_id": drug_ids})
    drugs["pubchem_cid"] = drugs["stitch_id"].map(stitch_to_pubchem_cid).astype(np.int64)
    drugs["in_combo"] = drugs["stitch_id"].isin(combo_drugs)
    drugs["n_targets"] = np.bincount(drug_targets["drug_idx"], minlength=len(drug_ids)).astype(np.int32)

    tables = {"drugs": drugs, "effects": effects, "pair_labels": pair_labels, "drug_targets": drug_targets, "ppi": ppi_out}
    return tables, stats


def run(raw_dir: Path = RAW_DIR, out_dir: Path | None = None) -> dict:
    out_dir = out_dir or snapshot_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()

    raw_hashes = {name: sha256(raw_dir / fname) for name, fname in RAW_FILES.items()}
    tables, stats = build_tables(read_raw(raw_dir))

    outputs = {}
    for name in TABLES:
        path = out_dir / f"{name}.parquet"
        tables[name].to_parquet(path, index=False)
        outputs[name] = {"file": path.name, "rows": len(tables[name]), "sha256": sha256(path)}

    manifest = {
        "snapshot": out_dir.name,
        "created_at": utc_now(),
        "git_commit": git_commit(),
        "raw": {name: {"file": RAW_FILES[name], "sha256": h} for name, h in raw_hashes.items()},
        "tables": outputs,
        "etl_stats": stats,
        "seconds": round(time.time() - start, 1),
    }
    write_json(out_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()
    manifest = run(args.raw_dir, args.out_dir)
    for name, info in manifest["tables"].items():
        print(f"{name:13s} {info['rows']:>10,d} rows")
    print(f"manifest -> {(args.out_dir or snapshot_dir()) / 'manifest.json'} ({manifest['seconds']}s)")


if __name__ == "__main__":
    main()
