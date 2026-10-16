"""Tên hiển thị và chỉ mục tên cho thuốc (PubChem) và gene target (NCBI Gene).

Chạy: python -m dsp391m.names [--snapshot-dir DIR] [--offline]

Vấn đề: CID trong Decagon thường là dạng "flat" hoặc dạng ion (ví dụ CID 2173 là anion của ampicillin), và
PubChem gần như không có tên thường gọi cho các CID đó. Cách xử lý cho mỗi thuốc:
1. Lấy synonyms của chính CID. Nếu synonym đầu trông như tên thuốc thì dùng (name_source = "self").
2. Nếu không: lấy CID cha (parent) rồi các CID cùng connectivity với cha; chọn CID có nhiều synonym nhất
   (name_source = "related"). Cách này có thể nhầm giữa các đồng phân lập thể (ofloxacin và levofloxacin),
   nên mọi tên "related" đều có needs_review = True để dược sĩ duyệt.

Đầu ra trong snapshot: drug_names.parquet, gene_names.parquet, names_report.json.
Phản hồi API được cache trong data/external/{pubchem,ncbi}/ để chạy lại không cần mạng (--offline).
"""
import argparse
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests

from .http import OfflineCacheMiss, RateLimited, batch_key as _batch_key, cached as _cached, request as _request  # noqa: F401
from .manifest import utc_now, write_json
from .paths import EXTERNAL_DIR, snapshot_dir

PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBCHEM_CACHE = EXTERNAL_DIR / "pubchem"
NCBI_CACHE = EXTERNAL_DIR / "ncbi"
MAX_SYNONYMS = 30
MAX_RELATED = 20
NAME_LIKE = re.compile(r"[A-Za-z][A-Za-z0-9 ,'()+\-]{2,40}")


def _synonym_cache() -> dict[int, list[str]]:
    """Đọc cache synonym: file theo từng CID (`cid_<n>.json`) và file theo lô cũ (phản hồi PubChem nguyên văn)."""
    out: dict[int, list[str]] = {}
    for path in sorted((PUBCHEM_CACHE / "synonyms").glob("*.json")):
        payload = json.loads(path.read_text())
        if path.name.startswith("cid_"):
            out[int(path.stem[4:])] = payload["synonyms"]
            continue
        for info in payload["data"].get("InformationList", {}).get("Information", []):
            out[int(info["CID"])] = info.get("Synonym", [])[:MAX_SYNONYMS * 4]
        for cid in payload.get("requested_cids", []):
            out.setdefault(int(cid), [])
    return out


def fetch_synonyms(cids: list[int], offline: bool = False, strict: bool = True) -> dict[int, list[str]]:
    """Synonym theo CID, cache từng CID. strict=False: lô nào lỗi mạng thì bỏ qua (CID đó vắng trong kết quả)."""
    cache = _synonym_cache()
    missing = sorted(set(cids) - set(cache))
    for i in range(0, len(missing), 100):
        batch = missing[i:i + 100]
        if offline:
            if strict:
                raise OfflineCacheMiss(f"Thiếu synonym cho {len(missing)} CID ở chế độ --offline")
            break
        try:
            r = _request("POST", f"{PUG}/compound/cid/synonyms/JSON", data={"cid": ",".join(map(str, batch))})
            payload = {} if r.status_code == 404 else (r.raise_for_status() or r.json())
        except requests.RequestException:
            if strict:
                raise
            break
        got = {int(x["CID"]): x.get("Synonym", [])[:MAX_SYNONYMS * 4]
               for x in payload.get("InformationList", {}).get("Information", [])}
        (PUBCHEM_CACHE / "synonyms").mkdir(parents=True, exist_ok=True)
        for cid in batch:  # CID không có synonym cũng được ghi để không hỏi lại
            cache[cid] = got.get(cid, [])
            (PUBCHEM_CACHE / "synonyms" / f"cid_{cid}.json").write_text(
                json.dumps({"fetched_at": utc_now(), "synonyms": cache[cid]}))
        time.sleep(0.3)
    return {c: cache[c] for c in cids if c in cache}


def _cid_list(url: str, path: Path, offline: bool) -> list[int]:
    def fetch():
        r = _request("GET", url)
        if r.status_code == 404:
            return {}
        r.raise_for_status()
        return r.json()

    data = _cached(path, fetch, offline)["data"]
    return [int(c) for c in data.get("IdentifierList", {}).get("CID", [])]


def related_cids(cid: int, offline: bool = False) -> list[int]:
    parents = _cid_list(f"{PUG}/compound/cid/{cid}/cids/JSON?cids_type=parent",
                        PUBCHEM_CACHE / "parent" / f"{cid}.json", offline)
    out: list[int] = []
    for p in parents or [cid]:
        same = _cid_list(f"{PUG}/compound/fastidentity/cid/{p}/cids/JSON?identity_type=same_connectivity",
                         PUBCHEM_CACHE / "same_connectivity" / f"{p}.json", offline)
        out += [p] + same[:MAX_RELATED]
    return list(dict.fromkeys(out))


def is_name_like(synonym: str | None) -> bool:
    """Tên thuốc thường gọi: ngắn, bắt đầu bằng chữ, không phải mã số hay tên IUPAC dài."""
    if not synonym or not NAME_LIKE.fullmatch(synonym):
        return False
    letters = sum(ch.isalpha() for ch in synonym)
    return letters >= 0.6 * len(synonym.replace(" ", "")) and not re.fullmatch(r"[A-Z0-9\-]+", synonym)


