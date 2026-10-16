import json
from dataclasses import asdict

import pytest

from dsp391m.catalog import Catalog
from dsp391m.releases import publish, read_release, source_manifest
from dsp391m.workbench import publish_corpus
from test_consumer_foundation import catalog_doc, evidence


def test_publication_requires_explicit_source_bound_human_review(tmp_path):
    cat = catalog_doc()
    publish(tmp_path / "catalog.json", cat)
    e = evidence()
    draft = {"schema_version": 1, "source_manifest": source_manifest({}, {}),
             "records": [{"record": asdict(e), "content_hash": e.content_hash}]}
    publish(tmp_path / "draft.json", draft)
    decision = {**asdict(e), "content_hash": e.content_hash, "rationale": "TEST ONLY"}
    path = tmp_path / "decisions.json"
    path.write_text(json.dumps([decision]))
    out = tmp_path / "corpus.json"
    result = publish_corpus(tmp_path / "catalog.json", tmp_path / "draft.json", path, out)
    assert result["approved_pair_statements"] == 1
    payload, _ = read_release(out)
    assert payload["catalog_version"] == Catalog(cat).version
    decision["content_hash"] = "wrong"
    path.write_text(json.dumps([decision]))
    with pytest.raises(ValueError, match="source has changed"):
        publish_corpus(tmp_path / "catalog.json", tmp_path / "draft.json", path, tmp_path / "bad.json")


def test_pending_review_is_not_published(tmp_path):
    publish(tmp_path / "catalog.json", catalog_doc())
    e = evidence()
    publish(tmp_path / "draft.json", {"records": [{"record": asdict(e), "content_hash": e.content_hash}],
                                     "source_manifest": source_manifest({}, {})})
    path = tmp_path / "decisions.json"
    path.write_text(json.dumps([{"evidence_id": e.evidence_id, "content_hash": e.content_hash,
                                "review_status": "pending"}]))
    result = publish_corpus(tmp_path / "catalog.json", tmp_path / "draft.json", path, tmp_path / "out.json")
    assert result["approved_pair_statements"] == 0
