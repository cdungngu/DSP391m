"""Hồi quy cho review 2026-10-10: metadata rò rỉ, ghi đè split, đọc split không xác minh."""
import numpy as np
import pandas as pd
import pytest

from dsp391m import dataview, splits
from dsp391m.manifest import read_json

from test_leakage import snap  # noqa: F401  (dùng lại fixture snapshot tổng hợp)


def test_prediction_view_metadata_derived_from_train_only(snap):
    view = dataview.prediction_view(snap=snap)
    train_counts = view.pair_labels["effect_idx"].value_counts()
    assert "n_rows" not in view.effects.columns
    assert (view.effects.set_index("effect_idx")["n_rows_train"] == train_counts.reindex(view.effects["effect_idx"]).fillna(0).astype(int).to_numpy()).all()
    assert "in_combo" not in view.drugs.columns
    train_drugs = set(view.pair_labels["drug_a"]) | set(view.pair_labels["drug_b"])
    assert set(view.drugs.loc[view.drugs["in_train"], "drug_idx"]) == train_drugs


def test_rerun_with_same_params_does_not_rewrite(snap):
    d = splits.split_dir(snap)
    before = {p.name: p.stat().st_mtime_ns for p in d.iterdir()}
    splits.run(snap, min_rows=20)
    assert {p.name: p.stat().st_mtime_ns for p in d.iterdir()} == before


def test_rerun_with_changed_params_refuses_same_split_id(snap):
    with pytest.raises(splits.SplitExistsError):
        splits.run(snap, min_rows=1)
    assert read_json(splits.split_dir(snap) / "split_manifest.json")["params"]["min_rows"] == 20


def test_tampered_split_file_is_rejected(snap):
    path = splits.split_dir(snap) / "pair_splits.parquet"
    pairs = pd.read_parquet(path)
    pairs.loc[pairs.index[pairs["split"] == "test"][0], "split"] = "train"
    pairs.to_parquet(path, index=False)
    with pytest.raises(splits.SplitIntegrityError):
        dataview.prediction_view(snap=snap)
    with pytest.raises(splits.SplitIntegrityError):
        dataview.load_eval_targets("val", snap=snap)


def test_split_from_other_snapshot_is_rejected(snap):
    path = snap / "pair_labels.parquet"
    labels = pd.read_parquet(path)
    labels.iloc[:-1].to_parquet(path, index=False)
    with pytest.raises(splits.SplitIntegrityError):
        dataview.prediction_view(snap=snap)


def test_cache_key_depends_on_split_content(snap):
    view = dataview.prediction_view(snap=snap)
    other = splits.run(snap, split_id="other_seed", min_rows=20, seed=7)
    view2 = dataview.prediction_view(split_id="other_seed", snap=snap)
    assert other["files"] != read_json(splits.split_dir(snap) / "split_manifest.json")["files"]
    assert view.split_hash != view2.split_hash
    assert view.cache_key("q") != view2.cache_key("q")
