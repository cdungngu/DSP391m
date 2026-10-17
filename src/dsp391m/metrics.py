"""Metric thuần cho ma trận cặp × nhãn (plan du_doan_cap/03). Không đọc dữ liệu: caller truyền y và score.

- AP dùng quy tắc ties của sklearn: ô cùng điểm tạo một ngưỡng, precision lấy tại cuối nhóm điểm bằng nhau.
  `weighted_ap` nhận trọng số theo hàng (số lần một cặp được lấy trong bootstrap), tương đương lặp hàng.
  Sắp xếp một lần cho mỗi model, mỗi resample chỉ cộng dồn trọng số; dùng chung cho macro AP (cột = nhãn),
  micro AP (một cột gồm mọi ô) và AP theo cặp (cột = cặp).
- Top-k theo cặp: điểm giảm dần, hòa thì CUI tăng dần (khớp demo). NDCG@k nhị phân: DCG = sum y_i/log2(i+1),
  IDCG đặt min(k, số dương) nhãn đầu bằng 1. Cặp không có dương: AP/recall/precision/NDCG là NaN (null trong
  JSON) và bị loại khỏi trung bình; số đơn vị hợp lệ được báo kèm.
- Paired bootstrap: cùng chỉ số resample cho hai model, delta tính trong từng resample, CI95 percentile.
  Chỉ số resample luôn sinh tuần tự ở tiến trình cha từ một seed, rồi mới chia lô cho các worker; vì vậy kết quả
  giống hệt nhau với mọi số worker (mỗi worker cần khoảng 0,6 GB RAM trên val).
"""
import os
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from dataclasses import dataclass

import numpy as np
from sklearn.metrics import roc_auc_score

PAIR_KS = (5, 10)
NDCG_K = 10
PAIR_METRICS = ("pair_ap", "precision@5", "recall@5", "precision@10", "recall@10", "ndcg@10")
MAIN_METRICS = ("macro_ap", "micro_ap") + PAIR_METRICS


@dataclass(frozen=True)
class SortedColumns:
    order: np.ndarray  # [n, m] chỉ số hàng theo điểm giảm dần (stable)
    ys: np.ndarray     # [n, m] nhãn theo thứ tự đó
    gend: np.ndarray   # [n, m] vị trí cuối nhóm điểm bằng nhau chứa mỗi vị trí


def sort_columns(y: np.ndarray, s: np.ndarray) -> SortedColumns:
    order = np.argsort(-s, axis=0, kind="stable").astype(np.int32)
    ss = np.take_along_axis(s, order, 0)
    n = len(s)
    is_end = np.ones(ss.shape, dtype=bool)
    is_end[:-1] = ss[:-1] != ss[1:]
    idx = np.where(is_end, np.arange(n)[:, None], n)
    gend = np.minimum.accumulate(idx[::-1], axis=0)[::-1].astype(np.int32)
    return SortedColumns(order, np.take_along_axis(y, order, 0).astype(np.int8), gend)


def weighted_ap(sc: SortedColumns, w: np.ndarray) -> np.ndarray:
    """AP từng cột với trọng số hàng w (>= 0). Cột không có dương (theo trọng số) trả NaN."""
    m = sc.order.shape[1]
    if not len(sc.order):
        return np.full(m, np.nan)
    ws = w[sc.order]
    tp = sc.ys * ws
    ctp, cw = np.cumsum(tp, 0), np.cumsum(ws, 0)
    num, den = np.take_along_axis(ctp, sc.gend, 0), np.take_along_axis(cw, sc.gend, 0)
    precision = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
    total = ctp[-1]
    out = np.full(m, np.nan)
    ok = total > 0
    out[ok] = (tp[:, ok] * precision[:, ok]).sum(0) / total[ok]
    return out


def finite_mean(values) -> float | None:
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    return float(v.mean()) if len(v) else None


def weighted_mean(values: np.ndarray, w: np.ndarray) -> float | None:
    ok = np.isfinite(values)
    den = w[ok].sum()
    return float((values[ok] * w[ok]).sum() / den) if den > 0 else None


def topk_order(s: np.ndarray, cui_rank: np.ndarray) -> np.ndarray:
    """Thứ tự nhãn của từng cặp: điểm giảm dần, hòa thì CUI tăng dần."""
    return np.lexsort((np.broadcast_to(cui_rank, s.shape), -s), axis=-1)


def pair_metrics(y: np.ndarray, s: np.ndarray, cui_rank: np.ndarray) -> dict[str, np.ndarray]:
    """Metric theo từng cặp (mảng dài n_pairs); cặp không có dương là NaN."""
    n, m = y.shape
    npos = y.sum(1)
    valid = npos > 0
    out = {"pair_ap": weighted_ap(sort_columns(y.T, s.T), np.ones(m))}
    yo = np.take_along_axis(y, topk_order(s, cui_rank), 1)
    for k in PAIR_KS:
        hits = yo[:, :k].sum(1).astype(float)
        out[f"precision@{k}"] = np.where(valid, hits / k, np.nan)
        out[f"recall@{k}"] = np.divide(hits, npos, out=np.full(n, np.nan), where=valid)
    disc = 1 / np.log2(np.arange(2, NDCG_K + 2))
    dcg = (yo[:, :NDCG_K] * disc[: min(NDCG_K, m)]).sum(1)
    ideal = np.r_[0, np.cumsum(disc)][np.minimum(npos, NDCG_K)]
    out[f"ndcg@{NDCG_K}"] = np.divide(dcg, ideal, out=np.full(n, np.nan), where=valid)
    return out


