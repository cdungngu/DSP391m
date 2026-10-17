"""Hợp đồng chung cho mọi bộ dự đoán cặp (plan du_doan_cap/01).

- Đầu vào: bảng cặp (drug_a, drug_b) theo drug_idx của snapshot; A–B và B–A là cùng một truy vấn.
- Đầu ra: ma trận float32 [n_cặp, n_nhãn] theo thứ tự label_idx của vocabulary; điểm là mức ưu tiên xếp hạng,
  không phải xác suất lâm sàng.
- Định danh: config_id chỉ băm cấu hình; model_release_id băm nội dung đã học (trọng số/đếm) cùng identity
  của dữ liệu. Cache và final lock dùng model_release_id, không dùng config_id.
"""
import hashlib
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd

from .manifest import sha256
from .releases import IntegrityError, digest, publish, read_release

SCHEMA_VERSION = 1
SCORE_DTYPE = np.float32
ARTIFACT_META = "model.json"


def canonical_pairs(pairs: pd.DataFrame, n_drugs: int) -> pd.DataFrame:
    """Đặt drug_a < drug_b cho từng hàng, giữ nguyên thứ tự hàng. Từ chối self-pair và ID ngoài [0, n_drugs)."""
    if not {"drug_a", "drug_b"} <= set(pairs.columns):
        raise ValueError("pairs cần cột drug_a, drug_b")
    x = pairs[["drug_a", "drug_b"]].to_numpy()
    if x.dtype.kind not in "iu":
        raise ValueError("drug index phải là số nguyên")
    if len(x) and ((x < 0).any() or (x >= n_drugs).any()):
        raise ValueError(f"drug index nằm ngoài [0, {n_drugs})")
    if (x[:, 0] == x[:, 1]).any():
        raise ValueError("Cặp phải gồm hai thuốc khác nhau")
    return pd.DataFrame({"drug_a": x.min(1).astype(np.int64), "drug_b": x.max(1).astype(np.int64)},
                        index=pairs.index)


def identity(view) -> dict:
    """Định danh dữ liệu mà một model được fit trên đó: snapshot, split, thứ tự ID thuốc và thứ tự CUI."""
    drugs = view.drugs.sort_values("drug_idx")
    if not np.array_equal(drugs["drug_idx"].to_numpy(), np.arange(len(drugs))):
        raise ValueError("drug_idx phải liên tục 0..n-1")
    vocab = view.label_vocab.sort_values("label_idx")
    return {"snapshot_hash": view.snapshot_hash, "split_id": view.split_id, "split_hash": view.split_hash,
            "n_drugs": len(drugs), "n_labels": len(vocab),
            "drug_order_hash": digest(drugs["stitch_id"].tolist())[:16],
            "label_order_hash": digest(vocab["effect_cui"].tolist())[:16]}


def pairs_hash(pairs: pd.DataFrame) -> str:
    """Hash thứ tự hàng của bảng cặp; dùng để phát hiện score và nhãn lệch hàng."""
    return digest(pairs[["drug_a", "drug_b"]].to_numpy().astype(int).tolist())[:16]


def check_scores(s: np.ndarray, n_pairs: int, n_labels: int) -> np.ndarray:
    s = np.asarray(s, dtype=SCORE_DTYPE)
    if s.shape != (n_pairs, n_labels):
        raise ValueError(f"Score shape {s.shape}, cần {(n_pairs, n_labels)}")
    if not np.isfinite(s).all():
        raise ValueError("Score có giá trị không hữu hạn")
    return s


def config_id(name: str, config: dict) -> str:
    return f"{name}-{digest(config)[:8]}"


def arrays_digest(arrays: dict[str, np.ndarray]) -> str:
    """Hash nội dung mảng (tên, dtype, shape, bytes), không phụ thuộc định dạng file."""
    h = hashlib.sha256()
    for name in sorted(arrays):
        a = np.ascontiguousarray(arrays[name])
        h.update(f"{name}|{a.dtype.str}|{a.shape}|".encode())
        h.update(a.tobytes())
    return h.hexdigest()


def release_id(name: str, config: dict, ident: dict, content_digest: str) -> str:
    return f"{name}-{digest({'config': config, 'identity': ident, 'content': content_digest})[:12]}"


class Predictor(Protocol):
    name: str
    score_kind: str
    config: dict
    model_release_id: str

    def fit(self, view) -> "Predictor": ...
    def score_pairs(self, pairs: pd.DataFrame) -> np.ndarray: ...
    def save(self, directory: Path) -> str: ...


def write_artifact(directory: Path, weights_file: str, meta: dict) -> str:
    """Ghi model.json bất biến cho artifact đã có file trọng số; trả content hash của meta."""
    meta = {"schema_version": SCHEMA_VERSION, **meta, "weights_file": weights_file,
            "weights_sha256": sha256(directory / weights_file)}
    return publish(directory / ARTIFACT_META, meta)


def read_artifact(directory: Path, view=None) -> dict:
    """Đọc model.json, xác minh checksum meta và file trọng số; nếu có view thì identity phải khớp."""
    meta, _ = read_release(directory / ARTIFACT_META)
    weights = directory / meta["weights_file"]
    if not weights.is_file() or sha256(weights) != meta["weights_sha256"]:
        raise IntegrityError(f"File trọng số thiếu hoặc bị sửa: {weights}")
    if view is not None and meta["identity"] != identity(view):
        raise IntegrityError("Artifact được fit trên snapshot/split/thứ tự ID khác với view hiện tại")
    return meta
