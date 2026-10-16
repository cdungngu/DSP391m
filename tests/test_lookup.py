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
    idx = lookup.load_index(snap)
    idx._snap = snap
    return idx


def index_snapshot(index):
    return index._snap


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


def test_chembl_and_dailymed_evidence_in_pairs(index):
    mecs = pd.DataFrame({
        "drug_idx": [0, 1], "parent_chembl_id": ["CHEMBL1", "CHEMBL2"], "mec_id": [11, 12],
        "action_type": ["INHIBITOR", "SUBSTRATE"], "mechanism_of_action": ["X inhibitor", "X substrate"],
        "direct_interaction": [True, True], "target_chembl_id": ["CHEMBLT", "CHEMBLT"], "target_name": ["Enzyme X"] * 2,
        "target_type": ["SINGLE PROTEIN"] * 2, "organism": ["Homo sapiens"] * 2, "is_human": [True, True],
        "gene_symbols": [["GENEX"], ["GENEX"]], "decagon_gene_ids": [[], []], "refs": [["ref1"], []]})
    sections = pd.DataFrame({
        "drug_idx": [0], "stitch_id": [S1], "setid": ["s"], "spl_version": [1], "published_date": ["Jan 01, 2026"],
        "spl_title": ["ALPHAMYCIN TABLET"], "chunk_id": ["dailymed:s:v1:0"], "section": ["drug_interactions"],
        "title": ["7.1 Betacol"], "text": ["Coadministration with betacol increases exposure."]})
    idx = lookup.EvidenceIndex(index.view, pd.read_parquet(index_snapshot(index) / "drug_names.parquet"),
                               None, mecs, sections)
    r = idx.review(["alphamycin", "betacol", "gammazole"])
    p12 = next(p for p in r["pairs"] if [d["stitch_id"] for d in p["drugs"]] == [S1, S2])
    assert p12["shared_mechanism_targets"][0]["actions"] == [["INHIBITOR"], ["SUBSTRATE"]]
    assert p12["shared_mechanism_targets"][0]["kind"] == "pair_hypothesis"
    nonhuman = lookup.EvidenceIndex(index.view, None, None, mecs.assign(is_human=[True, False],
                                                                         organism=["Homo sapiens", "Rattus"]), None)
    assert nonhuman.shared_mechanism_targets(0, 1) == []
    assert p12["label_mentions"][0]["evidence_id"] == "dailymed:s:v1:0" and p12["label_mentions"][0]["matched"] == "betacol"
    missing = [(m["subject"], m["what"]) for m in r["missing_data"] if m["scope"] == "drug"]
    assert any(s == S3 and w.startswith("không có cơ chế ChEMBL") for s, w in missing)
    assert any(s == S2 and w.startswith("chưa có nhãn DailyMed") for s, w in missing)
    assert "nhãn DailyMed của alphamycin" in lookup.render_text(r)


def test_broad_target_panel_flagged(index, monkeypatch):
    monkeypatch.setattr(lookup, "BROAD_PANEL_MIN_TARGETS", 1)  # thuốc 1 có 2 target -> coi là panel rộng
    ctx = index.review([S1, S4])["pairs"][0]["mechanism_context"]
    assert ctx["status"] == "low_specificity" and ctx["broad_panel_drugs"] == [S1]
