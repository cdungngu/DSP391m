"""GĐ1b: vocabulary nhãn cố định và chia tập theo cặp (plan mục 6.1, D1–D2).

Chạy: python -m dsp391m.splits [--snapshot-dir DIR]

Đầu ra trong <snapshot>/splits/<split_id>/:
- label_vocab.parquet: effect_idx -> label_idx (0..n-1) cho các nhãn có >= MIN_ROWS dòng.
- pair_splits.parquet: drug_a, drug_b, split ("train" | "val" | "test").
- split_manifest.json: tham số, số đếm, hash, phân tích độ nhạy vocabulary.

Split được đóng băng: chạy lại với cùng tham số chỉ xác minh, không ghi; đổi tham số với cùng split_id sẽ bị
từ chối. Mọi nơi đọc split phải qua load_verified_split() (kiểm tra checksum và snapshot).
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .manifest import read_json, sha256, utc_now, write_json
from .paths import snapshot_dir

MIN_ROWS = 500
RATIOS = {"train": 0.7, "val": 0.1, "test": 0.2}
SEED = 391
SPLIT_ID = "pair_70-10-20_s391"


def split_dir(snap: Path, split_id: str = SPLIT_ID) -> Path:
    return snap / "splits" / split_id


def build_vocabulary(effects: pd.DataFrame, min_rows: int = MIN_ROWS) -> pd.DataFrame:
    vocab = effects.loc[effects["n_rows"] >= min_rows, ["effect_idx", "effect_cui", "effect_name", "n_rows"]]
    vocab = vocab.sort_values("effect_idx").reset_index(drop=True)
    vocab.insert(0, "label_idx", np.arange(len(vocab), dtype=np.int16))
    return vocab


def split_pairs(pair_labels: pd.DataFrame, vocab: pd.DataFrame, ratios: dict = RATIOS, seed: int = SEED) -> pd.DataFrame:
    """Chia các cặp có ít nhất một nhãn trong vocabulary. Mọi nhãn của một cặp nằm cùng một split."""
    in_vocab = pair_labels["effect_idx"].isin(vocab["effect_idx"])
    pairs = pair_labels.loc[in_vocab, ["drug_a", "drug_b"]].drop_duplicates().sort_values(["drug_a", "drug_b"])
    pairs = pairs.reset_index(drop=True)
    order = np.random.default_rng(seed).permutation(len(pairs))
    n_train = int(round(ratios["train"] * len(pairs)))
    n_val = int(round(ratios["val"] * len(pairs)))
    split = np.empty(len(pairs), dtype=object)
    split[order[:n_train]] = "train"
    split[order[n_train:n_train + n_val]] = "val"
    split[order[n_train + n_val:]] = "test"
    pairs["split"] = pd.Categorical(split, categories=list(ratios))
    return pairs


def train_only_vocab_size(pair_labels: pd.DataFrame, pairs: pd.DataFrame, min_rows: int = MIN_ROWS) -> int:
    """Độ nhạy: số nhãn đạt ngưỡng nếu ngưỡng chỉ tính trên train (ngưỡng nhân theo tỷ lệ train)."""
    train = pairs.loc[pairs["split"] == "train", ["drug_a", "drug_b"]]
    rows = pair_labels.merge(train, on=["drug_a", "drug_b"])
    return int((rows["effect_idx"].value_counts() >= min_rows * RATIOS["train"]).sum())


class SplitExistsError(RuntimeError):
    """Split ID đã tồn tại với tham số hoặc snapshot khác: phải dùng split ID mới."""


class SplitIntegrityError(RuntimeError):
    """File split hoặc snapshot không khớp manifest: không được dùng."""


SPLIT_FILES = ("label_vocab.parquet", "pair_splits.parquet")


def _params(min_rows: int, seed: int) -> dict:
    return {"min_rows": min_rows, "ratios": RATIOS, "seed": seed, "unit": "unordered drug pair"}


def _snapshot_labels_sha(snap: Path) -> str:
    """Hash pair_labels theo manifest snapshot, sau khi xác minh file thật khớp manifest."""
    expected = read_json(snap / "manifest.json")["tables"]["pair_labels"]["sha256"]
    if sha256(snap / "pair_labels.parquet") != expected:
        raise SplitIntegrityError(f"{snap / 'pair_labels.parquet'} không khớp manifest của snapshot")
    return expected


def load_verified_split(snap: Path, split_id: str = SPLIT_ID) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Đọc split sau khi kiểm tra checksum và quan hệ với snapshot. Trả về (vocab, pairs, split_hash)."""
    d = split_dir(snap, split_id)
    if not (d / "split_manifest.json").exists():
        raise SplitIntegrityError(f"Không có split {split_id!r} trong {snap}")
    manifest = read_json(d / "split_manifest.json")
    if manifest.get("split_id") != split_id:
        raise SplitIntegrityError(f"Manifest ghi split_id {manifest.get('split_id')!r}, khác {split_id!r}")
    if manifest["snapshot_pair_labels_sha256"] != _snapshot_labels_sha(snap):
        raise SplitIntegrityError(f"Split {split_id!r} được tạo từ snapshot khác")
    for name in SPLIT_FILES:
        if sha256(d / name) != manifest["files"][name]:
            raise SplitIntegrityError(f"{name} của split {split_id!r} không khớp checksum trong manifest")
    split_hash = hashlib.sha256(json.dumps([split_id, manifest["files"]], sort_keys=True).encode()).hexdigest()[:16]
    return pd.read_parquet(d / "label_vocab.parquet"), pd.read_parquet(d / "pair_splits.parquet"), split_hash


