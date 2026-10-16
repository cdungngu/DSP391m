# Mã triển khai

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
| `dsp391m.evaluate`, `dsp391m.models.b0` | Bộ chấm điểm dùng chung; B0 (popularity, per-drug) | `results/<split>/<model>.json` |
| `dsp391m.dataview` | Điểm truy cập nhãn duy nhất: `evidence_view`, `prediction_view` (chỉ train), `load_eval_targets` (chỉ bộ chấm điểm), `Cache` có khóa theo chế độ | — |

**Quy tắc truy cập dữ liệu:** code dự đoán, truy xuất và giải thích chỉ đọc nhãn qua một `DataView`, không tự đọc `pair_labels.parquet`. Benchmark luôn dùng `prediction_view`; chỉ bộ chấm điểm gọi `load_eval_targets`. Mọi cache dùng `dataview.Cache` để khóa gồm mode, split và snapshot. Split chỉ được đọc qua `splits.load_verified_split`; đổi tham số thì tạo `split_id` mới (code từ chối ghi đè).
