> **HẾT HIỆU LỰC HƯỚNG DẪN (v2.1).** Giữ để truy vết lịch sử. Dùng [bộ dự đoán cặp v3](../du_doan_cap/00_Dieu_phoi_va_ra_soat.md) và [kế hoạch tổng](../Ke_hoach_trien_khai.md). Các cổng duyệt và thứ tự bên dưới không áp dụng cho lõi v3.

# 06 — Chuẩn hóa nhãn và xếp hạng kết quả

Ngày: 2026-10-17 · Chủ trì: retrieval + dược sĩ · Phụ thuộc [01](01_Pham_vi_san_pham_va_hop_dong_dau_ra.md), [04](04_ChEMBL_va_bang_chung_co_che.md), [05](05_DailyMed_va_kho_doan_bang_chung.md).

## 1. Vấn đề và mục tiêu

lookup.py hiện sort theo số cặp hoặc enrichment. Số cặp ưu tiên nhãn phổ biến; enrichment ưu tiên hiếm, có thể nhiễu. Decagon chứa nhãn có thể là bệnh nền/chỉ định. “Observed” chỉ xác nhận có bản ghi, không xác nhận tác dụng phụ do cặp gây ra.

Mục tiêu consumer là hiển thị thông tin liên quan có nguồn đúng; mục tiêu nghiên cứu là giữ nguyên thống kê và giải thích thuật toán. Hai mục tiêu không dùng chung bảng xếp hạng âm thầm.

## 2. Đầu vào/đầu ra

Đầu vào: candidate claims/evidence, canonical pairs, catalog, source applicability.
Đầu ra: ranked cards + ranking_trace; mỗi card giữ contributing_pairs và evidence_ids.

Glossary có effect_cui, raw_name, preferred_name_vi, definition_source, reviewer, version. Không sửa raw label; thuật ngữ chưa duyệt giữ tên nguồn và ghi chưa có bản dịch duyệt.

Annotation theo claim/context gồm role: adverse_event / indication / comorbidity / unclear. Cùng một CUI có thể có vai trò khác trong nguồn khác; không tạo blacklist toàn cục từ một demo.

## 3. Xếp hạng mặc định

Consumer:
1. Loại claim chưa đủ hỗ trợ theo verifier; giữ chúng trong missing/conflicting section.
2. Nhóm thông tin trực tiếp về cặp và thông tin áp dụng qua nhóm thuốc đã xác minh.
3. Trong cùng nhóm, ưu tiên applicability phù hợp và relevance do dược sĩ gán cho dev; khi chưa có điểm dùng thứ tự ổn định theo pair ID và evidence ID.
4. Severity chỉ dùng khi chính nguồn cung cấp và được giữ nguyên ngữ cảnh; không suy từ số nhãn/cặp.
5. Gộp card trùng nội dung, giữ mọi cặp đóng góp; mặc định 5 card và nút xem thêm, báo tổng số.

Research:
Giữ hai sort hiện có làm baseline, thêm evidence-aware ranking. Không đổi điểm model. Mọi enrichment ghi mẫu số “cặp có nhãn trong snapshot”, không là tỷ lệ bệnh nhân.

## 4. Thí nghiệm E06

Dev gold gán relevance 0/1/2: không liên quan, có liên quan nhưng chỉ bối cảnh, trực tiếp hữu ích cho câu hỏi. Tập ứng viên cố định để so ranking; một thí nghiệm khác mới đo thêm nguồn.

So sánh pairs, enrichment và evidence-aware. Metric: nDCG@10, Precision@5 với relevance=2, tỷ lệ card chỉ định/bệnh nền bị diễn đạt sai và coverage theo cặp. NDCG chỉ trên query có ít nhất một relevant item; báo số bị loại. Thêm kiểm tra candidate recall để không đổ lỗi ranking khi retrieval bỏ sót.

Giữ phương án mới nếu nDCG@10 tăng ít nhất 0,05 trên dev và không tăng số overclaim; ngưỡng là quyết định thiết kế, chưa là kết quả. Khi không đạt, dùng thứ tự phân nhóm bằng chứng ổn định và ghi chưa có ranker đã kiểm chứng.

## 5. Lỗi và tương thích

Không có thông tin được hỗ trợ: hiện missing-data card, không lấp top-5 bằng nhãn Decagon. Hai nguồn trái nhau: đưa vào conflicting riêng, không bỏ nguồn có điểm thấp hơn. Lookup CLI cũ giữ sort để tái lập; consumer không dùng trực tiếp effects list làm cảnh báo.

## 6. Checklist nghiệm thu

- [ ] Glossary không làm mất CUI/raw names.
- [ ] Context annotations có source và reviewer.
- [ ] Regression: nhãn bệnh nền không tự biến thành adverse event.
- [ ] B0/PPI không xuất hiện trong consumer warning cards.
- [ ] Tie-break và góp cặp bất biến khi đảo input.
- [ ] Report lưu candidates, ranking config và per-query metrics.

Bước triển khai: annotation schema → card grouping → stable baseline → E06 → khóa config. Ước lượng 1–2 ngày công, không gồm gán nhãn.
