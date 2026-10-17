"""Kiểm tra toàn val bổ sung cho lô 20 ca: độ đa dạng top-10 và tên thuốc 'ok' có dạng đáng ngờ (chỉ đọc)."""
import re

import numpy as np
import pandas as pd

from dsp391m import metrics, predictor
from dsp391m.dataview import load_eval_targets, prediction_view, train_label_matrix
from dsp391m.evaluate import RESULTS_DIR, cui_rank, load_scores
from dsp391m.paths import snapshot_dir

view = prediction_view()
pairs, y, vocab = load_eval_targets("val")
ident, phash, rank = predictor.identity(view), predictor.pairs_hash(pairs), cui_rank(vocab)
_, ytr = train_label_matrix(view)
train_freq = ytr.mean(0)
name = vocab.sort_values("label_idx")["effect_name"].to_numpy()
for mid in ("b0_alpha0-db2b9c960215", "distmult_d128-dbd218398318"):
    s = load_scores(RESULTS_DIR, "val", mid, phash, ident)
    top = metrics.topk_order(s, rank)[:, :10]
    counts = np.bincount(top.ravel(), minlength=y.shape[1])
    common = ", ".join(f"{name[j]} {counts[j] / len(y):.0%}" for j in np.argsort(-counts)[:5])
    nd = metrics.pair_metrics(y, s, rank)["ndcg@10"]
    print(f"{mid}: {int((counts > 0).sum())} nhãn khác nhau trong top-10; median tần suất train của nhãn top-10 "
          f"{np.median(train_freq[top]):.3f}; NDCG@10=0 ở {(nd == 0).mean():.1%} cặp, =1 ở {(nd == 1).mean():.1%}; "
          f"phổ biến nhất: {common}")
names = pd.read_parquet(snapshot_dir() / "drug_names.parquet")
ok = names[~names["needs_review"]]
# Chỉ các dạng chắc chắn không phải tên hoạt chất để hiển thị: nhãn đồng vị, tạp chất, điện tích, dạng bào chế/HCl.
pat = re.compile(r"(?:-d\d\b|13C|15N|impurity|\(\d?[+-]\)|\bhfa\b|\bHCl\b|\(.+\))", re.I)
sus = ok[ok["display_name"].str.contains(pat)]
print(f"Tên needs_review=False: {len(ok)}; dạng chắc chắn không phù hợp hiển thị: {len(sus)}")
print("; ".join(f"{r.stitch_id}={r.display_name}" for r in sus.itertuples()))
