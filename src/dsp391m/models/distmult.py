"""DistMult cho cặp thuốc × nhãn (plan du_doan_cap/05): s(A,B,e) = sum_j z_Aj * r_ej * z_Bj.

Đối xứng theo A/B vì phép nhân giao hoán. Score là logit xếp hạng (score_kind="bilinear_logit"), không phải
xác suất lâm sàng. Kích thước lấy từ view (số thuốc, số nhãn), không hard-code. Cần torch (requirements-train.txt).
Artifact suy luận lưu trọng số dạng npz (không pickle) cùng model.json; checkpoint huấn luyện nằm ở training/.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

from .. import predictor

WEIGHTS = "weights.npz"
SCORE_BATCH = 4096


class DistMult(nn.Module):
    def __init__(self, n_drugs: int, n_labels: int, dim: int):
        super().__init__()
        self.drug = nn.Embedding(n_drugs, dim)
        self.rel = nn.Embedding(n_labels, dim)
        nn.init.xavier_uniform_(self.drug.weight)
        nn.init.xavier_uniform_(self.rel.weight)

    def forward(self, a: torch.Tensor, b: torch.Tensor, e: torch.Tensor) -> torch.Tensor:
        """a, b: [B]; e: [B] hoặc [B, K] -> score cùng shape với e."""
        pair = self.drug(a) * self.drug(b)
        if e.dim() == 2:
            pair = pair[:, None, :]
        return (pair * self.rel(e)).sum(-1)

    def score_all(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return (self.drug(a) * self.drug(b)) @ self.rel.weight.T


class DistMultPredictor:
    score_kind = "bilinear_logit"

    def __init__(self, module: DistMult, config: dict, ident: dict):
        self.module = module.eval()
        self.config = config
        self.name = f"distmult_d{config['dim']}"
        self.config_id = predictor.config_id(self.name, config)
        self.identity = ident
        self.model_release_id = predictor.release_id(self.name, config, ident, predictor.arrays_digest(self._arrays()))

    def _arrays(self) -> dict:
        return {"drug": self.module.drug.weight.detach().cpu().numpy(),
                "rel": self.module.rel.weight.detach().cpu().numpy()}

    def fit(self, view):
        raise NotImplementedError("Huấn luyện qua dsp391m.training.trainer")

    @torch.no_grad()
    def score_pairs(self, pairs: pd.DataFrame) -> np.ndarray:
        n_drugs, n_labels = self.module.drug.num_embeddings, self.module.rel.num_embeddings
        pairs = predictor.canonical_pairs(pairs, n_drugs)
        a = torch.from_numpy(pairs["drug_a"].to_numpy())
        b = torch.from_numpy(pairs["drug_b"].to_numpy())
        out = [self.module.score_all(a[i:i + SCORE_BATCH], b[i:i + SCORE_BATCH]).numpy()
               for i in range(0, len(pairs), SCORE_BATCH)]
        s = np.concatenate(out) if out else np.zeros((0, n_labels), dtype=np.float32)
        return predictor.check_scores(s, len(pairs), n_labels)

    def save(self, directory: Path) -> str:
        directory.mkdir(parents=True, exist_ok=False)
        np.savez(directory / WEIGHTS, **self._arrays())
        predictor.write_artifact(directory, WEIGHTS, {
            "name": self.name, "score_kind": self.score_kind, "config": self.config, "config_id": self.config_id,
            "model_release_id": self.model_release_id, "identity": self.identity})
        return self.model_release_id

    @classmethod
    def load(cls, directory: Path, view=None) -> "DistMultPredictor":
        meta = predictor.read_artifact(directory, view)
        with np.load(directory / meta["weights_file"]) as z:
            drug, rel = z["drug"], z["rel"]
        module = DistMult(drug.shape[0], rel.shape[0], drug.shape[1])
        module.drug.weight.data = torch.from_numpy(drug.copy())
        module.rel.weight.data = torch.from_numpy(rel.copy())
        model = cls(module, meta["config"], meta["identity"])
        if model.model_release_id != meta["model_release_id"]:
            raise predictor.IntegrityError("Nội dung trọng số không khớp model_release_id")
        return model