def run(snap: Path | None = None, split_id: str = SPLIT_ID, min_rows: int = MIN_ROWS, seed: int = SEED) -> dict:
    """Tạo split mới. Nếu split ID đã tồn tại: cùng tham số và snapshot thì chỉ xác minh, không ghi;
    khác thì báo SplitExistsError. Split đã đóng băng không bao giờ bị ghi đè."""
    snap = snap or snapshot_dir()
    out = split_dir(snap, split_id)
    labels_sha = _snapshot_labels_sha(snap)
    if (out / "split_manifest.json").exists():
        existing = read_json(out / "split_manifest.json")
        if existing["params"] != _params(min_rows, seed) or existing["snapshot_pair_labels_sha256"] != labels_sha:
            raise SplitExistsError(
                f"Split {split_id!r} đã tồn tại với tham số/snapshot khác; hãy dùng split_id mới thay vì ghi đè")
        load_verified_split(snap, split_id)
        return existing
    if out.exists() and any(out.iterdir()):
        raise SplitExistsError(f"{out} có file nhưng thiếu manifest; xem lại bằng tay trước khi tạo split")

    effects = pd.read_parquet(snap / "effects.parquet")
    pair_labels = pd.read_parquet(snap / "pair_labels.parquet")
    vocab = build_vocabulary(effects, min_rows)
    pairs = split_pairs(pair_labels, vocab, seed=seed)
    out.mkdir(parents=True, exist_ok=True)
    vocab.to_parquet(out / "label_vocab.parquet", index=False)
    pairs.to_parquet(out / "pair_splits.parquet", index=False)

    labeled = pair_labels[["drug_a", "drug_b"]].drop_duplicates()
    manifest = {
        "split_id": split_id,
        "created_at": utc_now(),
        "snapshot": read_json(snap / "manifest.json")["snapshot"],
        "snapshot_pair_labels_sha256": labels_sha,
        "params": _params(min_rows, seed),
        "labels_in_vocab": len(vocab),
        "pairs_in_split": len(pairs),
        "labeled_pairs_without_vocab_label": len(labeled) - len(pairs),
        "pairs_per_split": pairs["split"].value_counts().reindex(list(RATIOS)).to_dict(),
        "sensitivity_train_only_vocab_size": train_only_vocab_size(pair_labels, pairs, min_rows),
        "files": {name: sha256(out / name) for name in SPLIT_FILES},
    }
    write_json(out / "split_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    m = run(parser.parse_args().snapshot_dir)
    print(f"{m['split_id']}: {m['labels_in_vocab']} nhãn; cặp {m['pairs_per_split']}; "
          f"cặp chỉ có nhãn ngoài vocab: {m['labeled_pairs_without_vocab_label']}; "
          f"vocab nếu chỉ tính trên train: {m['sensitivity_train_only_vocab_size']}")


if __name__ == "__main__":
    main()
