# 00 — Điều phối bộ kế hoạch chi tiết

Ngày thiết kế: **2026-10-17**. Trạng thái: **tài liệu thiết kế; chưa nghiệm thu sản phẩm**.
Nguồn quyết định: [kế hoạch tổng](../Ke_hoach_trien_khai.md), các lựa chọn của người dùng trong phiên lập kế hoạch và mã nguồn đọc ngày 17/10.

## 1. Mục tiêu và phạm vi

Giữ A + D + B0; B2 chỉ qua cổng M. Sản phẩm hướng tới người dùng phổ thông, tiếng Việt, khoảng 50 hoạt chất và alias/tên thương mại được dược sĩ duyệt. B0 chỉ dùng trong chế độ nghiên cứu. Không mở lại HODDI/GNN/B1.

Đây là kế hoạch triển khai các bài toán, không phải tuyên bố chúng đã chạy. Dữ liệu mẫu giả định phải gắn nhãn fixture; không dùng làm gold hoặc bằng chứng y khoa.

## 2. Hiện trạng đã đối chiếu

| Thành phần | Bằng chứng trong repo | Kết luận được phép |
|---|---|---|
| ETL, split, DataView, lookup | src/dsp391m; tests/test_leakage.py, test_split_integrity.py, test_lookup.py | Có triển khai và test; đợt viết plan không chạy lại |
| B0, evaluator | results/val/b0_per_drug.json | Val 6.347 cặp × 963 nhãn; macro AP 0,2714309; micro AP 0,3507799; AUROC 0,8360128 |
| Tên thuốc | names_report.json đọc trong phiên | 374 self, 253 pending, 18 none; 271 tên hiển thị vẫn là STITCH ID |
| ChEMBL, DailyMed | chembl.py, dailymed.py, lookup.py và test tương ứng | Có collector và tích hợp lookup; kiểm tra cuối phiên thấy DailyMed 8 thuốc/129 chunks; chưa có chứng cứ duyệt catalog, chưa thấy chembl_report.json |
| LLM, verifier, web, gold | Chưa có module/artifact tương ứng trong danh sách kiểm tra | Cần triển khai, không đánh dấu hoàn thành |

Kết quả val có timestamp UTC 16/10; ghi ngày địa phương phải chuyển sang Asia/Ho_Chi_Minh. Không dùng lại con số CI từ một lần chạy cũ mà không ghi run tương ứng.

Workspace có cập nhật đồng thời trong lúc viết tài liệu: ChEMBL thêm nhánh neutralized, lookup thêm nguồn cơ chế/nhãn thuốc. Bộ plan đã bổ sung các thay đổi quan sát được; trước khi triển khai phải đọc lại mã, không ghi đè công việc đang có. Số liệu coverage nói trên là đọc artifact, chưa xác minh từng record.

## 3. Bản đồ bài toán và bàn giao

