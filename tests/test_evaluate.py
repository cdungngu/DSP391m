import numpy as np
import pytest

from dsp391m import dataview, evaluate
from dsp391m.models.b0 import B0


def test_undefined_metrics_are_json_null_not_nan():
    import json
    y = np.zeros((3, 2), dtype=int)
    result = evaluate.core_metrics(y, np.zeros_like(y))
    assert result["macro_ap"] is None and result["macro_auroc"] is None
    assert result["undefined_reason"] == "no_positive_labels"
    json.dumps(result, allow_nan=False)
    assert evaluate.bootstrap(y, y, 5)["macro_ap"] is None


def test_smoothing_and_pair_symmetry(snap):
    view = dataview.prediction_view(snap=snap)
    base, smoothed = B0().fit(view), B0(alpha=20).fit(view)
    n = base.n_train_pairs_per_drug[:, None]
    expected = (base.freq * n + 20 * base.popularity) / (n + 20)
    assert np.allclose(smoothed.freq, expected)
    pairs = view.pair_labels[["drug_a", "drug_b"]].drop_duplicates()
    reverse = pairs.rename(columns={"drug_a": "drug_b", "drug_b": "drug_a"})
    assert np.allclose(smoothed.score(pairs), smoothed.score(reverse))
    bad = pairs.copy()
    bad.iloc[0, 0] = -1
    with pytest.raises(ValueError):
        smoothed.score(bad)
    with pytest.raises(ValueError):
        B0(alpha=float("nan"))


def test_test_split_requires_final(snap, tmp_path):
    with pytest.raises(PermissionError):
        evaluate.run("b0_per_drug", "test", n_boot=0, snap=snap, results_dir=tmp_path)
    assert evaluate.run("b0_per_drug", "test", n_boot=0, final=True, snap=snap, results_dir=tmp_path)["split"] == "test"


def test_popularity_macro_ap_equals_mean_prevalence(snap, tmp_path):
    r = evaluate.run("b0_popularity", "val", n_boot=5, snap=snap, results_dir=tmp_path)
    _, y, _ = dataview.load_eval_targets("val", snap=snap)
    prev = y.mean(0)[y.sum(0) > 0]
    assert r["metrics"]["macro_ap"] == pytest.approx(prev.mean())
    assert r["metrics"]["macro_auroc"] == pytest.approx(0.5)
    lo, hi = r["ci95"]["macro_ap"]
    assert lo <= hi
    assert (tmp_path / "val" / "b0_popularity.json").exists()


def test_b0_uses_only_train_labels(snap):
    view = dataview.prediction_view(snap=snap)
    model = B0().fit(view)
    # Tần suất theo thuốc phải tính lại được từ nhãn train của view.
    lab = dict(zip(view.label_vocab["effect_idx"], view.label_vocab["label_idx"]))
    d = int(view.pair_labels["drug_a"].iloc[0])
    pairs = view.pair_labels[["drug_a", "drug_b"]].drop_duplicates()
    n_pairs = int(((pairs["drug_a"] == d) | (pairs["drug_b"] == d)).sum())
    rows = view.pair_labels[(view.pair_labels["drug_a"] == d) | (view.pair_labels["drug_b"] == d)]
    expected = np.bincount(rows["effect_idx"].map(lab), minlength=len(lab)) / n_pairs
    assert np.allclose(model.freq[d], expected)
    with pytest.raises(ValueError):
        B0().fit(dataview.evidence_view(snap))
