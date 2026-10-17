"""Bộ chấm điểm dùng chung trên val (plan du_doan_cap/03–04).

Chạy: python -m dsp391m.evaluate --model b0_alpha100 [--bootstrap 0]
      python -m dsp391m.evaluate --rescore ID [ID ...]   # dựng lại score cache val từ results/models/ (máy mới)

- Mô hình fit trên prediction view (chỉ nhãn train), rồi chấm toàn ma trận cặp × 963 nhãn của val.
  Nhãn vắng mặt là "âm giả định"; không lấy mẫu âm khi chấm.
- Metric chính: macro AP theo nhãn. Phụ: micro AP, AP theo cặp, Precision/Recall@5/10, NDCG@10, macro AUROC
  (định nghĩa trong metrics.py). So sánh hai model có CI ghép cặp: python -m dsp391m.compare.
- Test KHÔNG chấm được ở đây: chỉ python -m dsp391m.final với lock đã xác minh.
Đầu ra (không ghi đè):
- results/models/<model_release_id>/: artifact model đã fit (gitignore, sinh lại được)
- results/scores/val/<model_release_id>__<pairs_hash>.npy + .json: score cache cho compare (gitignore)
- results/val/<model_release_id>/<run_id>.json: kết quả chấm, envelope có content hash
File cũ results/val/b0_*.json (schema 1) giữ nguyên để truy vết.
"""
import argparse
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from . import metrics, predictor
from .dataview import load_eval_targets, prediction_view, train_label_matrix
from .manifest import git_commit, sha256, utc_now
from .models.b0 import B0
from .paths import ROOT
from .releases import IntegrityError, publish, read_release
from .splits import SPLIT_ID

SCHEMA_VERSION = 2
RESULTS_DIR = ROOT / "results"
MODELS = {
    "popularity": lambda: B0("popularity"),
    "b0_alpha0": lambda: B0(alpha=0),
    "b0_alpha100": lambda: B0(alpha=100),
    # Tên cũ (schema 1), cùng cấu hình nên cùng model_release_id.
    "b0_per_drug": lambda: B0(alpha=0),
    "b0_popularity": lambda: B0("popularity"),
}
TEST_REFUSED = "Test chỉ chấm qua `python -m dsp391m.final run --lock ...` sau khi khóa cấu hình trên val"


# --- API schema 1, giữ cho b0_experiment và kết quả cũ -------------------------------------------------------
def finite_mean(values):
    return metrics.finite_mean(values)


def ap_columns(y: np.ndarray, s: np.ndarray) -> np.ndarray:
    """AP từng nhãn bằng sklearn. Nhãn không có dương trả NaN."""
    out = np.full(y.shape[1], np.nan)
    for j in np.where(y.sum(0) > 0)[0]:
        out[j] = average_precision_score(y[:, j], s[:, j])
    return out


def core_metrics(y: np.ndarray, s: np.ndarray) -> dict:
    pos = y.sum(0)
    cols = np.where(pos > 0)[0]
    auc_cols = np.where((pos > 0) & (pos < len(y)))[0]
    return {
        "macro_ap": finite_mean([average_precision_score(y[:, j], s[:, j]) for j in cols]),
        "micro_ap": float(average_precision_score(y.ravel(), s.ravel())) if y.size and y.sum() else None,
        "macro_auroc": finite_mean([roc_auc_score(y[:, j], s[:, j]) for j in auc_cols]),
        "labels_scored": int(len(cols)),
        "undefined_reason": "no_positive_labels" if not len(cols) else None,
    }


def bootstrap(y: np.ndarray, s: np.ndarray, n: int, seed: int = 391) -> dict:
    rng = np.random.default_rng(seed)
    macro, micro = [], []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        yb, sb = y[idx], s[idx]
        macro.append(finite_mean(ap_columns(yb, sb)))
        micro.append(float(average_precision_score(yb.ravel(), sb.ravel())) if yb.sum() else None)
    def q(values):
        values = [v for v in values if v is not None and np.isfinite(v)]
        return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))] if values else None
    return {"n": n, "unit": "pair", "macro_ap": q(macro), "micro_ap": q(micro)}


# --- Schema 2 -------------------------------------------------------------------------------------------------
def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + os.urandom(3).hex()


