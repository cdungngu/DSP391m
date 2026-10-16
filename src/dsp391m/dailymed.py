"""GĐ3 (phần DailyMed): đoạn nhãn thuốc (SPL) làm bằng chứng văn bản cho giải thích.

Chạy: python -m dsp391m.dailymed aspirin simvastatin ...      # tên, STITCH ID hoặc CID như lookup
      python -m dsp391m.dailymed --file demo_drugs.txt        # một thuốc mỗi dòng (danh mục demo)

Với mỗi thuốc: tìm SPL theo tên hoạt chất → chọn nhãn đơn chất (tiêu đề bắt đầu bằng tên, không phải
chế phẩm phối hợp), phiên bản mới nhất → tải XML → tách các mục theo mã LOINC thành đoạn (mỗi tiểu mục một
đoạn), giữ set_id, version, ngày xuất bản. Kết quả gộp vào <snapshot>/dailymed_sections.parquet.

Đây là nguồn mạnh nhất trong thứ tự bằng chứng (plan GĐ4), nhưng chỉ phủ các thuốc đã chạy module này.
Chỉ chạy theo danh mục nhỏ (mặc định nghỉ 1 giây mỗi request): DailyMed thuộc NLM, cùng hệ thống từng chặn
IP vì gọi dồn PubChem.
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

from .http import RateLimited, batch_key, cached, request
from .manifest import utc_now, write_json
from .paths import EXTERNAL_DIR, snapshot_dir

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
CACHE = EXTERNAL_DIR / "dailymed"
PAUSE = 1.0
NS = {"v3": "urn:hl7-org:v3"}
SECTIONS = {
    "34073-7": "drug_interactions",
    "43685-7": "warnings_and_precautions",
    "34071-1": "warnings",
    "34070-3": "contraindications",
    "34084-4": "adverse_reactions",
    "34066-1": "boxed_warning",
    "43679-0": "mechanism_of_action",
}


def search_spls(name: str, offline: bool = False) -> list[dict]:
    def fetch():
        r = request("GET", f"{BASE}/spls.json", params={"drug_name": name, "pagesize": 100})
        r.raise_for_status()
        return r.json().get("data", [])

    return cached(CACHE / "search" / f"{batch_key([name.lower()])}.json", fetch, offline, PAUSE)["data"]


def choose_spl(name: str, spls: list[dict]) -> dict | None:
    """Nhãn đơn chất: tiêu đề bắt đầu bằng tên hoạt chất và không chứa ' AND ' (chế phẩm phối hợp)."""
    n = name.upper()
    single = [s for s in spls if s["title"].upper().startswith(n) and " AND " not in s["title"].upper()]
    if not single:
        return None
    return max(single, key=lambda s: (pd.to_datetime(s["published_date"]), s["spl_version"]))


def fetch_spl_xml(setid: str, offline: bool = False) -> str:
    def fetch():
        r = request("GET", f"{BASE}/spls/{setid}.xml")
        r.raise_for_status()
        return r.text

    return cached(CACHE / "spl" / f"{setid}.json", fetch, offline, PAUSE)["data"]


def _text(el) -> str:
    return re.sub(r"\s+", " ", " ".join(el.itertext())).strip() if el is not None else ""


def parse_sections(xml: str) -> list[dict]:
    """Tách các mục quan tâm thành đoạn: phần mở đầu của mục và từng tiểu mục (có tiêu đề) là một đoạn."""
    root = ET.fromstring(xml)
    chunks = []
    for sec in root.iter(f"{{{NS['v3']}}}section"):
        code = sec.find("v3:code", NS)
        kind = SECTIONS.get(code.get("code") if code is not None else None)
        if not kind:
            continue
        title = _text(sec.find("v3:title", NS))
        intro = _text(sec.find("v3:text", NS))
        if intro:
            chunks.append({"section": kind, "title": title, "text": intro})
        for sub in sec.findall("v3:component/v3:section", NS):
            body = " ".join(_text(t) for t in sub.iter(f"{{{NS['v3']}}}text"))
            if body:
                chunks.append({"section": kind, "title": _text(sub.find("v3:title", NS)) or title, "text": body})
    return chunks


def collect(drug_rows: pd.DataFrame, offline: bool = False) -> tuple[pd.DataFrame, list[dict]]:
    rows, status = [], []
    for d in drug_rows.itertuples(index=False):
        try:
            spl = choose_spl(d.display_name, search_spls(d.display_name, offline))
            if spl is None:
                status.append({"stitch_id": d.stitch_id, "name": d.display_name, "status": "no_single_ingredient_spl"})
                continue
            chunks = parse_sections(fetch_spl_xml(spl["setid"], offline))
        except RateLimited as e:
            status.append({"stitch_id": d.stitch_id, "name": d.display_name, "status": f"rate_limited: {e}"})
            break
        for i, c in enumerate(chunks):
            rows.append({"drug_idx": d.drug_idx, "stitch_id": d.stitch_id, "setid": spl["setid"],
                         "spl_version": spl["spl_version"], "published_date": spl["published_date"],
                         "spl_title": spl["title"], "chunk_id": f"dailymed:{spl['setid']}:v{spl['spl_version']}:{i}",
                         **c})
        status.append({"stitch_id": d.stitch_id, "name": d.display_name, "status": "ok", "setid": spl["setid"],
                       "chunks": len(chunks),
                       "has_drug_interactions": any(c["section"] == "drug_interactions" for c in chunks)})
    return pd.DataFrame(rows), status


def find_mentions(sections: pd.DataFrame, drug_a: int, names_b: list[str], section: str = "drug_interactions"
                  ) -> pd.DataFrame:
    """Đoạn trong nhãn của thuốc A (mục `section`) có nhắc tới một tên của thuốc B (khớp nguyên từ).
    Không bắt được cách nhắc theo nhóm thuốc (ví dụ "strong CYP3A4 inhibitors"); đó là giới hạn đã biết."""
    chunks = sections[(sections["drug_idx"] == drug_a) & (sections["section"] == section)]
    terms = [n for n in {n.lower() for n in names_b} if len(n) >= 4]
    if chunks.empty or not terms:
        return chunks.iloc[0:0].assign(matched="")
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, sorted(terms, key=len, reverse=True))) + r")\b", re.I)
    hits = chunks["text"].str.extract(pattern, expand=False)
    return chunks.assign(matched=hits.str.lower()).dropna(subset=["matched"])


def run(tokens: list[str], snap: Path | None = None, offline: bool = False) -> dict:
    from .lookup import load_index  # tránh import vòng

    snap = snap or snapshot_dir()
    index = load_index(snap)
    resolved = [index.resolve(t) for t in tokens]
    idxs = [r.drug_idx for r in resolved if r.drug_idx is not None]
    names = pd.read_parquet(snap / "drug_names.parquet")
    todo = names[names["drug_idx"].isin(idxs)]
    new, status = collect(todo, offline)

    path = snap / "dailymed_sections.parquet"
    old = pd.read_parquet(path) if path.exists() else new.iloc[0:0]
    merged = pd.concat([old[~old["drug_idx"].isin(new["drug_idx"].unique())], new], ignore_index=True) if len(new) else old
    merged.to_parquet(path, index=False)
    report = {
        "created_at": utc_now(), "source": BASE,
        "requested": tokens, "unresolved": [r.input for r in resolved if r.drug_idx is None],
        "status": status,
        "drugs_in_store": int(merged["drug_idx"].nunique()) if len(merged) else 0,
        "chunks_in_store": len(merged),
    }
    write_json(snap / "dailymed_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("drugs", nargs="*")
    parser.add_argument("--file", type=Path, help="danh sách thuốc, một thuốc mỗi dòng")
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    tokens = list(args.drugs) + ([line.strip() for line in args.file.read_text().splitlines() if line.strip()]
                                 if args.file else [])
    r = run(tokens, args.snapshot_dir, args.offline)
    for s in r["status"]:
        print(f"  {s['name']:20s} {s['status']}" + (f" ({s['chunks']} đoạn, DI: {s['has_drug_interactions']})"
                                                      if s["status"] == "ok" else ""))
    if r["unresolved"]:
        print("không nhận diện được:", ", ".join(r["unresolved"]))
    print(f"kho DailyMed: {r['drugs_in_store']} thuốc, {r['chunks_in_store']} đoạn")
    return 0


if __name__ == "__main__":
    sys.exit(main())
