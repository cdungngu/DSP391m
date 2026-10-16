"""Validation-only smoothing experiment E08; cannot load the final test split."""
import argparse
from pathlib import Path

from .dataview import load_eval_targets, prediction_view
from .evaluate import core_metrics
from .manifest import git_commit, utc_now
from .models.b0 import B0
from .releases import publish
from .splits import SPLIT_ID


def run(out: Path, snap: Path | None = None) -> dict:
    if out.exists():
        raise FileExistsError(out)
    view = prediction_view(SPLIT_ID, snap)
    pairs, y, vocab = load_eval_targets("val", SPLIT_ID, snap)
    if not vocab["effect_cui"].equals(view.label_vocab["effect_cui"]):
        raise ValueError("Label identity/order mismatch")
    rows = []
    for alpha in (0, 5, 20, 100):
        model = B0(alpha=alpha).fit(view)
        rows.append({"alpha": alpha, **core_metrics(y, model.score(pairs))})
    best = max(r["macro_ap"] for r in rows)
    selected = min(r["alpha"] for r in rows if r["macro_ap"] >= best - 0.001)
    result = {"experiment": "E08_smoothing", "split": "val", "split_hash": view.split_hash,
              "snapshot_hash": view.snapshot_hash, "n_pairs": len(pairs), "n_labels": len(vocab),
              "created_at": utc_now(), "git_commit": git_commit(), "results": rows,
              "selected_alpha": selected, "selection_rule": "smallest alpha within 0.001 macro AP of best",
              "limitations": ["No final test evaluated", "No paired bootstrap yet",
                              "No clinical-risk interpretation", "Candidate selection, not deployment"]}
    publish(out, result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    r = run(args.out)
    for row in r["results"]:
        print(f"alpha={row['alpha']:3} macro_ap={row['macro_ap']:.6f}")
    print(f"selected_alpha={r['selected_alpha']}")


if __name__ == "__main__":
    main()
