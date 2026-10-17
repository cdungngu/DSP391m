# 00 — Điều phối và rà soát chuyển sang dự đoán cặp

Ngày: 2026-10-17 · Thiết kế v3, chưa triển khai các hạng mục mới.
Điểm vào: [kế hoạch tổng](../Ke_hoach_trien_khai.md).

## Kết luận rà soát

Kế hoạch v2.1 tối ưu cho tra cứu có giải thích dành cho người dùng phổ thông. Danh mục duyệt, nguồn, gold giải thích và verifier trở thành đường phụ thuộc bắt buộc trước huấn luyện. Điều này không còn phù hợp mục tiêu dự đoán cặp và nguồn lực duyệt hạn chế. Không phải dữ liệu ChEMBL thất bại; phạm vi sản phẩm đã lớn hơn bài toán gốc.

Tái sử dụng ETL, split, DataView, B0, releases và dữ liệu đã thu. Không xóa module consumer hoặc tự đổi pending thành approved. Bỏ sự phụ thuộc của benchmark vào các module ấy.

## Bản đồ thay thế toàn bộ 15 plan cũ

| Plan cũ trong chi_tiet | Xử lý | Nơi tiếp nhận |
|---|---|---|
| 00 Điều phối | Thay thứ tự và cổng nghiệm thu | File này |
| 01 Phạm vi/contracts | Thu về đúng hai ID và 963 điểm | [01](01_Bai_toan_va_hop_dong.md) |
| 02 Danh mục/danh tính | ID nghiên cứu bắt buộc; catalog consumer hoãn | [02](02_Du_lieu_va_chong_ro_ri.md), [07](07_Suy_luan_va_demo.md) |
| 03 Snapshot/DataView | Giữ và bổ sung manifest mô hình | [02](02_Du_lieu_va_chong_ro_ri.md) |
| 04 ChEMBL | Phân tích phân tầng trước; feature tùy chọn | [08](08_Mo_rong_va_thi_nghiem.md) |
| 05 DailyMed | Giữ collector/cache; hoãn mở rộng và duyệt corpus | [08](08_Mo_rong_va_thi_nghiem.md) |
| 06 Chuẩn hóa/xếp hạng | CUI làm khóa; xếp hạng bằng score, không enrichment | [01](01_Bai_toan_va_hop_dong.md), [03](03_Danh_gia_va_khoa_test.md) |
| 07 Graph/text retrieval | Rời đường dự đoán chính | [08](08_Mo_rong_va_thi_nghiem.md) |
| 08 B0 | Giữ kết quả, bổ sung đánh giá theo cặp | [04](04_Baseline_va_shortcut.md) |
| 09 LLM tiếng Việt | Hoãn; template đủ cho demo | [07](07_Suy_luan_va_demo.md), [08](08_Mo_rong_va_thi_nghiem.md) |
| 10 Verifier | Giữ cho consumer tương lai; thêm validation đầu ra số | [07](07_Suy_luan_va_demo.md) |
| 11 Gold/dược sĩ | Không bắt buộc gold lâm sàng; hai đợt xem kết quả | [09](09_Ban_giao_va_duyet_theo_dot.md) |
| 12 UI/vận hành | Demo nghiên cứu nhỏ, CLI trước | [07](07_Suy_luan_va_demo.md) |
| 13 Cổng M/B2 | Thay bằng kiểm tra dữ liệu, evaluator và ngân sách; DistMult vào lõi | [05](05_DistMult_va_huan_luyen.md), [06](06_Thuc_nghiem_va_chon_model.md) |
| 14 Tổng đánh giá | Tập trung prediction, reproducibility, giới hạn | [03](03_Danh_gia_va_khoa_test.md), [09](09_Ban_giao_va_duyet_theo_dot.md) |

Các file cũ có banner hết hiệu lực. [Bản tổng v2.1 lưu trữ](../Ke_hoach_trien_khai_v2_1_lich_su.md) giữ nguyên nội dung lịch sử; không dùng làm chỉ dẫn hiện hành.

## Đường phụ thuộc và ước lượng

| Bước | Đầu ra để chuyển bước | Ngày công dự kiến |
|---|---|---|
| 01 → 02 | Contract, kiểm toán train-only, bảng coverage | 1–2 |
| 03 → 04 | Evaluator đúng, baseline có top-k và manifest | 2–3 |
| 05 → 06 | DistMult có checkpoint, 4 cấu hình và 3 seed cấu hình chọn | 3–5 |
| 07 | CLI rồi demo từ backend đã khóa | 1–2 |
| 09 | Final runs, model card, báo cáo | 1–2 |
| 08 | Chỉ nhận tối đa một mở rộng sau lõi | Ngoài ngân sách lõi |

Tổng 8–14 ngày công là ước lượng thiết kế, không cam kết ngày lịch hay tự khởi động lại khung sáu tuần trước. Đo thời gian một epoch và một vòng đánh giá trước khi chọn máy chạy; không mặc định cần thuê GPU.

## Cổng kỹ thuật thay cổng M cũ

- G0: split/vocab giữ nguyên; input/metric và nhãn âm giả định được ghi rõ.
- G1: kiểm thử evaluator và leakage đạt, baseline cùng giao thức; được bắt đầu DistMult, không chờ dược sĩ.
- G2: hoàn tất ngân sách thử nghiệm hoặc ghi nguyên nhân dừng; quyết định backend bằng val.
- G3: khóa cấu hình và danh sách checkpoint trước test; bàn giao kết quả đúng artifact.

Nếu mô hình mới không tốt hơn, B0 vẫn là đầu ra hợp lệ; nghiên cứu phải báo thử nghiệm thất bại. Nếu lỗi leakage, dừng bước phụ thuộc và sửa, không chuyển sang thêm nguồn/LLM để che vấn đề.

## Trạng thái đầu kỳ

Đã có dữ liệu, split, B0/smoothing và foundation; chưa có DistMult, top-k evaluator đầy đủ, paired CI, final lock hay demo predictor. 61 test nhanh + 2 test thật là kết quả đợt triển khai trước, không phải chứng nhận bộ v3. Phiên này chỉ thay tài liệu.

