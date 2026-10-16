"""GĐ2: tra cứu bằng chứng cho một đơn thuốc (evidence mode, không LLM).

Chạy: python -m dsp391m.lookup warfarin aspirin "CID000002173" [--json] [--top 15] [--context 5]

Với 2–10 thuốc: chuẩn hóa đầu vào → tạo mọi cặp không thứ tự → tra nhãn Decagon đã quan sát → gộp theo
tác dụng phụ, giữ các cặp đóng góp và ID bằng chứng → thêm bối cảnh target/PPI có giới hạn → báo phần thiếu dữ liệu.

Ba trường hợp được tách riêng (plan GĐ2):
- đầu vào không nhận diện được hoặc mơ hồ: nằm trong `unresolved`, không xử lý tiếp;
- cặp không có nhãn đã ghi nhận: `status = "no_data"` cho riêng cặp đó, các cặp khác vẫn có kết quả;
- thuốc thiếu target: giữ nguyên kết quả nhãn, chỉ đánh dấu phần bối cảnh cơ chế là thiếu.

Nhãn Decagon là liên hệ thống kê từ báo cáo tự phát. Không có nhãn KHÔNG có nghĩa là an toàn.
Chế độ này dùng toàn bộ dữ liệu nên KHÔNG được dùng để chấm điểm dự đoán.
"""
import argparse
import difflib
import itertools
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .dataview import EVIDENCE, DataView, evidence_view
from .manifest import utc_now
from .names import normalize
from .paths import snapshot_dir

MIN_DRUGS, MAX_DRUGS = 2, 10
# Thuốc có hơn ngưỡng này target trong Decagon gần như dùng chung một panel khoảng 158 gene GPCR (83/284 thuốc,
# Jaccard trung vị 0,88): target của chúng ít đặc hiệu, "target chung" với thuốc khác phần lớn là nhiễu.
BROAD_PANEL_MIN_TARGETS = 100
CONTEXT_NOTE = "Bối cảnh cấu trúc (target/PPI không có chiều tác động), không phải bằng chứng cơ chế."
LABEL_NOTE = ("Nhãn Decagon là liên hệ thống kê từ báo cáo tự phát (TWOSIDES/FAERS), không xác lập nhân quả, "
              "mức độ hay tần suất. Không có nhãn không có nghĩa là an toàn.")


def evidence_id(stitch_a: str, stitch_b: str, cui: str) -> str:
    return f"decagon:combo:{stitch_a}:{stitch_b}:{cui}"


@dataclass
class Resolution:
    input: str
    drug_idx: int | None = None
    match: str | None = None  # "stitch_id" | "pubchem_cid" | "name"
    reason: str | None = None  # "not_found" | "ambiguous"
    candidates: list[int] | None = None


