"""Ánh xạ thuốc -> cấu trúc phân tử qua PubChem PUG REST, kiểm tra bằng RDKit.

Chạy: python -m dsp391m.structures [--snapshot-dir DIR] [--offline]

Đầu ra trong snapshot:
- drug_structures.parquet: mỗi thuốc một dòng, gồm SMILES, InChIKey, tên, trạng thái và cờ cảnh báo.
- structure_coverage.json: độ phủ theo nhóm thuốc và danh sách trường hợp cần xem tay.

Phản hồi PubChem được cache nguyên văn trong data/external/pubchem/, nên chạy lại không gọi
mạng (--offline bắt buộc chỉ dùng cache). Bước này chỉ đo độ phủ và kiểm tra RDKit
parse/tạo được fingerprint; việc lưu fingerprint làm feature thuộc B1 (GĐ3).
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import pandas as pd
import requests
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator

from .manifest import read_json, utc_now, write_json
from .paths import EXTERNAL_DIR, snapshot_dir

PUG_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/property/{props}/JSON"
PROPERTIES = "Title,InChIKey,SMILES,ConnectivitySMILES,MolecularFormula,Charge,HeavyAtomCount"
# PubChem đổi tên trường SMILES theo thời gian; lấy trường đầu tiên có mặt.
SMILES_FIELDS = ("SMILES", "IsomericSMILES", "ConnectivitySMILES", "CanonicalSMILES")
BATCH_SIZE = 100
CACHE_DIR = EXTERNAL_DIR / "pubchem"

MORGAN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
RDLogger.DisableLog("rdApp.*")


def _cache_path(cids: list[int]) -> Path:
    key = hashlib.sha256(",".join(map(str, cids)).encode()).hexdigest()[:16]
    return CACHE_DIR / f"props_{key}.json"


def fetch_properties(cids: list[int], offline: bool = False) -> dict[int, dict]:
    """Trả về {cid: record PubChem}. CID không có trong phản hồi sẽ vắng mặt."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    records: dict[int, dict] = {}
    for i in range(0, len(cids), BATCH_SIZE):
        batch = sorted(cids[i:i + BATCH_SIZE])
        path = _cache_path(batch)
        if path.exists():
            payload = json.loads(path.read_text())
        elif offline:
            raise FileNotFoundError(f"Thiếu cache cho batch {i // BATCH_SIZE} ({path.name}) ở chế độ --offline")
        else:
            resp = requests.post(PUG_URL.format(props=PROPERTIES), data={"cid": ",".join(map(str, batch))}, timeout=60)
            resp.raise_for_status()
            payload = {"requested_cids": batch, "fetched_at": utc_now(), "response": resp.json()}
            path.write_text(json.dumps(payload))
            time.sleep(0.3)  # PubChem giới hạn khoảng 5 request/giây
        for rec in payload["response"].get("PropertyTable", {}).get("Properties", []):
            records[int(rec["CID"])] = rec
    return records


def assess(record: dict | None) -> dict:
    """Đánh giá một record PubChem: có SMILES không, RDKit có parse và tạo fingerprint được không, cờ cảnh báo."""
    if record is None:
        return {"status": "not_found", "flags": ""}
    smiles = next((record[f] for f in SMILES_FIELDS if record.get(f)), None)
    out = {
        "title": record.get("Title"),
        "inchikey": record.get("InChIKey"),
        "smiles": smiles,
        "formula": record.get("MolecularFormula"),
        "charge": record.get("Charge"),
        "heavy_atoms": record.get("HeavyAtomCount"),
    }
    if not smiles:
        return {**out, "status": "no_smiles", "flags": ""}
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {**out, "status": "parse_failed", "flags": ""}
    MORGAN.GetFingerprint(mol)
    flags = []
    if "." in smiles:
        flags.append("multi_component")  # muối, hỗn hợp: có thể không phải hoạt chất gốc
    if (record.get("Charge") or 0) != 0:
        flags.append("charged")
    if (record.get("HeavyAtomCount") or 0) <= 3:
        flags.append("tiny")  # ion hoặc phân tử rất nhỏ, ví dụ calcium cation (CID 271)
    return {**out, "status": "ok", "flags": ",".join(flags)}


def build(drugs: pd.DataFrame, records: dict[int, dict]) -> pd.DataFrame:
    rows = [{"drug_idx": d.drug_idx, "stitch_id": d.stitch_id, "pubchem_cid": d.pubchem_cid,
             "in_combo": d.in_combo, "has_targets": d.n_targets > 0, **assess(records.get(d.pubchem_cid))}
            for d in drugs.itertuples(index=False)]
    cols = ["drug_idx", "stitch_id", "pubchem_cid", "in_combo", "has_targets", "status", "flags",
            "title", "inchikey", "smiles", "formula", "charge", "heavy_atoms"]
    return pd.DataFrame(rows).reindex(columns=cols)


def coverage(table: pd.DataFrame) -> dict:
    def summary(df: pd.DataFrame) -> dict:
        ok = df["status"] == "ok"
        return {"drugs": len(df), "fingerprint_ok": int(ok.sum()),
                "fingerprint_ok_rate": round(float(ok.mean()), 4) if len(df) else None,
                "status_counts": df["status"].value_counts().to_dict(),
                "flagged_among_ok": int((ok & (df["flags"] != "")).sum())}

    combo = table[table["in_combo"]]
    review = table[(table["status"] != "ok") | (table["flags"] != "")]
    return {
        "combo_drugs": summary(combo),
        "combo_drugs_with_targets": summary(combo[combo["has_targets"]]),
        "combo_drugs_without_targets": summary(combo[~combo["has_targets"]]),
        "duplicate_inchikey_groups": int(table.dropna(subset=["inchikey"]).duplicated("inchikey", keep=False).sum()),
        "needs_review": review[["stitch_id", "pubchem_cid", "status", "flags", "title", "formula"]]
        .to_dict("records"),
    }


def run(snap: Path | None = None, offline: bool = False) -> dict:
    snap = snap or snapshot_dir()
    drugs = pd.read_parquet(snap / "drugs.parquet")
    records = fetch_properties(drugs["pubchem_cid"].tolist(), offline=offline)
    table = build(drugs, records)
    table.to_parquet(snap / "drug_structures.parquet", index=False)
    report = {"snapshot": read_json(snap / "manifest.json")["snapshot"], "created_at": utc_now(),
              "source": "PubChem PUG REST", "smiles_field_priority": list(SMILES_FIELDS),
              "fingerprint": "Morgan radius 2, 2048 bits (RDKit)", **coverage(table)}
    write_json(snap / "structure_coverage.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    parser.add_argument("--offline", action="store_true", help="chỉ dùng cache, không gọi PubChem")
    args = parser.parse_args()
    report = run(args.snapshot_dir, args.offline)
    for group in ("combo_drugs", "combo_drugs_with_targets", "combo_drugs_without_targets"):
        s = report[group]
        print(f"{group:28s} {s['fingerprint_ok']}/{s['drugs']} fingerprint ok ({s['fingerprint_ok_rate']:.1%}); "
              f"status={s['status_counts']}; flagged={s['flagged_among_ok']}")
    print(f"cần xem tay: {len(report['needs_review'])} thuốc; trùng InChIKey: {report['duplicate_inchikey_groups']}")


if __name__ == "__main__":
    main()
