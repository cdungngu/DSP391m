# 12 — Giao diện và vận hành

Ngày: 2026-10-17 · Chủ trì: sản phẩm · Phụ thuộc [01](01_Pham_vi_san_pham_va_hop_dong_dau_ra.md), [02](02_Danh_muc_thuoc_va_phan_giai_danh_tinh.md), [07](07_Truy_xuat_do_thi_va_van_ban.md), [09](09_LLM_va_giai_thich_tieng_Viet.md), [10](10_Verifier_va_xu_ly_thieu_bang_chung.md).

## 1. Kiến trúc mặc định

Streamlit demo gọi Python service dùng chung với CLI. Không thêm frontend/backend riêng ở v1. Package logic không import UI. Provider LLM qua adapter, credentials từ environment, không ghi vào config hoặc repo.

Đầu tiên demo local/internal; việc deploy công khai là công việc riêng sau nghiệm thu, không tự thực hiện từ plan này.

## 2. Luồng màn hình

1. Tìm/chọn từ catalog approved; hiển thị tên hoạt chất và thành phần trước nút phân tích.
2. Chặn unresolved/ambiguous; gộp trùng hoạt chất có thông báo.
3. Phân tích 2–5 hoạt chất, báo tiến trình theo nhận diện/truy xuất/tổng hợp.
4. Kết quả có cards theo cặp, điều kiện, nguồn mở rộng và phần thiếu.
5. Người dùng có thể mở đoạn gốc/version; không cần hiểu graph hay hash để dùng.
6. Research view riêng có Decagon/B0 và metric; không là tab mặc định consumer. Khi phân phối consumer, server config tắt research view, không chỉ giấu bằng CSS.

Không có màu xanh “an toàn” cho cặp thiếu nhãn. Không có phần trăm rủi ro từ B0 hoặc tổng số nhãn. Câu về hành động chỉ được diễn đạt từ nguồn đã duyệt, không tự kê đơn.

## 3. Trạng thái và lỗi

needs_resolution: chưa gọi retrieval/LLM.
partial: nguồn tải thiếu, LLM lỗi và dùng template hoặc chỉ một số cặp có bằng chứng; từng cặp có reason.
failed: không có artifact nguồn hợp lệ hoặc lỗi integrity, dừng có thông báo.
completed: pipeline hoàn tất, vẫn có thể thiếu bằng chứng; không đồng nghĩa “đơn không có vấn đề”.

Hiện trạng collector không gọi trong đường request người dùng: chuẩn bị corpus trước. Thiếu nguồn không kích hoạt tải hàng loạt trong UI.

## 4. Vận hành và ngân sách

Tải chỉ mục một lần theo source hash; session input không chia sẻ giữa người dùng.
HTTP ingestion có retry hữu hạn, Retry-After khi có, timeout và cache; không nhầm 429/503 với no_data. LLM request có timeout trong tổng budget 15 giây; timeout chuyển template, ghi fallback.
Metric: index load, resolution, retrieval, generation, verification, total; warm/cold; successful vs fallback. p95 target lookup<1s, total<15s là mục tiêu cần đo.

Log mặc định lưu query_id ngẫu nhiên, version, duration, tokens, error code; không lưu text đơn, tên người dùng hoặc khóa API. Cache kết quả không chứa thông tin định danh cá nhân; không thêm tài khoản/lịch sử đơn trong v1.

## 5. Thí nghiệm sản phẩm

So sánh hai cách trình bày: nhóm theo cặp và nhóm theo kết luận có contributing_pairs, trên cùng nội dung. Pilot file 11 đo người dùng tìm đúng cặp/điều kiện/nguồn; chọn giao diện ít hiểu sai hơn, không chọn bằng số click đơn thuần.
Mặc định nhóm theo cặp vì truy vết rõ; summary toàn đơn chỉ tổng hợp các claims đã verify.

## 6. Checklist và nghiệm thu

- [ ] Service fixture chạy không mạng; CLI và UI cho cùng semantic output.
- [ ] Input mơ hồ không bị bỏ; phối hợp nhiều hoạt chất áp dụng giới hạn đúng.
- [ ] Không rò B0/association vào consumer cards hoặc export.
- [ ] UI nhận đủ partial/fallback states; không spinner vô hạn.
- [ ] Hai session không chia sẻ input; secrets không ở log.
- [ ] Đo ít nhất 100 query sau warmup, báo cold runs riêng; không dùng cache hits như latency LLM.
- [ ] Chạy usability pilot và ghi lỗi đã sửa.

Ước lượng 2–4 ngày công; không cần triển khai hệ thống tài khoản hoặc hạ tầng phân tán.