class EvidenceIndex:
    """Chỉ mục tra cứu nhanh trên một evidence view. Dựng một lần, truy vấn nhiều lần."""

    def __init__(self, view: DataView, drug_names: pd.DataFrame | None = None, gene_names: pd.DataFrame | None = None,
                 mechanisms: pd.DataFrame | None = None, label_sections: pd.DataFrame | None = None):
        if view.mode != EVIDENCE:
            raise ValueError("EvidenceIndex chỉ dùng evidence view; benchmark phải dùng prediction view")
        self.view = view
        self.n_drugs = len(view.drugs)
        labels = view.pair_labels
        key = labels["drug_a"].to_numpy(np.int64) * self.n_drugs + labels["drug_b"].to_numpy(np.int64)
        order = np.argsort(key, kind="stable")
        self.key, self.label_effect = key[order], labels["effect_idx"].to_numpy()[order]

        effects = view.effects.set_index("effect_idx").sort_index()
        self.effect_cui = effects["effect_cui"].to_numpy()
        self.effect_name = effects["effect_name"].to_numpy()
        # Tỷ lệ nền: phần trăm cặp có nhãn mang tác dụng phụ này (mỗi bộ ba cặp–nhãn là duy nhất sau ETL).
        n_labeled_pairs = len(np.unique(self.key))
        self.base_rate = np.bincount(self.label_effect, minlength=len(effects)) / max(n_labeled_pairs, 1)

        drugs = view.drugs.set_index("drug_idx").sort_index()
        self.stitch = drugs["stitch_id"].to_numpy()
        self.by_stitch = {s.upper(): i for i, s in enumerate(self.stitch)}
        self.by_cid = {int(c): i for i, c in enumerate(drugs["pubchem_cid"])}

        self.names = np.array(self.stitch, dtype=object)
        self.name_review = np.zeros(self.n_drugs, dtype=bool)
        self.name_index: dict[str, set[int]] = {}
        if drug_names is not None:
            dn = drug_names.set_index("drug_idx").sort_index()
            self.names = dn["display_name"].to_numpy(dtype=object)
            self.name_review = dn["needs_review"].to_numpy()
            for idx, row in dn.iterrows():
                if row["name_cid"] is not None and not pd.isna(row["name_cid"]):
                    self.by_cid.setdefault(int(row["name_cid"]), idx)
                for s in {row["display_name"], *row["synonyms"]}:
                    self.name_index.setdefault(normalize(s), set()).add(idx)

        self.targets = {d: set(g["gene_id"]) for d, g in view.drug_targets.groupby("drug_idx")}
        self.ppi_a = view.ppi["gene_a"].to_numpy()
        self.ppi_b = view.ppi["gene_b"].to_numpy()
        self.degree = pd.Series(np.concatenate([self.ppi_a, self.ppi_b])).value_counts().to_dict()
        self.symbol = {}
        if gene_names is not None:
            self.symbol = dict(zip(gene_names["gene_id"], gene_names["symbol"]))
        # Nguồn GĐ3 (tùy chọn): cơ chế ChEMBL và đoạn nhãn DailyMed.
        self.mechanisms = {d: g for d, g in mechanisms.groupby("drug_idx")} if mechanisms is not None else None
        self.label_sections = label_sections
        self.labelled_drugs = set(label_sections["drug_idx"]) if label_sections is not None else set()
        self.drug_name_terms: dict[int, list[str]] = {}
        if drug_names is not None:
            for row in drug_names.itertuples(index=False):
                self.drug_name_terms[row.drug_idx] = [row.display_name, *row.synonyms]

    # ---- chuẩn hóa đầu vào ----
    def resolve(self, token: str) -> Resolution:
        raw = token.strip()
        t = raw.upper().replace(" ", "")
        if t in self.by_stitch:
            return Resolution(raw, self.by_stitch[t], "stitch_id")
        m = re.fullmatch(r"(?:CID)?0*(\d+)", t)
        if m and int(m.group(1)) in self.by_cid:
            return Resolution(raw, self.by_cid[int(m.group(1))], "pubchem_cid")
        hits = self.name_index.get(normalize(raw), set())
        if len(hits) == 1:
            return Resolution(raw, next(iter(hits)), "name")
        if len(hits) > 1:
            return Resolution(raw, reason="ambiguous", candidates=sorted(hits))
        close = difflib.get_close_matches(normalize(raw), list(self.name_index), n=3, cutoff=0.8)
        return Resolution(raw, reason="not_found", candidates=sorted({i for c in close for i in self.name_index[c]}))

    # ---- tra cứu ----
    def pair_effects(self, x: int, y: int) -> np.ndarray:
        a, b = min(x, y), max(x, y)
        k = a * self.n_drugs + b
        lo, hi = np.searchsorted(self.key, k, "left"), np.searchsorted(self.key, k, "right")
        return self.label_effect[lo:hi]

    def mechanism_context(self, x: int, y: int, limit: int) -> dict:
        missing = [self.stitch[d] for d in (x, y) if not self.targets.get(d)]
        if missing:
            return {"status": "missing_targets", "missing_for": missing, "note": CONTEXT_NOTE}
        broad = [self.stitch[d] for d in (x, y) if len(self.targets[d]) > BROAD_PANEL_MIN_TARGETS]
        tx, ty = self.targets[x], self.targets[y]
        shared = sorted(tx & ty)
        ox, oy = np.array(sorted(tx - ty)), np.array(sorted(ty - tx))
        hit = (np.isin(self.ppi_a, ox) & np.isin(self.ppi_b, oy)) | (np.isin(self.ppi_a, oy) & np.isin(self.ppi_b, ox))
        links = []
        for ga, gb in zip(self.ppi_a[hit], self.ppi_b[hit]):
            gx, gy = (ga, gb) if ga in tx else (gb, ga)
            # Phạt mềm theo bậc: cạnh giữa hai protein hub có điểm thấp, nhưng không bị xóa.
            score = 1.0 / np.sqrt(self.degree.get(gx, 1) * self.degree.get(gy, 1))
            links.append((score, int(gx), int(gy)))
        links.sort(reverse=True)
        return {
            "status": "low_specificity" if broad else "available",
            "broad_panel_drugs": broad,
            "n_targets": [len(tx), len(ty)],
            "shared_targets": [self._gene(g) for g in shared[:limit]],
            "n_shared_targets": len(shared),
            "ppi_links": [{"from": self._gene(gx), "to": self._gene(gy), "score": round(s, 5)}
                          for s, gx, gy in links[:limit]],
            "n_ppi_links": len(links),
            "note": CONTEXT_NOTE,
        }

    def drug_mechanisms(self, d: int) -> list[dict]:
        if self.mechanisms is None or d not in self.mechanisms:
            return []
        return [{"evidence_id": f"chembl:mechanism:{m.mec_id}", "action_type": m.action_type,
                 "mechanism_of_action": m.mechanism_of_action, "target_chembl_id": m.target_chembl_id,
                 "target_name": m.target_name, "organism": m.organism, "is_human": bool(m.is_human),
                 "gene_symbols": list(m.gene_symbols),
                 "refs": list(m.refs)[:3]}
                for m in self.mechanisms[d].itertuples(index=False)]

    def shared_mechanism_targets(self, x: int, y: int) -> list[dict]:
        """Target ChEMBL (chỉ của người) mà cả hai thuốc cùng tác động, kèm chiều tác động của từng thuốc.
        Đây là giả thuyết cặp dựa trên hai fact đơn thuốc, không phải bằng chứng tương tác hay outcome (plan 04)."""
        mx = [m for m in self.drug_mechanisms(x) if m["is_human"]]
        my = [m for m in self.drug_mechanisms(y) if m["is_human"]]
        out = []
        for t in sorted({m["target_chembl_id"] for m in mx} & {m["target_chembl_id"] for m in my}):
            ax = sorted({m["action_type"] for m in mx if m["target_chembl_id"] == t})
            ay = sorted({m["action_type"] for m in my if m["target_chembl_id"] == t})
            name = next(m["target_name"] for m in mx if m["target_chembl_id"] == t)
            out.append({"target_chembl_id": t, "target_name": name, "actions": [ax, ay], "kind": "pair_hypothesis",
                        "evidence_ids": [m["evidence_id"] for m in mx + my if m["target_chembl_id"] == t]})
        return out

    def label_mentions(self, x: int, y: int, limit: int) -> list[dict]:
        """Đoạn mục Drug Interactions trong nhãn DailyMed của thuốc này có nhắc tên thuốc kia."""
        if self.label_sections is None:
            return []
        from .dailymed import find_mentions

        out = []
        for a, b in ((x, y), (y, x)):
            hits = find_mentions(self.label_sections, a, self.drug_name_terms.get(b, []))
            for h in hits.head(limit).itertuples(index=False):
                pos = h.text.lower().find(h.matched)
                snippet = h.text[max(0, pos - 160): pos + 240]
                out.append({"evidence_id": h.chunk_id, "label_of": self.stitch[a], "mentions": self.stitch[b],
                            "section_title": h.title, "matched": h.matched, "snippet": snippet,
                            "spl_title": h.spl_title, "published_date": h.published_date})
        return out

    def _gene(self, gene_id: int) -> dict:
        return {"gene_id": int(gene_id), "symbol": self.symbol.get(gene_id), "ppi_degree": int(self.degree.get(gene_id, 0))}

    def _drug(self, d: int) -> dict:
        return {"stitch_id": self.stitch[d], "name": self.names[d], "name_needs_review": bool(self.name_review[d])}

    # ---- đơn thuốc ----
    def review(self, tokens: list[str], context_limit: int = 5, sort: str = "pairs") -> dict:
        start = time.perf_counter()
        result = {"mode": EVIDENCE, "snapshot_hash": self.view.snapshot_hash, "generated_at": utc_now(),
                  "query": {"inputs": tokens}, "drugs": [], "unresolved": [], "duplicates": [],
                  "pairs": [], "effects": [], "missing_data": [], "notes": [LABEL_NOTE]}
        chosen: list[int] = []
        for res in map(self.resolve, tokens):
            if res.drug_idx is None:
                result["unresolved"].append({"input": res.input, "reason": res.reason,
                                             "candidates": [self._drug(c) for c in res.candidates or []]})
                result["missing_data"].append({"scope": "input", "subject": res.input,
                                               "what": "không nhận diện được thuốc" if res.reason == "not_found"
                                               else "tên mơ hồ, cần chọn một thuốc cụ thể"})
            elif res.drug_idx in chosen:
                result["duplicates"].append({"input": res.input, "same_as": self.stitch[res.drug_idx]})
            else:
                chosen.append(res.drug_idx)
                n_t = len(self.targets.get(res.drug_idx, ()))
                mecs = self.drug_mechanisms(res.drug_idx)
                result["drugs"].append({"input": res.input, "match": res.match, **self._drug(res.drug_idx),
                                        "n_targets": n_t, "mechanisms": mecs,
                                        "has_label": res.drug_idx in self.labelled_drugs})
                if self.mechanisms is not None and not mecs:
                    result["missing_data"].append({"scope": "drug", "subject": self.stitch[res.drug_idx],
                                                   "what": "không có cơ chế ChEMBL"})
                if self.label_sections is not None and res.drug_idx not in self.labelled_drugs:
                    result["missing_data"].append({"scope": "drug", "subject": self.stitch[res.drug_idx],
                                                   "what": "chưa có nhãn DailyMed trong kho (chạy dsp391m.dailymed)"})
                if n_t == 0:
                    result["missing_data"].append({"scope": "drug", "subject": self.stitch[res.drug_idx],
                                                   "what": "không có target trong snapshot: thiếu bối cảnh cơ chế; "
                                                           "nhãn tương tác vẫn được tra cứu"})
        if not MIN_DRUGS <= len(chosen) <= MAX_DRUGS:
            result["status"] = "error"
            result["error"] = f"cần {MIN_DRUGS}–{MAX_DRUGS} thuốc đã nhận diện, hiện có {len(chosen)}"
            return result

        contributions: dict[int, list[tuple[int, int]]] = {}
        for x, y in itertools.combinations(sorted(chosen), 2):
            effects = self.pair_effects(x, y)
            pair = {"drugs": [self._drug(x), self._drug(y)],
                    "status": "observed" if len(effects) else "no_data",
                    "n_effects": int(len(effects)),
                    "mechanism_context": self.mechanism_context(x, y, context_limit),
                    "shared_mechanism_targets": self.shared_mechanism_targets(x, y),
                    "label_mentions": self.label_mentions(x, y, context_limit)}
            result["pairs"].append(pair)
            if not len(effects):
                result["missing_data"].append({"scope": "pair", "subject": [self.stitch[x], self.stitch[y]],
                                               "what": "không có nhãn tác dụng phụ đã ghi nhận cho cặp này "
                                                       "(chưa quan sát, không có nghĩa là an toàn)"})
            for e in effects:
                contributions.setdefault(int(e), []).append((x, y))

        n_pairs_total = len(chosen) * (len(chosen) - 1) // 2
        for e, pairs in contributions.items():
            base = float(self.base_rate[e])
            result["effects"].append({
                "effect_id": self.effect_cui[e], "effect_name": self.effect_name[e], "status": "observed",
                "n_contributing_pairs": len(pairs),
                "base_rate": round(base, 4),
                # Heuristic xếp hạng (quan sát / kỳ vọng nếu cặp trong đơn giống một cặp ngẫu nhiên có nhãn),
                # không phải xác suất hay mức độ nguy cơ.
                "enrichment": round(len(pairs) / (n_pairs_total * base), 2) if base else None,
                "contributing_pairs": [[self.stitch[x], self.stitch[y]] for x, y in pairs],
                "evidence_ids": [evidence_id(self.stitch[x], self.stitch[y], self.effect_cui[e]) for x, y in pairs],
            })
        if sort == "pairs":
            result["effects"].sort(key=lambda r: (-r["n_contributing_pairs"], r["base_rate"], r["effect_name"].lower()))
        else:
            result["effects"].sort(key=lambda r: (-(r["enrichment"] or 0), -r["n_contributing_pairs"],
                                                  r["effect_name"].lower()))
        result["ranking"] = {"sort": sort, "note": "Chưa có cách xếp hạng đã kiểm chứng. 'pairs' đẩy tác dụng phụ chung "
                             "chung lên đầu; 'enrichment' (số cặp / (số cặp trong đơn × tỷ lệ nền)) đẩy nhãn hiếm, "
                             "có thể là nhiễu. Cả hai là heuristic, không phải xác suất hay mức độ nguy cơ."}
        n_pairs = len(result["pairs"])
        result["coverage"] = {
            "drugs_resolved": len(chosen), "pairs_total": n_pairs,
            "pairs_with_labels": sum(p["status"] == "observed" for p in result["pairs"]),
            "drugs_with_targets": sum(d["n_targets"] > 0 for d in result["drugs"]),
            "distinct_effects": len(result["effects"]),
        }
        result["status"] = "ok"
        result["timing"] = {"query_seconds": round(time.perf_counter() - start, 4)}
        return result


