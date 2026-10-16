import pandas as pd

from dsp391m import dailymed

XML = """<document xmlns="urn:hl7-org:v3"><component><structuredBody>
<component><section><code code="34073-7"/><title>7 DRUG INTERACTIONS</title><text>Intro about interactions.</text>
  <component><section><title>7.1 Strong CYP3A4 Inhibitors</title><text><paragraph>Avoid with clarithromycin and
  itraconazole.</paragraph></text></section></component>
  <component><section><title>7.2 Warfarin</title><text>Monitor INR when given with Warfarin.</text></section></component>
</section></component>
<component><section><code code="34067-9"/><title>1 INDICATIONS</title><text>Not collected.</text></section></component>
<component><section><code code="34084-4"/><title>6 ADVERSE REACTIONS</title><text>Myopathy.</text></section></component>
</structuredBody></component></document>"""


def test_parse_sections_keeps_wanted_codes_and_subsections():
    chunks = dailymed.parse_sections(XML)
    assert [(c["section"], c["title"]) for c in chunks] == [
        ("drug_interactions", "7 DRUG INTERACTIONS"),
        ("drug_interactions", "7.1 Strong CYP3A4 Inhibitors"),
        ("drug_interactions", "7.2 Warfarin"),
        ("adverse_reactions", "6 ADVERSE REACTIONS")]
    assert chunks[1]["text"] == "Avoid with clarithromycin and itraconazole."


def test_choose_single_ingredient_latest():
    spls = [{"title": "EZETIMIBE AND SIMVASTATIN TABLET", "published_date": "Sep 02, 2026", "spl_version": 9, "setid": "a"},
            {"title": "SIMVASTATIN TABLET [X]", "published_date": "Jan 01, 2025", "spl_version": 3, "setid": "b"},
            {"title": "SIMVASTATIN TABLET [Y]", "published_date": "Sep 02, 2026", "spl_version": 2, "setid": "c"}]
    assert dailymed.choose_spl("simvastatin", spls)["setid"] == "c"
    assert dailymed.choose_spl("aspirin", spls) is None


def test_find_mentions_whole_word_in_drug_interactions_only():
    rows = [dict(c, drug_idx=0, chunk_id=f"x:{i}") for i, c in enumerate(dailymed.parse_sections(XML))]
    sections = pd.DataFrame(rows)
    hits = dailymed.find_mentions(sections, 0, ["warfarin", "Coumadin"])
    assert hits["chunk_id"].tolist() == ["x:2"] and hits["matched"].tolist() == ["warfarin"]
    assert dailymed.find_mentions(sections, 0, ["myopathy"]).empty  # chỉ tìm trong mục drug interactions
    assert dailymed.find_mentions(sections, 0, ["itra"]).empty       # khớp nguyên từ, bỏ tên quá ngắn
