"""Metric thuần và paired bootstrap (plan du_doan_cap/03)."""
import json

import numpy as np
import pytest
from sklearn.metrics import average_precision_score

from dsp391m import metrics


def _random(seed=0, n=60, m=7, ties=True):
    rng = np.random.default_rng(seed)
    y = (rng.random((n, m)) < 0.3).astype(np.int8)
    y[0] = 1  # bảo đảm mọi cột có dương
    s = rng.random((n, m))
    if ties:
        s = np.round(s, 1)
    return y, s


def test_weighted_ap_matches_sklearn_with_ties_and_weights():
    y, s = _random()
    w = np.random.default_rng(1).integers(0, 4, len(y)).astype(float)
    got = metrics.weighted_ap(metrics.sort_columns(y, s), w)
    for j in range(y.shape[1]):
        if (y[:, j] * w).sum() == 0:
            assert np.isnan(got[j])
            continue
        assert got[j] == pytest.approx(average_precision_score(y[:, j], s[:, j], sample_weight=w), abs=1e-12)
        rep = np.repeat(np.arange(len(y)), w.astype(int))
        assert got[j] == pytest.approx(average_precision_score(y[rep, j], s[rep, j]), abs=1e-12)


def test_micro_and_macro_match_sklearn():
    y, s = _random(2)
    v = metrics.ModelState(y, s, np.arange(y.shape[1])).values()
    assert v["micro_ap"] == pytest.approx(average_precision_score(y.ravel(), s.ravel()), abs=1e-12)
    assert v["macro_ap"] == pytest.approx(np.mean([average_precision_score(y[:, j], s[:, j])
                                                   for j in range(y.shape[1])]), abs=1e-12)


def test_pair_metrics_hand_computed_with_cui_tiebreak():
    # 1 cặp, 4 nhãn; nhãn 1 và 2 hòa điểm. CUI rank: nhãn 2 đứng trước nhãn 1.
    y = np.array([[0, 1, 0, 1]], dtype=np.int8)
    s = np.array([[0.9, 0.5, 0.5, 0.1]])
    cui_rank = np.array([0, 2, 1, 3])
    np.testing.assert_array_equal(metrics.topk_order(s, cui_rank), [[0, 2, 1, 3]])
    out = metrics.pair_metrics(y, s, cui_rank)
    assert out["precision@5"][0] == pytest.approx(2 / 5)
    assert out["recall@5"][0] == 1.0
    dcg = 1 / np.log2(4) + 1 / np.log2(5)
    idcg = 1 / np.log2(2) + 1 / np.log2(3)
    assert out["ndcg@10"][0] == pytest.approx(dcg / idcg)
    # AP kiểu sklearn: nhãn 1 nằm trong nhóm hòa (0.5) -> precision tại cuối nhóm = 1/3.
    assert out["pair_ap"][0] == pytest.approx(average_precision_score(y[0], s[0]))


def test_no_positive_pairs_and_labels_are_null():
    y = np.array([[1, 0], [0, 0]], dtype=np.int8)
    s = np.array([[0.2, 0.1], [0.3, 0.4]])
    r = metrics.summarize(y, s, np.arange(2))
    assert r["pairs_with_positive"] == 1 and r["labels_scored"] == 1
    json.dumps(r, allow_nan=False)
    empty = metrics.summarize(np.zeros((2, 2), np.int8), s, np.arange(2))
    assert empty["macro_ap"] is None and empty["micro_ap"] is None and empty["pair_ap"] is None
    assert empty["undefined_reason"] == "no_positive_labels"
    with pytest.raises(ValueError):
        metrics.summarize(y, np.array([[np.nan, 0], [0, 0]]), np.arange(2))
    with pytest.raises(ValueError):
        metrics.summarize(y, s, np.array([0, 0]))


def test_paired_bootstrap_identical_scores_zero_delta_and_reproducible():
    y, s = _random(3)
    r = metrics.paired_bootstrap(y, s, s.copy(), np.arange(y.shape[1]), n=20)
    for k, v in r["metrics"].items():
        assert v["delta"] == 0 and v["ci95_delta"] == [0.0, 0.0], k
    s2 = s + np.random.default_rng(4).normal(0, 0.1, s.shape)
    a = metrics.paired_bootstrap(y, s, s2, np.arange(y.shape[1]), n=20, seed=7)
    b = metrics.paired_bootstrap(y, s, s2, np.arange(y.shape[1]), n=20, seed=7)
    assert a == b
    json.dumps(a, allow_nan=False)
    assert a["metrics"]["macro_ap"]["n_valid"] == 20
