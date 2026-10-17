"""Paired comparison trên val và final lock (plan du_doan_cap/03)."""
import json

import numpy as np
import pytest

from dsp391m import compare, evaluate, final
from dsp391m.models.b0 import WEIGHTS
from dsp391m.releases import IntegrityError, read_release

CLEAN = {"commit": "abc123", "dirty": False, "dirty_entries": []}


@pytest.fixture
def evaluated(snap, tmp_path, monkeypatch):
    monkeypatch.setattr(final, "code_state", lambda root=None: dict(CLEAN))
    ids = {name: evaluate.run(name, snap=snap, results_dir=tmp_path)["model_release_id"]
           for name in ("popularity", "b0_alpha0", "b0_alpha100")}
    return snap, tmp_path, ids


def _no_test_labels(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("test labels loaded before verification")
    monkeypatch.setattr(final, "load_eval_targets", refuse)


def test_compare_identical_models_zero_delta(evaluated):
    snap, res, ids = evaluated
    r = compare.run(ids["b0_alpha0"], ids["b0_alpha0"], n_boot=10, snap=snap, results_dir=res)
    assert all(v["delta"] == 0 and v["ci95_delta"] == [0.0, 0.0] for v in r["metrics"].values())
    r = compare.run(ids["popularity"], ids["b0_alpha100"], n_boot=10, snap=snap, results_dir=res)
    json.dumps(r, allow_nan=False)
    assert read_release(res / "val" / "comparisons" / f"{r['run_id']}.json")[0]["cand"] == ids["b0_alpha100"]


def test_compare_has_no_test_split_and_rejects_bad_cache(evaluated):
    snap, res, ids = evaluated
    with pytest.raises(SystemExit):
        compare.main(["--base", "x", "--cand", "y", "--split", "test"])
    with pytest.raises(FileNotFoundError):
        compare.run(ids["b0_alpha0"], "unknown-model", n_boot=2, snap=snap, results_dir=res)


def test_lock_and_final_run(evaluated):
    snap, res, ids = evaluated
    lock = res / "final" / "locks" / "l1.json"
    final.create_lock(lock, list(ids.values()), ids["b0_alpha100"], "fixture", n_boot=5, snap=snap, results_dir=res)
    with pytest.raises(FileExistsError):
        final.create_lock(lock, list(ids.values()), ids["b0_alpha100"], "again", snap=snap, results_dir=res)
    r = final.run_final(lock, "run1", snap=snap, results_dir=res)
    assert set(r["models"]) == set(ids.values()) and len(r["comparisons_vs_reference"]) == 2
    assert all(m["split"] == "test" for m in r["models"].values())
    json.dumps(r, allow_nan=False)
    with pytest.raises(FileExistsError):
        final.run_final(lock, "run1", snap=snap, results_dir=res)
    with pytest.raises(ValueError):
        final.run_final(lock, "run2", retry_of="run1", snap=snap, results_dir=res)
    assert final.run_final(lock, "run2", retry_of="run1", reason="fixture retry", snap=snap,
                           results_dir=res)["retry_of"] == "run1"


def test_dirty_worktree_cannot_lock(evaluated, monkeypatch):
    snap, res, ids = evaluated
    monkeypatch.setattr(final, "code_state", lambda root=None: {"commit": "abc123", "dirty": True,
                                                                "dirty_entries": ["?? src/dsp391m/new.py"]})
    with pytest.raises(RuntimeError):
        final.create_lock(res / "l.json", [ids["b0_alpha0"]], ids["b0_alpha0"], "x", snap=snap, results_dir=res)


def test_final_refuses_before_loading_test(evaluated, monkeypatch):
    snap, res, ids = evaluated
    lock = res / "lock.json"
    final.create_lock(lock, [ids["b0_alpha0"], ids["b0_alpha100"]], ids["b0_alpha0"], "x", snap=snap, results_dir=res)
    _no_test_labels(monkeypatch)
    # Commit khác lock
    monkeypatch.setattr(final, "code_state", lambda root=None: {**CLEAN, "commit": "other"})
    with pytest.raises(IntegrityError):
        final.run_final(lock, "r", snap=snap, results_dir=res)
    # Worktree bẩn sau khi khóa
    monkeypatch.setattr(final, "code_state", lambda root=None: {**CLEAN, "dirty": True})
    with pytest.raises(IntegrityError):
        final.run_final(lock, "r", snap=snap, results_dir=res)
    monkeypatch.setattr(final, "code_state", lambda root=None: dict(CLEAN))
    # Requirements đổi
    monkeypatch.setattr(final, "requirements_hashes", lambda root=None: {"requirements.txt": "changed"})
    with pytest.raises(IntegrityError):
        final.run_final(lock, "r", snap=snap, results_dir=res)
    monkeypatch.undo()
    monkeypatch.setattr(final, "code_state", lambda root=None: dict(CLEAN))
    _no_test_labels(monkeypatch)
    # Lock bị sửa để thêm model ngoài danh sách
    doc = json.loads(lock.read_text())
    doc["payload"]["models"].append(dict(doc["payload"]["models"][0], model_release_id=ids["popularity"]))
    tampered = res / "tampered.json"
    tampered.write_text(json.dumps(doc))
    with pytest.raises(IntegrityError):
        final.run_final(tampered, "r", snap=snap, results_dir=res)
    # Trọng số bị sửa sau khi khóa
    w = res / "models" / ids["b0_alpha100"] / WEIGHTS
    w.write_bytes(w.read_bytes() + b"x")
    with pytest.raises(IntegrityError):
        final.run_final(lock, "r", snap=snap, results_dir=res)
    assert not (res / "final" / "r").exists()
