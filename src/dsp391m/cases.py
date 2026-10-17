"""Lô ca val để xem thủ công (plan du_doan_cap/06, gói duyệt đợt 1). Chỉ val; không dùng test.

Chạy: python -m dsp391m.cases --base <model_release_id> --cand <model_release_id> --out results/val/error_analysis/<id>.json
      [--markdown analysis/<ngày>/<id>.md] [--per-group 5] [--seed 391]

Quy tắc chọn (cố định trước khi xem ca):
- delta = NDCG@10(cand) − NDCG@10(base) theo từng cặp val (cặp không có nhãn quan sát bị loại).
- improve: delta lớn nhất; decline: delta nhỏ nhất (hòa: drug_a, drug_b tăng dần).
- low_degree: cặp có bậc train nhỏ hơn của hai thuốc nằm ở tertile thấp (ngưỡng tính trên cặp train), thứ tự
  hoán vị default_rng([seed, 1]); random: mọi cặp val, hoán vị default_rng([seed, 2]).
- Điền theo thứ tự improve → decline → low_degree → random; cặp đã chọn thì lấy cặp kế tiếp trong chính nhóm đó.
Mỗi ca gồm ID, tên kèm cờ (tên chờ duyệt, cờ cấu trúc, kiểu khớp ChEMBL, panel target rộng), độ phủ, nhãn quan
sát trên val, top-10 của hai model kèm điểm, và provenance. Nhãn quan sát là âm giả định cho phần còn lại: nhãn
không quan sát trong top-10 không có nghĩa là sai ngoài đời. Không dùng kết quả này làm benchmark accuracy.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import metrics, predictor
from .dataview import load_eval_targets, prediction_view, train_label_matrix
from .evaluate import RESULTS_DIR, check_label_order, cui_rank, load_scores
from .manifest import git_commit, utc_now
from .paths import snapshot_dir
from .releases import publish
from .splits import SPLIT_ID

GROUPS = ("improve", "decline", "low_degree", "random")
BROAD_PANEL_MIN_TARGETS = 100  # cùng ngưỡng với lookup.py
TOP_K = 10
RULE = __doc__.split("Quy tắc chọn")[1].split("Mỗi ca gồm")[0].strip()


def group_orders(delta: np.ndarray, pairs: pd.DataFrame, low_mask: np.ndarray, seed: int) -> dict:
    """Thứ tự ứng viên của từng nhóm (chỉ số hàng val)."""
    valid = np.flatnonzero(np.isfinite(delta))
    a, b = pairs["drug_a"].to_numpy()[valid], pairs["drug_b"].to_numpy()[valid]
    return {
        "improve": valid[np.lexsort((b, a, -delta[valid]))],
        "decline": valid[np.lexsort((b, a, delta[valid]))],
        "low_degree": np.random.default_rng([seed, 1]).permutation(valid[low_mask[valid]]),
        "random": np.random.default_rng([seed, 2]).permutation(valid),
    }


def select(orders: dict, per_group: int) -> list[tuple[str, int, int]]:
    """(nhóm, thứ hạng trong nhóm, hàng val); bỏ trùng bằng cặp kế tiếp trong cùng nhóm."""
    chosen, seen = [], set()
    for g in GROUPS:
        taken = 0
        for rank, row in enumerate(orders[g]):
            if taken == per_group:
                break
            if row in seen:
                continue
            seen.add(int(row))
            chosen.append((g, rank, int(row)))
            taken += 1
    return chosen


def _drug_table(view, snap: Path, degree: np.ndarray) -> pd.DataFrame:
    d = view.drugs[["drug_idx", "stitch_id", "n_targets"]].copy()
    d["train_degree"] = degree[d["drug_idx"].to_numpy()]
    d["broad_target_panel"] = d["n_targets"] > BROAD_PANEL_MIN_TARGETS
    optional = {"drug_names.parquet": ["display_name", "name_source", "needs_review"],
                "drug_structures.parquet": ["flags"], "chembl_map.parquet": ["match_type"]}
    for file, cols in optional.items():
        if (snap / file).exists():
            t = pd.read_parquet(snap / file)[["drug_idx", *cols]]
            if file == "drug_names.parquet":
                t = t.rename(columns={"needs_review": "name_needs_review"})
            d = d.merge(t, on="drug_idx", how="left")
    if (snap / "chembl_mechanisms.parquet").exists():
        mech = pd.read_parquet(snap / "chembl_mechanisms.parquet")
        human = set(mech.loc[mech["is_human"], "drug_idx"])
        d["chembl_human_mechanism"] = d["drug_idx"].isin(human)
    return d.set_index("drug_idx")


def _top(s_row: np.ndarray, y_row: np.ndarray, order: np.ndarray, vocab: pd.DataFrame) -> list[dict]:
    return [{"rank": r + 1, "effect_cui": vocab.at[j, "effect_cui"], "effect_name": vocab.at[j, "effect_name"],
             "score": float(s_row[j]), "observed": bool(y_row[j])} for r, j in enumerate(order[:TOP_K])]


def _clean(v):
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return None if not np.isfinite(v) else float(v)
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else v


def run(base: str, cand: str, out: Path, per_group: int = 5, seed: int = 391, split_id: str = SPLIT_ID,
        snap: Path | None = None, results_dir: Path = RESULTS_DIR) -> dict:
    snap_path = snap or snapshot_dir()
    view = prediction_view(split_id, snap)
    ident = predictor.identity(view)
    pairs, y, vocab = load_eval_targets("val", split_id, snap)
    check_label_order(view, vocab)
    phash = predictor.pairs_hash(pairs)
    scores = {m: load_scores(results_dir, "val", m, phash, ident) for m in (base, cand)}
    rank = cui_rank(vocab)
    pm = {m: metrics.pair_metrics(y, s, rank) for m, s in scores.items()}
    order = {m: metrics.topk_order(s, rank) for m, s in scores.items()}
    delta = pm[cand]["ndcg@10"] - pm[base]["ndcg@10"]

    train_pairs, _ = train_label_matrix(view)
    degree = np.bincount(train_pairs.ravel(), minlength=len(view.drugs))
    low_edge = float(np.quantile(np.minimum(degree[train_pairs[:, 0]], degree[train_pairs[:, 1]]), 1 / 3))
    pair_deg = np.minimum(degree[pairs["drug_a"].to_numpy()], degree[pairs["drug_b"].to_numpy()])
    chosen = select(group_orders(delta, pairs, pair_deg <= low_edge, seed), per_group)

    drugs = _drug_table(view, snap_path, degree)
    voc = vocab.set_index("label_idx")
    cases = []
    for g, g_rank, row in chosen:
        a, b = int(pairs.at[row, "drug_a"]), int(pairs.at[row, "drug_b"])
        obs = np.flatnonzero(y[row])
        top = {m: _top(scores[m][row], y[row], order[m][row], voc) for m in (base, cand)}
        overlap = len({t["effect_cui"] for t in top[base]} & {t["effect_cui"] for t in top[cand]})
        cases.append({
            "case_id": f"{g}-{g_rank + 1:02d}", "group": g, "rank_in_group": g_rank + 1, "val_row": row,
            "drugs": [{"drug_idx": d, **{k: _clean(v) for k, v in drugs.loc[d].items()}} for d in (a, b)],
            "pair_min_train_degree": int(pair_deg[row]), "low_degree_edge": low_edge,
            "n_observed_labels": int(len(obs)),
            "observed_labels": [{"effect_cui": voc.at[j, "effect_cui"], "effect_name": voc.at[j, "effect_name"]}
                                for j in obs],
            "models": {m: {"ndcg@10": _clean(pm[m]["ndcg@10"][row]), "pair_ap": _clean(pm[m]["pair_ap"][row]),
                           "precision@10": _clean(pm[m]["precision@10"][row]), "top10": top[m]}
                       for m in (base, cand)},
            "ndcg10_delta": _clean(delta[row]), "top10_overlap": overlap,
        })
    result = {
        "schema_version": 1, "created_at": utc_now(), "git_commit": git_commit(), "split": "val",
        "base": base, "cand": cand, "identity": ident, "pairs_hash": phash, "seed": seed, "per_group": per_group,
        "selection_rule": RULE, "n_cases": len(cases), "n_val_pairs_eligible": int(np.isfinite(delta).sum()),
        "interpretation": ("Nhãn quan sát của Decagon là ground truth giả định; nhãn không quan sát trong top-10 "
                           "không chứng minh sai. Ca để phát hiện nhãn bệnh nền, thuốc mơ hồ, dự đoán giống nhau "
                           "và hiển thị gây hiểu sai; không phải đánh giá đúng/sai y khoa."),
        "cases": cases,
    }
    publish(out, result)
    return result


def render_markdown(r: dict) -> str:
    base, cand = r["base"], r["cand"]
    lines = [f"# Lô {r['n_cases']} ca val — {base} vs {cand}", "",
             f"Tạo {r['created_at']} · commit `{r['git_commit'][:10]}` · split hash `{r['identity']['split_hash']}` "
             f"· seed {r['seed']}. Chỉ val; không dùng test.", "",
             f"**Quy tắc chọn:** {r['selection_rule']}", "", f"**Cách đọc:** {r['interpretation']} "
             "✓ = nhãn có quan sát trên val cho cặp này.", ""]
    for c in r["cases"]:
        names = []
        for d in c["drugs"]:
            flags = [f for f in (("tên chờ duyệt" if d.get("name_needs_review") else None),
                                 (f"cấu trúc: {d['flags']}" if d.get("flags") else None),
                                 (f"ChEMBL: {d['match_type']}" if d.get("match_type") not in (None, "exact") else None),
                                 ("panel target rộng" if d.get("broad_target_panel") else None)) if f]
            names.append(f"**{d.get('display_name') or d['stitch_id']}** (`{d['stitch_id']}`, bậc train "
                         f"{d['train_degree']}, {d['n_targets']} target{'; ' + '; '.join(flags) if flags else ''})")
        mb, mc = c["models"][base], c["models"][cand]
        lines += [f"## {c['case_id']}: {names[0]} + {names[1]}", "",
                  f"Nhãn quan sát: {c['n_observed_labels']} · bậc train nhỏ hơn: {c['pair_min_train_degree']} · "
                  f"NDCG@10 {mb['ndcg@10']:.3f} → {mc['ndcg@10']:.3f} (Δ {c['ndcg10_delta']:+.3f}) · "
                  f"top-10 trùng {c['top10_overlap']}/10", "",
                  f"| # | {base} | điểm | {cand} | điểm |", "|---:|---|---:|---|---:|"]
        for tb, tc in zip(mb["top10"], mc["top10"]):
            lines.append(f"| {tb['rank']} | {'✓ ' if tb['observed'] else ''}{tb['effect_name']} (`{tb['effect_cui']}`) "
                         f"| {tb['score']:.3f} | {'✓ ' if tc['observed'] else ''}{tc['effect_name']} "
                         f"(`{tc['effect_cui']}`) | {tc['score']:.3f} |")
        lines += ["", "Ghi chú người xem: _…_", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True)
    parser.add_argument("--cand", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--per-group", type=int, default=5)
    parser.add_argument("--seed", type=int, default=391)
    args = parser.parse_args(argv)
    if args.markdown and args.markdown.exists():
        print(f"{args.markdown} đã tồn tại; không ghi đè", file=sys.stderr)
        return 2
    r = run(args.base, args.cand, args.out, args.per_group, args.seed)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(r) + "\n")
    for c in r["cases"]:
        names = " + ".join(d.get("display_name") or d["stitch_id"] for d in c["drugs"])
        print(f"{c['case_id']:14s} Δ NDCG {c['ndcg10_delta']:+.3f}  bậc {c['pair_min_train_degree']:4d}  {names}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
