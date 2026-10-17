"""Trainer DistMult (plan du_doan_cap/05).

Chạy: python -m dsp391m.training.trainer --dim 64 --lr 0.001 --seed 391 --out results/runs/<run_id>
      [--max-epochs 50] [--purpose selection|runtime_probe] [--resume]

- Chỉ fit trên prediction view; mỗi epoch evaluator trả val macro AP qua callback (trainer không thấy nhãn val).
- Loss mỗi positive: softplus(-s_pos) + mean_j softplus(s_neg_j) (âm có mask), rồi mean theo batch.
- Early stopping: cải thiện > min_delta mới tính; hòa giữ epoch sớm hơn; dừng sau `patience` epoch không cải thiện.
- Checkpoint: last.pt để resume (trọng số, optimizer, RNG torch, best_metric, best_epoch, patience_counter,
  next_epoch, history) và best.pt để suy luận. Resume chỉ khi config, identity và code commit khớp.
- Kết thúc: xuất best thành artifact predictor (results/models/<model_release_id>), chấm val qua evaluate.run_fitted
  và ghi summary.json bất biến trong thư mục run.
"""
import argparse
import dataclasses
import json
import resource
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from .. import predictor
from ..dataview import prediction_view, train_label_matrix
from ..manifest import git_commit, utc_now
from ..models.distmult import DistMult, DistMultPredictor
from ..releases import IntegrityError, publish
from ..splits import SPLIT_ID
from .sampler import NegativeSampler

LOSS_VERSION = "pos_plus_mean_neg_v1"


@dataclass(frozen=True)
class TrainConfig:
    dim: int = 64
    lr: float = 0.001
    seed: int = 391
    batch_size: int = 2048
    n_neg: int = 5
    weight_decay: float = 1e-5
    max_epochs: int = 50
    patience: int = 5
    min_delta: float = 1e-4
    loss_version: str = LOSS_VERSION
    device: str = "cpu"

    def to_dict(self) -> dict:
        return {"model": "distmult", **dataclasses.asdict(self)}


def peak_rss_mb() -> float:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(rss / (1e6 if sys.platform == "darwin" else 1e3), 1)  # macOS: byte, Linux: KiB


