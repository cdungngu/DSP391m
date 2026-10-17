# 01 — Định nghĩa bài toán và hợp đồng đầu ra

Phụ thuộc: [00](00_Dieu_phoi_va_ra_soat.md). Trạng thái: thiết kế.

## Câu hỏi nghiên cứu

Cho hai thuốc phân biệt A và B trong không gian 645 ID Decagon, xếp hạng 963 nhãn tác dụng phụ theo điểm mô hình. Kiểm tra khả năng khôi phục các nhãn quan sát trên cặp được giữ lại khỏi train.

Đây là lựa chọn thiết kế dựa trên dữ liệu đang có. “Dự đoán cặp” được cụ thể hóa thành bài toán đa nhãn, không tự chuyển thành phân loại tương tác có/không. Các cặp chưa báo cáo và các ô chưa có nhãn không tạo thành ground truth an toàn. Nếu sau này cần bài toán nhị phân, phải thiết kế nguồn nhãn và protocol riêng.

## Không gian và ý nghĩa

- Canonical pair = hai ID được sắp thứ tự; A–B và B–A cùng một truy vấn.
- y(A,B,e)=1 nếu snapshot ghi nhận e; 0 nghĩa là chưa quan sát và được coi âm giả định trong phép đo.
- Score là mức ưu tiên xếp hạng, không phải xác suất biến cố, độ nặng hoặc khuyến nghị sử dụng.
- Tập test gồm cặp có báo cáo bị giữ lại. Không gọi kết quả là kiểm định trên mọi cặp chưa từng có báo cáo, thuốc hoàn toàn mới hay dự đoán theo thời gian.
- Không nhận đơn từ ba thuốc, không tổng hợp rủi ro bệnh nhân, không sinh cơ chế bằng LLM ở lõi.

## Hợp đồng nội bộ đề xuất

Predictor có fit(train_view), score_pairs(pairs) → ma trận float32 [n_pairs,963], save/load. DistMult trainer tách fit để nhận validation callback của evaluator; callback chỉ trả metrics cần chọn checkpoint, không cấp test labels.

PredictionRequest: schema_version, drug_a_id, drug_b_id, model_release_id, top_k (1–963).
PredictionResult: schema_version, canonical_pair, model_release_id, snapshot_hash, split_hash, vocabulary_hash, score_kind, predictions, input_flags, trained_drug_coverage.
Mỗi prediction: effect_cui, raw_effect_name, score, rank. Khi hòa điểm xếp CUI tăng dần. Không đưa bản dịch tự sinh thành nhãn chuẩn.

score_kind: frequency_sum cho B0, bilinear_logit cho DistMult. Không so trực tiếp trị số score giữa hai loại mô hình.
Status: scored / invalid_input / unsupported_drug / artifact_mismatch. Không dùng status “safe”.

ObservationPanel là kết quả lookup riêng: observed/not_observed, nguồn và phiên bản. Chỉ nối sau scoring, không chuyển các nhãn quan sát vào predictor. Trong benchmark không bật panel. Gắn train_seen_pair rõ cho demo các cặp đã học.

## Biên và lỗi

ID ngoài snapshot, A=B, thiếu một ID hoặc top_k không hợp lệ → lỗi có cấu trúc. Không âm thầm bỏ thuốc rồi chấm tập con. Drug có trong vocab nhưng không có train support → báo coverage; DistMult từ chối suy luận riêng trường hợp embedding chưa được học, không dùng vector ngẫu nhiên. Trong benchmark phải đếm và công bố các trường hợp này trước khi chạy; nếu có, đăng ký fallback B0 cho mọi model liên quan và báo metric phân tầng, không loại cặp để làm đẹp điểm.

## Tiêu chí nghiệm thu

- [ ] Fixture đảo thứ tự A/B cho cùng kết quả.
- [ ] ID và CUI gắn với artifact hash, không phụ thuộc vị trí DataFrame tình cờ.
- [ ] 963 điểm hữu hạn, thứ tự ổn định, save/load không đổi kết quả trong tolerance công bố.
- [ ] Output không có phần trăm nguy cơ hay nhãn “không tương tác”.
- [ ] Ví dụ scored và mọi lỗi biên được lưu như fixture, không nhầm với dữ liệu y khoa.

Bàn giao: schema, ví dụ JSON và adapter chung cho B0/DistMult. Giữ consumer contracts cũ nguyên nghĩa; research contract mới không gọi resolver chỉ nhận approved catalog.

