# 06 — Thí nghiệm, lựa chọn mô hình và phân tích lỗi

Phụ thuộc: [03](03_Danh_gia_va_khoa_test.md), [04](04_Baseline_va_shortcut.md), [05](05_DistMult_va_huan_luyen.md).

## Ma trận bắt buộc

| Run | Mục đích | Dữ liệu chọn |
|---|---|---|
| Popularity | Mốc tần suất toàn cục | Không tune |
| B0 alpha0 | Nối kết quả cũ | Không tune |
| B0 alpha100 | Baseline mạnh đã chọn | Val E08 |
| DistMult 4 configs seed391 | Chọn dimension/lr | Val |
| DistMult config chọn, seeds392/393 | Kiểm ổn định | Val |
| Final danh sách khóa | Báo cáo cuối | Test chỉ sau lock |

Không ép DistMult phải thắng để dự án “thành công”. Không đổi metric chính, split hoặc ngưỡng sau khi xem kết quả.

## Quy tắc chọn và đưa vào demo

Chọn config DistMult bằng macro AP val seed391; chênh dưới 0,001 ưu tiên dimension nhỏ, rồi learning rate nhỏ. Checkpoint theo early stopping file05. Sau đó chạy thêm hai seed cùng config.

Quy tắc promotion đề xuất v3, thay ngưỡng cũ +0,02 và cổng chuyên môn:
- Cả ba seed đều có delta macro AP >0 so B0 alpha100.
- Mean delta macro AP ≥0,005 (0,5 điểm phần trăm tuyệt đối).
- Seed391 có paired CI95 delta macro AP với cận dưới >0.
- Mean NDCG@10 không giảm quá 0,005 tuyệt đối so B0.
- Không có lỗi leakage/artifact và runtime demo đạt ngân sách đã đo.

Các ngưỡng này là quy ước kỹ thuật để tránh thêm độ phức tạp vì cải thiện quá nhỏ, không là ngưỡng ý nghĩa y khoa. Khóa trước chạy search; báo đủ giá trị liên tục kể cả không đạt. Không được sửa ngưỡng để vừa kết quả. Chọn checkpoint seed391 cho demo nếu promotion đạt; không chọn seed tốt nhất sau khi xem ba seed. B0 vẫn fallback chính nếu không đạt.

Không ensemble ở lõi để tránh thêm quy tắc chọn. Có thể nghiên cứu sau theo file08. Final báo ba seed riêng và mean/std; mỗi checkpoint giữ nguyên train-only, không retrain trên train+val trong v3.

## Phân tích định lượng

Tính delta theo nhãn, train-degree nhóm cặp (dùng min degree hai thuốc), số nhãn quan sát mỗi cặp, target coverage 0/1/2. Ngưỡng degree tính train, không từ val/test. Mọi bảng có n_pairs/n_labels và phần bị undefined.

Trên ChEMBL, phân tầng coverage không phải chứng minh cơ chế cải thiện mô hình. Nhóm có cơ chế có thể khác tần suất báo cáo; báo degree đi kèm. Đánh giá trên cùng cặp; không so model trên tập có feature với B0 trên toàn val.

## Lô 20 ca để xem thủ công

Từ val: 5 cải thiện NDCG lớn nhất, 5 suy giảm lớn nhất, 5 degree thấp chọn seed cố định, 5 ngẫu nhiên. Dedupe; bù từ cùng nhóm theo quy tắc cố định. File xuất gồm ID, tên kèm flags, nhãn quan sát, top-10 hai model, scores, coverage, provenance. Không dùng case test để đổi thiết kế.

Mục tiêu: phát hiện nhãn bệnh nền, thuốc mơ hồ, dự đoán gần như giống nhau cho mọi cặp và UI gây hiểu sai. Không yêu cầu dược sĩ gán “đúng/sai y khoa” cho 200 dự đoán. Ghi nhận quan sát chuyên môn riêng nếu có, không dùng nó thành benchmark accuracy.

## Khi thất bại

- Loss lỗi hoặc không học fixture: sửa trainer, chưa mở rộng model.
- Thắng popularity nhưng thua B0: kết luận embedding chưa vượt thống kê từng thuốc.
- Macro AP tăng nhưng NDCG giảm: giữ B0 demo, báo tradeoff.
- Chỉ một seed tốt: chưa đủ ổn định.
- Hết ngân sách: xuất partial report, các run thiếu ghi rõ; không dựng metric giả.

Bàn giao: experiment registry (run ID, config/hash, trạng thái, thời gian), bảng so sánh, 20 ca và model_selection.json. Có thể review một lần cả lô thay vì duyệt từng bước.

