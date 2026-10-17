# 07 — Suy luận và demo nghiên cứu

Phụ thuộc: [01](01_Bai_toan_va_hop_dong.md), [04](04_Baseline_va_shortcut.md); nhận backend cuối từ [06](06_Thuc_nghiem_va_chon_model.md).

## Luồng tối thiểu

Chọn đúng hai ID → xác minh model release → score 963 nhãn → top-10 → hiện tên nhãn gốc, CUI, điểm xếp hạng và phiên bản. Template tiếng Việt giải thích “đây là nhãn mô hình ưu tiên theo dữ liệu nghiên cứu”; không cần LLM.

CLI trước, giao diện mỏng sau. Có thể dùng Streamlit khi triển khai nếu cài đặt phù hợp môi trường; UI gọi service Python, không viết lại scoring. Lệnh mới và module predictor chỉ được thêm vào README khi đã tồn tại và chạy được.

## Danh tính và tên thuốc

- ID Decagon là khóa chọn chính, không phụ thuộc 50 thuốc duyệt.
- Tên nguồn chỉ hỗ trợ hiển thị, kèm ID và trạng thái mapping.
- Alias mơ hồ không tự resolve; tên dựa connectivity chưa duyệt không tự chuyển thành ID.
- Cho phép tìm và chọn ID rõ ràng; khi không chắc tên thì hiển thị ID thay vì đoán.
- Không tự khai triển tên thương mại, chế phẩm phối hợp hoặc muối thành hoạt chất.
- Catalog consumer/review modules giữ nguyên; demo nghiên cứu có đường ID riêng và nhãn phạm vi rõ.

0 mapping approved không có nghĩa không thể chạy benchmark; cũng không có nghĩa đã xác nhận 645 thuốc là hoạt chất dùng thực tế.

## Phân biệt dự đoán và tra cứu

Predictor chỉ tải checkpoint/counts đã học; không gọi API ngoài lúc chấm. Nếu bật “xem dữ liệu đã ghi nhận”, lookup chạy sau và nằm panel riêng. Hiện cặp đã nằm train hay chưa; một demo trên cặp train không được giới thiệu là kiểm thử độc lập.

Không cho demo tra cứu test labels trong quá trình tuning. Trước final dùng tập demo train/val cố định; tính năng lookup toàn snapshot chỉ mở sau final lock và kết quả cuối, để tránh xem test rồi điều chỉnh mô hình.

Với cặp vắng trong toàn snapshot, vẫn có thể score nếu hai thuốc có train support, nhưng ghi “truy vấn thăm dò; benchmark hiện tại chưa xác nhận hiệu quả trên nhóm cặp này”.

## Vận hành

Load model một lần; cache theo model+snapshot+split+canonical pair+top_k. Không log thông tin bệnh nhân; request chỉ gồm IDs. Có CLI JSON để so output với evaluator.
Mục tiêu đo dự kiến: warm scoring top-10 p95 <1 giây cho batch một cặp trên máy ghi rõ cấu hình; cold load đo riêng, không tính thời gian mạng ngoài vì không có API trong scoring.

## Kiểm thử và nghiệm thu

- [ ] API/CLI/UI cùng scores và top-k; đảo hai thuốc không đổi.
- [ ] Nhập một thuốc, trùng ID, ID lạ, alias mơ hồ có thông báo phù hợp.
- [ ] Model mismatch hoặc file hỏng bị chặn; không âm thầm nạp model khác.
- [ ] Không quy đổi B0 score hay sigmoid DistMult thành phần trăm nguy cơ.
- [ ] Train-seen flag đúng; observed panel không lọt vào model input.
- [ ] Chạy offline từ artifact và manifest đã bàn giao.
- [ ] Bảng top-k không hiển thị mức độ nặng hoặc khuyến nghị đổi thuốc tự sinh.

Bàn giao: predictor service, CLI, demo nhỏ, ảnh/record ca đã chọn và số đo latency. Nếu thiếu thời gian làm UI, CLI JSON + trang báo cáo là mốc lõi tối thiểu, không trì hoãn đánh giá vì giao diện.

