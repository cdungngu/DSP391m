"""GĐ2: tra cứu bằng chứng, gồm ba trường hợp thiếu dữ liệu phải tách riêng."""
import json

import pandas as pd
import pytest

from dsp391m import etl, lookup
from dsp391m.dataview import evidence_view, prediction_view
from dsp391m import splits

# Fixture conftest.raw_dir: thuốc 1,2,3 có trong combo; thuốc 4 chỉ có target.
# Cặp (1,3): nausea; (1,2): anaemia; (2,3): anaemia + nausea. Target: 1 -> {10, 20}; 4 -> {20}. PPI: 10-20, 10-30.
S1, S2, S3, S4 = (f"CID00000000{i}" for i in (1, 2, 3, 4))


@pytest.fixture
def index(raw_dir, tmp_path):
    snap = tmp_path / "snap"
    etl.run(raw_dir, snap)
    names = pd.DataFrame({
        "drug_idx": [0, 1, 2, 3], "stitch_id": [S1, S2, S3, S4], "pubchem_cid": [1, 2, 3, 4],
        "name_cid": [101, 2, 3, 4], "name_source": ["related", "self", "self", "self"],
        "display_name": ["alphamycin", "betacol", "gammazole", "deltane"],
        "synonyms": [["alphamycin", "alpha"], ["betacol", "shared name"], ["gammazole", "shared name"], ["deltane"]],
        "needs_review": [True, False, False, False]})
    names.to_parquet(snap / "drug_names.parquet", index=False)
    pd.DataFrame({"gene_id": [10, 20], "symbol": ["GENE10", "GENE20"], "description": ["", ""]}) \
        .to_parquet(snap / "gene_names.parquet", index=False)
    return lookup.load_index(snap)


def test_resolve_by_stitch_cid_name_and_related_cid(index):
    assert index.resolve("cid000000002").match == "stitch_id"
    assert index.resolve("3").drug_idx == 2
    assert index.resolve("CID 101").drug_idx == 0  # CID của tên (parent/related) cũng nhận diện được
    assert index.resolve("  Alpha ").match == "name"
    amb = index.resolve("shared name")
    assert amb.reason == "ambiguous" and amb.candidates == [1, 2]
    miss = index.resolve("alphamycn")
    assert miss.reason == "not_found" and miss.candidates == [0]


def test_effects_aggregated_with_contributing_pairs_and_evidence_ids(index):
    r = index.review(["alphamycin", "betacol", "gammazole"])
    assert r["status"] == "ok"
    assert r["coverage"] == {"drugs_resolved": 3, "pairs_total": 3, "pairs_with_labels": 3,
                             "drugs_with_targets": 1, "distinct_effects": 2}
    by_name = {e["effect_name"]: e for e in r["effects"]}
    assert by_name["anaemia"]["contributing_pairs"] == [[S1, S2], [S2, S3]]
    assert by_name["nausea"]["evidence_ids"] == [f"decagon:combo:{S1}:{S3}:C0000002", f"decagon:combo:{S2}:{S3}:C0000002"]
    assert all(e["status"] == "observed" for e in r["effects"])


def test_three_missing_data_cases_are_distinct(index):
    r = index.review(["alphamycin", "betacol", "deltane", "nosuchdrug"])
    # 1) đầu vào không nhận diện được: không xử lý, chỉ báo
    assert [u["input"] for u in r["unresolved"]] == ["nosuchdrug"]
    # 2) cặp không có nhãn: no_data cho riêng cặp đó, cặp khác vẫn có kết quả
    status = {tuple(d["stitch_id"] for d in p["drugs"]): p["status"] for p in r["pairs"]}
    assert status == {(S1, S2): "observed", (S1, S4): "no_data", (S2, S4): "no_data"}
    # 3) thuốc thiếu target: nhãn của cặp vẫn giữ, chỉ bối cảnh cơ chế bị đánh dấu thiếu
    p12 = next(p for p in r["pairs"] if p["drugs"][1]["stitch_id"] == S2)
    assert p12["n_effects"] == 1 and p12["mechanism_context"]["status"] == "missing_targets"
    assert p12["mechanism_context"]["missing_for"] == [S2]
    scopes = sorted((m["scope"], str(m["subject"])) for m in r["missing_data"])
    assert ("drug", S2) in scopes and ("input", "nosuchdrug") in scopes
    assert sum(m["scope"] == "pair" for m in r["missing_data"]) == 2


def test_mechanism_context_shared_targets_and_ppi(index):
    r = index.review([S1, S4])
    ctx = r["pairs"][0]["mechanism_context"]
    assert ctx["status"] == "available"
    assert [g["symbol"] for g in ctx["shared_targets"]] == ["GENE20"]
    # 10 chỉ là target của thuốc 1, 20 là target chung nên không tính là "liên kết giữa target của hai thuốc".
    assert ctx["n_ppi_links"] == 0


def test_duplicates_and_too_few_drugs(index):
    r = index.review(["alphamycin", S1, "CID 1"])
    assert len(r["duplicates"]) == 2 and r["status"] == "error"
    assert "cần 2–10" in r["error"]


def test_text_rendering_mentions_safety_caveat(index):
    text = lookup.render_text(index.review(["alphamycin", "deltane"]))
    assert "KHÔNG có dữ liệu" in text and "không có nghĩa là an toàn" in text
    assert "(tên cần duyệt)" in text


def test_index_refuses_prediction_view(raw_dir, tmp_path):
    snap = tmp_path / "snap"
    etl.run(raw_dir, snap)
    splits.run(snap, min_rows=1)
    with pytest.raises(ValueError):
        lookup.EvidenceIndex(prediction_view(snap=snap))
    assert lookup.EvidenceIndex(evidence_view(snap)).n_drugs == 4


def test_cli_json_output(index, raw_dir, tmp_path, capsys):
    code = lookup.main(["alphamycin,betacol", "--json", "--snapshot-dir", str(tmp_path / "snap")])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["status"] == "ok" and "load_seconds" in out["timing"]


def test_enrichment_ranking_and_base_rate(index):
    r = index.review(["alphamycin", "betacol", "gammazole"])
    # Fixture: 3 cặp có nhãn; anaemia ở 2/3 cặp, nausea ở 2/3 cặp -> tỷ lệ nền 2/3, trội = 2 / (3 × 2/3) = 1.0
    assert {e["effect_name"]: (e["base_rate"], e["enrichment"]) for e in r["effects"]} == \
        {"anaemia": (0.6667, 1.0), "nausea": (0.6667, 1.0)}
    assert r["ranking"]["sort"] == "pairs"
    assert index.review(["alphamycin", "betacol", "gammazole"], sort="enrichment")["ranking"]["sort"] == "enrichment"
