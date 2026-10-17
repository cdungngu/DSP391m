"""DistMult, sampler và trainer (plan du_doan_cap/05). Bỏ qua nếu chưa cài requirements-train.txt."""
import numpy as np
import pandas as pd
import pytest

torch = pytest.importorskip("torch")

from dsp391m import dataview, evaluate  # noqa: E402
from dsp391m.models.distmult import WEIGHTS, DistMult, DistMultPredictor  # noqa: E402
from dsp391m.releases import IntegrityError  # noqa: E402
from dsp391m.training.sampler import NegativeSampler  # noqa: E402
from dsp391m.training.trainer import Trainer, TrainConfig  # noqa: E402


def test_score_hand_computed_and_symmetric():
    m = DistMult(3, 2, 2)
    m.drug.weight.data = torch.tensor([[1.0, 2.0], [3.0, -1.0], [0.5, 0.5]])
    m.rel.weight.data = torch.tensor([[1.0, 1.0], [2.0, 0.0]])
    a, b = torch.tensor([0]), torch.tensor([1])
    # z0*z1 = [3, -2]; r0 -> 1; r1 -> 6
    assert m(a, b, torch.tensor([0])).item() == pytest.approx(1.0)
    assert m(a, b, torch.tensor([[0, 1]])).tolist() == [[1.0, 6.0]]
    assert torch.equal(m.score_all(a, b), m.score_all(b, a))
    assert m.score_all(a, b).tolist() == [[1.0, 6.0]]


def test_sampler_negatives_are_unobserved_unique_and_reproducible():
    rng = np.random.default_rng(0)
    y = rng.random((30, 12)) < 0.4
    y[0] = True
    y[0, :2] = False          # cặp 0 chỉ còn 2 nhãn âm: phải dùng mask
    y[1] = False
    y[1, 0] = True
    s = NegativeSampler(y, n_neg=5, batch_size=7, seed=3)
    seen = []
    for rows, labels, neg, mask in s.epoch(0):
        assert y[rows, labels].all()
        for r, n, mk in zip(rows, neg, mask):
            chosen = n[mk]
            assert not y[r, chosen].any() and len(set(chosen)) == len(chosen)
            assert mk.sum() == min(5, (~y[r]).sum())
        seen += list(zip(rows, labels))
    assert sorted(seen) == sorted(zip(*np.nonzero(y)))       # mỗi positive đúng một lần
    a = [n.tolist() for *_, n, _ in s.epoch(1)]
    b = [n.tolist() for *_, n, _ in NegativeSampler(y, 5, 7, 3).epoch(1)]
    assert a == b and a != [n.tolist() for *_, n, _ in s.epoch(2)]


def _trainer(snap, out, callback, **kw):
    view = dataview.prediction_view(snap=snap)
    cfg = TrainConfig(dim=8, lr=0.05, batch_size=64, **kw)
    return view, cfg, Trainer(view, cfg, out, callback)


def test_overfit_fixture_loss_decreases(snap, tmp_path):
    _, _, t = _trainer(snap, tmp_path / "run", lambda f: 0.0, max_epochs=30, patience=100)
    state = t.fit()
    losses = [h["loss"] for h in state["history"]]
    assert losses[-1] < 0.5 * losses[0]
    assert all(np.isfinite(losses)) and state["stopped"] == "max_epochs"


def test_early_stopping_keeps_earliest_best(snap, tmp_path):
    seq = iter([0.1, 0.3, 0.3, 0.30005, 0.2, 0.9])
    _, _, t = _trainer(snap, tmp_path / "run", lambda f: next(seq), max_epochs=10, patience=3)
    state = t.fit()
    assert state["best_epoch"] == 1 and state["stopped"] == "early_stopping"
    assert len(state["history"]) == 5


def test_resume_matches_continuous_run(snap, tmp_path):
    view, cfg, full = _trainer(snap, tmp_path / "full", lambda f: 0.5, max_epochs=4, patience=10)
    full.fit()
    _, _, part = _trainer(snap, tmp_path / "part", lambda f: 0.5, max_epochs=4, patience=10)
    part.fit(2)
    resumed = Trainer.resume(view, cfg, tmp_path / "part", lambda f: 0.5)
    resumed.fit()
    for k, v in full.model.state_dict().items():
        assert torch.equal(v, resumed.model.state_dict()[k])
    strip = lambda h: [{k: x[k] for k in ("epoch", "loss")} for x in h]  # noqa: E731
    assert strip(full.state["history"]) == strip(resumed.state["history"])
    with pytest.raises(IntegrityError):
        Trainer.resume(view, TrainConfig(dim=8, lr=0.01, batch_size=64, max_epochs=4), tmp_path / "part",
                       lambda f: 0.5)


def test_best_predictor_save_load_and_tamper(snap, tmp_path):
    callback = evaluate.val_macro_ap_callback(snap=snap)
    view, _, t = _trainer(snap, tmp_path / "run", callback, max_epochs=3, patience=10)
    state = t.fit()
    best = t.best_predictor()
    pairs, _, _ = dataview.load_eval_targets("val", snap=snap)
    assert callback(best.score_pairs) == pytest.approx(state["best_metric"])
    swapped = pairs.rename(columns={"drug_a": "drug_b", "drug_b": "drug_a"})
    assert np.array_equal(best.score_pairs(pairs), best.score_pairs(swapped))
    rid = best.save(tmp_path / "m")
    loaded = DistMultPredictor.load(tmp_path / "m", view)
    assert loaded.model_release_id == rid
    assert np.array_equal(loaded.score_pairs(pairs), best.score_pairs(pairs))
    other = view.__class__(**{**view.__dict__, "split_hash": "x"})
    with pytest.raises(IntegrityError):
        DistMultPredictor.load(tmp_path / "m", other)
    np.savez(tmp_path / "m" / WEIGHTS, drug=np.zeros((2, 2), np.float32), rel=np.zeros((2, 2), np.float32))
    with pytest.raises(IntegrityError):
        DistMultPredictor.load(tmp_path / "m", view)
    r = evaluate.run_fitted(best, view, snap=snap, results_dir=tmp_path / "res")
    assert r["score_kind"] == "bilinear_logit" and r["metrics"]["macro_ap"] == pytest.approx(state["best_metric"])
    with pytest.raises(ValueError):
        best.score_pairs(pd.DataFrame({"drug_a": [0], "drug_b": [0]}))
