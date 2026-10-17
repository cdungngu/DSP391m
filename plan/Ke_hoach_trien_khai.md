# Kế hoạch v3 — dự đoán nhãn tác dụng phụ theo cặp thuốc

DSP391m · Cập nhật 2026-10-17 · **Thiết kế hiện hành; chưa triển khai các hạng mục mới.**

## 1. Phạm vi và quyết định thay thế

Theo yêu cầu mới của người dùng, tập trung dự đoán cặp với thời gian và nhân lực duyệt hạn chế. Lõi: **dữ liệu/split → evaluator → baseline → DistMult → chọn mô hình → demo nghiên cứu và báo cáo**.

Bài toán cụ thể: nhập hai thuốc bằng ID, xếp hạng 963 nhãn tác dụng phụ. Kế thừa benchmark hiện có; không chuyển thành nhị phân “có tương tác hay không”, vì dữ liệu vắng nhãn không chứng minh không tương tác.

Thay quyết định A+D+B0 và cổng M của v2–v2.1: DistMult vào lõi sau khi dữ liệu/evaluator đạt yêu cầu, không chờ catalog 50 thuốc, gold giải thích hay dược sĩ chấm top-10. ChEMBL, DailyMed, Graph RAG và LLM là mở rộng. Demo v3 phục vụ nghiên cứu, không sinh khuyến nghị dùng thuốc hay xác suất lâm sàng.

Giữ code/data và cổng approved của consumer đã xây; không tự duyệt pending hoặc nới kiểm soát consumer. Tạo đường dự đoán nghiên cứu bằng ID riêng.

## 2. Xuất phát điểm thực tế

| Thành phần | Đã có | Cần làm |
|---|---|---|
| Decagon/split | 645 thuốc; 963 nhãn; train/val/test 44.430/6.347/12.695 cặp | Kiểm tra train support, giữ hash |
| DataView | Tách prediction/evidence, kiểm split | Sampler và model contracts |
| B0 gốc | Val macro AP 0,271431 | Metric theo cặp và adapter |
| B0 alpha100 | Val macro AP 0,288953 | Paired CI và release |
| ChEMBL | 599 khớp; 271 có cơ chế; 218 cơ chế người; 0 mapping duyệt | Phân tầng tùy chọn |
| Foundation | contracts/releases/catalog/review/workbench | Tái dùng release, consumer giữ riêng |
| DistMult | Chưa có | Trainer, sampler, checkpoint, thí nghiệm |
| Demo predictor/final | Chưa hoàn tất | CLI/UI, final lock, báo cáo |

61 test nhanh và 2 test dữ liệu thật là kết quả trước phiên này; không chứng nhận tính năng mới. Chưa chạy huấn luyện hoặc final test trong phiên viết kế hoạch.

Nguồn: [báo cáo thực thi](Bao_cao_trien_khai_2026_10_17.md), [B0 smoothing](../results/experiments/2026-10-17_b0_smoothing_v1.json), [phân tích ban đầu](../analysis/2026-10-08/Bao_cao_danh_gia_huong_trien_khai.md).

## 3. Bộ 10 bài toán nhỏ hiện hành

| File | Phạm vi và bàn giao |
|---|---|
| [00 Điều phối và rà soát](du_doan_cap/00_Dieu_phoi_va_ra_soat.md) | Bảng chuyển đổi đủ 15 plan cũ, phụ thuộc, cổng G0–G3 |
| [01 Bài toán và hợp đồng](du_doan_cap/01_Bai_toan_va_hop_dong.md) | Hai ID → 963 điểm; ý nghĩa và lỗi biên |
| [02 Dữ liệu và chống rò rỉ](du_doan_cap/02_Du_lieu_va_chong_ro_ri.md) | Readiness, train-only inputs, ID order và manifests |
| [03 Đánh giá và khóa test](du_doan_cap/03_Danh_gia_va_khoa_test.md) | AP/top-k/NDCG, paired CI, final lock |
| [04 Baseline và shortcut](du_doan_cap/04_Baseline_va_shortcut.md) | Popularity, B0 gốc, alpha100; kiểm tần suất |
| [05 DistMult và huấn luyện](du_doan_cap/05_DistMult_va_huan_luyen.md) | Công thức, sampler, loss, budget, checkpoint |
| [06 Thí nghiệm và chọn model](du_doan_cap/06_Thuc_nghiem_va_chon_model.md) | 4 cấu hình, 3 seed, quy tắc chọn, 20 ca lỗi |
| [07 Suy luận và demo](du_doan_cap/07_Suy_luan_va_demo.md) | CLI trước, UI mỏng, offline, đúng hai ID |
| [08 Mở rộng](du_doan_cap/08_Mo_rong_va_thi_nghiem.md) | Residual/ChEMBL có đối chứng, không chặn lõi |
| [09 Bàn giao và duyệt theo đợt](du_doan_cap/09_Ban_giao_va_duyet_theo_dot.md) | Hai gói xem kết quả, cards, final report |

## 4. Các quyết định kỹ thuật chính

