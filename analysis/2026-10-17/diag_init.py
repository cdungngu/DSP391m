"""Chẩn đoán nháp: loss sau ~400 bước với các cách khởi tạo khác nhau (không ghi kết quả chính thức)."""
import torch, numpy as np
from dsp391m.dataview import prediction_view
from dsp391m.training.trainer import Trainer, TrainConfig
view = prediction_view()
for label, scale in [("xavier", None), ("normal std=0.1", 0.1), ("normal std=0.3", 0.3), ("normal std=1/sqrt(h)^(1/3)?", 0.5)]:
    t = Trainer(view, TrainConfig(dim=64, lr=0.001), __import__("pathlib").Path("/tmp/none"), lambda f: 0)
    if scale:
        torch.nn.init.normal_(t.model.drug.weight, std=scale); torch.nn.init.normal_(t.model.rel.weight, std=scale)
    it = t.sampler.epoch(0); losses = []
    for step in range(400):
        loss = t.loss(*next(it)); t.opt.zero_grad(); loss.backward(); t.opt.step(); losses.append(float(loss))
    with torch.no_grad():
        s = t.model.score_all(torch.arange(5), torch.arange(5, 10)).abs().mean().item()
    print(f"{label:28s} loss bước 0 {losses[0]:.4f}  bước 399 {losses[-1]:.4f}  |score| {s:.4f}")
