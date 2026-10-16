import pandas as pd

from dsp391m import chembl

ASPIRIN = {"molecule_chembl_id": "CHEMBL25", "pref_name": "ASPIRIN", "max_phase": "4.0",
           "molecule_hierarchy": {"parent_chembl_id": "CHEMBL25"},
           "molecule_structures": {"standard_inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"}}
AMPICILLIN = {"molecule_chembl_id": "CHEMBL174", "pref_name": "AMPICILLIN", "max_phase": "4.0",
              "molecule_hierarchy": {"parent_chembl_id": "CHEMBL174"}}
AMP_SALT = {"molecule_chembl_id": "CHEMBL1200", "pref_name": "AMPICILLIN SODIUM", "max_phase": "4.0",
            "molecule_hierarchy": {"parent_chembl_id": "CHEMBL174"}}
AMP_JUNK = {"molecule_chembl_id": "CHEMBL1473908", "pref_name": None, "max_phase": None, "molecule_hierarchy": None}


def fake_get_all(endpoint, params, list_key, offline):
    if endpoint == "molecule" and "molecule_structures__standard_inchi_key__in" in params:
        keys = params["molecule_structures__standard_inchi_key__in"].split(",")
        return [ASPIRIN] if ASPIRIN["molecule_structures"]["standard_inchi_key"] in keys else []
    if endpoint == "molecule" and "molecule_structures__standard_inchi_key__startswith" in params:
        return [AMP_JUNK, AMP_SALT] if params["molecule_structures__standard_inchi_key__startswith"] == "AVKUERGKIZMTKX" else []
    if endpoint == "molecule":
        return [{"molecule_chembl_id": i, "pref_name": n, "max_phase": "4.0",
                 "molecule_synonyms": [{"molecule_synonym": s} for s in syn]}
                for i, n, syn in (("CHEMBL25", "ASPIRIN", ["Acetylsalicylic acid"]), ("CHEMBL174", "AMPICILLIN", ["Penbritin"]))
                if i in params["molecule_chembl_id__in"].split(",")]
    if endpoint == "mechanism":
        return [{"molecule_chembl_id": "CHEMBL25", "mec_id": 1, "action_type": "INHIBITOR",
                 "mechanism_of_action": "Cyclooxygenase inhibitor", "target_chembl_id": "CHEMBL2094253",
                 "mechanism_refs": [{"ref_type": "PubMed", "ref_id": "1", "ref_url": "http://europepmc.org/abstract/MED/1"}]}]
    if endpoint == "target":
        return [{"target_chembl_id": "CHEMBL2094253", "pref_name": "Cyclooxygenase", "target_type": "PROTEIN FAMILY",
                 "organism": "Homo sapiens", "target_components": [
                     {"target_component_synonyms": [{"component_synonym": "PTGS1", "syn_type": "GENE_SYMBOL"},
                                                    {"component_synonym": "COX1", "syn_type": "UNIPROT"}]},
                     {"target_component_synonyms": [{"component_synonym": "PTGS2", "syn_type": "GENE_SYMBOL"}]}]}]
    raise AssertionError((endpoint, params))


STRUCTS = pd.DataFrame({"drug_idx": [0, 1, 2], "stitch_id": ["CID000002244", "CID000002173", "CID000099999"],
                        "inchikey": ["BSYNRYMUTXBXSQ-UHFFFAOYSA-N", "AVKUERGKIZMTKX-UHFFFAOYSA-M", "ZZZZZZZZZZZZZZ-UHFFFAOYSA-N"]})


def test_map_exact_connectivity_and_none(monkeypatch):
    monkeypatch.setattr(chembl, "_get_all", fake_get_all)
    m = chembl.map_drugs(STRUCTS).set_index("stitch_id")
    assert m.loc["CID000002244", ["match_type", "parent_chembl_id"]].tolist() == ["exact", "CHEMBL25"]
    # Dạng ion của ampicillin: khớp theo connectivity, chọn phân tử đã duyệt có tên, quy về phân tử cha
    assert m.loc["CID000002173", ["match_type", "matched_chembl_id", "parent_chembl_id"]].tolist() == \
        ["connectivity", "CHEMBL1200", "CHEMBL174"]
    assert m.loc["CID000099999", "match_type"] == "none"


def test_mechanisms_map_gene_symbols_to_decagon(monkeypatch):
    monkeypatch.setattr(chembl, "_get_all", fake_get_all)
    genes = pd.DataFrame({"gene_id": [5742, 5743], "symbol": ["PTGS1", "PTGS2"], "description": ["", ""]})
    mec = chembl.mechanisms(["CHEMBL25"], genes)
    row = mec.iloc[0]
    assert row["action_type"] == "INHIBITOR" and row["gene_symbols"] == ["PTGS1", "PTGS2"]
    assert row["decagon_gene_ids"] == [5742, 5743] and row["refs"] == ["http://europepmc.org/abstract/MED/1"]


def test_update_names_fills_pending_only(monkeypatch):
    monkeypatch.setattr(chembl, "_get_all", fake_get_all)
    mapping = chembl.map_drugs(STRUCTS)
    mapping = mapping.merge(chembl.parent_info(mapping["parent_chembl_id"].dropna().tolist()), on="parent_chembl_id", how="left")
    mapping["chembl_synonyms"] = mapping["chembl_synonyms"].apply(lambda v: v if isinstance(v, list) else [])
    names = pd.DataFrame({"drug_idx": [0, 1, 2], "stitch_id": STRUCTS["stitch_id"], "pubchem_cid": [2244, 2173, 99999],
                          "name_cid": [2244, 2173, 99999], "name_source": ["self", "pending", "pending"],
                          "display_name": ["aspirin", "CID000002173", "CID000099999"],
                          "synonyms": [["aspirin"], [], []], "needs_review": [False, True, True]})
    out = chembl.update_names(names, mapping).set_index("stitch_id")
    assert out.loc["CID000002244", "display_name"] == "aspirin" and "acetylsalicylic acid" in out.loc["CID000002244", "synonyms"]
    assert out.loc["CID000002173", ["display_name", "name_source", "needs_review"]].tolist() == ["ampicillin", "chembl", True]
    assert out.loc["CID000099999", ["display_name", "name_source"]].tolist() == ["CID000099999", "pending"]
