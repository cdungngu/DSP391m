"""So sánh hai model trên val bằng paired bootstrap (plan du_doan_cap/03).

Chạy: python -m dsp391m.compare --base <model_release_id> --cand <model_release_id> [--bootstrap 1000]

Chỉ chạy trên val; không có tùy chọn split. Đọc score cache do `dsp391m.evaluate` ghi, xác minh checksum,
identity và thứ tự cặp, rồi dùng cùng chỉ số resample cho hai model. Kết quả ghi bất biến tại
results/val/comparisons/<run_id>.json. Phép tính dùng chung (metrics.paired_bootstrap) nhận y/score từ caller;
chỉ final runner được nạp nhãn test.
"""
import argparse
import sys
import time
from pathlib import Path

from . import metrics, predictor
from .dataview import load_eval_targets, prediction_view
from .evaluate import RESULTS_DIR, check_label_order, cui_rank, load_scores, new_run_id
from .manifest import git_commit, utc_now
from .releases import publish
from .splits import SPLIT_ID


def run(base: str, cand: str, n_boot: int = 1000, seed: int = 391, split_id: str = SPLIT_ID,
        snap: Path | None = None, results_dir: Path = RESULTS_DIR, workers: int = 1) -> dict:
    start = time.time()
    view = prediction_view(split_id, snap)
    ident = predictor.identity(view)
    pairs, y, vocab = load_eval_targets("val", split_id, snap)
    check_label_order(view, vocab)
    phash = predictor.pairs_hash(pairs)
    s_base = load_scores(results_dir, "val", base, phash, ident)
    s_cand = load_scores(results_dir, "val", cand, phash, ident)
    result = {"schema_version": 1, "split": "val", "base": base, "cand": cand, "identity": ident,
              "pairs_hash": phash, "git_commit": git_commit(), "created_at": utc_now(),
              **metrics.paired_bootstrap(y, s_base, s_cand, cui_rank(vocab), n_boot, seed, workers=workers)}
    result["workers"] = workers
    result["run_id"] = new_run_id()
    result["seconds"] = round(time.time() - start, 1)
    out = results_dir / "val" / "comparisons" / f"{result['run_id']}.json"
    publish(out, result)
    result["path"] = str(out)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True)
    parser.add_argument("--cand", required=True)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=391)
    parser.add_argument("--workers", type=int, default=metrics.default_workers(),
                        help="số tiến trình song song; không đổi kết quả (mặc định %(default)s)")
    args = parser.parse_args(argv)
    r = run(args.base, args.cand, args.bootstrap, args.seed, workers=args.workers)
    print(f"{r['cand']} - {r['base']} @ val, {r['n_resamples']} resample, {r['workers']} worker, "
          f"{r['seconds']} s -> {r['path']}")
    for k, v in r["metrics"].items():
        ci = v["ci95_delta"]
        print(f"  {k:14s} base {v['base']:.6f}  cand {v['cand']:.6f}  delta {v['delta']:+.6f}"
              + (f"  CI95 [{ci[0]:+.6f}, {ci[1]:+.6f}]" if ci else "") + f"  (n={v['n_valid']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
