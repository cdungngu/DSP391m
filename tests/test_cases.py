"""Chọn lô ca val theo quy tắc cố định (plan du_doan_cap/06)."""
import json

import numpy as np
import pandas as pd
import pytest

from dsp391m import cases, evaluate
from dsp391m.releases import read_release


def test_select_dedupes_within_group_order():
    orders = {"improve": np.array([1, 2, 3]), "decline": np.array([3, 1, 4, 5]),
              "low_degree": np.array([2, 6, 7]), "random": np.array([1, 7, 8, 9])}
    got = cases.select(orders, 2)
    assert [(g, row) for g, _, row in got] == [("improve", 1), ("improve", 2), ("decline", 3), ("decline", 4),
                                               ("low_degree", 6), ("low_degree", 7), ("random", 8), ("random", 9)]
    assert got[3][1] == 2  # thứ hạng gốc trong nhóm được giữ (bỏ qua hàng trùng)


def test_group_orders_rank_by_delta_with_deterministic_ties():
    delta = np.array([0.1, np.nan, 0.5, 0.1, -0.2])
    pairs = pd.DataFrame({"drug_a": [3, 0, 1, 2, 4], "drug_b": [9, 9, 9, 9, 9]})
    o = cases.group_orders(delta, pairs, np.array([True] * 5), seed=1)
    assert o["improve"].tolist() == [2, 3, 0, 4] and o["decline"].tolist() == [4, 3, 0, 2]
    assert 1 not in o["random"] and sorted(o["low_degree"]) == [0, 2, 3, 4]


def test_run_on_fixture(snap, tmp_path):
    res = tmp_path / "res"
    ids = [evaluate.run(m, snap=snap, results_dir=res)["model_release_id"] for m in ("popularity", "b0_alpha100")]
    r = cases.run(ids[0], ids[1], tmp_path / "c.json", per_group=2, snap=snap, results_dir=res)
    json.dumps(r, allow_nan=False)
    rows = [c["val_row"] for c in r["cases"]]
    assert len(rows) == len(set(rows)) == min(8, r["n_val_pairs_eligible"])
    deltas = [c["ndcg10_delta"] for c in r["cases"] if c["group"] == "improve"]
    assert deltas == sorted(deltas, reverse=True)
    c = r["cases"][0]
    assert len(c["models"][ids[1]]["top10"]) == 3  # fixture chỉ có 3 nhãn trong vocab
    assert all(t["observed"] == (t["effect_cui"] in {o["effect_cui"] for o in c["observed_labels"]})
               for t in c["models"][ids[1]]["top10"])
    assert read_release(tmp_path / "c.json")[0]["n_cases"] == r["n_cases"]
    again = cases.run(ids[0], ids[1], tmp_path / "c2.json", per_group=2, snap=snap, results_dir=res)
    assert [x["val_row"] for x in again["cases"]] == rows
    md = cases.render_markdown(r)
    assert md.count("## ") == r["n_cases"]
    with pytest.raises(FileExistsError):
        cases.run(ids[0], ids[1], tmp_path / "c.json", per_group=2, snap=snap, results_dir=res)
