"""Hash file và đọc/ghi manifest của snapshot."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .paths import ROOT


def sha256(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=int) + "\n")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())