def _validate(y: np.ndarray, s: np.ndarray, cui_rank: np.ndarray) -> None:
    if y.shape != s.shape or y.ndim != 2:
        raise ValueError(f"y {y.shape} và score {s.shape} phải cùng shape 2 chiều")
    if len(cui_rank) != y.shape[1] or sorted(cui_rank) != list(range(y.shape[1])):
        raise ValueError("cui_rank phải là hoán vị 0..n_nhãn-1")
    if not np.isfinite(s).all():
        raise ValueError("Score có giá trị không hữu hạn")


class ModelState:
    """Cấu trúc đã sắp xếp của một model để tính metric có trọng số nhanh trong bootstrap."""

    def __init__(self, y: np.ndarray, s: np.ndarray, cui_rank: np.ndarray):
        _validate(y, s, cui_rank)
        self.n, self.m = y.shape
        self.cui_rank = cui_rank
        self.columns = sort_columns(y, s)
        self.micro = sort_columns(y.reshape(-1, 1), s.reshape(-1, 1))
        self.pairs = pair_metrics(y, s, cui_rank)

    def column_ap(self, w: np.ndarray | None = None) -> np.ndarray:
        return weighted_ap(self.columns, np.ones(self.n) if w is None else w)

    def values(self, w: np.ndarray | None = None) -> dict:
        w = np.ones(self.n) if w is None else np.asarray(w, dtype=float)
        out = {"macro_ap": finite_mean(self.column_ap(w)),
               "micro_ap": float(v) if np.isfinite(v := weighted_ap(self.micro, np.repeat(w, self.m))[0]) else None}
        out.update({k: weighted_mean(v, w) for k, v in self.pairs.items()})
        return out


def macro_auroc(y: np.ndarray, s: np.ndarray) -> float | None:
    pos = y.sum(0)
    cols = np.where((pos > 0) & (pos < len(y)))[0]
    return finite_mean([roc_auc_score(y[:, j], s[:, j]) for j in cols])


def summarize(y: np.ndarray, s: np.ndarray, cui_rank: np.ndarray, state: ModelState | None = None) -> dict:
    state = state or ModelState(y, s, cui_rank)
    out = state.values()
    out["macro_auroc"] = macro_auroc(y, s)
    out["labels_scored"] = int((y.sum(0) > 0).sum())
    out["pairs_with_positive"] = int((y.sum(1) > 0).sum())
    out["undefined_reason"] = None if out["labels_scored"] else "no_positive_labels"
    return out


def _ci(values: list) -> list | None:
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))] if values else None


_WORKER: dict = {}


def _init_worker(y, s_base, s_cand, cui_rank) -> None:
    _WORKER["states"] = (ModelState(y, s_base, cui_rank), ModelState(y, s_cand, cui_rank))


def _eval_chunk(index_rows: np.ndarray, states=None) -> list:
    base, cand = states or _WORKER["states"]
    out = []
    for idx in index_rows:
        w = np.bincount(idx, minlength=base.n).astype(float)
        out.append((base.values(w), cand.values(w)))
    return out


def default_workers() -> int:
    return max(1, min(6, (os.cpu_count() or 2) - 2))


def paired_bootstrap(y: np.ndarray, s_base: np.ndarray, s_cand: np.ndarray, cui_rank: np.ndarray,
                     n: int = 1000, seed: int = 391, metrics: tuple = MAIN_METRICS, workers: int = 1) -> dict:
    """So sánh hai model trên cùng cặp: cùng chỉ số resample, delta = cand - base tính trong từng resample.
    workers > 1 chạy song song bằng tiến trình con; kết quả không phụ thuộc workers."""
    states = (ModelState(y, s_base, cui_rank), ModelState(y, s_cand, cui_rank))
    point_b, point_c = states[0].values(), states[1].values()
    rng = np.random.default_rng(seed)
    index = np.empty((n, len(y)), dtype=np.int32)
    for i in range(n):
        index[i] = rng.integers(0, len(y), len(y))
    if workers <= 1 or n < 2:
        values = _eval_chunk(index, states)
    else:
        del states  # giải phóng RAM của tiến trình cha trước khi worker dựng state riêng
        chunks = [c for c in np.array_split(index, min(n, workers * 4)) if len(c)]
        with ProcessPoolExecutor(workers, mp_context=get_context("spawn"), initializer=_init_worker,
                                 initargs=(y, s_base, s_cand, cui_rank)) as pool:
            values = [v for part in pool.map(_eval_chunk, chunks) for v in part]
    draws = {k: {"base": [], "cand": [], "delta": []} for k in metrics}
    for vb, vc in values:
        for k in metrics:
            if vb[k] is not None and vc[k] is not None:
                draws[k]["base"].append(vb[k])
                draws[k]["cand"].append(vc[k])
                draws[k]["delta"].append(vc[k] - vb[k])
    out = {}
    for k in metrics:
        b, c = point_b[k], point_c[k]
        out[k] = {"base": b, "cand": c, "delta": None if b is None or c is None else c - b,
                  "ci95_delta": _ci(draws[k]["delta"]), "ci95_base": _ci(draws[k]["base"]),
                  "ci95_cand": _ci(draws[k]["cand"]), "n_valid": len(draws[k]["delta"])}
    return {"n_resamples": n, "seed": seed, "unit": "pair", "metrics": out}
