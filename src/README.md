# Mã triển khai

Phạm vi hiện hành là v3 ([kế hoạch tổng](../plan/Ke_hoach_trien_khai.md), [10 plan](../plan/du_doan_cap/00_Dieu_phoi_va_ra_soat.md)): dự đoán 963 nhãn cho một cặp ID. Đường lõi v3: `predictor` (hợp đồng chung) → `readiness` → `evaluate`/`metrics`/`compare` (chỉ val) → `final` (lock + test) → `models.b0`, `models.distmult` + `training/`. Đã chạy search DistMult v1 (không promote) và lô 20 ca; tiếp theo là E1 residual (plan 08), lock/test, rồi demo predictor (plan 07). Các nhãn GĐ trong bảng dưới là tên giai đoạn của plan cũ, giữ để truy vết.

## Luồng consumer và gói duyệt (2026-10-17, nhánh riêng, hoãn trong v3)

`contracts.py`, `releases.py`, `catalog.py`, `review.py`, `workbench.py` bổ sung luồng template chỉ dùng catalog và câu có nguồn đã được duyệt. Không tự dùng nhãn Decagon/B0 làm cảnh báo consumer. Benchmark v3 không phụ thuộc luồng này; gói duyệt mới nhất là `data/review/2026-10-17_foundation_v2`.

```bash
.venv/bin/python -m dsp391m.workbench prepare --out data/review/NEW_PACKET_ID
.venv/bin/python -m dsp391m.catalog --help
.venv/bin/python -m dsp391m.review --help
.venv/bin/python -m dsp391m.b0_experiment --out results/experiments/NEW_RUN_ID.json
```

Không ghi đè packet/run đã có. Quy trình import review và trạng thái từng plan nằm trong [báo cáo triển khai](../plan/Bao_cao_trien_khai_2026_10_17.md). Catalog thật đang chờ dược sĩ; test fixtures không phải dữ liệu đã duyệt để sử dụng thực tế.

Package `dsp391m` (cài bằng `pip install -e .` từ thư mục gốc). Hiện có GĐ1, GĐ2, B0 và phần lớn GĐ3 của kế hoạch (`plan/Ke_hoach_trien_khai.md`):

| Module | Việc | Đầu ra trong `data/processed/decagon_v1/` |
|---|---|---|
| `dsp391m.etl` | Đọc ba CSV gốc (chỉ đọc), chuẩn hóa khóa và cặp không thứ tự | `*.parquet`, `manifest.json` |
| `dsp391m.quality` | Kiểm tra invariant và đối chiếu số đếm đã kiểm chứng | `qa_report.json` |
| `dsp391m.structures` | STITCH → PubChem → SMILES, kiểm tra RDKit, đo độ phủ | `drug_structures.parquet`, `structure_coverage.json` |
| `dsp391m.splits` | Vocabulary 963 nhãn, chia tập theo cặp 70/10/20 seed 391 (đóng băng) | `splits/pair_70-10-20_s391/` |
| `dsp391m.names` | Tên thuốc (PubChem synonyms; CID liên quan khi CID gốc không có tên) và symbol gene (NCBI); chịu được giới hạn tốc độ API | `drug_names.parquet`, `gene_names.parquet`, `names_report.json` |
| `dsp391m.lookup` | GĐ2: tra cứu bằng chứng cho đơn 2–10 thuốc (evidence mode), xuất văn bản hoặc JSON | — |
| `dsp391m.http` | Gọi API ngoài: cache, backoff, ngắt sớm khi host chặn (mọi module lấy dữ liệu ngoài phải dùng) | — |
| `dsp391m.chembl` | GĐ3: khớp thuốc → ChEMBL, cơ chế có `action_type`, bổ sung tên | `chembl_map.parquet`, `chembl_mechanisms.parquet`, `chembl_report.json` |
| `dsp391m.dailymed` | GĐ3: đoạn nhãn SPL theo mục LOINC cho danh mục thuốc nhỏ | `dailymed_sections.parquet`, `dailymed_report.json` |
| `dsp391m.evaluate`, `dsp391m.models.b0` | Chấm val (test bị từ chối), score cache (`--rescore` dựng lại từ artifact), phân tầng, shortcut; B0 popularity/alpha0/alpha100 | `results/val/<model_release_id>/<run_id>.json`, `results/scores/` |
| `dsp391m.predictor` | Hợp đồng chung: `canonical_pairs`, `identity` (hash snapshot/split/thứ tự ID/CUI), `config_id` vs `model_release_id`, artifact `model.json` + checksum trọng số | `results/models/<model_release_id>/` |
| `dsp391m.readiness` | Kiểm tra dữ liệu trước huấn luyện (train support, overlap, phân bố nhãn), fail closed | `results/readiness/<id>.json` |
| `dsp391m.metrics` | Metric thuần: macro/micro AP, AP theo cặp, P/R@5/10, NDCG@10, paired bootstrap có trọng số | — |
| `dsp391m.compare` | So sánh hai model trên **val** (không có tùy chọn split), CI95 ghép cặp | `results/val/comparisons/` |
| `dsp391m.final` | `lock` (yêu cầu worktree sạch) và `run` (xác minh lock rồi mới nạp test) | `results/final/` |
| `dsp391m.cases` | Chọn lô ca val theo quy tắc cố định (plan 06), top-10 hai model cạnh nhau, cờ tên/độ phủ | `results/val/error_analysis/` |
| `dsp391m.models.distmult`, `dsp391m.training` | DistMult, sampler âm train-only, trainer có early stopping, `last.pt`/`best.pt`, resume | `results/runs/<run_id>/` |
| `dsp391m.dataview` | Điểm truy cập nhãn duy nhất: `evidence_view`, `prediction_view` (chỉ train), `load_eval_targets` (chỉ bộ chấm điểm), `Cache` có khóa theo chế độ | — |

**Quy tắc truy cập dữ liệu:** code dự đoán, truy xuất và giải thích chỉ đọc nhãn qua một `DataView`, không tự đọc `pair_labels.parquet`. Benchmark luôn dùng `prediction_view`; chỉ bộ chấm điểm gọi `load_eval_targets`. Mọi cache dùng `dataview.Cache` để khóa gồm mode, split và snapshot. Split chỉ được đọc qua `splits.load_verified_split`; đổi tham số thì tạo `split_id` mới (code từ chối ghi đè).
