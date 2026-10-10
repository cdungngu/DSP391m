"""4 test rò rỉ của GĐ1b (plan mục 6, GĐ1b) và tính đóng băng của split."""
import numpy as np
import pandas as pd
import pytest

from dsp391m import dataview, etl, splits
from dsp391m.manifest import read_json, sha256
from dsp391m.paths import snapshot_dir


@pytest.fixture
def snap(tmp_path):
    """Snapshot tổng hợp: 40 thuốc, 200 cặp, 4 nhãn (nhãn thứ 4 hiếm, nằm ngoài vocab)."""
    rng = np.random.default_rng(1)
    drugs = [f"CID{i:09d}" for i in range(1, 41)]
    all_pairs = [(a, b) for i, a in enumerate(drugs) for b in drugs[i + 1:]]
    chosen = rng.choice(len(all_pairs), 200, replace=False)
    rows = []
    for k in chosen:
        a, b = all_pairs[k]
        for e in rng.choice(3, rng.integers(1, 4), replace=False):
            rows.append((a, b, f"C000000{e}", f"effect {e}"))
    rows.append((drugs[0], drugs[1], "C0000009", "rare"))
    raw = tmp_path / "raw"
    raw.mkdir()
    pd.DataFrame(rows, columns=["STITCH 1", "STITCH 2", "Polypharmacy Side Effect", "Side Effect Name"]) \
        .to_csv(raw / "bio-decagon-combo.csv", index=False)
    pd.DataFrame({"STITCH": drugs[:5], "Gene": range(5)}).to_csv(raw / "bio-decagon-targets.csv", index=False)
    pd.DataFrame({"Gene 1": [0, 1], "Gene 2": [1, 2]}).to_csv(raw / "bio-decagon-ppi.csv", index=False)
    out = tmp_path / "snap"
    etl.run(raw, out)
    splits.run(out, min_rows=20)
    return out


def _pairs(snap):
    return pd.read_parquet(splits.split_dir(snap) / "pair_splits.parquet")


def _keys(df):
    return set(zip(df["drug_a"], df["drug_b"]))


def test_a_no_pair_in_two_splits(snap):
    pairs = _pairs(snap)
    assert not pairs.duplicated(["drug_a", "drug_b"]).any()
    by = {s: _keys(pairs[pairs["split"] == s]) for s in ("train", "val", "test")}
    assert not (by["train"] & by["val"]) and not (by["train"] & by["test"]) and not (by["val"] & by["test"])
    assert set(pairs["split"].value_counts().index) == {"train", "val", "test"}


def test_b_prediction_view_contains_only_train_pairs_and_vocab_labels(snap):
    pairs = _pairs(snap)
    view = dataview.prediction_view(snap=snap)
    assert _keys(view.pair_labels) <= _keys(pairs[pairs["split"] == "train"])
    vocab = pd.read_parquet(splits.split_dir(snap) / "label_vocab.parquet")
    assert set(view.pair_labels["effect_idx"]) <= set(vocab["effect_idx"])
    assert "rare" not in set(view.effects["effect_name"])


def test_c_prediction_view_cannot_retrieve_heldout_labels(snap):
    pairs = _pairs(snap)
    pred, evid = dataview.prediction_view(snap=snap), dataview.evidence_view(snap)
    for row in pairs[pairs["split"] != "train"].itertuples():
        assert pred.labels_for_pair(row.drug_a, row.drug_b).empty
        assert not evid.labels_for_pair(row.drug_b, row.drug_a).empty  # evidence mode vẫn thấy, kể cả đảo thứ tự


def test_d_no_cache_hit_across_modes(snap, tmp_path):
    pred, evid = dataview.prediction_view(snap=snap), dataview.evidence_view(snap)
    dataview.Cache(evid, tmp_path / "cache").set({"secret": "test label"}, "query", 1, 2)
    assert dataview.Cache(pred, tmp_path / "cache").get("query", 1, 2) is None
    assert evid.cache_key("query", 1, 2) != pred.cache_key("query", 1, 2)
    assert dataview.Cache(evid, tmp_path / "cache").get("query", 1, 2) == {"secret": "test label"}


def test_eval_targets_match_evidence_labels(snap):
    pairs, y, vocab = dataview.load_eval_targets("val", snap=snap)
    evid = dataview.evidence_view(snap)
    for i, row in enumerate(pairs.itertuples()):
        expected = set(evid.labels_for_pair(row.drug_a, row.drug_b)["effect_idx"]) & set(vocab["effect_idx"])
        assert set(vocab.loc[y[i] == 1, "effect_idx"]) == expected
    with pytest.raises(ValueError):
        dataview.load_eval_targets("train", snap=snap)


def test_split_is_deterministic(snap, tmp_path):
    first = read_json(splits.split_dir(snap) / "split_manifest.json")["files"]
    again = splits.run(snap, split_id="rerun", min_rows=20)["files"]
    assert first == again


@pytest.mark.slow
def test_official_split_is_frozen_and_leak_free():
    snap = snapshot_dir()
    d = splits.split_dir(snap)
    if not d.exists():
        pytest.skip("Chưa tạo split chính thức: chạy python -m dsp391m.splits")
    manifest = read_json(d / "split_manifest.json")
    for name, digest in manifest["files"].items():
        assert sha256(d / name) == digest, f"{name} đã thay đổi so với split đã đóng băng"
    pairs = pd.read_parquet(d / "pair_splits.parquet")
    assert not pairs.duplicated(["drug_a", "drug_b"]).any()
    view = dataview.prediction_view(snap=snap)
    assert not (_keys(view.pair_labels) & _keys(pairs[pairs["split"] != "train"]))
