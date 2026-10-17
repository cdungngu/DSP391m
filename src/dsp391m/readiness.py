"""Báo cáo sẵn sàng dữ liệu trước huấn luyện (plan du_doan_cap/02).

Chạy: python -m dsp391m.readiness --out results/readiness/<id>.json

Chỉ đọc split qua load_verified_split và nhãn qua prediction_view (train); không đọc nhãn val/test, chỉ danh
sách cặp. Hash sai thì dừng (fail closed). Ghi bất biến bằng releases.publish; thoát mã 1 nếu có kiểm tra thất bại.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

from . import predictor
from .dataview import prediction_view, train_label_matrix
from .manifest import read_json, utc_now
from .paths import snapshot_dir
from .releases import publish
from .splits import SPLIT_ID, load_verified_split, split_dir

PREPROCESSING_VERSION = "readiness_v1"


def _quantiles(x: np.ndarray) -> dict:
    q = np.percentile(x, [0, 25, 50, 75, 100]) if len(x) else [None] * 5
    return dict(zip(["min", "p25", "median", "p75", "max"], [None if v is None else float(v) for v in q]))


def report(snap: Path | None = None, split_id: str = SPLIT_ID) -> dict:
    snap = snap or snapshot_dir()
    view = prediction_view(split_id, snap)
    _, pairs, _ = load_verified_split(snap, split_id)
    train_pairs, y = train_label_matrix(view)
    n_drugs = len(view.drugs)
    keys = {s: set(zip(g["drug_a"], g["drug_b"])) for s, g in pairs.groupby("split", observed=True)}
    deg = np.bincount(train_pairs.ravel(), minlength=n_drugs)
    held = pairs[pairs["split"] != "train"]
    untrained = (deg[held["drug_a"].to_numpy()] == 0) | (deg[held["drug_b"].to_numpy()] == 0)
    label_pos = y.sum(0)
    per_pair = y.sum(1)
    checks = {
        "no_pair_in_two_splits": not (keys["train"] & keys["val"] or keys["train"] & keys["test"]
                                      or keys["val"] & keys["test"]),
        "no_duplicate_pairs": not pairs.duplicated(["drug_a", "drug_b"]).any(),
        "no_self_pairs": bool((pairs["drug_a"] != pairs["drug_b"]).all()),
        "pairs_canonical": bool((pairs["drug_a"] < pairs["drug_b"]).all()),
        "train_matrix_matches_view": int(y.sum()) == len(view.pair_labels),
        "every_train_pair_has_label": bool((per_pair > 0).all()),
    }
    manifest = read_json(split_dir(snap, split_id) / "split_manifest.json")
    return {
        "schema_version": 1, "preprocessing_version": PREPROCESSING_VERSION, "created_at": utc_now(),
        "identity": predictor.identity(view),
        "pairs_per_split": {s: len(k) for s, k in keys.items()},
        "train_positive_cells": int(y.sum()),
        "drugs": {"n": n_drugs, "train_degree_zero": int((deg == 0).sum()), "train_degree_lt10": int((deg < 10).sum()),
                  "train_degree": _quantiles(deg)},
        "heldout_pairs_with_untrained_drug": {s: int(untrained[(held["split"] == s).to_numpy()].sum())
                                              for s in ("val", "test")},
        "labels": {"n": int(y.shape[1]), "train_positive_zero": int((label_pos == 0).sum()),
                   "train_positive_pairs": _quantiles(label_pos)},
        "labels_per_train_pair": _quantiles(per_pair),
        "vocabulary_note": ("963 nhãn chọn bằng ngưỡng >=500 dòng trên toàn snapshot (quy ước lịch sử); fit mô hình "
                            "chỉ dùng train. Sensitivity ngưỡng chỉ tính trên train: "
                            f"{manifest['sensitivity_train_only_vocab_size']} nhãn."),
        "assumed_negatives": "Ô cặp × nhãn không quan sát được coi là âm giả định khi chấm, không phải an toàn.",
        "checks": checks, "passed": all(checks.values()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--split-id", default=SPLIT_ID)
    args = parser.parse_args(argv)
    r = report(split_id=args.split_id)
    publish(args.out, r)
    print(f"{args.out}: cặp {r['pairs_per_split']}; thuốc bậc train 0: {r['drugs']['train_degree_zero']}; "
          f"cặp held-out có thuốc chưa học: {r['heldout_pairs_with_untrained_drug']}; "
          f"nhãn không có dương train: {r['labels']['train_positive_zero']}")
    for k, ok in r["checks"].items():
        print(f"  {'OK  ' if ok else 'FAIL'} {k}")
    return 0 if r["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
