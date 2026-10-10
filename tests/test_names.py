import pandas as pd
import requests

from dsp391m import names


def test_is_name_like():
    assert names.is_name_like("aspirin") and names.is_name_like("Calcium chloride")
    for bad in ("50-78-2", "DTXSID20859077", "STK177241", None, "",
                "6-{[amino(phenyl)acetyl]amino}-3,3-dimethyl-7-oxo-4-thia-1-azabicyclo[3.2.0]heptane-2-carboxylate"):
        assert not names.is_name_like(bad)


def test_resolve_self_related_and_pending(monkeypatch):
    synonyms = {
        2244: ["aspirin", "Acetylsalicylic acid"],
        2173: ["6-{[amino(phenyl)acetyl]amino}-3,3-dimethyl-7-oxo-4-thia-1-azabicyclo[3.2.0]heptane-2-carboxylate"],
        2174: ["DTXSID20859077"], 6249: ["ampicillin", "Aminobenzylpenicillin", "69-53-4"], 9999: ["Ampicillin sodium"],
        5555: ["XYZ-123"],
    }

    def fake_synonyms(cids, offline=False, strict=True):
        return {c: synonyms[c] for c in cids if c in synonyms}

    def fake_related(cid, offline=False):
        if cid == 5555:
            raise requests.HTTPError("429")
        return [2174, 6249, 9999]

    monkeypatch.setattr(names, "fetch_synonyms", fake_synonyms)
    monkeypatch.setattr(names, "related_cids", fake_related)
    drugs = pd.DataFrame({"drug_idx": [0, 1, 2], "stitch_id": ["CID000002244", "CID000002173", "CID000005555"],
                          "pubchem_cid": [2244, 2173, 5555]})
    out = names.resolve_drug_names(drugs).set_index("stitch_id")
    assert out.loc["CID000002244", ["display_name", "name_source", "needs_review"]].tolist() == ["aspirin", "self", False]
    # CID liên quan có nhiều synonym nhất và tên trông như tên thuốc được chọn; luôn cần dược sĩ duyệt
    assert out.loc["CID000002173", ["display_name", "name_cid", "name_source", "needs_review"]].tolist() == \
        ["ampicillin", 6249, "related", True]
    # API lỗi: chưa có tên, đánh dấu pending, không đưa synonym rác vào chỉ mục tên
    assert out.loc["CID000005555", ["display_name", "name_source", "synonyms"]].tolist() == ["CID000005555", "pending", []]
