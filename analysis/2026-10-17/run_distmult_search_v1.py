"""Điều phối search DistMult v1 theo đăng ký results/experiments/2026-10-17_distmult_search_v1_registration.json.

Chạy từ thư mục gốc: .venv/bin/python analysis/2026-10-17/run_distmult_search_v1.py
- 4 cấu hình seed 391, mỗi cấu hình một tiến trình trainer riêng (peak RSS có nghĩa); run lỗi vẫn được ghi.
- Chọn cấu hình bằng quy tắc đã đăng ký, chạy thêm seed 392/393, rồi paired compare seed391 với hai mốc.
- Ghi registry và model_selection bất biến; không chấm test. Chạy lại: thư mục run đã có thì tái dùng summary.
"""
import glob
import subprocess
import sys
import time
from pathlib import Path

from dsp391m import compare
from dsp391m.manifest import git_commit, utc_now
from dsp391m.metrics import default_workers
from dsp391m.releases import publish, read_release

REG = Path("results/experiments/2026-10-17_distmult_search_v1_registration.json")
RUNS = Path("results/runs")
PREFIX = "2026-10-17_search_v1"


def train(dim: int, lr: float, seed: int) -> dict:
    out = RUNS / f"{PREFIX}_d{dim}_lr{lr:g}_s{seed}"
    entry = {"dim": dim, "lr": lr, "seed": seed, "run_dir": str(out)}
    if not out.exists():
        t0 = time.time()
        p = subprocess.run([sys.executable, "-m", "dsp391m.training.trainer", "--dim", str(dim), "--lr", str(lr),
                            "--seed", str(seed), "--negatives", "mixed", "--weight-decay", "0", "--out", str(out)],
                           capture_output=True, text=True)
        (out.parent / f"{out.name}.log").write_text(p.stdout + p.stderr)
        entry["wall_s"] = round(time.time() - t0, 1)
        if p.returncode:
            entry.update(status="failed", returncode=p.returncode, error_tail=(p.stdout + p.stderr)[-2000:])
            print(f"FAILED {out.name}", flush=True)
            return entry
    summaries = sorted(glob.glob(str(out / "summary_*.json")))
    if not summaries:
        return entry | {"status": "failed", "error_tail": "no summary (interrupted?)"}
    s, _ = read_release(Path(summaries[-1]))
    m = s["val_metrics"]
    entry.update(status="done", model_release_id=s["model_release_id"], best_epoch=s["state"]["best_epoch"],
                 epochs_run=len(s["state"]["history"]), stopped=s["state"]["stopped"], runtime=s["runtime"],
                 val={k: m[k] for k in ("macro_ap", "micro_ap", "pair_ap", "precision@5", "recall@10", "ndcg@10")})
    print(f"{out.name}: macro AP {m['macro_ap']:.6f} NDCG@10 {m['ndcg@10']:.6f} best epoch {entry['best_epoch']} "
          f"({entry['epochs_run']} epoch, {s['runtime']['total_s']} s)", flush=True)
    return entry


def main() -> int:
    reg, reg_hash = read_release(REG)
    rule = reg["promotion_rule"]
    grid = [train(c["dim"], c["lr"], 391) for c in reg["grid_seed391"]]
    done = [g for g in grid if g["status"] == "done"]
    if not done:
        print("Không cấu hình nào chạy xong", file=sys.stderr)
        return 1
    best = max(g["val"]["macro_ap"] for g in done)
    chosen = min((g for g in done if g["val"]["macro_ap"] >= best - 0.001), key=lambda g: (g["dim"], g["lr"]))
    seeds = [chosen] + [train(chosen["dim"], chosen["lr"], s) for s in reg["stability_seeds"]]
    ok_seeds = [s for s in seeds if s["status"] == "done"]

    workers = default_workers()
    cmp_macro = compare.run(rule["macro_ap_reference"], chosen["model_release_id"], 1000, 391, workers=workers)
    cmp_ndcg = compare.run(rule["ndcg_reference"], chosen["model_release_id"], 1000, 391, workers=workers)
    ref_macro = cmp_macro["metrics"]["macro_ap"]["base"]
    ref_ndcg = cmp_ndcg["metrics"]["ndcg@10"]["base"]
    deltas = [s["val"]["macro_ap"] - ref_macro for s in ok_seeds]
    mean_ndcg = sum(s["val"]["ndcg@10"] for s in ok_seeds) / len(ok_seeds)
    ndcg_ci = cmp_ndcg["metrics"]["ndcg@10"]["ci95_delta"]
    checks = {
        "three_seeds_completed": len(ok_seeds) == 3,
        "all_seeds_macro_ap_delta_gt_0": all(d > 0 for d in deltas),
        "mean_macro_ap_delta_ge_0.005": sum(deltas) / len(deltas) >= rule["mean_macro_ap_delta_ge"],
        "seed391_ci95_macro_ap_lower_gt_0": cmp_macro["metrics"]["macro_ap"]["ci95_delta"][0] > 0,
        "mean_ndcg10_ge_alpha0_minus_0.005": mean_ndcg >= ref_ndcg - 0.005,
    }
    promoted = all(checks.values())
    selection = {
        "experiment": reg["experiment"], "registration": str(REG), "registration_hash": reg_hash,
        "created_at": utc_now(), "git_commit": git_commit(), "grid_seed391": grid, "chosen_config":
        {"dim": chosen["dim"], "lr": chosen["lr"]}, "seeds": seeds,
        "references": {"macro_ap": {"id": rule["macro_ap_reference"], "value": ref_macro},
                       "ndcg10": {"id": rule["ndcg_reference"], "value": ref_ndcg}},
        "macro_ap_delta_per_seed": deltas, "mean_ndcg10": mean_ndcg,
        "comparisons": {"vs_macro_ref": cmp_macro["path"], "vs_ndcg_ref": cmp_ndcg["path"]},
        "seed391_ci95": {"macro_ap_delta": cmp_macro["metrics"]["macro_ap"]["ci95_delta"],
                         "ndcg10_delta_vs_alpha0": ndcg_ci},
        "noninferiority_ndcg_claim_allowed": ndcg_ci[0] > -0.005,
        "checks": checks, "promoted": promoted,
        "demo_backend": chosen["model_release_id"] if promoted else rule["demo_backend_if_not_promoted"],
        "note": "Thăm dò trước đó đã nhìn val; xem registration.status_of_prior_work. Không chấm test.",
    }
    publish(Path(f"results/experiments/{PREFIX}_model_selection.json"), selection)
    print(f"Chọn dim {chosen['dim']} lr {chosen['lr']:g}; promotion {promoted}; checks {checks}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
