# Xác minh môi trường — 2026-10-17

- `.venv` dùng để sinh mọi kết quả v3: Python 3.12.4 (Anaconda), macOS arm64, numpy 2.5.3. Freeze: `2026-10-17_dot_venv_freeze.txt` (dòng torch ghi đường wheel cục bộ, tương ứng torch==2.5.1 từ PyPI).
- `requirements.txt` trước đó khóa numpy 1.26.4 nhưng `.venv` đã chạy 2.5.3 từ trước phiên v3; `pip check` đạt.
- Venv sạch dựng từ cùng interpreter với requirements dự kiến (numpy 2.5.3) + requirements-train: chỉ khác pillow 13.0.0 và pluggy 1.7.0 (gián tiếp, nay được pin theo `.venv`).
- Trong venv sạch: 88 test nhanh + 2 slow đạt; popularity/B0 alpha0/alpha100 cho cùng model_release_id, metric và phân tầng **giống hệt** artifact đã commit; trainer DistMult dim 64 hai epoch cho loss và val macro AP giống hệt probe.
- Kết luận: cập nhật `requirements.txt` sang numpy 2.5.3. Artifact cũ giữ metadata môi trường của chúng.
