"""B0: dự đoán bằng đếm tần suất, không huấn luyện (plan mục 4, D6).

- popularity: tỷ lệ cặp train có nhãn e; giống nhau cho mọi cặp (mức sàn).
- per_drug:   score(A,B,e) = f(A,e) + f(B,e), với f(d,e) là tỷ lệ cặp train chứa thuốc d có nhãn e.
              Thuốc không có cặp nào trong train dùng tỷ lệ popularity thay cho f.
Chỉ đọc nhãn từ prediction view (train), nên không thể dùng nhãn val/test.
"""
import numpy as np
import pandas as pd

from ..dataview import PREDICTION, DataView


class B0:
    def __init__(self, variant: str = "per_drug"):
        if variant not in ("per_drug", "popularity"):
            raise ValueError(variant)
        self.variant = variant
        self.name = f"b0_{variant}"

    def fit(self, view: DataView) -> "B0":
        if view.mode != PREDICTION or view.label_vocab is None:
            raise ValueError("B0 chỉ được fit trên prediction view")
        vocab = view.label_vocab
        to_label = pd.Series(vocab["label_idx"].to_numpy(), index=vocab["effect_idx"])
        labels = view.pair_labels
        lab = to_label.reindex(labels["effect_idx"]).to_numpy()
        a, b = labels["drug_a"].to_numpy(), labels["drug_b"].to_numpy()
        n_drugs, n_labels = len(view.drugs), len(vocab)

        pairs = labels[["drug_a", "drug_b"]].drop_duplicates()
        self.popularity = np.bincount(lab, minlength=n_labels) / max(len(pairs), 1)
        pairs_per_drug = np.bincount(np.r_[pairs["drug_a"], pairs["drug_b"]], minlength=n_drugs)
        counts = np.zeros((n_drugs, n_labels))
        np.add.at(counts, (a, lab), 1)
        np.add.at(counts, (b, lab), 1)
        freq = counts / np.maximum(pairs_per_drug, 1)[:, None]
        freq[pairs_per_drug == 0] = self.popularity
        self.freq = freq
        self.n_train_pairs_per_drug = pairs_per_drug
        return self

    def score(self, pairs: pd.DataFrame) -> np.ndarray:
        if self.variant == "popularity":
            return np.tile(self.popularity, (len(pairs), 1))
        return self.freq[pairs["drug_a"].to_numpy()] + self.freq[pairs["drug_b"].to_numpy()]