| File | Chủ trì theo vai trò | Bàn giao | Phụ thuộc |
|---|---|---|---|
| [01 Phạm vi và hợp đồng](01_Pham_vi_san_pham_va_hop_dong_dau_ra.md) | Sản phẩm | Contract v1, ví dụ đầu ra | 00 |
| [02 Danh tính thuốc](02_Danh_muc_thuoc_va_phan_giai_danh_tinh.md) | Dữ liệu + dược sĩ | Catalog, mapping review | 01 |
| [03 Snapshot và rò rỉ](03_Snapshot_DataView_va_chong_ro_ri.md) | Dữ liệu | Source manifest, context | 01 |
| [04 ChEMBL](04_ChEMBL_va_bang_chung_co_che.md) | Dữ liệu + dược sĩ | Mechanism evidence | 02,03 |
| [05 DailyMed](05_DailyMed_va_kho_doan_bang_chung.md) | Dữ liệu + dược sĩ | SPL và chunks | 02,03 |
| [06 Nhãn và xếp hạng](06_Chuan_hoa_nhan_va_xep_hang_ket_qua.md) | Retrieval + dược sĩ | Ranking config, glossary | 01,04,05 |
| [07 Truy xuất](07_Truy_xuat_do_thi_va_van_ban.md) | Retrieval | EvidenceBundle | 03–06 |
| [08 B0](08_B0_va_giao_thuc_du_doan.md) | Dự đoán | Val report, scoring contract | 03 |
| [09 LLM](09_LLM_va_giai_thich_tieng_Viet.md) | Giải thích | Draft claims | 01,07 |
| [10 Verifier](10_Verifier_va_xu_ly_thieu_bang_chung.md) | Giải thích | Verified claims | 01,09 |
| [11 Gold set](11_Gold_set_va_quy_trinh_duoc_si.md) | Đánh giá + dược sĩ | Dev/final, rubric | 01–03; bắt đầu sớm |
| [12 Giao diện](12_Giao_dien_va_van_hanh.md) | Sản phẩm | Web demo, telemetry | 02,07,09,10 |
| [13 Cổng M](13_Cong_M_va_B2_co_dieu_kien.md) | Nhóm + dược sĩ | Quyết định, B2 nếu đạt | 08–12 đạt dev |
| [14 Đánh giá](14_Danh_gia_tong_hop_va_ban_giao.md) | Đánh giá | Final runs, data card | 11,12; 13 nếu chọn |

## 4. Thứ tự triển khai

1. Khóa contract 01, danh mục và nguồn 02–03; lập rubric 11 ngay.
2. Hoàn thiện collectors 04–05 độc lập; B0/evaluator 08 có thể làm cùng thời gian.
3. Nối 06–07; chạy template trước LLM. Làm gold dev khi đã có nguồn thật.
4. Nối 09–10 và web 12; kiểm tra D7 và thử hiểu nội dung.
5. Ghi quyết định 13. Đóng băng cấu hình rồi chạy 14.

Ước lượng **ngày công**, chưa đo: nền/contracts 2–3; mapping/nguồn 5–8; retrieval/ranking 3–5; LLM/verifier 4–6; web 2–4; đánh giá/tài liệu 4–6; B2 thêm tối đa 5. Công dược sĩ: hai phiên đầu chọn danh mục/rubric, sau đó chấm theo lô 10–20 ca; đo thời gian pilot để quyết định sản lượng. Không coi 4 người luôn làm song song được mọi phần. Lịch sáu tuần là khung cũ, không tự khởi động lại ngày 17/10.

## 5. Cổng và cách báo cáo

- G0: contracts thống nhất, 50 thuốc là danh sách có người duyệt hoặc trạng thái pending rõ.
- G1: mọi mapping công khai được duyệt, nguồn có version/hash; nguồn lỗi khác nguồn không có dữ liệu.
- G2: retrieval/template tái lập, không hiển thị nhãn thống kê thành cảnh báo.
- G3: dev đạt D7 theo mẫu số file 11; lỗi citation/mapping nghiêm trọng được sửa.
- M: quyết định nghiên cứu B2 bằng file 13; không ảnh hưởng đường sản phẩm chính.
- G4: config lock, final report và demo khớp nhau.

Mỗi báo cáo tiến độ ghi: artifact, lệnh đã chạy, kết quả thực, giới hạn, việc tiếp theo. Không dùng checkbox hoàn thành thiết kế để suy ra hoàn thành code.

## 6. Checklist thực hiện và kiểm tra bộ tài liệu

- [x] Đối chiếu plan tổng, code collector, lookup, DataView, evaluator và kết quả val.
- [x] Chốt 15 tài liệu có liên kết, contract chung, đầu ra và tiêu chí.
- [ ] Gán tên người thực hiện cho các vai trò.
- [ ] Thực hiện G0 rồi đi theo thứ tự trên.
- [ ] Sau mỗi cổng cập nhật plan tổng và CLAUDE.md trong cùng phiên.

Bộ tài liệu được kiểm tra liên kết nội bộ và phạm vi; các thí nghiệm ở file con **chưa chạy trong công việc viết plan**.
