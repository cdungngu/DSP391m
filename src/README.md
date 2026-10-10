# Mã triển khai

Package `dsp391m` (cài bằng `pip install -e .` từ thư mục gốc). Hiện có GĐ1a và GĐ1b của kế hoạch (`plan/Ke_hoach_trien_khai.md`):

| Module | Việc | Đầu ra trong `data/processed/decagon_v1/` |
|---|---|---|
| `dsp391m.etl` | Đọc ba CSV gốc (chỉ đọc), chuẩn hóa khóa và cặp không thứ tự | `*.parquet`, `manifest.json` |
| `dsp391m.quality` | Kiểm tra invariant và đối chiếu số đếm đã kiểm chứng | `qa_report.json` |
| `dsp391m.structures` | STITCH → PubChem → SMILES, kiểm tra RDKit, đo độ phủ | `drug_structures.parquet`, `structure_coverage.json` |
| `dsp391m.splits` | Vocabulary 963 nhãn, chia tập theo cặp 70/10/20 seed 391 (đóng băng) | `splits/pair_70-10-20_s391/` |
| `dsp391m.dataview` | Điểm truy cập nhãn duy nhất: `evidence_view`, `prediction_view` (chỉ train), `load_eval_targets` (chỉ bộ chấm điểm), `Cache` có khóa theo chế độ | — |

**Quy tắc truy cập dữ liệu:** code dự đoán, truy xuất và giải thích chỉ đọc nhãn qua một `DataView`, không tự đọc `pair_labels.parquet`. Benchmark luôn dùng `prediction_view`; chỉ bộ chấm điểm gọi `load_eval_targets`. Mọi cache dùng `dataview.Cache` để khóa gồm mode, split và snapshot. Split chỉ được đọc qua `splits.load_verified_split`; đổi tham số thì tạo `split_id` mới (code từ chối ghi đè).
