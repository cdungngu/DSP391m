"""Kiểm tra sau khi chuyển máy: score cache dựng lại từ artifact cho cùng metric val như kết quả đã commit.

Chạy từ thư mục gốc, sau `python -m dsp391m.evaluate --rescore ...`:
  .venv/bin/python analysis/2026-10-17/verify_transfer.py
Với mỗi model trong results/models/ có run val đã commit: tính lại macro AP, micro AP, pair AP, NDCG@10 từ score cache
và so với run cũ (dung sai 1e-5, vì BLAS khác nền tảng có thể lệch ở chữ số cuối). Thoát mã 1 nếu lệch hoặc thiếu.
"""
import sys
from pathlib import Path

from dsp391m import metrics, predictor
from dsp391m.dataview import load_eval_targets, prediction_view
from dsp391m.evaluate import RESULTS_DIR, cui_rank, load_scores
from dsp391m.releases import read_release

TOL = 1e-5
KEYS = ("macro_ap", "micro_ap", "pair_ap", "ndcg@10")


def main() -> int:
    view = prediction_view()
    ident = predictor.identity(view)
    pairs, y, vocab = load_eval_targets("val")
    phash, rank = predictor.pairs_hash(pairs), cui_rank(vocab)
    bad = 0
    for d in sorted((RESULTS_DIR / "models").iterdir()):
        runs = sorted((RESULTS_DIR / "val" / d.name).glob("*.json"))
        if not runs:
            continue
        old = read_release(runs[-1])[0]["metrics"]
        try:
            new = metrics.ModelState(y, load_scores(RESULTS_DIR, "val", d.name, phash, ident), rank).values()
        except FileNotFoundError:
            print(f"THIẾU score cache {d.name}: chạy python -m dsp391m.evaluate --rescore {d.name}")
            bad += 1
            continue
        diff = max(abs(new[k] - old[k]) for k in KEYS)
        ok = diff <= TOL
        bad += not ok
        print(f"{'OK ' if ok else 'LỆCH'} {d.name}: macro AP {new['macro_ap']:.6f} (cũ {old['macro_ap']:.6f}), "
              f"NDCG@10 {new['ndcg@10']:.6f}, lệch tối đa {diff:.2e}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
