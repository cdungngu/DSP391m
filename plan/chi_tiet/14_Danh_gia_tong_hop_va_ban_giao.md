> **HẾT HIỆU LỰC HƯỚNG DẪN (v2.1).** Giữ để truy vết lịch sử. Dùng [bộ dự đoán cặp v3](../du_doan_cap/00_Dieu_phoi_va_ra_soat.md) và [kế hoạch tổng](../Ke_hoach_trien_khai.md). Các cổng duyệt và thứ tự bên dưới không áp dụng cho lõi v3.

# 14 — Đánh giá tổng hợp và bàn giao

Ngày: 2026-10-17 · Chủ trì: đánh giá · Phụ thuộc [11](11_Gold_set_va_quy_trinh_duoc_si.md), [12](12_Giao_dien_va_van_hanh.md), [13](13_Cong_M_va_B2_co_dieu_kien.md) nếu chọn B2.

## 1. Mục tiêu

Báo riêng chất lượng dự đoán, truy xuất, giải thích, khả năng hiểu và vận hành. Một metric không thay thế phần còn lại. Không dùng dữ liệu nhãn đầy đủ của evidence mode để tuyên bố dự đoán chưa quan sát.

Hiện evaluate.py có --final; cần thêm quy trình khóa cấu hình và artifact runs không ghi đè. Cờ CLI không ngăn con người tune trên test, nên cả quy trình và manifest phải được lưu.

## 2. Ma trận thí nghiệm

| Nhóm | Cấu hình | Giữ cố định | Câu hỏi |
|---|---|---|---|
| Prediction | popularity, B0 gốc, B0 chọn val, B2 nếu qua M | Split/vocab/full matrix | Cải thiện score tới đâu? |
| Explanation tổng | LLM không retrieval; Graph RAG đơn giản; Decagon-only; đầy đủ | Query/model/budget/rubric | Hiệu quả hệ thống tổng? |
| Nguồn | Decagon; +ChEMBL; +DailyMed | Retrieval policy và generator | Nguồn nào bổ sung giá trị? |
| Verifier | Cùng draft trước/sau verify | Bundle và draft outputs | Giảm false claim với mất coverage bao nhiêu? |
| Retrieval | BM25; MMR; hybrid nếu đã thử | Corpus/query/token budget | Đủ evidence hơn không? |
| Diễn đạt | Template; LLM | EvidenceBundle | Dễ hiểu hơn mà vẫn đúng? |

Không bắt buộc chạy mọi biến thể hybrid/B2 nếu không qua cổng. Các baseline yếu chỉ chạy trong harness, không công khai cho người dùng.

## 3. Khóa đánh giá cuối

Tạo evaluation_lock gồm code/config/model/prompt/corpus/catalog/gold/split hashes và danh sách models. Phê duyệt lock nội bộ trước mở nhãn test. Mỗi model/config final chạy một lần theo lock; bootstrap không phải huấn luyện lại.
Output vào results/final/run_id, không ghi đè. Lỗi kỹ thuật có thể chạy lại với retry_of và lý do, giữ artifact lỗi; thay thuật toán sau xem test phải đánh dấu exploratory, không thay kết quả final đã đăng ký.

Không tuyên bố test “chưa dùng” nếu lịch sử cho thấy đã chấm. Kiểm tra artifacts/logs trước khi đóng lock.

## 4. Thống kê và báo cáo

Prediction: macro/micro AP, AUROC phụ, per-label/per-pair và phân tầng theo file08; CI theo cặp, so model bằng paired resamples.
Explanation: các mẫu số file11; CI resample theo case hoặc component chứa cặp trùng, không coi mỗi claim độc lập.
Latency: cold/warm, cache hit/miss, timeout/fallback, p50/p95; tokens thực và chi phí theo giá có ngày kiểm tra.
Báo numerator/denominator, số ca thiếu/loại và lý do. Metric undefined là null có reason.

D7 là support≥90%, coverage≥70% theo định nghĩa đã khóa; báo cả evidence availability và fact completeness. Không hạ ngưỡng sau xem final. Nếu thất bại, mô tả phần chưa đạt và giới hạn phạm vi demo.

## 5. Tiêu chí bàn giao

- [ ] Final prediction không rò rỉ; manifest đủ tái lập.
- [ ] Không citation giả/sai chủ thể được publish trong challenge suite.
- [ ] Consumer không hiển thị B0 hoặc suy thiếu dữ liệu thành an toàn.
- [ ] Có kết quả dev/final tách biệt, error analysis và trường hợp chưa giải quyết.
- [ ] Data card ghi nguồn, license, coverage, mapping và snapshot.
- [ ] Model/system card ghi endpoint, assumed negatives, giới hạn causal/clinical.
- [ ] Hướng dẫn offline fixtures, chạy pipeline và tái tạo report.
- [ ] Các số trong README/plan/demo khớp run artifacts.

## 6. Báo cáo tiến độ thực hiện bộ tài liệu

Công việc hoàn thành của đợt 17/10 là **viết thiết kế 00–14 và cập nhật đường dẫn điều phối**. Các checklist triển khai còn mở được giữ [ ]. Không chạy API LLM, huấn luyện B2 hoặc tập test trong đợt viết plan.

Bước thực thi sản phẩm đầu tiên: contract01 + catalog review02 + source versioning03; đồng thời chuẩn bị rubric11. Các collector đã có phải được hoàn thiện theo lỗi cụ thể ở 04–05, không viết lại tùy ý.

## 7. Phương án thu gọn

Nếu thiếu thời gian/dược sĩ: giảm danh mục công khai xuống tập đã duyệt, giữ template cho case chưa có LLM đủ chuẩn, bỏ các thí nghiệm tùy chọn. Không bỏ provenance, kiểm soát mapping, tách research/consumer hay giao thức test để kịp demo.
