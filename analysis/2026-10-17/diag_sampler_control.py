"""Đối chứng sampler có kiểm soát: label-only vs mixed (cân 0,5/0,5), cùng seed/lr/dim/wd/số epoch.
Thăm dò phát triển phương pháp trên val, không phải run chọn model."""
import sys
import time
from pathlib import Path

from dsp391m import metrics
from dsp391m.dataview import load_eval_targets, prediction_view
from dsp391m.evaluate import cui_rank
from dsp391m.training.trainer import Trainer, TrainConfig

LR, DIM, EPOCHS = float(sys.argv[1]) if len(sys.argv) > 1 else 0.01, 64, 5
view = prediction_view()
pairs, y, vocab = load_eval_targets("val")
rank = cui_rank(vocab)
for negatives in ("label", "mixed"):
    t = Trainer(view, TrainConfig(dim=DIM, lr=LR, weight_decay=0.0, negatives=negatives), Path("/tmp/none"),
                lambda f: 0)
    for ep in range(EPOCHS):
        t0 = time.time()
        st = t.train_epoch(ep)
        v = metrics.ModelState(y, t.predictor().score_pairs(pairs), rank).values()
        print(f"{negatives:5s} lr {LR:g} epoch {ep} loss {st['loss']:.4f} macro AP {v['macro_ap']:.4f} "
              f"pair AP {v['pair_ap']:.4f} NDCG@10 {v['ndcg@10']:.4f} ({time.time() - t0:.0f}s)", flush=True)