def cui_rank(vocab: pd.DataFrame) -> np.ndarray:
    """Hạng CUI tăng dần của từng label_idx; dùng để phá hòa top-k."""
    cuis = vocab.sort_values("label_idx")["effect_cui"].to_numpy()
    return np.argsort(np.argsort(cuis, kind="stable"), kind="stable")


def check_label_order(view, vocab: pd.DataFrame) -> None:
    cols = ["label_idx", "effect_idx", "effect_cui"]
    if not vocab[cols].reset_index(drop=True).equals(view.label_vocab[cols].reset_index(drop=True)):
        raise RuntimeError("Thứ tự nhãn của model và bộ chấm điểm không khớp")


def store_model(model, results_dir: Path) -> Path:
    """Lưu artifact theo model_release_id; nếu đã có thì xác minh thay vì ghi đè."""
    d = results_dir / "models" / model.model_release_id
    if d.exists():
        meta = predictor.read_artifact(d)
        if meta["model_release_id"] != model.model_release_id:
            raise IntegrityError(f"{d} chứa model khác")
    else:
        model.save(d)
    return d


def _score_paths(results_dir: Path, split: str, release_id: str, phash: str) -> tuple[Path, Path]:
    base = results_dir / "scores" / split / f"{release_id}__{phash}"
    return base.with_suffix(".npy"), base.with_suffix(".json")


def save_scores(results_dir: Path, split: str, release_id: str, ident: dict, pairs: pd.DataFrame,
                s: np.ndarray) -> Path:
    phash = predictor.pairs_hash(pairs)
    npy, meta = _score_paths(results_dir, split, release_id, phash)
    if meta.exists():
        if not np.array_equal(load_scores(results_dir, split, release_id, phash, ident), s):
            raise IntegrityError(f"Score cache {npy} khác score vừa tính cho cùng model_release_id")
        return npy
    npy.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=npy.parent, prefix=".scores-", suffix=".npy")
    try:
        with os.fdopen(fd, "wb") as f:
            np.save(f, s)
        os.link(tmp, npy)
    finally:
        Path(tmp).unlink(missing_ok=True)
    publish(meta, {"model_release_id": release_id, "split": split, "identity": ident, "pairs_hash": phash,
                   "shape": list(s.shape), "dtype": str(s.dtype), "sha256": sha256(npy)})
    return npy


def load_scores(results_dir: Path, split: str, release_id: str, phash: str, ident: dict | None = None) -> np.ndarray:
    npy, meta_path = _score_paths(results_dir, split, release_id, phash)
    meta, _ = read_release(meta_path)
    if not npy.is_file() or sha256(npy) != meta["sha256"]:
        raise IntegrityError(f"Score cache thiếu hoặc bị sửa: {npy}")
    if ident is not None and meta["identity"] != ident:
        raise IntegrityError("Score cache được tạo trên snapshot/split/thứ tự ID khác")
    return np.load(npy)


