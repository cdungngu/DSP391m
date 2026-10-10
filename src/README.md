# Mã triển khai

Package `dsp391m` (cài bằng `pip install -e .` từ thư mục gốc). Hiện có GĐ1a của kế hoạch (`plan/Ke_hoach_trien_khai.md`):

| Module | Việc | Đầu ra trong `data/processed/decagon_v1/` |
|---|---|---|
| `dsp391m.etl` | Đọc ba CSV gốc (chỉ đọc), chuẩn hóa khóa và cặp không thứ tự | `*.parquet`, `manifest.json` |
| `dsp391m.quality` | Kiểm tra invariant và đối chiếu số đếm đã kiểm chứng | `qa_report.json` |
| `dsp391m.structures` | STITCH → PubChem → SMILES, kiểm tra RDKit, đo độ phủ | `drug_structures.parquet`, `structure_coverage.json` |

Chưa có vocabulary nhãn, split hay data view theo chế độ: các phần này thuộc GĐ1b và chỉ làm sau khi giao thức đánh giá (plan mục 5.1) được chốt.
