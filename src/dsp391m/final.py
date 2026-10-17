"""Khóa đánh giá và chấm test cuối (plan du_doan_cap/03, cổng G3). Đường duy nhất được nạp nhãn test.

Chạy:
  python -m dsp391m.final lock --models ID [ID ...] --reference ID --selection "lý do chọn" --out results/final/locks/<id>.json
  python -m dsp391m.final run --lock results/final/locks/<id>.json --run-id <run_id> [--retry-of RUN --reason "..."]

- `lock` chỉ chạy khi code đã commit và worktree sạch (ngoài results/), kể cả file untracked. Lock ghi protocol,
  định nghĩa metric, identity dữ liệu, commit, hash requirements, model_release_id + sha256 trọng số, cấu hình
  bootstrap, chính sách fallback và quyết định chọn model. Lock là release bất biến (không ghi đè).
- `run` xác minh lock, protocol, commit, worktree sạch, requirements, identity và từng artifact TRƯỚC khi nạp test;
  chỉ chấm model có trong lock; ghi results/final/<run_id>/ tạo độc quyền. Chạy lại vì lỗi kỹ thuật dùng run_id mới
  với --retry-of và --reason. Thay đổi thuật toán sau khi xem test là exploratory, không sửa kết quả chính.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from . import metrics, predictor
from .dataview import load_eval_targets, prediction_view
from .evaluate import RESULTS_DIR, check_label_order, cui_rank, evaluation_record
from .manifest import sha256, utc_now
from .models.b0 import B0
from .paths import ROOT
from .releases import IntegrityError, publish, read_release
from .splits import SPLIT_ID

PROTOCOL_VERSION = "v3-pair-ranking-1"
METRIC_DEFINITIONS = {
    "macro_ap": "Mean over labels with >=1 positive of sklearn-style AP ranking pairs per label; primary metric",
    "micro_ap": "AP over all pair x label cells",
    "pair_ap": "Mean over pairs with >=1 positive of AP ranking the labels of that pair",
    "precision@k": "hits in top-k / k, order = score desc then CUI asc; k in {5,10}",
    "recall@k": "hits in top-k / positives of the pair",
    "ndcg@10": "binary DCG@10 / IDCG@10 with deterministic order; pairs without positives excluded",
    "negatives": "unobserved cells are assumed negatives, not safety evidence",
    "bootstrap": "pairs resampled with replacement; same indices for compared models; percentile CI95",
}
FALLBACK_POLICY = "B0 alpha100 is the demo backend unless the v3 promotion rule (plan 06) passed on val"
REQUIREMENTS = ("requirements.txt", "requirements-train.txt")
IGNORED_DIRTY_PREFIXES = ("results/",)


def _loader(model_kind: str):
    if model_kind == "b0":
        return B0.load
    if model_kind == "distmult":
        from .models.distmult import DistMultPredictor
        return DistMultPredictor.load
    raise IntegrityError(f"Không có loader cho model {model_kind!r}")


def requirements_hashes(root: Path = ROOT) -> dict:
    return {name: sha256(root / name) for name in REQUIREMENTS if (root / name).exists()}


def code_state(root: Path = ROOT) -> dict:
    def git(*args):
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout
    entries = [line for line in git("status", "--porcelain", "--untracked-files=all").splitlines()
               if not line[3:].startswith(IGNORED_DIRTY_PREFIXES)]
    return {"commit": git("rev-parse", "HEAD").strip(), "dirty": bool(entries), "dirty_entries": entries[:50]}


def create_lock(out: Path, model_ids: list[str], reference: str, selection: str, n_boot: int = 1000,
                seed: int = 391, split_id: str = SPLIT_ID, snap: Path | None = None,
                results_dir: Path = RESULTS_DIR, allow_dirty: bool = False) -> dict:
    """allow_dirty chỉ dành cho test fixture; lock thật luôn yêu cầu worktree sạch."""
    code = code_state()
    if code["dirty"] and not allow_dirty:
        raise RuntimeError("Worktree chưa sạch (kể cả file untracked): commit code trước khi khóa\n"
                           + "\n".join(code["dirty_entries"]))
    if reference not in model_ids or len(set(model_ids)) != len(model_ids):
        raise ValueError("reference phải nằm trong danh sách model, không trùng model")
    view = prediction_view(split_id, snap)
    models = []
    for mid in model_ids:
        meta = predictor.read_artifact(results_dir / "models" / mid, view)
        if meta["model_release_id"] != mid:
            raise IntegrityError(f"Artifact {mid} ghi model_release_id khác")
        models.append({"model_release_id": mid, "name": meta["name"], "config": meta["config"],
                       "score_kind": meta["score_kind"], "weights_sha256": meta["weights_sha256"]})
    payload = {"protocol_version": PROTOCOL_VERSION, "created_at": utc_now(), "metric_definitions": METRIC_DEFINITIONS,
               "identity": predictor.identity(view), "code": {"commit": code["commit"], "dirty": code["dirty"],
                                                             "requirements": requirements_hashes()},
               "allow_dirty": allow_dirty, "models": models, "reference": reference,
               "bootstrap": {"n": n_boot, "seed": seed, "unit": "pair"},
               "fallback_policy": FALLBACK_POLICY, "selection_decision": selection}
    publish(out, payload)
    return payload


def verify_lock(lock: dict, view, results_dir: Path, allow_dirty: bool = False) -> list:
    """Kiểm mọi điều kiện của lock; trả các model đã nạp. Không đọc nhãn."""
    if lock["protocol_version"] != PROTOCOL_VERSION:
        raise IntegrityError(f"Protocol {lock['protocol_version']!r} khác {PROTOCOL_VERSION!r}")
    code = code_state()
    if code["commit"] != lock["code"]["commit"]:
        raise IntegrityError(f"Commit hiện tại {code['commit']} khác commit trong lock {lock['code']['commit']}")
    if code["dirty"] and not (allow_dirty and lock["allow_dirty"]):
        raise IntegrityError("Worktree có thay đổi so với commit đã khóa")
    if requirements_hashes() != lock["code"]["requirements"]:
        raise IntegrityError("requirements khác lúc khóa")
    if predictor.identity(view) != lock["identity"]:
        raise IntegrityError("Snapshot/split/thứ tự ID khác lúc khóa")
    loaded = []
    for m in lock["models"]:
        d = results_dir / "models" / m["model_release_id"]
        meta = predictor.read_artifact(d, view)
        if meta["weights_sha256"] != m["weights_sha256"] or meta["config"] != m["config"]:
            raise IntegrityError(f"Artifact {m['model_release_id']} khác lúc khóa")
        model = _loader(meta["config"]["model"])(d, view)
        if model.model_release_id != m["model_release_id"]:
            raise IntegrityError(f"Model nạp từ {d} có model_release_id khác")
        loaded.append(model)
    return loaded


def run_final(lock_path: Path, run_id: str, retry_of: str | None = None, reason: str | None = None,
              snap: Path | None = None, results_dir: Path = RESULTS_DIR, allow_dirty: bool = False,
              workers: int = 1) -> dict:
    if retry_of and not reason:
        raise ValueError("Chạy lại phải ghi --reason")
    lock, lock_hash = read_release(lock_path)
    view = prediction_view(lock["identity"]["split_id"], snap)
    models = verify_lock(lock, view, results_dir, allow_dirty)
    out = results_dir / "final" / run_id
    out.mkdir(parents=True, exist_ok=False)
    pairs, y, vocab = load_eval_targets("test", lock["identity"]["split_id"], snap)
    check_label_order(view, vocab)
    scores = {m.model_release_id: m.score_pairs(pairs) for m in models}
    records = {m.model_release_id: evaluation_record(m, "test", view, pairs, y, scores[m.model_release_id], vocab)
               for m in models}
    ref = lock["reference"]
    b = lock["bootstrap"]
    comparisons = {mid: metrics.paired_bootstrap(y, scores[ref], s, cui_rank(vocab), b["n"], b["seed"],
                                                   workers=workers)
                   for mid, s in scores.items() if mid != ref}
    result = {"run_id": run_id, "lock_path": str(lock_path), "lock_content_hash": lock_hash, "retry_of": retry_of,
              "reason": reason, "created_at": utc_now(), "reference": ref, "models": records,
              "comparisons_vs_reference": comparisons}
    publish(out / "results.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    lk = sub.add_parser("lock")
    lk.add_argument("--models", nargs="+", required=True)
    lk.add_argument("--reference", required=True)
    lk.add_argument("--selection", required=True)
    lk.add_argument("--bootstrap", type=int, default=1000)
    lk.add_argument("--out", type=Path, required=True)
    rn = sub.add_parser("run")
    rn.add_argument("--lock", type=Path, required=True)
    rn.add_argument("--run-id", required=True)
    rn.add_argument("--retry-of")
    rn.add_argument("--reason")
    rn.add_argument("--workers", type=int, default=metrics.default_workers(), help="không đổi kết quả")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "lock":
            create_lock(args.out, args.models, args.reference, args.selection, args.bootstrap)
            print(f"Đã khóa {len(args.models)} model -> {args.out}")
        else:
            r = run_final(args.lock, args.run_id, args.retry_of, args.reason, workers=args.workers)
            print(f"Final {r['run_id']}: {len(r['models'])} model -> results/final/{r['run_id']}/results.json")
    except (RuntimeError, IntegrityError, ValueError, FileExistsError) as e:
        print(e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
