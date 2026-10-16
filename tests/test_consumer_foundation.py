import copy
import json
from dataclasses import asdict, replace

import pytest

from dsp391m.catalog import Catalog, apply_decisions
from dsp391m.contracts import Claim, EvidenceRecord, RunContext, consumer_claim
from dsp391m.releases import IntegrityError, digest, publish, read_release, source_manifest, verify_sources
from dsp391m.review import run_review, verify


def catalog_doc():
    return {"schema_version": 1, "source_hash": "fixture-source", "ingredients": [
        {"ingredient_id": i, "display_name_vi": i, "aliases": [i.lower()], "source_hash": "fixture-source",
         "review_status": "approved", "reviewer": "fixture-reviewer", "reviewed_at": "2026-10-17",
         "rationale": "TEST ONLY", "review_source": "https://example.org/fixture", "products": []}
        for i in ("A", "B", "C")]}


def evidence():
    return EvidenceRecord("fixture-e", "drug_label", ("A", "B"), "https://example.org/fixture",
                          "fixture-label", "1", "Fixture source; not medical information.",
                          "Dữ liệu thử nghiệm, chỉ áp dụng trong điều kiện X.", ("X",),
                          "approved", "fixture-reviewer", "2026-10-17")


def corpus(cat, *records):
    return {"schema_version": 1, "catalog_version": cat.version, "snapshot_hash": "fixture-snapshot",
            "evidence": [asdict(r) for r in records]}


def test_no_review_of_partial_input_and_no_automatic_fuzzy_resolution():
    cat = Catalog(catalog_doc())
    r = run_review(["A", "B", "unknown"], cat, corpus(cat, evidence()), "fixture")
    assert r["execution_status"] == "needs_resolution" and not r["claims"]
    assert cat.resolve("unknown")["status"] == "not_found"
    assert not cat.resolve_all(["A", "A"])["ready"]


def test_pending_alias_is_unavailable_even_by_id():
    doc = catalog_doc()
    doc["ingredients"][0]["review_status"] = "pending"
    cat = Catalog(doc)
    assert cat.resolve("A")["status"] == "not_found"


def test_ambiguous_alias_requires_explicit_id():
    doc = catalog_doc()
    for item in doc["ingredients"][:2]:
        item["aliases"].append("same")
    cat = Catalog(doc)
    assert cat.resolve("same")["status"] == "ambiguous"
    assert cat.resolve("A")["ingredient_ids"] == ["A"]


def test_products_expand_only_approved_ingredients_and_deduplicate():
    doc = catalog_doc()
    p = {"product_id": "P", "brand": "fixture product", "country": "fixture",
         "route": "fixture", "formulation": "fixture", "source_url": "https://example.org/fixture",
         "ingredient_ids": ["A", "B"]}
    doc["ingredients"][0]["products"] = [p]
    cat = Catalog(doc)
    assert cat.resolve_all(["P", "B"])["ingredient_ids"] == ["A", "B"]
    assert cat.resolve_all(["P", "B"])["duplicates"] == ["B"]
    p["ingredient_ids"].append("UNAPPROVED")
    with pytest.raises(ValueError):
        Catalog(doc)


def test_review_decisions_are_bound_to_source_and_require_provenance():
    doc = catalog_doc()
    for row in doc["ingredients"]:
        row["review_status"] = "pending"
    decision = dict(doc["ingredients"][0], review_status="approved")
    assert len(Catalog(apply_decisions(doc, [decision])).items) == 1
    with pytest.raises(ValueError):
        apply_decisions(doc, [dict(decision, source_hash="changed")])
    with pytest.raises(ValueError):
        apply_decisions(doc, [dict(decision, reviewer="")])
    with pytest.raises(ValueError):
        apply_decisions(doc, [decision, decision])


