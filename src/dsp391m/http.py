"""Gọi API ngoài một cách lịch sự: cache trên đĩa, chờ và thử lại khi bị giới hạn, ngắt sớm khi host chặn.

Bài học từ PubChem (2026-10-10): gọi dồn khoảng 1.000 request khiến NCBI đánh dấu IP là lạm dụng. Vì vậy
mọi module lấy dữ liệu ngoài phải đi qua đây, luôn cache, và dừng ngay khi host đã chặn.
"""
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from .manifest import utc_now


class OfflineCacheMiss(FileNotFoundError):
    pass


class RateLimited(requests.RequestException):
    pass


_BLOCKED_HOSTS: set[str] = set()


def request(method: str, url: str, **kwargs) -> requests.Response:
    """429/503: chờ rồi thử lại; hết lượt hoặc bị chuyển tới trang chặn lạm dụng thì đánh dấu host bị chặn."""
    host = urlparse(url).netloc
    if host in _BLOCKED_HOSTS:
        raise RateLimited(f"{host} đang chặn; chạy lại sau")
    for attempt in range(4):
        r = requests.request(method, url, timeout=60, allow_redirects=False, **kwargs)
        if r.is_redirect and "misuse" in r.headers.get("location", ""):
            _BLOCKED_HOSTS.add(host)
            raise RateLimited(f"{host} chuyển tới trang chặn lạm dụng: {r.headers['location']}")
        if r.status_code not in (429, 503):
            return r
        time.sleep(5 * (attempt + 1))
    _BLOCKED_HOSTS.add(host)
    raise RateLimited(f"{host} trả {r.status_code} sau nhiều lần thử")


def cached(path: Path, fetch, offline: bool, pause: float = 0.3):
    """Đọc cache nếu có; nếu không thì gọi fetch(), lưu nguyên văn kèm thời điểm, rồi nghỉ `pause` giây."""
    if path.exists():
        return json.loads(path.read_text())
    if offline:
        raise OfflineCacheMiss(f"Thiếu cache {path} ở chế độ --offline")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = fetch()
    path.write_text(json.dumps({"fetched_at": utc_now(), "data": data}))
    time.sleep(pause)
    return {"data": data}


def batch_key(ids) -> str:
    return hashlib.sha256(",".join(map(str, sorted(ids))).encode()).hexdigest()[:16]
