# 03 — Evaluator, độ bất định và khóa test

Phụ thuộc: [01](01_Bai_toan_va_hop_dong.md), [02](02_Du_lieu_va_chong_ro_ri.md).
Hiện có evaluate.py: macro/micro AP, AUROC, bootstrap sơ bộ, phân tầng. Chưa đủ top-k, paired comparison và final lock bất biến.

## Hai hướng đánh giá khác nhau

| Metric | Đơn vị xếp hạng | Vai trò |
|---|---|---|
| Macro AP theo nhãn | Với mỗi e, xếp các cặp | Chính để chọn mô hình, nối kết quả cũ |
| Micro AP | Tất cả ô cặp × nhãn | Phụ, nhạy với nhãn phổ biến |
| Mean AP theo cặp | Với mỗi cặp, xếp 963 nhãn | Khớp hành vi demo |
| Precision@5/10, Recall@5/10 | Nhãn đầu danh sách mỗi cặp | Báo nhãn quan sát khôi phục được |
| NDCG@10 | Nhãn của từng cặp | Guardrail lựa chọn backend |
| Macro AUROC | Cặp theo từng nhãn | Phụ, không thay AP |

Chấm toàn ma trận, không sampled negatives ở val/test. Precision theo nhãn quan sát không phải tỷ lệ đúng lâm sàng: nhãn chưa ghi nhận có thể vẫn đúng ngoài đời.

AP dùng quy tắc ties của sklearn. Top-k sort score giảm rồi CUI tăng; NDCG dùng thứ tự deterministic đó để khớp demo, ghi rõ khác cách lấy kỳ vọng trên ties. Với relevance nhị phân: DCG@k=sum(y_i/log2(i+1)), i=1..k; IDCG đặt min(k,số dương) nhãn đầu bằng 1. Recall=hits/số dương, precision=hits/k.

Không có dương → AP/recall/NDCG null và lý do; báo số đơn vị hợp lệ, không biến thành 0 hoặc 1. AUROC cần cả hai lớp. Empty slice trả null; CLI và JSON phải xử lý được, cấm NaN/Infinity.

## So sánh có ghép cặp

Cache scores một lần với ID/CUI hashes. Bootstrap 1.000 resamples các hàng cặp, seed391; cùng indices cho baseline và candidate. Tính delta metric trong mỗi resample, báo estimate gốc, percentile CI95 và số resample hợp lệ. Macro AP phải tính lại trên resample, không lấy trung bình chênh lệch AP từng hàng.

Pilot 100 vòng để đo runtime; nếu cần giảm 1.000 phải ghi trước báo cáo, không dừng tùy kết quả. Không phải bootstrap dùng để chọn thêm hyperparameter. Các cặp chia sẻ thuốc nên không độc lập hoàn toàn: CI này mô tả bất định dưới giả định resample cặp trong snapshot, không chứng minh tổng quát hóa sang thuốc mới. Bootstrap cũng không bao gồm mọi bất định do model selection; báo thêm biến thiên ba seed.

## Final lock

Tạo evaluation_lock.json bất biến bằng releases sau khi xem val, trước khi chấm test thật. Chứa protocol version, metric definitions, split/vocab/source hashes, code commit + dirty diff hash nếu có, danh sách model/checkpoint hashes, seed, fallback policy, bootstrap config và selection decision.

--final hiện chỉ là cờ cho phép, chưa là lock. Bổ sung runner kiểm tra lock và ghi results/final/<run_id>/ không ghi đè. Chặn model ngoài lock; giữ retry_of và nguyên nhân nếu lỗi kỹ thuật. Thay thuật toán sau xem test là exploratory, không sửa kết quả chính. Khóa gồm popularity, B0 gốc, B0 alpha100 và ba checkpoint của cấu hình DistMult đã chọn nếu huấn luyện thành công. Chọn backend demo bằng val; không đổi dựa trên test.

## Kiểm thử và bàn giao

- [x] Ma trận nhỏ tính tay AP/top-k/NDCG; ties và thứ tự CUI.
- [x] Không dương, một lớp, tập rỗng, score không hữu hạn.
- [x] Score giống nhau → paired delta và CI bằng 0.
- [x] Đổi thứ tự cặp/nhãn được phát hiện; resample tái lập.
- [x] Lock mismatch, ghi đè run và test không lock đều bị từ chối.
- [x] Kết quả cũ vẫn đọc được, run mới có schema version.

Output: evaluation protocol, metrics module dùng chung, validation comparison và final runner. Chưa mở test trong lúc phát triển các phần này; tests sử dụng fixture.