def normalize(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def resolve_drug_names(drugs: pd.DataFrame, offline: bool = False) -> pd.DataFrame:
    own = fetch_synonyms(drugs["pubchem_cid"].tolist(), offline)
    choice: dict[int, tuple[int, str]] = {}
    pending: dict[int, list[int]] = {}
    for cid in drugs["pubchem_cid"]:
        syns = own.get(cid, [])
        if syns and is_name_like(syns[0]):
            choice[cid] = (cid, "self")
            continue
        try:
            pending[cid] = related_cids(cid, offline)
        except (requests.RequestException, OfflineCacheMiss):
            choice[cid] = (cid, "pending")  # chưa tra được CID liên quan; chạy lại sau sẽ bổ sung từ cache
    related_syns = fetch_synonyms(sorted({c for cs in pending.values() for c in cs}), offline, strict=False)
    for cid, cands in pending.items():
        if any(c not in related_syns for c in cands):
            choice[cid] = (cid, "pending")  # thiếu synonym của CID liên quan do API giới hạn
            continue
        named = [c for c in cands if related_syns.get(c) and is_name_like(related_syns[c][0])]
        best = max(named, key=lambda c: len(related_syns[c]), default=None)
        choice[cid] = (best, "related") if best else (cid, "none")

    rows = []
    for d in drugs.itertuples(index=False):
        name_cid, source = choice[d.pubchem_cid]
        syns = (own if source != "related" else related_syns).get(name_cid, [])
        display = syns[0] if syns and is_name_like(syns[0]) else d.stitch_id
        if source == "pending":
            syns = []  # synonym của CID gốc ở đây là tên IUPAC/mã, không dùng làm chỉ mục tên
        rows.append({"drug_idx": d.drug_idx, "stitch_id": d.stitch_id, "pubchem_cid": d.pubchem_cid,
                     "name_cid": name_cid, "name_source": source, "display_name": display,
                     "synonyms": [s for s in syns[:MAX_SYNONYMS * 4] if is_name_like(s)][:MAX_SYNONYMS],
                     "needs_review": source != "self"})
    return pd.DataFrame(rows)


def _trim_gene_summary(payload: dict) -> dict:
    """Chỉ giữ symbol và mô tả để cache nhỏ (bản tóm tắt đầy đủ của NCBI rất lớn)."""
    result = payload["result"]
    return {"result": {"uids": result.get("uids", []),
                       **{u: {"name": result[u].get("name"), "description": result[u].get("description")}
                          for u in result.get("uids", [])}}}


def fetch_gene_names(gene_ids: list[int], offline: bool = False) -> pd.DataFrame:
    rows = []
    for i in range(0, len(gene_ids), 300):
        batch = sorted(gene_ids[i:i + 300])

        def fetch(batch=batch):
            r = _request("POST", ESUMMARY, data={"db": "gene", "id": ",".join(map(str, batch)), "retmode": "json"})
            r.raise_for_status()
            return _trim_gene_summary(r.json())

        result = _cached(NCBI_CACHE / "gene_summary" / f"{_batch_key(batch)}.json", fetch, offline)["data"]["result"]
        for uid in result.get("uids", []):
            rec = result[uid]
            rows.append({"gene_id": int(uid), "symbol": rec.get("name") or None,
                         "description": rec.get("description") or None})
    return pd.DataFrame(rows, columns=["gene_id", "symbol", "description"])


def run(snap: Path | None = None, offline: bool = False) -> dict:
    snap = snap or snapshot_dir()
    drugs = pd.read_parquet(snap / "drugs.parquet")
    names = resolve_drug_names(drugs, offline)
    names.to_parquet(snap / "drug_names.parquet", index=False)

    genes = sorted(set(pd.read_parquet(snap / "drug_targets.parquet")["gene_id"]))
    gene_names = fetch_gene_names(genes, offline)
    gene_names.to_parquet(snap / "gene_names.parquet", index=False)

    return write_report(snap, names, gene_names)


def write_report(snap: Path, names: pd.DataFrame, gene_names: pd.DataFrame) -> dict:
    genes = gene_names["gene_id"].tolist()
    index: dict[str, set[int]] = {}
    for row in names.itertuples(index=False):
        for s in {row.display_name, *row.synonyms}:
            index.setdefault(normalize(s), set()).add(row.drug_idx)
    collisions = {k: sorted(v) for k, v in index.items() if len(v) > 1}
    report = {
        "created_at": utc_now(),
        "drugs": len(names),
        "name_source_counts": names["name_source"].value_counts().to_dict(),
        "needs_review": int(names["needs_review"].sum()),
        "pending_related_lookup": int((names["name_source"] == "pending").sum()),
        "display_name_is_stitch_id": int((names["display_name"] == names["stitch_id"]).sum()),
        "ambiguous_name_keys": len(collisions),
        "ambiguous_examples": dict(list(collisions.items())[:20]),
        "target_genes": len(genes),
        "target_genes_with_symbol": int(gene_names["symbol"].notna().sum()),
        "review_list": names.loc[names["needs_review"], ["stitch_id", "name_cid", "name_source", "display_name"]]
        .to_dict("records"),
    }
    write_json(snap / "names_report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    parser.add_argument("--offline", action="store_true", help="chỉ dùng cache, không gọi API")
    args = parser.parse_args()
    r = run(args.snapshot_dir, args.offline)
    print(f"thuốc: {r['drugs']}; nguồn tên: {r['name_source_counts']}; cần duyệt: {r['needs_review']}; "
          f"không có tên: {r['display_name_is_stitch_id']}; khóa tên mơ hồ: {r['ambiguous_name_keys']}")
    if r["pending_related_lookup"]:
        print(f"CHƯA XONG: {r['pending_related_lookup']} thuốc chưa tra được CID liên quan (API bị giới hạn); "
              "chạy lại lệnh này sau, phần đã có được lấy từ cache")
    print(f"gene target: {r['target_genes_with_symbol']}/{r['target_genes']} có symbol")


if __name__ == "__main__":
    main()
