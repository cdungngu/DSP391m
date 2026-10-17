"""B0: dự đoán bằng đếm tần suất, không huấn luyện (plan du_doan_cap/04).

- popularity: tỷ lệ cặp train có nhãn e; giống nhau cho mọi cặp (mức sàn).
- per_drug:   score(A,B,e) = f(A,e) + f(B,e), với f_alpha(d,e) = (n_de + alpha*p_e) / (N_d + alpha).
              Thuốc không có cặp nào trong train dùng p_e thay cho f.
Chỉ đọc nhãn từ prediction view (train), nên không thể dùng nhãn val/test.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from .. import predictor
from ..dataview import PREDICTION, DataView

WEIGHTS = "weights.npz"


class B0:
    score_kind = "frequency_sum"

    def __init__(self, variant: str = "per_drug", alpha: float = 0):
        if variant not in ("per_drug", "popularity"):
            raise ValueError(variant)
        self.variant = variant
        if not np.isfinite(alpha) or alpha < 0:
            raise ValueError("Smoothing alpha must be finite and non-negative")
        self.alpha = float(alpha)
        self.name = f"b0_alpha{self.alpha:g}" if variant == "per_drug" else "b0_popularity"
        self.config = {"model": "b0", "variant": variant} | ({"alpha": self.alpha} if variant == "per_drug" else {})
        self.config_id = predictor.config_id(self.name, self.config)

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
        freq = (counts + self.alpha * self.popularity) / np.maximum(pairs_per_drug + self.alpha, 1)[:, None]
        freq[pairs_per_drug == 0] = self.popularity
        self.freq = freq
        self.n_train_pairs_per_drug = pairs_per_drug
        self._set_release(predictor.identity(view))
        return self

    def _arrays(self) -> dict:
        return {"freq": self.freq, "popularity": self.popularity, "n_train_pairs_per_drug": self.n_train_pairs_per_drug}

    def _set_release(self, ident: dict) -> None:
        self.identity = ident
        self.model_release_id = predictor.release_id(self.name, self.config, ident, predictor.arrays_digest(self._arrays()))

    def score(self, pairs: pd.DataFrame) -> np.ndarray:
        """Điểm float64 theo thứ tự cột đầu vào (giữ cho mã cũ); mã mới dùng score_pairs."""
        if not hasattr(self, "freq"):
            raise ValueError("Fit B0 before scoring")
        indices = pairs[["drug_a", "drug_b"]].to_numpy()
        if indices.dtype.kind not in "iu" or (indices < 0).any() or (indices >= len(self.freq)).any():
            raise ValueError("Pair contains unknown or non-integer drug indices")
        if self.variant == "popularity":
            return np.tile(self.popularity, (len(pairs), 1))
        return self.freq[pairs["drug_a"].to_numpy()] + self.freq[pairs["drug_b"].to_numpy()]

    def score_pairs(self, pairs: pd.DataFrame) -> np.ndarray:
        if not hasattr(self, "freq"):
            raise ValueError("Fit B0 before scoring")
        pairs = predictor.canonical_pairs(pairs, len(self.freq))
        return predictor.check_scores(self.score(pairs), len(pairs), len(self.popularity))

    def save(self, directory: Path) -> str:
        directory.mkdir(parents=True, exist_ok=False)
        np.savez(directory / WEIGHTS, **self._arrays())
        predictor.write_artifact(directory, WEIGHTS, {
            "name": self.name, "score_kind": self.score_kind, "config": self.config, "config_id": self.config_id,
            "model_release_id": self.model_release_id, "identity": self.identity})
        return self.model_release_id

    @classmethod
    def load(cls, directory: Path, view: DataView | None = None) -> "B0":
        meta = predictor.read_artifact(directory, view)
        cfg = meta["config"]
        model = cls(cfg["variant"], cfg.get("alpha", 0))
        if model.config != cfg:
            raise predictor.IntegrityError("Config trong artifact không hợp lệ cho B0")
        with np.load(directory / meta["weights_file"]) as z:
            model.freq, model.popularity = z["freq"], z["popularity"]
            model.n_train_pairs_per_drug = z["n_train_pairs_per_drug"]
        model._set_release(meta["identity"])
        if model.model_release_id != meta["model_release_id"]:
            raise predictor.IntegrityError("Nội dung trọng số không khớp model_release_id")
        return model
