"""Chẩn đoán: gradient dữ liệu so với thành phần weight decay của Adam ở lr 0,001 (thăm dò val, không chọn model).

Adam (không phải AdamW) cộng wd*theta vào gradient bên trong step(); .grad sau backward() là gradient dữ liệu thuần.
"""
import time
from pathlib import Path

import torch

from dsp391m.dataview import prediction_view
from dsp391m.evaluate import val_macro_ap_callback
from dsp391m.training.trainer import Trainer, TrainConfig

view = prediction_view()
cb = val_macro_ap_callback()
for wd in (1e-5, 0.0):
    t = Trainer(view, TrainConfig(dim=64, lr=0.001, weight_decay=wd), Path("/tmp/none"), cb)
    t0 = time.time()
    for step, batch in enumerate(t.sampler.epoch(0)):
        loss = t.loss(*batch)
        t.opt.zero_grad()
        loss.backward()
        if step in (0, 100, 500, 1000, 1561):
            for name, p in (("drug", t.model.drug.weight), ("rel", t.model.rel.weight)):
                print(f"wd={wd:g} bước {step:4d} {name:4s} |theta| {p.norm():.4f} |grad dữ liệu| {p.grad.norm():.2e} "
                      f"|wd*theta| {wd * p.norm():.2e}  loss {float(loss):.6f}")
        t.opt.step()
    ap = cb(t.predictor().score_pairs)
    print(f"wd={wd:g}: sau 1 epoch val macro AP {ap:.6f} ({time.time() - t0:.0f}s)\n", flush=True)
