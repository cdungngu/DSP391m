"""Bộ chấm điểm dùng chung cho mọi phương pháp dự đoán (plan mục 6.1, D3–D5).

Chạy: python -m dsp391m.evaluate --model b0_per_drug [--split val] [--bootstrap 100]
      python -m dsp391m.evaluate --model b0_per_drug --split test --final   # chỉ khi đã khóa cấu hình

- Mô hình fit trên prediction view (chỉ nhãn train), rồi chấm toàn ma trận cặp × 963 nhãn của val/test.
  Nhãn vắng mặt là "âm giả định"; không lấy mẫu âm khi chấm.
- Metric chính: macro AP trên các nhãn có ít nhất một dương. Phụ: micro AP, macro AUROC.
- Khoảng tin cậy 95% bằng bootstrap percentile theo cặp (với AP, percentile bootstrap hơi lệch lên vì cặp
  lặp lại khi lấy mẫu; dùng để so sánh tương đối giữa các model trên cùng split). Tách kết quả theo nhóm tần suất nhãn trong train và
  theo số thuốc trong cặp có target.
Kết quả: results/<split>/<model>.json (kèm split_hash, snapshot_hash, git commit).
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from .dataview import load_eval_targets, prediction_view
from .manifest import git_commit, utc_now, write_json
from .models.b0 import B0
from .paths import ROOT
from .splits import SPLIT_ID

RESULTS_DIR = ROOT / "results"
MODELS = {"b0_per_drug": lambda: B0("per_drug"), "b0_popularity": lambda: B0("popularity")}


def ap_columns(y: np.ndarray, s: np.ndarray) -> np.ndarray:
    """AP từng nhãn bằng sklearn (xử lý điểm bằng nhau giống metric chính). Nhãn không có dương trả NaN."""
    out = np.full(y.shape[1], np.nan)
    for j in np.where(y.sum(0) > 0)[0]:
        out[j] = average_precision_score(y[:, j], s[:, j])
    return out


def core_metrics(y: np.ndarray, s: np.ndarray) -> dict:
    pos = y.sum(0)
    cols = np.where(pos > 0)[0]
    auc_cols = np.where((pos > 0) & (pos < len(y)))[0]
    return {
        "macro_ap": float(np.mean([average_precision_score(y[:, j], s[:, j]) for j in cols])),
        "micro_ap": float(average_precision_score(y.ravel(), s.ravel())),
        "macro_auroc": float(np.mean([roc_auc_score(y[:, j], s[:, j]) for j in auc_cols])),
        "labels_scored": int(len(cols)),
    }


def bootstrap(y: np.ndarray, s: np.ndarray, n: int, seed: int = 391) -> dict:
    rng = np.random.default_rng(seed)
    macro, micro = [], []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        yb, sb = y[idx], s[idx]
        macro.append(np.nanmean(ap_columns(yb, sb)))
        micro.append(average_precision_score(yb.ravel(), sb.ravel()))
    q = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]  # noqa: E731
    return {"n": n, "unit": "pair", "macro_ap": q(macro), "micro_ap": q(micro)}


def grouped(y: np.ndarray, s: np.ndarray, pairs: pd.DataFrame, view) -> dict:
    out = {}
    # Nhóm tần suất nhãn: chia ba theo số dòng nhãn trong train.
    freq = view.label_vocab.merge(view.effects[["effect_idx", "n_rows_train"]], on="effect_idx")
    freq = freq.sort_values("label_idx")["n_rows_train"].to_numpy()
    edges = np.quantile(freq, [1 / 3, 2 / 3])
    bucket = np.digitize(freq, edges)
    ap = ap_columns(y, s)
    for b, name in enumerate(["rare", "mid", "common"]):
        out[f"label_freq_{name}"] = {"labels": int((bucket == b).sum()), "macro_ap": float(np.nanmean(ap[bucket == b]))}
    # Nhóm theo số thuốc trong cặp có target.
    has_t = view.drugs.set_index("drug_idx")["n_targets"].gt(0)
    n_t = has_t.reindex(pairs["drug_a"]).to_numpy().astype(int) + has_t.reindex(pairs["drug_b"]).to_numpy().astype(int)
    for k, name in enumerate(["no_targets", "one_has_targets", "both_have_targets"]):
        m = n_t == k
        if m.sum():
            out[f"pairs_{name}"] = {"pairs": int(m.sum()), "macro_ap": float(np.nanmean(ap_columns(y[m], s[m])))}
    return out


def run(model_name: str, split: str = "val", n_boot: int = 100, final: bool = False, split_id: str = SPLIT_ID,
        snap: Path | None = None, results_dir: Path = RESULTS_DIR) -> dict:
    if split == "test" and not final:
        raise PermissionError("Tập test chỉ dùng cho đánh giá cuối: thêm --final khi cấu hình đã khóa trên val")
    start = time.time()
    view = prediction_view(split_id, snap)
    model = MODELS[model_name]().fit(view)
    pairs, y, vocab = load_eval_targets(split, split_id, snap)
    if not (vocab["label_idx"].to_numpy() == view.label_vocab["label_idx"].to_numpy()).all():
        raise RuntimeError("Thứ tự nhãn của model và bộ chấm điểm không khớp")
    s = model.score(pairs)
    result = {
        "model": model_name, "split": split, "split_id": split_id, "split_hash": view.split_hash,
        "snapshot_hash": view.snapshot_hash, "git_commit": git_commit(), "created_at": utc_now(),
        "n_pairs": len(pairs), "n_labels": int(y.shape[1]), "positive_rate": float(y.mean()),
        "metrics": core_metrics(y, s),
        "ci95": bootstrap(y, s, n_boot) if n_boot else None,
        "groups": grouped(y, s, pairs, view),
    }
    result["seconds"] = round(time.time() - start, 1)
    out = results_dir / split / f"{model_name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", choices=sorted(MODELS), required=True)
    parser.add_argument("--split", choices=["val", "test"], default="val")
    parser.add_argument("--bootstrap", type=int, default=100)
    parser.add_argument("--final", action="store_true", help="cho phép chấm trên test (chỉ một lần, khi đã khóa cấu hình)")
    args = parser.parse_args(argv)
    try:
        r = run(args.model, args.split, args.bootstrap, args.final)
    except PermissionError as e:
        print(e, file=sys.stderr)
        return 2
    m, ci = r["metrics"], r["ci95"]
    print(f"{r['model']} @ {r['split']} ({r['n_pairs']} cặp × {r['n_labels']} nhãn): "
          f"macro AP {m['macro_ap']:.4f}" + (f" [{ci['macro_ap'][0]:.4f}, {ci['macro_ap'][1]:.4f}]" if ci else "")
          + f", micro AP {m['micro_ap']:.4f}, macro AUROC {m['macro_auroc']:.4f}")
    for k, v in r["groups"].items():
        print(f"  {k:28s} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
