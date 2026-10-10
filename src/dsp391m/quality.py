"""Kiểm tra chất lượng snapshot đã xử lý.

Chạy: python -m dsp391m.quality [--snapshot-dir DIR]
Thoát với mã 1 nếu có kiểm tra thất bại. Kết quả ghi vào <snapshot>/qa_report.json.

Hai nhóm kiểm tra:
- invariant: luôn phải đúng với mọi snapshot (khóa hợp lệ, cặp chuẩn hóa, không trùng...).
- expected: số đếm đã kiểm chứng trong CLAUDE.md (mục "Sự thật về dữ liệu"). Chỉ áp dụng
  khi hash combo gốc khớp snapshot đã kiểm chứng; dữ liệu khác thì chỉ báo số đếm.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .etl import TABLES
from .manifest import read_json, utc_now, write_json
from .paths import snapshot_dir

VERIFIED_COMBO_SHA256 = "60bd3d071345473236f56638ebb732c3c964f0fd3468fdd29a444bcc1bf80d35"
EXPECTED = {
    "pair_label_rows": 4_649_441,
    "combo_drugs": 645,
    "labeled_pairs": 63_473,
    "effects": 1_317,
    "effects_at_least_500_rows": 963,
    "rows_in_effects_at_least_500": 4_576_287,
    "combo_drugs_with_targets": 284,
    "drug_target_rows": 18_690,
    "target_genes": 3_648,
    "target_genes_not_in_ppi": 8,
    "ppi_edges": 715_612,
    "ppi_genes": 19_081,
    "labels_per_pair_median": 53,
    "labels_per_pair_max": 540,
    "ppi_degree_median": 33,
    "ppi_degree_max": 2_519,
    "targets_per_drug_max": 2_840,
}


def load(snap: Path) -> dict[str, pd.DataFrame]:
    return {name: pd.read_parquet(snap / f"{name}.parquet") for name in TABLES}


def measure(t: dict[str, pd.DataFrame]) -> dict[str, float]:
    drugs, effects, labels, targets, ppi = (t[n] for n in TABLES)
    combo_drugs = drugs[drugs["in_combo"]]
    pair_sizes = labels.groupby(["drug_a", "drug_b"]).size()
    ppi_genes = pd.Index(np.concatenate([ppi["gene_a"], ppi["gene_b"]]))
    degree = ppi_genes.value_counts()
    target_genes = set(targets["gene_id"])
    return {
        "pair_label_rows": len(labels),
        "combo_drugs": len(combo_drugs),
        "labeled_pairs": len(pair_sizes),
        "effects": len(effects),
        "effects_at_least_500_rows": int((effects["n_rows"] >= 500).sum()),
        "rows_in_effects_at_least_500": int(effects.loc[effects["n_rows"] >= 500, "n_rows"].sum()),
        "combo_drugs_with_targets": int((combo_drugs["n_targets"] > 0).sum()),
        "drug_target_rows": len(targets),
        "target_genes": len(target_genes),
        "target_genes_not_in_ppi": len(target_genes - set(ppi_genes)),
        "ppi_edges": len(ppi),
        "ppi_genes": int(ppi_genes.nunique()),
        "labels_per_pair_median": float(pair_sizes.median()),
        "labels_per_pair_max": int(pair_sizes.max()),
        "ppi_degree_median": float(degree.median()),
        "ppi_degree_max": int(degree.max()),
        "targets_per_drug_max": int(drugs["n_targets"].max()),
        "possible_pairs": len(combo_drugs) * (len(combo_drugs) - 1) // 2,
    }


def invariants(t: dict[str, pd.DataFrame]) -> dict[str, bool]:
    drugs, effects, labels, targets, ppi = (t[n] for n in TABLES)
    n_drugs, n_effects = len(drugs), len(effects)
    combo_idx = set(drugs.loc[drugs["in_combo"], "drug_idx"])
    return {
        "drug_idx_is_0_to_n": drugs["drug_idx"].tolist() == list(range(n_drugs)),
        "stitch_id_unique": drugs["stitch_id"].is_unique,
        "effect_idx_is_0_to_n": effects["effect_idx"].tolist() == list(range(n_effects)),
        "effect_cui_unique": effects["effect_cui"].is_unique,
        "effect_name_present": bool(effects["effect_name"].notna().all()),
        "pairs_canonical_a_lt_b": bool((labels["drug_a"] < labels["drug_b"]).all()),
        "pair_drugs_valid": bool(labels["drug_b"].max() < n_drugs and labels["drug_a"].min() >= 0),
        "pair_drugs_in_combo": set(labels["drug_a"]).union(labels["drug_b"]) == combo_idx,
        "pair_effects_valid": bool(labels["effect_idx"].between(0, n_effects - 1).all()),
        "pair_labels_unique": not labels.duplicated().any(),
        "effect_n_rows_consistent": int(effects["n_rows"].sum()) == len(labels),
        "targets_unique": not targets.duplicated().any(),
        "targets_drug_valid": bool(targets["drug_idx"].between(0, n_drugs - 1).all()),
        "ppi_canonical_a_lt_b": bool((ppi["gene_a"] < ppi["gene_b"]).all()),
        "ppi_unique": not ppi.duplicated().any(),
    }


def run(snap: Path | None = None) -> dict:
    snap = snap or snapshot_dir()
    manifest = read_json(snap / "manifest.json")
    tables = load(snap)
    measured = measure(tables)
    checks = [{"group": "invariant", "name": k, "ok": bool(v)} for k, v in invariants(tables).items()]

    verified = manifest["raw"]["combo"]["sha256"] == VERIFIED_COMBO_SHA256
    if verified:
        for name, expected in EXPECTED.items():
            checks.append({"group": "expected", "name": name, "value": measured[name],
                           "expected": expected, "ok": measured[name] == expected})

    report = {
        "snapshot": manifest["snapshot"],
        "checked_at": utc_now(),
        "verified_snapshot": verified,
        "passed": all(c["ok"] for c in checks),
        "measured": measured,
        "checks": checks,
    }
    write_json(snap / "qa_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    report = run(parser.parse_args().snapshot_dir)
    failed = [c for c in report["checks"] if not c["ok"]]
    print(f"{len(report['checks']) - len(failed)}/{len(report['checks'])} checks passed"
          + ("" if report["verified_snapshot"] else " (snapshot chưa kiểm chứng: chỉ chạy invariant)"))
    for c in failed:
        print(f"FAIL [{c['group']}] {c['name']}: value={c.get('value')} expected={c.get('expected')}")
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