def test_release_is_exclusive_and_detects_tampering(tmp_path):
    path = tmp_path / "release.json"
    assert publish(path, {"x": 1}) == digest({"x": 1})
    with pytest.raises(FileExistsError):
        publish(path, {"x": 2})
    assert read_release(path)[0] == {"x": 1}
    raw = json.loads(path.read_text())
    raw["payload"]["x"] = 3
    path.write_text(json.dumps(raw))
    with pytest.raises(IntegrityError):
        read_release(path)


def test_manifest_checks_actual_source_bytes(tmp_path):
    source = tmp_path / "source"
    source.write_text("first")
    m = source_manifest({"source": source}, {"version": "1"})
    verify_sources(m)
    source.write_text("changed")
    with pytest.raises(IntegrityError):
        verify_sources(m)


def test_context_cache_changes_with_every_relevant_version():
    ctx = RunContext("consumer_review", "evidence", "s", "c", "b", "config")
    kwargs = dict(conditions={"route": "oral"}, retrieval={"top": 10}, model="template",
                  prompt_hash="p", verifier_version="1")
    key = ctx.cache_key(["A", "B"], **kwargs)
    assert key == ctx.cache_key(["B", "A"], **kwargs)
    for field in ("snapshot_hash", "catalog_version", "corpus_version", "config_hash"):
        assert replace(ctx, **{field: "changed"}).cache_key(["A", "B"], **kwargs) != key
    for field in ("conditions", "retrieval", "model", "prompt_hash", "verifier_version"):
        changed = dict(kwargs, **{field: {"changed": True} if field in ("conditions", "retrieval") else "changed"})
        assert ctx.cache_key(["A", "B"], **changed) != key
    with pytest.raises(ValueError):
        RunContext("prediction_eval", "evidence", "s", "c", "b", "config")
    with pytest.raises(ValueError):
        RunContext("prediction_eval", "prediction", "s", "c", "b", "config")


def test_template_preserves_conditions_and_only_returns_reviewed_pair_statements():
    cat = Catalog(catalog_doc())
    r = run_review(["A", "B", "C"], cat, corpus(cat, evidence()), "fixture")
    assert len(r["claims"]) == 1
    assert r["claims"][0]["conditions"] == ["X"]
    assert r["coverage"] == {"pairs_total": 3, "pairs_with_supported_claims": 1}
    assert len(r["missing_data"]) == 2
    assert "model_score" not in json.dumps(r) and "drug_frequency" not in json.dumps(r)


@pytest.mark.parametrize("kind", ["drug_frequency", "observed_association", "ppi_context", "single_drug_mechanism"])
def test_research_evidence_never_becomes_consumer_claim(kind):
    cat = Catalog(catalog_doc())
    e = replace(evidence(), evidence_type=kind)
    assert not run_review(["A", "B"], cat, corpus(cat, e), "fixture")["claims"]


def test_verifier_rejects_real_citation_with_wrong_content_or_subjects():
    e = evidence()
    c = Claim("c", e.subjects, e.statement_vi, (e.evidence_id,), e.conditions)
    assert verify(c, {e.evidence_id: e}).support_status == "supported"
    for changed in (replace(c, text_vi="Invented"), replace(c, subjects=("A", "C")),
                    replace(c, conditions=()), replace(c, evidence_ids=("fake",))):
        assert verify(changed, {e.evidence_id: e}).support_status == "insufficient"
    with pytest.raises(ValueError):
        consumer_claim(c, {e.evidence_id: e})


def test_corpus_version_duplicate_evidence_and_unapproved_subjects_rejected():
    cat = Catalog(catalog_doc())
    with pytest.raises(ValueError):
        run_review(["A", "B"], cat, dict(corpus(cat), catalog_version="wrong"), "fixture")
    with pytest.raises(ValueError):
        run_review(["A", "B"], cat, corpus(cat, evidence(), evidence()), "fixture")
    with pytest.raises(ValueError):
        run_review(["A", "B"], cat, corpus(cat, replace(evidence(), subjects=("A", "UNKNOWN"))), "fixture")
