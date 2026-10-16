# 09 — LLM và giải thích tiếng Việt

Ngày: 2026-10-17 · Chủ trì: giải thích · Phụ thuộc [01](01_Pham_vi_san_pham_va_hop_dong_dau_ra.md), [07](07_Truy_xuat_do_thi_va_van_ban.md); đầu ra sang [10](10_Verifier_va_xu_ly_thieu_bang_chung.md).

## 1. Mục tiêu và hiện trạng

Chưa thấy module LLM trong package lúc kiểm tra. Không cần LLM để sinh thông tin mới; nó diễn đạt các facts/statements được phép thành tiếng Việt dễ hiểu. Template phải chạy trước để có đối chứng và đường fallback.

Consumer chỉ nhận bằng chứng đủ điều kiện; không gửi B0 để model tự biến điểm thành cảnh báo. Nguồn đơn thuốc không tự trở thành kết luận về cả đơn.

## 2. Input/output và prompt

Input: EvidenceBundle đã giới hạn budget, glossary approved, claim policy và schema 01.
Output: danh sách Claim có text_vi, pair_ids, evidence_ids, conditions và claim_type; support_status ở giai đoạn sinh chỉ là dự kiến, verifier quyết định lại.

Prompt gồm: mục tiêu diễn đạt; giới hạn nguồn; cấm mở rộng chủ thể/outcome; giữ phủ định và điều kiện; văn bản nguồn trong trường data; ví dụ fixture đủ/thiếu/mâu thuẫn. Không yêu cầu chain-of-thought dài; cần câu ngắn có citation.

Không cho model tự tạo URL. UI giải citation qua evidence store, không qua text model. Đầu ra không có effect CUI khi nguồn không ánh xạ được; không ép LLM chọn nhãn gần nhất.

## 3. Luồng xử lý và lỗi

1. Validate bundle và glossary.
2. Sinh candidate facts/template để bảo đảm có fallback.
3. Một lần gọi model sinh claims (output budget ban đầu 1.200 tokens).
4. Parse và validate JSON; lỗi schema hoặc timeout → template, không gọi chuỗi sửa tự động.
5. Verifier kiểm tra từng claim; chỉ publish claim đạt.
6. Ghi model ID, provider, prompt hash, actual tokens, elapsed time và fallback reason.

Model/provider là cấu hình, chưa chọn theo tên thương mại trong plan. Trước pilot người triển khai chọn hai cấu hình đang sẵn có, ghi phiên bản và giá tại thời điểm chạy; quyết định bằng metric dev, không bằng lời quảng cáo. Không gọi API trả phí trong công việc viết tài liệu này.

## 4. Tiếng Việt và tính dễ hiểu

Dùng tên hoạt chất đã duyệt, giải thích thuật ngữ lần đầu; tránh từ “chắc chắn”, “an toàn” khi nguồn không hỗ trợ. Không dịch “may” thành khẳng định. Giữ điều kiện liều, route hoặc nhóm bệnh nhân nếu chúng có trong nguồn; không thêm khuyến nghị liều từ trí nhớ.

Câu hỏi người dùng cần được trả lời: thuốc/cặp nào, nguồn nói gì, điều kiện nào, chưa biết gì. Không hiển thị pipeline/hash như nội dung chính; thông tin kỹ thuật nằm ở chi tiết nghiên cứu.

## 5. Thí nghiệm E09

So sánh T0 template, T1 LLM từ bundle, T2 LLM từ facts đã cấu trúc. Cùng evidence và glossary; ghi model/version, budget, temperature thấp cố định nếu API hỗ trợ. 20 dev cases trước; pilot model 50–100 queries chỉ sau khi có nguồn hợp lệ.

Metric: claim support, overclaim, mất điều kiện, citation precision, readability từ thử người dùng, p50/p95 và chi phí. Giữ LLM nếu đạt D7 và cải thiện mức hiểu so template mà không tăng lỗi nghiêm trọng. Nếu không, ship template cho các trường hợp chưa đạt.

## 6. Checklist và nghiệm thu

- [ ] Provider adapter mock được, không network trong unit tests.
- [ ] Schema-invalid, timeout, rate-limit, empty evidence đều trả fallback đúng.
- [ ] Test nguồn chứa chỉ dẫn giả không thay đổi policy hay mở quyền công cụ.
- [ ] Test phủ định, số liệu, điều kiện và tên thuốc tiếng Việt.
- [ ] Ghi đủ token/cost metadata; không lưu input nguyên văn người dùng trong log mặc định.
- [ ] Không xuất URL tự sinh; mỗi evidence ID phải được store giải được.

Cổng đạt trên dev đã khóa rubric; không lấy chỉ số model tự chấm làm kết quả cuối. Ước lượng 2–3 ngày công cộng pilot.

