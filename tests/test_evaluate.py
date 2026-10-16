import numpy as np
import pytest

from dsp391m import dataview, evaluate
from dsp391m.models.b0 import B0

from test_leakage import snap  # noqa: F401


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
