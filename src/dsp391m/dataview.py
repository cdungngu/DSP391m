"""Data view theo chế độ: điểm truy cập dữ liệu nhãn duy nhất cho tra cứu, dự đoán và giải thích.

- evidence_view(): toàn bộ nhãn của snapshot. Dùng cho demo tra cứu; KHÔNG dùng cho benchmark.
- prediction_view(split_id): chỉ nhãn của cặp train, chỉ nhãn trong vocabulary. Nhãn val/test
  không tồn tại trong view này, nên mô hình, truy xuất và giải thích chạy trên nó không thể lộ nhãn.
- load_eval_targets(split_id, split): nhãn val/test cho bộ chấm điểm. Chỉ bộ chấm điểm được gọi hàm này.

Mọi cache phải lấy khóa từ DataView.cache_key(), khóa gồm mode, split_id và snapshot hash.
"""
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .manifest import read_json
from .paths import ROOT, snapshot_dir
from .splits import SPLIT_ID, split_dir

EVIDENCE = "evidence"
PREDICTION = "prediction"
CACHE_DIR = ROOT / "data" / "cache"


def snapshot_hash(snap: Path) -> str:
    tables = read_json(snap / "manifest.json")["tables"]
    joined = ",".join(f"{k}:{v['sha256']}" for k, v in sorted(tables.items()))
    return hashlib.sha256(joined.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class DataView:
    mode: str
    split_id: str | None
    snapshot_hash: str
    drugs: pd.DataFrame = field(repr=False)
    effects: pd.DataFrame = field(repr=False)
    pair_labels: pd.DataFrame = field(repr=False)
    drug_targets: pd.DataFrame = field(repr=False)
    ppi: pd.DataFrame = field(repr=False)

    def cache_key(self, *parts) -> str:
        payload = json.dumps([self.mode, self.split_id, self.snapshot_hash, *parts], default=str)
        return hashlib.sha256(payload.encode()).hexdigest()

    def labels_for_pair(self, drug_x: int, drug_y: int) -> pd.DataFrame:
        a, b = min(drug_x, drug_y), max(drug_x, drug_y)
        rows = self.pair_labels[(self.pair_labels["drug_a"] == a) & (self.pair_labels["drug_b"] == b)]
        return rows.merge(self.effects[["effect_idx", "effect_cui", "effect_name"]], on="effect_idx")


def _load_common(snap: Path) -> dict[str, pd.DataFrame]:
    return {name: pd.read_parquet(snap / f"{name}.parquet") for name in ("drugs", "effects", "drug_targets", "ppi")}


def evidence_view(snap: Path | None = None) -> DataView:
    snap = snap or snapshot_dir()
    return DataView(EVIDENCE, None, snapshot_hash(snap), pair_labels=pd.read_parquet(snap / "pair_labels.parquet"),
                    **_load_common(snap))


def _split_tables(snap: Path, split_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = split_dir(snap, split_id)
    return pd.read_parquet(d / "label_vocab.parquet"), pd.read_parquet(d / "pair_splits.parquet")


def prediction_view(split_id: str = SPLIT_ID, snap: Path | None = None) -> DataView:
    snap = snap or snapshot_dir()
    vocab, pairs = _split_tables(snap, split_id)
    train_pairs = pairs.loc[pairs["split"] == "train", ["drug_a", "drug_b"]]
    labels = pd.read_parquet(snap / "pair_labels.parquet")
    labels = labels[labels["effect_idx"].isin(vocab["effect_idx"])].merge(train_pairs, on=["drug_a", "drug_b"])
    common = _load_common(snap)
    common["effects"] = common["effects"][common["effects"]["effect_idx"].isin(vocab["effect_idx"])]
    return DataView(PREDICTION, split_id, snapshot_hash(snap), pair_labels=labels.reset_index(drop=True), **common)


def load_eval_targets(split: str, split_id: str = SPLIT_ID, snap: Path | None = None
                      ) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    """Trả về (cặp, ma trận nhãn cặp x vocab dạng 0/1, vocab) cho split "val" hoặc "test". Chỉ bộ chấm điểm dùng."""
    if split not in ("val", "test"):
        raise ValueError("Chỉ dùng cho val hoặc test")
    snap = snap or snapshot_dir()
    vocab, pairs = _split_tables(snap, split_id)
    pairs = pairs.loc[pairs["split"] == split, ["drug_a", "drug_b"]].reset_index(drop=True)
    labels = pd.read_parquet(snap / "pair_labels.parquet").merge(vocab[["effect_idx", "label_idx"]], on="effect_idx")
    labels = labels.merge(pairs.reset_index(names="row"), on=["drug_a", "drug_b"])
    y = np.zeros((len(pairs), len(vocab)), dtype=np.int8)
    y[labels["row"].to_numpy(), labels["label_idx"].to_numpy()] = 1
    return pairs, y, vocab


class Cache:
    """Cache JSON trên đĩa; khóa lấy từ view nên hai chế độ không bao giờ đọc chéo của nhau."""

    def __init__(self, view: DataView, root: Path = CACHE_DIR):
        self.view = view
        self.dir = root / view.mode / (view.split_id or "full") / view.snapshot_hash

    def _path(self, *parts) -> Path:
        return self.dir / f"{self.view.cache_key(*parts)}.json"

    def get(self, *parts):
        path = self._path(*parts)
        return json.loads(path.read_text()) if path.exists() else None

    def set(self, value, *parts) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self._path(*parts).write_text(json.dumps(value))
