"""Version-one contracts for the new service; legacy lookup output stays unchanged."""
from dataclasses import asdict, dataclass

from .releases import digest


@dataclass(frozen=True)
class RunContext:
    purpose: str
    data_mode: str
    snapshot_hash: str
    catalog_version: str
    corpus_version: str
    config_hash: str
    split_hash: str | None = None
    schema_version: int = 1

    def __post_init__(self):
        if self.purpose not in {"consumer_review", "research_explanation", "prediction_eval"}:
            raise ValueError("Unknown purpose")
        expected = "prediction" if self.purpose == "prediction_eval" else "evidence"
        if self.data_mode != expected or (expected == "prediction" and not self.split_hash):
            raise ValueError("Purpose/data mode/split mismatch")
        if self.schema_version != 1 or not all((self.snapshot_hash, self.catalog_version,
                                               self.corpus_version, self.config_hash)):
            raise ValueError("Missing or unsupported context version")

    def cache_key(self, ingredients: list[str], *, conditions: dict, retrieval: dict,
                  model: str, prompt_hash: str, verifier_version: str) -> str:
        return digest({"context": asdict(self), "ingredients": sorted(set(ingredients)),
                       "conditions": conditions, "retrieval": retrieval, "model": model,
                       "prompt_hash": prompt_hash, "verifier_version": verifier_version})


EVIDENCE_TYPES = {"curated_statement", "drug_label", "single_drug_mechanism",
                  "observed_association", "drug_frequency", "ppi_context"}


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    evidence_type: str
    subjects: tuple[str, ...]
    source_url: str
    source_record_id: str
    source_version: str
    source_text: str
    statement_vi: str
    conditions: tuple[str, ...]
    review_status: str
    reviewer: str
    reviewed_at: str
    relation: str = "interaction_statement"

    def __post_init__(self):
        if self.evidence_type not in EVIDENCE_TYPES:
            raise ValueError("Unknown evidence type")
        if self.review_status not in {"pending", "approved", "rejected"}:
            raise ValueError("Unknown review status")
        if not self.evidence_id or not self.subjects or len(set(self.subjects)) != len(self.subjects):
            raise ValueError("Invalid evidence identity/subjects")
        if not self.source_url.startswith(("https://", "http://")):
            raise ValueError("Evidence requires a source URL")
        if not all((self.source_record_id, self.source_version, self.source_text)):
            raise ValueError("Evidence provenance is incomplete")
        if self.review_status == "approved" and not all((self.statement_vi, self.reviewer, self.reviewed_at)):
            raise ValueError("Approved evidence requires a reviewed Vietnamese statement")

    @property
    def content_hash(self):
        return digest(asdict(self))

    @classmethod
    def from_dict(cls, obj: dict):
        return cls(**{**obj, "subjects": tuple(obj["subjects"]), "conditions": tuple(obj["conditions"])})


@dataclass(frozen=True)
class Claim:
    claim_id: str
    subjects: tuple[str, ...]
    text_vi: str
    evidence_ids: tuple[str, ...]
    conditions: tuple[str, ...]
    support_status: str = "insufficient"
    reason_codes: tuple[str, ...] = ()


def consumer_claim(claim: Claim, records: dict[str, EvidenceRecord]) -> dict:
    """Allowlist projection, deliberately excluding scores and research evidence."""
    if claim.support_status != "supported":
        raise ValueError("Cannot publish an unverified claim")
    if not claim.evidence_ids:
        raise ValueError("A supported claim must have evidence")
    evidence = [records[e] for e in claim.evidence_ids]
    if any(e.review_status != "approved" or
           e.evidence_type not in {"curated_statement", "drug_label"} for e in evidence):
        raise ValueError("Research evidence cannot be exposed as a consumer claim")
    return {"claim_id": claim.claim_id, "subjects": list(claim.subjects), "text_vi": claim.text_vi,
            "conditions": list(claim.conditions), "support_status": claim.support_status,
            "sources": [{"evidence_id": e.evidence_id, "url": e.source_url,
                         "version": e.source_version, "source_text": e.source_text,
                         "content_hash": e.content_hash} for e in evidence]}
