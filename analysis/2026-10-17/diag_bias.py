"""Chẩn đoán nháp: 1-2 epoch với lr lớn hơn hoặc thêm bias theo nhãn (không ghi kết quả chính thức)."""
import sys, time, torch
from pathlib import Path
from dsp391m.dataview import prediction_view
from dsp391m.evaluate import val_macro_ap_callback
from dsp391m.models import distmult
from dsp391m.training.trainer import Trainer, TrainConfig

class WithBias(distmult.DistMult):
    def __init__(self, n_drugs, n_labels, dim):
        super().__init__(n_drugs, n_labels, dim)
        self.bias = torch.nn.Parameter(torch.zeros(n_labels))
    def forward(self, a, b, e):
        return super().forward(a, b, e) + self.bias[e]
    def score_all(self, a, b):
        return super().score_all(a, b) + self.bias

view = prediction_view(); cb = val_macro_ap_callback()
for name, lr, bias in [("xavier lr0.01", 0.01, False), ("bias lr0.001", 0.001, True), ("bias lr0.003", 0.003, True)]:
    torch.manual_seed(391)
    t = Trainer(view, TrainConfig(dim=64, lr=lr), Path("/tmp/none"), cb)
    if bias:
        t.model = WithBias(len(view.drugs), len(view.label_vocab), 64)
        t.opt = torch.optim.Adam(t.model.parameters(), lr=lr, weight_decay=1e-5)
    for ep in range(2):
        t0 = time.time(); st = t.train_epoch(ep)
        with torch.no_grad():
            t.model.eval(); ap = cb(lambda p: t.model.score_all(torch.tensor(p.drug_a.values), torch.tensor(p.drug_b.values)).numpy())
        print(f"{name:14s} epoch {ep} loss {st['loss']:.4f} val macro AP {ap:.4f} ({time.time()-t0:.0f}s)", flush=True)
