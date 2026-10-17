"""Readiness và bất biến train-only (plan du_doan_cap/02)."""
import json
import shutil

import numpy as np
import pandas as pd
import pytest

from dsp391m import dataview, readiness, splits
from dsp391m.manifest import read_json, sha256, write_json
from dsp391m.models.b0 import B0
from dsp391m.releases import read_release


def test_report_counts_and_checks(snap, tmp_path):
    r = readiness.report(snap)
    json.dumps(r, allow_nan=False)
    assert r["passed"]
    pairs = pd.read_parquet(splits.split_dir(snap) / "pair_splits.parquet")
    assert r["pairs_per_split"] == pairs["split"].value_counts().to_dict()
    view = dataview.prediction_view(snap=snap)
    assert r["train_positive_cells"] == len(view.pair_labels)
    readiness.publish(tmp_path / "r.json", r)
    assert read_release(tmp_path / "r.json")[0]["passed"]


def test_train_label_matrix_matches_view(snap):
    view = dataview.prediction_view(snap=snap)
    pairs, y = dataview.train_label_matrix(view)
    lab = dict(zip(view.label_vocab["effect_idx"], view.label_vocab["label_idx"]))
    row = {tuple(p): i for i, p in enumerate(pairs.tolist())}
    expected = np.zeros_like(y)
    for r in view.pair_labels.itertuples():
        expected[row[(r.drug_a, r.drug_b)], lab[r.effect_idx]] = True
    assert np.array_equal(y, expected)
    with pytest.raises(ValueError):
        dataview.train_label_matrix(dataview.evidence_view(snap))


def _swap_heldout_labels(snap, out):
    """Bản sao snapshot chỉ khác nhãn (trong vocab) của các cặp val/test; cập nhật hash trong tmp."""
    shutil.copytree(snap, out)
    d = splits.split_dir(out)
    vocab = pd.read_parquet(d / "label_vocab.parquet")
    pairs = pd.read_parquet(d / "pair_splits.parquet")
    labels = pd.read_parquet(out / "pair_labels.parquet")
    held = labels.merge(pairs[pairs["split"] != "train"], on=["drug_a", "drug_b"], how="left")["split"].notna()
    ids = vocab["effect_idx"].tolist()
    in_vocab = labels["effect_idx"].isin(ids)
    rotate = {e: ids[(i + 1) % len(ids)] for i, e in enumerate(ids)}
    labels.loc[held & in_vocab, "effect_idx"] = labels.loc[held & in_vocab, "effect_idx"].map(rotate).astype(labels["effect_idx"].dtype)
    labels = labels.drop_duplicates(["drug_a", "drug_b", "effect_idx"])
    labels.to_parquet(out / "pair_labels.parquet", index=False)
    m = read_json(out / "manifest.json")
    m["tables"]["pair_labels"]["sha256"] = sha256(out / "pair_labels.parquet")
    write_json(out / "manifest.json", m)
    sm = read_json(d / "split_manifest.json")
    sm["snapshot_pair_labels_sha256"] = m["tables"]["pair_labels"]["sha256"]
    write_json(d / "split_manifest.json", sm)
    return held.sum()


def test_heldout_label_swap_does_not_change_training_inputs(snap, tmp_path):
    changed = _swap_heldout_labels(snap, tmp_path / "swapped")
    assert changed > 0
    a, b = dataview.prediction_view(snap=snap), dataview.prediction_view(snap=tmp_path / "swapped")
    assert not dataview.load_eval_targets("val", snap=snap)[1].tolist() == \
        dataview.load_eval_targets("val", snap=tmp_path / "swapped")[1].tolist()
    pd.testing.assert_frame_equal(a.pair_labels, b.pair_labels)
    for x, y in zip(dataview.train_label_matrix(a), dataview.train_label_matrix(b)):
        assert np.array_equal(x, y)
    assert np.array_equal(B0(alpha=100).fit(a).freq, B0(alpha=100).fit(b).freq)
