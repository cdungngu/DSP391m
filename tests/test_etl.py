import pandas as pd
import pytest

from dsp391m import etl, quality
from dsp391m.manifest import read_json
from dsp391m.paths import RAW_DIR


def test_tables_are_canonical(raw_dir):
    tables, stats = etl.build_tables(etl.read_raw(raw_dir))
    drugs, labels, ppi = tables["drugs"], tables["pair_labels"], tables["ppi"]

    # Thuốc chỉ có ở targets vẫn có drug_idx nhưng không thuộc combo.
    assert drugs["stitch_id"].tolist() == [f"CID00000000{i}" for i in (1, 2, 3, 4)]
    assert drugs["in_combo"].tolist() == [True, True, True, False]
    assert drugs["pubchem_cid"].tolist() == [1, 2, 3, 4]
    assert drugs["n_targets"].tolist() == [2, 0, 0, 1]

    # Dòng (3,1) và (1,3) cùng nhãn là một cặp không thứ tự.
    assert (labels["drug_a"] < labels["drug_b"]).all()
    assert len(labels) == 4
    assert stats["combo_duplicate_or_reverse_rows_dropped"] == 1
    assert tables["effects"]["n_rows"].tolist() == [2, 2]

    # PPI: bỏ cạnh đảo chiều và cạnh tự nối.
    assert ppi.values.tolist() == [[10, 20], [10, 30]]
    assert stats["ppi_self_rows_dropped"] == 1
    assert stats["ppi_duplicate_or_reverse_rows_dropped"] == 1


def test_run_writes_manifest_and_is_deterministic(raw_dir, tmp_path):
    first = etl.run(raw_dir, tmp_path / "a")
    second = etl.run(raw_dir, tmp_path / "b")
    assert set(first["tables"]) == set(etl.TABLES)
    for name in etl.TABLES:
        assert first["tables"][name]["sha256"] == second["tables"][name]["sha256"]
    assert read_json(tmp_path / "a" / "manifest.json")["raw"]["combo"]["sha256"] == first["raw"]["combo"]["sha256"]


def test_quality_invariants_pass_and_expected_counts_skipped_for_unverified_data(raw_dir, tmp_path):
    etl.run(raw_dir, tmp_path / "snap")
    report = quality.run(tmp_path / "snap")
    assert report["passed"]
    assert not report["verified_snapshot"]
    assert {c["group"] for c in report["checks"]} == {"invariant"}


def test_quality_detects_broken_pair(raw_dir, tmp_path):
    snap = tmp_path / "snap"
    etl.run(raw_dir, snap)
    labels = pd.read_parquet(snap / "pair_labels.parquet")
    labels.loc[0, ["drug_a", "drug_b"]] = labels.loc[0, ["drug_b", "drug_a"]].to_numpy()
    labels.to_parquet(snap / "pair_labels.parquet", index=False)
    failed = {c["name"] for c in quality.run(snap)["checks"] if not c["ok"]}
    assert "pairs_canonical_a_lt_b" in failed


def test_stitch_id_parsing():
    assert etl.stitch_to_pubchem_cid("CID000002173") == 2173
    with pytest.raises(ValueError):
        etl.stitch_to_pubchem_cid("2173")


@pytest.mark.slow
def test_real_snapshot_matches_verified_facts(tmp_path):
    etl.run(RAW_DIR, tmp_path / "snap")
    report = quality.run(tmp_path / "snap")
    assert report["verified_snapshot"]
    assert report["passed"], [c for c in report["checks"] if not c["ok"]]
