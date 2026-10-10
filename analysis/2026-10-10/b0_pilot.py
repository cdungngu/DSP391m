"""Thử nghiệm B0 tạm thời (không phải split chính thức) để quyết định có nên huấn luyện mô hình.

Split 80/20 theo cặp, seed 0, trên 963 nhãn có >=500 dòng; chấm toàn bộ ma trận cặp x nhãn.
Cần snapshot từ `python -m dsp391m.etl` và scikit-learn. Kết quả: b0_pilot.json cùng thư mục.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
SNAP = ROOT / "data" / "processed" / "decagon_v1"
labels = pd.read_parquet(SNAP / "pair_labels.parquet")
effects = pd.read_parquet(SNAP / "effects.parquet")
keep = effects.loc[effects.n_rows >= 500, "effect_idx"].to_numpy()
remap = -np.ones(len(effects), int)
remap[keep] = np.arange(len(keep))
labels = labels[np.isin(labels.effect_idx, keep)].assign(e=lambda d: remap[d.effect_idx])

pairs = labels[["drug_a", "drug_b"]].drop_duplicates().to_numpy()
perm = np.random.default_rng(0).permutation(len(pairs))
test_set = set(map(tuple, pairs[perm[: int(0.2 * len(pairs))]]))
is_test = np.array([k in test_set for k in zip(labels.drug_a, labels.drug_b)])
train, test = labels[~is_test], labels[is_test]

n_drugs, n_eff = 645, len(keep)
train_pairs = train[["drug_a", "drug_b"]].drop_duplicates()
pairs_per_drug = np.bincount(np.r_[train_pairs.drug_a, train_pairs.drug_b], minlength=n_drugs)
counts = np.zeros((n_drugs, n_eff))
np.add.at(counts, (train.drug_a.to_numpy(), train.e.to_numpy()), 1)
np.add.at(counts, (train.drug_b.to_numpy(), train.e.to_numpy()), 1)
freq = counts / np.maximum(pairs_per_drug, 1)[:, None]

test_pairs = pd.DataFrame(sorted(test_set), columns=["a", "b"])
row = {k: i for i, k in enumerate(map(tuple, test_pairs.to_numpy()))}
Y = np.zeros((len(test_pairs), n_eff), np.int8)
Y[[row[k] for k in zip(test.drug_a, test.drug_b)], test.e.to_numpy()] = 1


def evaluate(S):
    cols = np.where(Y.sum(0) > 0)[0]
    return {
        "macro_ap": float(np.mean([average_precision_score(Y[:, j], S[:, j]) for j in cols])),
        "macro_auroc": float(np.mean([roc_auc_score(Y[:, j], S[:, j]) for j in cols])),
        "micro_ap": float(average_precision_score(Y.ravel(), S.ravel())),
    }


popularity = np.tile(np.bincount(train.e, minlength=n_eff) / len(train_pairs), (len(test_pairs), 1))
result = {
    "note": "Pilot split 80/20 by pair, seed 0; NOT the official split. Full-matrix evaluation.",
    "test_pairs": len(test_pairs), "labels": n_eff, "positive_rate": float(Y.mean()),
    "popularity": evaluate(popularity),
    "b0_per_drug_sum": evaluate(freq[test_pairs.a] + freq[test_pairs.b]),
}
(Path(__file__).parent / "b0_pilot.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