class Trainer:
    def __init__(self, view, cfg: TrainConfig, out_dir: Path, val_callback):
        self.cfg, self.out, self.val_callback = cfg, out_dir, val_callback
        self.identity = predictor.identity(view)
        self.train_pairs, y = train_label_matrix(view)
        self.sampler = NegativeSampler(y, cfg.n_neg, cfg.batch_size, cfg.seed)
        torch.manual_seed(cfg.seed)
        np.random.seed(cfg.seed)
        torch.use_deterministic_algorithms(True)
        self.device = torch.device(cfg.device)
        self.model = DistMult(len(view.drugs), len(view.label_vocab), cfg.dim).to(self.device)
        self.opt = torch.optim.Adam(self.model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
        self.state = {"next_epoch": 0, "best_metric": None, "best_epoch": None, "patience_counter": 0,
                      "history": [], "stopped": None}
        self.code = git_commit()

    # --- checkpoint ------------------------------------------------------------------------------------------
    def _payload(self) -> dict:
        return {"model": self.model.state_dict(), "optimizer": self.opt.state_dict(),
                "torch_rng": torch.get_rng_state(), "state": self.state, "config": self.cfg.to_dict(),
                "identity": self.identity, "code": self.code}

    def _save(self, name: str) -> None:
        tmp = self.out / f".{name}.tmp"
        torch.save(self._payload(), tmp)
        tmp.replace(self.out / name)

    @classmethod
    def resume(cls, view, cfg: TrainConfig, out_dir: Path, val_callback) -> "Trainer":
        t = cls(view, cfg, out_dir, val_callback)
        ckpt = torch.load(out_dir / "last.pt", weights_only=False)
        if ckpt["config"] != cfg.to_dict():
            raise IntegrityError("Config khác checkpoint; không resume")
        if ckpt["identity"] != t.identity:
            raise IntegrityError("Snapshot/split/thứ tự ID khác checkpoint; không resume")
        if ckpt["code"] != t.code:
            raise IntegrityError(f"Code commit {t.code} khác checkpoint {ckpt['code']}; không resume")
        t.model.load_state_dict(ckpt["model"])
        t.opt.load_state_dict(ckpt["optimizer"])
        torch.set_rng_state(ckpt["torch_rng"])
        t.state = ckpt["state"]
        return t

    # --- huấn luyện ------------------------------------------------------------------------------------------
    def loss(self, rows, labels, neg, mask) -> torch.Tensor:
        pairs = torch.from_numpy(self.train_pairs[rows]).to(self.device)
        a, b = pairs[:, 0], pairs[:, 1]
        pos = self.model(a, b, torch.from_numpy(labels).to(self.device))
        s_neg = self.model(a, b, torch.from_numpy(neg).to(self.device))
        m = torch.from_numpy(mask).to(self.device).float()
        neg_term = (F.softplus(s_neg) * m).sum(1) / m.sum(1).clamp(min=1)
        return (F.softplus(-pos) + neg_term).mean()

    def train_epoch(self, epoch: int) -> dict:
        self.model.train()
        total, n, sampler_s, train_s, short = 0.0, 0, 0.0, 0.0, 0
        it = self.sampler.epoch(epoch)
        while True:
            t0 = time.perf_counter()
            batch = next(it, None)
            sampler_s += time.perf_counter() - t0
            if batch is None:
                break
            short += int((~batch[3]).any(1).sum())
            t0 = time.perf_counter()
            loss = self.loss(*batch)
            if not torch.isfinite(loss):
                raise FloatingPointError(f"Loss không hữu hạn ở epoch {epoch}")
            self.opt.zero_grad()
            loss.backward()
            for p in self.model.parameters():
                if not torch.isfinite(p.grad).all():
                    raise FloatingPointError(f"Gradient không hữu hạn ở epoch {epoch}")
            self.opt.step()
            train_s += time.perf_counter() - t0
            total += float(loss) * len(batch[0])
            n += len(batch[0])
        return {"loss": total / max(n, 1), "sampler_s": round(sampler_s, 2), "train_s": round(train_s, 2),
                "positives": n, "positives_with_fewer_negatives": short}

    def predictor(self) -> DistMultPredictor:
        module = DistMult(self.model.drug.num_embeddings, self.model.rel.num_embeddings, self.cfg.dim)
        module.load_state_dict({k: v.detach().cpu().clone() for k, v in self.model.state_dict().items()})
        return DistMultPredictor(module, self.cfg.to_dict(), self.identity)

    def fit(self, max_epochs: int | None = None) -> dict:
        """Huấn luyện tới max_epochs (mặc định cfg.max_epochs) hoặc early stop. Có thể gọi lại sau resume."""
        self.out.mkdir(parents=True, exist_ok=True)
        stop_at = min(max_epochs if max_epochs is not None else self.cfg.max_epochs, self.cfg.max_epochs)
        while self.state["next_epoch"] < stop_at and self.state["stopped"] is None:
            epoch = self.state["next_epoch"]
            stats = self.train_epoch(epoch)
            t0 = time.perf_counter()
            metric = float(self.val_callback(self.predictor().score_pairs))
            stats.update(epoch=epoch, val_macro_ap=metric, val_s=round(time.perf_counter() - t0, 2))
            self.state["history"].append(stats)
            best = self.state["best_metric"]
            if best is None or metric > best + self.cfg.min_delta:
                self.state.update(best_metric=metric, best_epoch=epoch, patience_counter=0)
                self.state["next_epoch"] = epoch + 1
                self._save("best.pt")
            else:
                self.state["patience_counter"] += 1
                self.state["next_epoch"] = epoch + 1
                if self.state["patience_counter"] >= self.cfg.patience:
                    self.state["stopped"] = "early_stopping"
            if self.state["next_epoch"] >= self.cfg.max_epochs and self.state["stopped"] is None:
                self.state["stopped"] = "max_epochs"
            self._save("last.pt")
        return self.state

    def best_predictor(self) -> DistMultPredictor:
        ckpt = torch.load(self.out / "best.pt", weights_only=False)
        module = DistMult(self.model.drug.num_embeddings, self.model.rel.num_embeddings, self.cfg.dim)
        module.load_state_dict(ckpt["model"])
        return DistMultPredictor(module, self.cfg.to_dict(), self.identity)


def main(argv: list[str] | None = None) -> int:
    from ..evaluate import RESULTS_DIR, run_fitted, val_macro_ap_callback
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dim", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=391)
    parser.add_argument("--max-epochs", type=int, default=50, help="trần cấu hình (early stopping vẫn áp dụng)")
    parser.add_argument("--stop-after", type=int, default=None, help="dừng sớm sau N epoch (runtime probe)")
    parser.add_argument("--purpose", choices=["selection", "runtime_probe"], default="selection")
    parser.add_argument("--threads", type=int, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    if args.threads:
        torch.set_num_threads(args.threads)
    if args.out.exists() and not args.resume:
        print(f"{args.out} đã tồn tại; dùng thư mục mới hoặc --resume", file=sys.stderr)
        return 2
    cfg = TrainConfig(dim=args.dim, lr=args.lr, seed=args.seed, max_epochs=args.max_epochs)
    start = time.time()
    t0 = time.perf_counter()
    view = prediction_view(SPLIT_ID)
    callback = val_macro_ap_callback(SPLIT_ID)
    load_s = round(time.perf_counter() - t0, 2)
    trainer = (Trainer.resume if args.resume else Trainer)(view, cfg, args.out, callback)
    state = trainer.fit(args.stop_after)
    for h in state["history"]:
        print(f"epoch {h['epoch']:2d} loss {h['loss']:.4f} val macro AP {h['val_macro_ap']:.6f} "
              f"(sampler {h['sampler_s']} s, train {h['train_s']} s, val {h['val_s']} s)")
    best = trainer.best_predictor()
    evaluation = run_fitted(best, view, start, extra={"training_run": str(args.out), "purpose": args.purpose})
    if abs(evaluation["metrics"]["macro_ap"] - state["best_metric"]) > 1e-6:
        raise IntegrityError("Model nạp lại từ best.pt cho val macro AP khác lúc huấn luyện")
    summary = {"schema_version": 1, "purpose": args.purpose, "created_at": utc_now(), "config": cfg.to_dict(),
               "identity": trainer.identity, "code": trainer.code, "state": state,
               "model_release_id": best.model_release_id, "evaluation_run": evaluation["path"],
               "val_metrics": evaluation["metrics"], "runtime": {
                   "data_load_s": load_s, "total_s": round(time.time() - start, 1), "peak_rss_mb": peak_rss_mb(),
                   "device": cfg.device, "torch": torch.__version__, "threads": torch.get_num_threads(),
                   "numpy": np.__version__}}
    publish(args.out / f"summary_{len(state['history'])}ep.json", summary)
    print(json.dumps({k: summary[k] for k in ("model_release_id", "runtime")}, ensure_ascii=False))
    print(f"best epoch {state['best_epoch']} val macro AP {state['best_metric']:.6f}; dừng: {state['stopped']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