Giữ split pair_70-10-20_s391 và vocab 963. Mọi nhãn của một cặp cùng split. Counts, sampler và feature từ train; chỉ evaluator đọc held-out labels. Công bố ngoại lệ lịch sử: chọn vocab từ toàn snapshot, nên không mô tả pipeline hoàn toàn train-only ngay từ bước chọn nhãn.

Chấm toàn ma trận cặp × nhãn với âm giả định. Test là các cặp có báo cáo bị giữ lại; không chứng minh hiệu quả trên mọi cặp chưa từng báo cáo hoặc thuốc mới.

B0 alpha100 làm baseline mạnh. DistMult dùng score=sum(z_A*r_e*z_B), đối xứng và không cần PPI/ChEMBL. Sample âm bằng đổi nhãn trên chính cặp train, lọc positives bằng train, không cần nhãn toàn snapshot.

Macro AP theo nhãn là chính; bổ sung AP theo cặp, Precision/Recall@5/10, NDCG@10. Paired bootstrap dùng cùng resamples; ba seed đánh giá độ ổn định. Chọn backend bằng val, giữ checkpoint train-only, khóa trước final.

Thử tối đa 4 cấu hình dimension/lr seed391; cấu hình chọn chạy thêm392/393. Quy tắc promotion cụ thể ở file06, thay ngưỡng cũ +0,02/cổng dược sĩ. Nếu DistMult không vượt B0 đủ ổn định, giữ B0 cho demo và báo đầy đủ kết quả nghiên cứu.

## 5. Thứ tự thực hiện và ngân sách

1. **Nền đánh giá, 3–5 ngày công:** contract → readiness/leakage → evaluator → baseline đầy đủ.
2. **Mô hình, 3–5 ngày công:** smoke test → cấu hình → ba seed → error analysis và chọn backend.
3. **Bàn giao, 2–4 ngày công:** predictor/demo → lock → final test → báo cáo.

Tổng 8–14 ngày công là ước lượng, phụ thuộc máy/runtime. Không tự bắt đầu lại khung sáu tuần cũ hoặc cam kết lịch khi chưa đo một epoch. CLI có thể dựng bằng B0 trong lúc làm trainer.

**Bước triển khai tiếp theo: file02 và file03.** Kiểm train support, bổ sung metric theo cặp, paired comparison và evaluation runs bất biến; rồi chuẩn hóa baseline và bắt đầu DistMult. Chưa cần tải thêm nguồn hoặc triển khai LLM.

## 6. Giảm công duyệt

Đợt 1 xem một gói baseline/pilot, ngân sách, 20 ca val được chọn có quy tắc. Đợt 2 xem model selection, final report và demo. Không yêu cầu duyệt từng dòng hay 645 mapping/129 chunks cho benchmark.

Nếu không có chuyên gia, giữ ID/mapping flags và không viết kết luận cơ chế. Việc xem báo cáo kỹ thuật không đồng nghĩa approved mapping hoặc kiểm định lâm sàng.

## 7. Phần hoãn và các hướng mới

Hoãn consumer catalog 50 thuốc, gold 100 cặp + 30 đơn, RAG/LLM sản phẩm, đơn ≥3 thuốc, GNN và cold-start. Giữ toàn bộ cache/collector/review artifacts. ChEMBL có thể dùng ngay để phân tầng lỗi; không bỏ công đã làm.

Sau lõi, nhận tối đa một mở rộng: residual DistMult trên B0 hoặc ChEMBL features với exact mapping và missing mask. File08 thiết kế phép đối chứng và điều kiện dừng; lợi ích phải đo, không mặc định mô hình nhiều thành phần tốt hơn.

## 8. Tiêu chí hoàn tất và lịch sử

Bàn giao benchmark tái lập, baselines, thử nghiệm DistMult trung thực, top-k/CI, final lock, demo đúng artifact và giới hạn rõ. Nếu DistMult đã thử đầy đủ nhưng không thắng, vẫn hoàn tất nghiên cứu; nếu chưa chạy đủ, ghi chưa hoàn tất thay vì đánh dấu xong.

[Bản tổng v2.1 lưu trữ](Ke_hoach_trien_khai_v2_1_lich_su.md) và [15 plan cũ](chi_tiet/00_Dieu_phoi_va_phu_thuoc.md) chỉ để truy vết. Bộ du_doan_cap là nguồn hướng dẫn hiện hành.

| Ngày | Quyết định |
|---|---|
| 2026-10-17 | v3 thay A+D+B0/cổng M của v2–v2.1 theo yêu cầu tập trung dự đoán cặp, ít nhân lực duyệt |
| 2026-10-17 | Tạo 10 plan mới; giữ bản tổng v2.1, đánh dấu 15 plan cũ hết hiệu lực |

Cơ sở phương pháp: [Decagon](https://arxiv.org/abs/1802.00543) cho dự đoán nhiều nhãn tác dụng phụ; [DistMult](https://arxiv.org/abs/1412.6575) cho mô hình bilinear nhỏ. Budget và cổng v3 là lựa chọn thiết kế của dự án, chưa là kết quả thực nghiệm.
