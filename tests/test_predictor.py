"""Hợp đồng predictor chung (plan du_doan_cap/01)."""
import numpy as np
import pandas as pd
import pytest

from dsp391m import dataview, predictor
from dsp391m.models.b0 import B0, WEIGHTS
from dsp391m.releases import IntegrityError


def _val_pairs(snap):
    pairs, _, _ = dataview.load_eval_targets("val", snap=snap)
    return pairs


def test_canonical_pairs_swaps_and_keeps_row_order():
    pairs = pd.DataFrame({"drug_a": [5, 1, 3], "drug_b": [2, 4, 0]}, index=[10, 11, 12])
    out = predictor.canonical_pairs(pairs, 6)
    assert out.index.tolist() == [10, 11, 12]
    assert out.values.tolist() == [[2, 5], [1, 4], [0, 3]]
    for bad in ([[1, 1]], [[0, 6]], [[-1, 2]]):
        with pytest.raises(ValueError):
            predictor.canonical_pairs(pd.DataFrame(bad, columns=["drug_a", "drug_b"]), 6)
    with pytest.raises(ValueError):
        predictor.canonical_pairs(pd.DataFrame({"drug_a": [0.0], "drug_b": [1.0]}), 6)


def test_score_pairs_symmetric_float32_finite(snap):
    view = dataview.prediction_view(snap=snap)
    model = B0(alpha=100).fit(view)
    pairs = _val_pairs(snap)
    s = model.score_pairs(pairs)
    swapped = model.score_pairs(pairs.rename(columns={"drug_a": "drug_b", "drug_b": "drug_a"}))
    assert s.dtype == np.float32 and s.shape == (len(pairs), len(view.label_vocab))
    assert np.array_equal(s, swapped)
    with pytest.raises(ValueError):
        predictor.check_scores(np.full((1, 2), np.nan), 1, 2)


def test_ids_separate_config_from_learned_content(snap):
    view = dataview.prediction_view(snap=snap)
    a0, a100 = B0(alpha=0).fit(view), B0(alpha=100).fit(view)
    assert a0.config_id != a100.config_id and a0.model_release_id != a100.model_release_id
    again = B0(alpha=100).fit(view)
    assert again.model_release_id == a100.model_release_id
    again.freq = again.freq.copy()
    again.freq[0, 0] += 1
    again._set_release(again.identity)
    assert again.config_id == a100.config_id and again.model_release_id != a100.model_release_id


def test_save_load_roundtrip_and_tamper(snap, tmp_path):
    view = dataview.prediction_view(snap=snap)
    model = B0(alpha=20).fit(view)
    rid = model.save(tmp_path / "m")
    with pytest.raises(FileExistsError):
        model.save(tmp_path / "m")
    loaded = B0.load(tmp_path / "m", view)
    pairs = _val_pairs(snap)
    assert loaded.model_release_id == rid
    assert np.array_equal(loaded.score_pairs(pairs), model.score_pairs(pairs))
    np.savez(tmp_path / "m" / WEIGHTS, freq=model.freq * 2, popularity=model.popularity,
             n_train_pairs_per_drug=model.n_train_pairs_per_drug)
    with pytest.raises(IntegrityError):
        B0.load(tmp_path / "m", view)


def test_load_rejects_other_identity(snap, tmp_path):
    view = dataview.prediction_view(snap=snap)
    B0().fit(view).save(tmp_path / "m")
    other = view.__class__(**{**view.__dict__, "snapshot_hash": "different"})
    with pytest.raises(IntegrityError):
        B0.load(tmp_path / "m", other)
