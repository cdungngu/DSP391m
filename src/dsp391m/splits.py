"""GĐ1b: vocabulary nhãn cố định và chia tập theo cặp (plan mục 6.1, D1–D2).

Chạy: python -m dsp391m.splits [--snapshot-dir DIR]

Đầu ra trong <snapshot>/splits/<split_id>/:
- label_vocab.parquet: effect_idx -> label_idx (0..n-1) cho các nhãn có >= MIN_ROWS dòng.
- pair_splits.parquet: drug_a, drug_b, split ("train" | "val" | "test").
- split_manifest.json: tham số, số đếm, hash, phân tích độ nhạy vocabulary.

Split được đóng băng: chạy lại với cùng tham số phải cho cùng hash. Muốn đổi thì tạo split_id mới,
không ghi đè split cũ.
"""
import argparse
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


def run(snap: Path | None = None, split_id: str = SPLIT_ID, min_rows: int = MIN_ROWS) -> dict:
    snap = snap or snapshot_dir()
    out = split_dir(snap, split_id)
    out.mkdir(parents=True, exist_ok=True)
    effects = pd.read_parquet(snap / "effects.parquet")
    pair_labels = pd.read_parquet(snap / "pair_labels.parquet")

    vocab = build_vocabulary(effects, min_rows)
    pairs = split_pairs(pair_labels, vocab)
    vocab.to_parquet(out / "label_vocab.parquet", index=False)
    pairs.to_parquet(out / "pair_splits.parquet", index=False)

    labeled = pair_labels[["drug_a", "drug_b"]].drop_duplicates()
    manifest = {
        "split_id": split_id,
        "created_at": utc_now(),
        "snapshot": read_json(snap / "manifest.json")["snapshot"],
        "snapshot_pair_labels_sha256": read_json(snap / "manifest.json")["tables"]["pair_labels"]["sha256"],
        "params": {"min_rows": min_rows, "ratios": RATIOS, "seed": SEED, "unit": "unordered drug pair"},
        "labels_in_vocab": len(vocab),
        "pairs_in_split": len(pairs),
        "labeled_pairs_without_vocab_label": len(labeled) - len(pairs),
        "pairs_per_split": pairs["split"].value_counts().reindex(list(RATIOS)).to_dict(),
        "sensitivity_train_only_vocab_size": train_only_vocab_size(pair_labels, pairs, min_rows),
        "files": {name: sha256(out / name) for name in ("label_vocab.parquet", "pair_splits.parquet")},
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
