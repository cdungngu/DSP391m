"""Chấm bộ xếp nhãn của repo Pancasel/dsp (commit 0288b52) trên split val của DSP391m, cùng evaluator v3.

Chạy từ thư mục gốc (cần score cache val: python -m dsp391m.evaluate --rescore ...):
  .venv/bin/python analysis/2026-10-17/pancasel_scorer_val.py
Đếm nhãn chỉ trên prediction_view (train). Đây là thăm dò trên val, không phải run chọn model; không chạm test.
- pancasel_graph: điểm Tier 3 / A3 "graph" của họ = 1e6·[cả hai thuốc có nhãn] + count_A + count_B (count thô)
- pancasel_graph_norm: count / tổng cạnh train của thuốc (A3 "graph_norm")
- ablation: tách phần đóng góp (count thô, cờ in_both, bậc cặp, B0 alpha0 nhân bậc cặp)
"""
import numpy as np

from dsp391m import metrics, predictor
from dsp391m.dataview import load_eval_targets, prediction_view, train_label_matrix
from dsp391m.evaluate import RESULTS_DIR, cui_rank, load_scores

OURS = {"B0 alpha0": "b0_alpha0-db2b9c960215", "B0 alpha100": "b0_alpha100-60eb89cd5f55",
        "DistMult d128 s391": "distmult_d128-dbd218398318", "popularity": "b0_popularity-c9cb1df52e07"}


def main() -> None:
    view = prediction_view()
    train_pairs, y_train = train_label_matrix(view)
    n_drugs = len(view.drugs)
    count = np.zeros((n_drugs, y_train.shape[1]))
    np.add.at(count, train_pairs[:, 0], y_train)
    np.add.at(count, train_pairs[:, 1], y_train)
    degree = np.bincount(train_pairs.ravel(), minlength=n_drugs).astype(float)  # số cặp train của thuốc
    edges = np.maximum(count.sum(1, keepdims=True), 1)

    pairs, y, vocab = load_eval_targets("val")
    a, b = pairs["drug_a"].to_numpy(), pairs["drug_b"].to_numpy()
    ca, cb = count[a], count[b]
    ident, phash = predictor.identity(view), predictor.pairs_hash(pairs)
    ours = {k: load_scores(RESULTS_DIR, "val", rid, phash, ident).astype(np.float64) for k, rid in OURS.items()}
    scores = {
        "pancasel_graph (1e6·in_both + count)": ((ca > 0) & (cb > 0)) * 1e6 + ca + cb,
        "pancasel_graph_norm (count/cạnh)": ca / edges[a] + cb / edges[b],
        **ours,
        "ablation: count thô (ca+cb)": ca + cb,
        "ablation: chỉ in_both": ((ca > 0) & (cb > 0)).astype(float),
        "ablation: bậc A·bậc B (mọi nhãn như nhau)": np.repeat((degree[a] * degree[b])[:, None], y.shape[1], 1),
        "ablation: B0 alpha0 × (bậc A + bậc B)": ours["B0 alpha0"] * (degree[a] + degree[b])[:, None],
    }
    rank = cui_rank(vocab)
    print(f"{'model':44s} macroAP microAP pairAP  P@5    P@10   R@10   NDCG@10")
    for k, s in scores.items():
        m = metrics.ModelState(y, s, rank).values()
        print(f"{k:44s} {m['macro_ap']:.4f}  {m['micro_ap']:.4f}  {m['pair_ap']:.4f}  {m['precision@5']:.4f} "
              f"{m['precision@10']:.4f} {m['recall@10']:.4f} {m['ndcg@10']:.4f}")


if __name__ == "__main__":
    main()