def load_index(snap: Path | None = None) -> EvidenceIndex:
    snap = snap or snapshot_dir()
    names = pd.read_parquet(snap / "drug_names.parquet") if (snap / "drug_names.parquet").exists() else None
    genes = pd.read_parquet(snap / "gene_names.parquet") if (snap / "gene_names.parquet").exists() else None
    mecs = pd.read_parquet(snap / "chembl_mechanisms.parquet") if (snap / "chembl_mechanisms.parquet").exists() else None
    labels = pd.read_parquet(snap / "dailymed_sections.parquet") if (snap / "dailymed_sections.parquet").exists() else None
    return EvidenceIndex(evidence_view(snap), names, genes, mecs, labels)


def _label(d: dict) -> str:
    flag = " (tên cần duyệt)" if d.get("name_needs_review") else ""
    return f"{d['name']} [{d['stitch_id']}]{flag}"


def render_text(r: dict, top: int = 15) -> str:
    out = [f"Đơn thuốc ({r['mode']} mode, snapshot {r['snapshot_hash']})"]
    for d in r["drugs"]:
        mec = "; ".join(sorted({f"{m['action_type']} {m['target_name']}" for m in d.get("mechanisms", [])
                                if m["is_human"]})[:3])
        out.append(f"  • {_label(d)}: nhập '{d['input']}' ({d['match']}), {d['n_targets']} target Decagon"
                   + (f"; cơ chế ChEMBL: {mec}" if mec else ""))
    for u in r["unresolved"]:
        cands = ", ".join(_label(c) for c in u["candidates"]) or "không có gợi ý"
        reason = "không tìm thấy" if u["reason"] == "not_found" else "mơ hồ"
        out.append(f"  ✗ '{u['input']}': {reason}. Gợi ý: {cands}")
    for dup in r["duplicates"]:
        out.append(f"  = '{dup['input']}' trùng với {dup['same_as']}, đã bỏ qua")
    if r["status"] != "ok":
        out.append(f"\nLỗi: {r['error']}")
        return "\n".join(out)

    c = r["coverage"]
    out.append(f"\nCặp thuốc: {c['pairs_with_labels']}/{c['pairs_total']} cặp có nhãn đã ghi nhận; "
               f"{c['distinct_effects']} tác dụng phụ khác nhau.")
    for p in r["pairs"]:
        a, b = (d["name"] for d in p["drugs"])
        line = f"  - {a} + {b}: " + (f"{p['n_effects']} tác dụng phụ đã ghi nhận" if p["status"] == "observed"
                                    else "KHÔNG có dữ liệu (chưa quan sát, không có nghĩa là an toàn)")
        ctx = p["mechanism_context"]
        if ctx["status"] == "low_specificity":
            line += (f"; bối cảnh target ít đặc hiệu ({', '.join(ctx['broad_panel_drugs'])} có >{BROAD_PANEL_MIN_TARGETS}"
                     f" target dạng panel rộng; {ctx['n_shared_targets']} target chung, bỏ qua khi diễn giải)")
        elif ctx["status"] == "available":
            shared = ", ".join(g["symbol"] or str(g["gene_id"]) for g in ctx["shared_targets"])
            line += f"; bối cảnh: {ctx['n_shared_targets']} target chung" + (f" ({shared})" if shared else "")
            line += f", {ctx['n_ppi_links']} liên kết PPI giữa target"
        else:
            line += "; bối cảnh cơ chế: thiếu target cho " + ", ".join(ctx["missing_for"])
        out.append(line)
        for t in p.get("shared_mechanism_targets", []):
            out.append(f"      giả thuyết: cùng tác động lên {t['target_name']} (ChEMBL, chưa phải bằng chứng tương tác): "
                       f"{a} {'/'.join(t['actions'][0])}, {b} {'/'.join(t['actions'][1])}")
        for m in p.get("label_mentions", []):
            who = a if m["label_of"] == p["drugs"][0]["stitch_id"] else b
            out.append(f"      nhãn DailyMed của {who}, mục \"{m['section_title']}\": …{m['snippet']}… [{m['evidence_id']}]")

    if r["effects"]:
        order = "mức trội so với tỷ lệ nền" if r["ranking"]["sort"] == "enrichment" else "số cặp đóng góp"
        out.append(f"\nTác dụng phụ đã ghi nhận (top {min(top, len(r['effects']))}/{len(r['effects'])}, xếp theo {order}):")
        names = {d["stitch_id"]: d["name"] for d in r["drugs"]}
        for e in r["effects"][:top]:
            if e["n_contributing_pairs"] == c["pairs_total"] > 1:
                pairs = f"tất cả {c['pairs_total']} cặp"
            else:
                pairs = "; ".join(f"{names[a]} + {names[b]}" for a, b in e["contributing_pairs"])
            out.append(f"  {e['effect_name']} ({e['effect_id']}): {e['n_contributing_pairs']}/{c['pairs_total']} cặp, "
                       f"tỷ lệ nền {e['base_rate']:.1%}, trội ×{e['enrichment']} ← {pairs}")
    if r["missing_data"]:
        out.append("\nThiếu dữ liệu:")
        for m in r["missing_data"]:
            subject = " + ".join(m["subject"]) if isinstance(m["subject"], list) else m["subject"]
            out.append(f"  ! [{m['scope']}] {subject}: {m['what']}")
    out.append("\nLưu ý: " + " ".join(r["notes"]) + " " + CONTEXT_NOTE)
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("drugs", nargs="+", help="tên thuốc, STITCH ID (CID000002173) hoặc PubChem CID; có thể ngăn bằng dấu phẩy")
    parser.add_argument("--json", action="store_true", help="xuất JSON đầy đủ thay cho văn bản")
    parser.add_argument("--top", type=int, default=15, help="số tác dụng phụ hiển thị ở dạng văn bản")
    parser.add_argument("--context", type=int, default=5, help="số target chung / liên kết PPI tối đa mỗi cặp")
    parser.add_argument("--sort", choices=["pairs", "enrichment"], default="pairs",
                        help="pairs (mặc định): số cặp đóng góp, hòa thì nhãn hiếm hơn trước; "
                             "enrichment: mức trội so với tỷ lệ nền (dễ đẩy nhãn hiếm, nhiễu lên đầu)")
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    tokens = [t.strip() for arg in args.drugs for t in arg.split(",") if t.strip()]

    t0 = time.perf_counter()
    index = load_index(args.snapshot_dir)
    load_s = time.perf_counter() - t0
    result = index.review(tokens, args.context, args.sort)
    result.setdefault("timing", {})["load_seconds"] = round(load_s, 3)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str) if args.json else render_text(result, args.top))
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())