def grouped(y: np.ndarray, s: np.ndarray, pairs: pd.DataFrame, view, state: metrics.ModelState) -> dict:
    out = {}
    # Nhóm tần suất nhãn: chia ba theo số dòng nhãn trong train.
    freq = view.label_vocab.merge(view.effects[["effect_idx", "n_rows_train"]], on="effect_idx")
    freq = freq.sort_values("label_idx")["n_rows_train"].to_numpy()
    bucket = np.digitize(freq, np.quantile(freq, [1 / 3, 2 / 3]))
    ap = state.column_ap()
    for b, name in enumerate(["rare", "mid", "common"]):
        m = bucket == b
        out[f"label_freq_{name}"] = {"n_labels": int(m.sum()), "n_undefined": int(np.isnan(ap[m]).sum()),
                                     "macro_ap": metrics.finite_mean(ap[m])}
    # Nhóm theo số thuốc trong cặp có target.
    has_t = view.drugs.set_index("drug_idx")["n_targets"].gt(0)
    n_t = has_t.reindex(pairs["drug_a"]).to_numpy().astype(int) + has_t.reindex(pairs["drug_b"]).to_numpy().astype(int)
    for k, name in enumerate(["no_targets", "one_has_targets", "both_have_targets"]):
        m = n_t == k
        if m.sum():
            sub = metrics.ModelState(y[m], s[m], state.cui_rank)
            v = sub.values()
            out[f"pairs_{name}"] = {"n_pairs": int(m.sum()), "macro_ap": v["macro_ap"], "ndcg@10": v["ndcg@10"]}
    # Nhóm theo cặp: bậc train nhỏ hơn của hai thuốc, và số nhãn quan sát của cặp. Ngưỡng tertile tính trên train.
    train_pairs, train_y = train_label_matrix(view)
    deg = np.bincount(train_pairs.ravel(), minlength=len(view.drugs))
    pair_deg = np.minimum(deg[pairs["drug_a"].to_numpy()], deg[pairs["drug_b"].to_numpy()])
    deg_edges = np.quantile(np.minimum(deg[train_pairs[:, 0]], deg[train_pairs[:, 1]]), [1 / 3, 2 / 3])
    n_lab_edges = np.quantile(train_y.sum(1), [1 / 3, 2 / 3])
    for key, values, edges in (("pair_min_train_degree", pair_deg, deg_edges),
                               ("pair_n_labels", y.sum(1), n_lab_edges)):
        b = np.digitize(values, edges)
        for k, name in enumerate(["low", "mid", "high"]):
            m = b == k
            entry = {"n_pairs": int(m.sum()), "train_edges": [float(e) for e in edges]}
            if m.sum():
                v = metrics.ModelState(y[m], s[m], state.cui_rank).values()
                entry.update({"macro_ap": v["macro_ap"], "pair_ap": v["pair_ap"], "ndcg@10": v["ndcg@10"]})
            out[f"{key}_{name}"] = entry
    return out


def shortcut(view, pairs: pd.DataFrame, s: np.ndarray, rank: np.ndarray, k: int = 10) -> dict:
    """Overlap top-k của cặp với top-k popularity và với hợp top-k tần suất từng thuốc (B0 alpha0, train).
    Overlap cao gợi ý model chủ yếu học tần suất; không tự chứng minh điều ngược lại."""
    prior = B0(alpha=0).fit(view)
    k = min(k, s.shape[1])
    top = metrics.topk_order(s, rank)[:, :k]
    drug_top = metrics.topk_order(prior.freq, rank)[:, :k]
    pop_top = set(metrics.topk_order(prior.popularity[None, :], rank)[0, :k])
    a, b = pairs["drug_a"].to_numpy(), pairs["drug_b"].to_numpy()
    pop = np.array([len(pop_top & set(t)) / k for t in top])
    single = np.array([len((set(drug_top[x]) | set(drug_top[y])) & set(t)) / k for t, x, y in zip(top, a, b)])
    return {"k": k, "mean_overlap_popularity_topk": float(pop.mean()),
            "mean_overlap_single_drug_topk_union": float(single.mean()),
            "share_pairs_topk_inside_single_drug_union": float((single == 1).mean())}


def evaluation_record(model, split: str, view, pairs: pd.DataFrame, y: np.ndarray, s: np.ndarray,
                      vocab: pd.DataFrame, n_boot: int = 0) -> dict:
    rank = cui_rank(vocab)
    state = metrics.ModelState(y, s, rank)
    record = {
        "schema_version": SCHEMA_VERSION, "split": split, "model": model.name,
        "model_release_id": model.model_release_id, "config_id": model.config_id, "config": model.config,
        "score_kind": model.score_kind, "identity": predictor.identity(view), "pairs_hash": predictor.pairs_hash(pairs),
        "git_commit": git_commit(), "created_at": utc_now(),
        "n_pairs": len(pairs), "n_labels": int(y.shape[1]), "positive_rate": float(y.mean()),
        "metrics": metrics.summarize(y, s, rank, state),
        "groups": grouped(y, s, pairs, view, state),
        "shortcut": shortcut(view, pairs, s, rank),
    }
    if n_boot:
        rng = np.random.default_rng(391)
        draws = [state.values(np.bincount(rng.integers(0, len(y), len(y)), minlength=len(y)).astype(float))
                 for _ in range(n_boot)]
        record["ci95"] = {"n": n_boot, "seed": 391, "unit": "pair", **{
            k: metrics._ci([d[k] for d in draws if d[k] is not None]) for k in metrics.MAIN_METRICS}}
    return record


