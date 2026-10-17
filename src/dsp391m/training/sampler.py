"""Sampler âm train-only (plan du_doan_cap/05).

Chỉ nhận ma trận nhãn train (dataview.train_label_matrix); không đọc snapshot hay nhãn val/test.
Mỗi positive (cặp p, nhãn e) lấy tối đa n_neg nhãn e' chưa quan sát trên chính cặp p, không hoàn lại trong nhóm.
RNG mỗi epoch là default_rng([seed, epoch]) nên resume ở ranh giới epoch cho cùng batch mà không cần lưu RNG.
Không có vòng lặp vô hạn: rút một lô ứng viên, thiếu thì chọn từ phần bù của cặp; cặp có phần bù < n_neg dùng mask.
"""
from collections.abc import Iterator

import numpy as np

OVERSAMPLE = 4


class NegativeSampler:
    def __init__(self, y_train: np.ndarray, n_neg: int = 5, batch_size: int = 2048, seed: int = 391):
        if y_train.dtype != bool or y_train.ndim != 2:
            raise ValueError("y_train phải là ma trận bool [n_cặp, n_nhãn]")
        self.y = y_train
        self.n_neg, self.batch_size, self.seed = n_neg, batch_size, seed
        self.pos_pair, self.pos_label = np.nonzero(y_train)
        self.n_labels = y_train.shape[1]

    def __len__(self) -> int:
        return -(-len(self.pos_pair) // self.batch_size)

    def negatives(self, pair_rows: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
        k, m = self.n_neg, self.n_neg * OVERSAMPLE
        cand = rng.integers(0, self.n_labels, (len(pair_rows), m))
        valid = ~self.y[pair_rows[:, None], cand]
        for j in range(1, m):  # bỏ ứng viên trùng trong cùng hàng, giữ lần xuất hiện đầu
            valid[:, j] &= ~(cand[:, :j] == cand[:, j:j + 1]).any(1)
        pick = np.argsort(~valid, axis=1, kind="stable")[:, :k]
        neg = np.take_along_axis(cand, pick, 1)
        mask = np.take_along_axis(valid, pick, 1)
        for i in np.where(~mask.all(1))[0]:
            complement = np.flatnonzero(~self.y[pair_rows[i]])
            chosen = rng.choice(complement, min(k, len(complement)), replace=False)
            neg[i, :len(chosen)], neg[i, len(chosen):] = chosen, 0
            mask[i] = np.arange(k) < len(chosen)
        return neg, mask

    def epoch(self, epoch: int) -> Iterator[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
        """Duyệt mỗi positive đúng một lần: (pair_rows, labels, negatives [B,K], mask [B,K])."""
        rng = np.random.default_rng([self.seed, epoch])
        perm = rng.permutation(len(self.pos_pair))
        for start in range(0, len(perm), self.batch_size):
            idx = perm[start:start + self.batch_size]
            rows = self.pos_pair[idx]
            neg, mask = self.negatives(rows, rng)
            yield rows, self.pos_label[idx], neg, mask
