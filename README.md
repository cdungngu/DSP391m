# DSP391m · Group 8

Dự án nghiên cứu dự đoán đa nhãn tác dụng phụ theo cặp thuốc trên dữ liệu Decagon (BioSNAP, Stanford): nhập hai thuốc bằng ID, xếp hạng 963 nhãn tác dụng phụ. Lõi gồm baseline đếm tần suất (B0), DistMult và bộ đánh giá; Graph RAG/LLM là hướng mở rộng, không thuộc lõi.

## Bố cục

- `data/decagon/`: CSV Decagon gốc; chỉ đọc.
- `data/processed/`: đầu ra ETL, split đã đóng băng, bảng tên thuốc/gene.
- `docs/submission/`: các tài liệu báo cáo đã nộp (phản ánh thiết kế cũ).
- `docs/literature/`: bảng tổng quan tài liệu.
- `analysis/`: các đợt kiểm toán dữ liệu và thử nghiệm ban đầu.
- `plan/`: kế hoạch v3 (`Ke_hoach_trien_khai.md`) và 10 plan con trong `plan/du_doan_cap/`; `plan/chi_tiet/` là bản lịch sử.
- `src/dsp391m/`: package triển khai (xem `src/README.md`); `tests/`: pytest.
- `results/`: kết quả chấm điểm trên val và các thí nghiệm.
- `CLAUDE.md`: trạng thái, quyết định, lệnh chạy và quy ước làm việc chi tiết.

## Bắt đầu

Đọc `CLAUDE.md` trước khi thay đổi phạm vi hoặc xử lý dữ liệu. Cài đặt, chạy pipeline và test được ghi trong mục **Lệnh** của file đó.
