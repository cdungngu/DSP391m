"""Content-addressed local releases. Never overwrite a published release."""
import hashlib
import json
import os
import tempfile
from pathlib import Path


class IntegrityError(ValueError):
    pass


def digest(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def publish(path: Path, payload: dict) -> str:
    """Atomic, exclusive publication; even identical releases cannot be overwritten."""
    envelope = {"payload": payload, "content_hash": digest(payload)}
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".release-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(envelope, f, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.link(name, path)  # atomic create-if-absent on the same filesystem
    finally:
        Path(name).unlink(missing_ok=True)
    return envelope["content_hash"]


def read_release(path: Path) -> tuple[dict, str]:
    doc = json.loads(path.read_text())
    if set(doc) != {"payload", "content_hash"} or digest(doc["payload"]) != doc["content_hash"]:
        raise IntegrityError(f"Release checksum mismatch: {path}")
    return doc["payload"], doc["content_hash"]


def source_manifest(files: dict[str, Path], metadata: dict) -> dict:
    """Describe source bytes without modifying them; caller supplies provenance/version."""
    return {"schema_version": 1, "metadata": metadata, "files": {
        name: {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for name, path in sorted(files.items())
    }}


def verify_sources(manifest: dict) -> None:
    for name, record in manifest["files"].items():
        path = Path(record["path"])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise IntegrityError(f"Source missing or changed: {name}")
