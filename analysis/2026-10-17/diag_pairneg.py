"""Chẩn đoán nháp: âm thay nhãn (plan 05) vs thêm âm thay cặp train (không ghi kết quả chính thức)."""
import time, numpy as np, torch, torch.nn.functional as F
from pathlib import Path
from dsp391m import metrics
from dsp391m.dataview import prediction_view, load_eval_targets
from dsp391m.evaluate import cui_rank
from dsp391m.training.trainer import Trainer, TrainConfig

view = prediction_view(); pairs, y, vocab = load_eval_targets("val"); rank = cui_rank(vocab)
def evaluate(t):
    with torch.no_grad():
        s = t.model.score_all(torch.tensor(pairs.drug_a.values), torch.tensor(pairs.drug_b.values)).numpy()
    v = metrics.ModelState(y, s, rank).values()
    return f"macro AP {v['macro_ap']:.4f} pair AP {v['pair_ap']:.4f} NDCG@10 {v['ndcg@10']:.4f}"

for mode in ("label_only", "label+pair"):
    torch.manual_seed(391)
    t = Trainer(view, TrainConfig(dim=64, lr=0.03), Path("/tmp/none"), lambda f: 0)
    Y = t.sampler.y; n_pairs = len(Y)
    for ep in range(3):
        rng = np.random.default_rng([7, ep]); t0 = time.time(); tot = 0
        for rows, labels, neg, mask in t.sampler.epoch(ep):
            loss = t.loss(rows, labels, neg, mask)
            if mode == "label+pair":
                cand = rng.integers(0, n_pairs, (len(rows), 5))
                ok = ~Y[cand, labels[:, None]]
                pr = torch.from_numpy(t.train_pairs[cand])
                s_neg = t.model(pr[..., 0].reshape(-1), pr[..., 1].reshape(-1),
                                torch.from_numpy(np.repeat(labels, 5))).reshape(-1, 5)
                m = torch.from_numpy(ok).float()
                loss = loss + ((F.softplus(s_neg) * m).sum(1) / m.sum(1).clamp(min=1)).mean()
            t.opt.zero_grad(); loss.backward(); t.opt.step(); tot += float(loss)
        print(f"{mode:11s} epoch {ep} loss {tot/len(t.sampler):.4f} {evaluate(t)} ({time.time()-t0:.0f}s)", flush=True)
