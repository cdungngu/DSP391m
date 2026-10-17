# 09 — Bàn giao và hai đợt xem kết quả

Phụ thuộc: G0–G3 ở [00](00_Dieu_phoi_va_ra_soat.md).
Mục tiêu là giảm số lần cần người dùng/chuyên gia tham gia, không tự tạo phê duyệt chuyên môn.

## Đợt 1 — Một gói sau baseline và pilot

Xuất một báo cáo gồm: định nghĩa bài toán, bảng dữ liệu, baseline AP/top-k, thời gian epoch, ngân sách còn lại, 20 ca theo file06 và các vấn đề cần quyết định thật sự. Người dùng có thể xem cùng lúc, không duyệt từng mapping.

Tự động tiếp tục theo mặc định của bộ plan nếu không có quyết định mới: giữ ID, 963 nhãn, ngân sách đã ghi, không bật giải thích lâm sàng. Đây là tiến hành công việc đã được yêu cầu, không coi im lặng là approved catalog hoặc nguồn chuyên môn.

## Đợt 2 — Gói bàn giao

Gồm model selection, final metrics, demo, hướng dẫn tái lập, lỗi còn lại và giới hạn. Nếu có dược sĩ, chỉ nhờ nhận xét các câu mô tả chuyên môn và ca mơ hồ thực sự xuất hiện. Không cần người chấm nhãn mọi cặp để tính benchmark.

Không dùng “đã được chuyên gia duyệt” nếu chỉ người dùng kỹ thuật đọc báo cáo. Các quyết định duyệt nếu có giữ nguồn, người duyệt, thời điểm và phạm vi.

## Artifact bàn giao bắt buộc

| Artifact | Nội dung và điều kiện |
|---|---|
| Data card | Nguồn, snapshot/hash, counts, split, missingness, assumed negatives, kiểm tra điều khoản trước phân phối lại dữ liệu |
| Protocol | Metric definitions, chọn config, fallback, final lock |
| Model releases | Baseline và DistMult nếu thành công; maps/config/checkpoints/hashes |
| Experiment registry | Mọi run kể cả lỗi, thời gian, seed, lý do dừng |
| Final report | Baselines, ba seed mô hình chọn, CI, top-k, phân tầng, hạn chế |
| Error analysis | Ca val theo quy tắc, không chỉ kết quả đẹp |
| Demo và hướng dẫn | Offline, đúng hai ID, model release cố định |
| Reproduction guide | Lệnh thực đã chạy, dependency versions, máy, runtime, đường artifact |

Không viết sẵn lệnh chưa triển khai như thể đã chạy. README/src README chỉ cập nhật ở phiên code tương ứng.

## Bố cục báo cáo cuối

1. Câu hỏi và phạm vi dự đoán cặp.
2. Dữ liệu, split và mối liên hệ giữa quan sát với nhãn âm giả định.
3. Baseline và DistMult: công thức, sampling, training budget.
4. Kết quả val và lý do chọn model; test chỉ là đánh giá cuối.
5. Per-pair ranking, phân tầng và các lỗi điển hình.
6. Độ trễ, tái lập, các tính năng chưa thực hiện.
7. Hạn chế: thiếu nhãn, selection bias báo cáo, shared drugs, không cold-start/time split, không xác suất lâm sàng.

Báo cáo nộp tiếng Anh nếu tái sử dụng yêu cầu trước; ghi chú kế hoạch tiếng Việt. Không tự sửa tài liệu nộp lịch sử trong phiên thiết kế này.

## Definition of done

- [ ] Dữ liệu/split được xác minh, không chạy lại split để tăng điểm.
- [ ] Baselines và DistMult được thử trong ngân sách; nếu thất bại có artifact và nguyên nhân.
- [ ] Evaluator có top-k, paired comparison, null handling, final lock.
- [ ] Backend chọn bằng val, không tune trên test.
- [ ] Demo output khớp score artifact và không phụ thuộc dược sĩ duyệt liên tục.
- [ ] Model/data card nói rõ không kết luận tương tác có/không hoặc thuốc an toàn.
- [ ] Không còn plan đang hoạt động yêu cầu quay về cổng M/consumer trước khi train.

Nếu chỉ hoàn thành B0 do DistMult lỗi/hết ngân sách: đánh dấu hạng mục DistMult chưa hoàn tất, báo phạm vi thực; không gắn “hoàn thành toàn bộ” cho kết quả một phần. Nếu DistMult đã chạy đầy đủ nhưng không thắng, nghiên cứu vẫn hoàn tất và B0 là lựa chọn có căn cứ.

