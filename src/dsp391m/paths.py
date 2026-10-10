"""Đường dẫn chuẩn của dự án. Mọi module đọc/ghi dữ liệu dùng các hằng số này."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "decagon"
PROCESSED_DIR = ROOT / "data" / "processed"
EXTERNAL_DIR = ROOT / "data" / "external"

# Tên snapshot đã xử lý. Đổi tên khi logic ETL thay đổi theo cách làm khác kết quả.
SNAPSHOT = "decagon_v1"


def snapshot_dir(snapshot: str = SNAPSHOT) -> Path:
    return PROCESSED_DIR / snapshot
