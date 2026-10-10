import pandas as pd

from dsp391m import structures


def test_assess_ok_and_flags():
    aspirin = {"CID": 2244, "Title": "Aspirin", "SMILES": "CC(=O)OC1=CC=CC=C1C(=O)O", "Charge": 0, "HeavyAtomCount": 13}
    assert structures.assess(aspirin)["status"] == "ok"
    assert structures.assess(aspirin)["flags"] == ""

    calcium = {"CID": 271, "Title": "Calcium Cation", "SMILES": "[Ca+2]", "Charge": 2, "HeavyAtomCount": 1}
    assert structures.assess(calcium)["flags"] == "charged,tiny"

    salt = {"CID": 5234, "SMILES": "[Na+].[Cl-]", "Charge": 0, "HeavyAtomCount": 2}
    assert structures.assess(salt)["flags"] == "multi_component,tiny"


def test_assess_failure_modes():
    assert structures.assess(None)["status"] == "not_found"
    assert structures.assess({"CID": 1, "Title": "x"})["status"] == "no_smiles"
    assert structures.assess({"CID": 1, "SMILES": "not-a-smiles(("})["status"] == "parse_failed"
    # PubChem cũ trả CanonicalSMILES thay vì SMILES.
    assert structures.assess({"CID": 1, "CanonicalSMILES": "CCO", "HeavyAtomCount": 3})["smiles"] == "CCO"


def test_build_and_coverage_by_group():
    drugs = pd.DataFrame({"drug_idx": [0, 1, 2], "stitch_id": ["CID000000001", "CID000000002", "CID000000003"],
                          "pubchem_cid": [1, 2, 3], "in_combo": [True, True, False], "n_targets": [5, 0, 0]})
    records = {1: {"CID": 1, "SMILES": "CCO", "Charge": 0, "HeavyAtomCount": 3}}
    table = structures.build(drugs, records)
    cov = structures.coverage(table)
    assert cov["combo_drugs"]["fingerprint_ok"] == 1
    assert cov["combo_drugs_with_targets"]["fingerprint_ok_rate"] == 1.0
    assert cov["combo_drugs_without_targets"]["status_counts"] == {"not_found": 1}
    assert {r["stitch_id"] for r in cov["needs_review"]} == {"CID000000001", "CID000000002", "CID000000003"}