def run_fitted(model, view, start: float | None = None, split_id: str = SPLIT_ID, snap: Path | None = None,
               results_dir: Path = RESULTS_DIR, n_boot: int = 0, extra: dict | None = None) -> dict:
    """Chấm một model đã fit trên val: lưu artifact, score cache và run bất biến."""
    start = start or time.time()
    pairs, y, vocab = load_eval_targets("val", split_id, snap)
    check_label_order(view, vocab)
    s = model.score_pairs(pairs)
    store_model(model, results_dir)
    save_scores(results_dir, "val", model.model_release_id, model.identity, pairs, s)
    result = evaluation_record(model, "val", view, pairs, y, s, vocab, n_boot) | (extra or {})
    result["run_id"] = new_run_id()
    result["seconds"] = round(time.time() - start, 1)
    out = results_dir / "val" / model.model_release_id / f"{result['run_id']}.json"
    publish(out, result)
    result["path"] = str(out)
    return result


def run(model_name: str, split: str = "val", n_boot: int = 0, split_id: str = SPLIT_ID,
        snap: Path | None = None, results_dir: Path = RESULTS_DIR) -> dict:
    if split != "val":
        raise PermissionError(TEST_REFUSED)
    start = time.time()
    view = prediction_view(split_id, snap)
    model = MODELS[model_name]().fit(view)
    return run_fitted(model, view, start, split_id, snap, results_dir, n_boot)


def rescore(release_id: str, split_id: str = SPLIT_ID, snap: Path | None = None,
            results_dir: Path = RESULTS_DIR) -> Path:
    """Dựng lại score cache val từ artifact đã commit, không ghi run mới. Dùng khi results/scores/ chưa có."""
    from .final import _loader  # final import evaluate, nên nạp muộn
    view = prediction_view(split_id, snap)
    d = results_dir / "models" / release_id
    meta = predictor.read_artifact(d, view)
    model = _loader(meta["config"]["model"])(d, view)
    if model.model_release_id != release_id:
        raise IntegrityError(f"Model nạp từ {d} có model_release_id {model.model_release_id}")
    pairs, _, vocab = load_eval_targets("val", split_id, snap)
    check_label_order(view, vocab)
    return save_scores(results_dir, "val", release_id, model.identity, pairs, model.score_pairs(pairs))


def val_macro_ap_callback(split_id: str = SPLIT_ID, snap: Path | None = None):
    """Callback cho trainer: nhận hàm score(pairs) và chỉ trả val macro AP. Nhãn val nằm trong closure của
    evaluator, trainer không nhận được nhãn."""
    pairs, y, _ = load_eval_targets("val", split_id, snap)
    ones = np.ones(len(y))

    def callback(score_fn) -> float:
        s = score_fn(pairs)
        if s.shape != y.shape or not np.isfinite(s).all():
            raise ValueError("Score val sai shape hoặc không hữu hạn")
        return metrics.finite_mean(metrics.weighted_ap(metrics.sort_columns(y, s), ones))
    return callback


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    what = parser.add_mutually_exclusive_group(required=True)
    what.add_argument("--model", choices=sorted(MODELS))
    what.add_argument("--rescore", nargs="+", metavar="ID", help="model_release_id trong results/models/")
    parser.add_argument("--split", choices=["val", "test"], default="val")
    parser.add_argument("--bootstrap", type=int, default=0, help="CI riêng một model (so sánh: dùng dsp391m.compare)")
    args = parser.parse_args(argv)
    if args.rescore:
        for rid in args.rescore:
            print(f"{rid} -> {rescore(rid)}")
        return 0
    try:
        r = run(args.model, args.split, args.bootstrap)
    except PermissionError as e:
        print(e, file=sys.stderr)
        return 2
    m = r["metrics"]
    print(f"{r['model_release_id']} @ val ({r['n_pairs']} cặp × {r['n_labels']} nhãn) -> {r['path']}")
    for k in (*metrics.MAIN_METRICS, "macro_auroc"):
        print(f"  {k:14s} {m[k]:.6f}" if m[k] is not None else f"  {k:14s} null")
    for k, v in r["groups"].items():
        print(f"  {k:28s} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
