# 11 — Gold set và quy trình dược sĩ

Ngày: 2026-10-17 · Chủ trì: đánh giá + dược sĩ · Phụ thuộc [01](01_Pham_vi_san_pham_va_hop_dong_dau_ra.md)–[03](03_Snapshot_DataView_va_chong_ro_ri.md). Bắt đầu cùng collectors, không đợi giao diện.

## 1. Mục tiêu và hiện trạng

Chưa thấy gold set được duyệt trong repo lúc đọc. Kế hoạch tổng có 20 dev, khoảng 100 cặp + 30 đơn cuối và D7 support≥90%, coverage≥70%. Cần định nghĩa mẫu số trước khi dùng hai ngưỡng này.

Gold phục vụ chất lượng bằng chứng/diễn đạt, không xác nhận hệ thống đã được kiểm định lâm sàng. Dược sĩ là người xác nhận nội dung chuyên môn; thành viên thứ hai chấm độc lập về hỗ trợ nguồn theo rubric.

## 2. Thiết kế mẫu

- Dev: 20 ca ban đầu, gồm cặp và đơn; đủ nguồn, thiếu nguồn, mapping mơ hồ, không target, class mention và nguồn bất đồng.
- Final: 100 cặp riêng + 30 đơn 3–5 thuốc trong catalog; phân tầng có/không nhãn Decagon, có/không target, có/không đoạn phù hợp.
- Dedupe canonical pairs giữa dev và final, kể cả cặp xuất hiện trong đơn. Các đơn final trùng một cặp được gom thành component phụ thuộc khi bootstrap; ưu tiên chọn đơn ít trùng để đủ đơn vị độc lập.
- Tập query cố định trước khi xem model outputs. Không chỉ chọn ca có nguồn dễ tìm.
- Gold final không được dùng viết prompt, glossary riêng cho test hoặc chọn config. Glossary/catalog chung được khóa trước.

Nếu tổ hợp catalog không đủ thỏa mọi tầng, báo số đạt và điều chỉnh thiết kế trước đánh giá cuối; không bịa ca hoặc lặng lẽ loại ca khó.

## 3. Biểu mẫu gán nhãn

Case: case_id, ingredient_ids, route nếu có, canonical_pairs, stratum, split, source_snapshot.
Expected fact: fact_id, pair_id, source_ids/spans, conditions, answerability, expected_scope.
Output annotation: system_blind_id, claim_id, supported/contradicted/insufficient, citation_correct, overclaim, condition_preserved, rationale.
Review: annotator_id, timestamp, independent_label, adjudicated_label, adjudication_reason.

Nguồn được đọc trước để lập expected facts. Người chấm không thấy tên cấu hình; giữ nhãn độc lập trước phân xử.

## 4. Định nghĩa metric chính

- **Claim support:** số claim nguyên tử supported / tổng claim nội dung được publish. Câu boilerplate “thiếu dữ liệu” không tính vào mẫu số. Không có claim thì metric null, không 100%.
- **Coverage D7:** số cặp truy vấn answerable có ít nhất một claim supported hữu ích / tổng cặp answerable trong gold. Đếm cặp phân biệt; báo riêng cặp/đơn.
- **Evidence availability:** số cặp answerable / mọi cặp yêu cầu; giúp không che độ phủ nguồn thấp.
- **Fact completeness:** expected facts được phản ánh đúng / expected facts, tránh tối ưu chỉ trả một fact dễ.
- **Citation precision:** claim–citation links hỗ trợ đúng / mọi claim–citation links được publish.
- Báo overclaim, contradicted, false abstention và source conflict handling riêng.

D7 giữ 90%/70% là ngưỡng tạm từ plan; dược sĩ xác nhận sau pilot và trước final. Nếu thay, ghi lý do và ngày, không nhìn final để sửa.

## 5. Quy trình chấm

1. Dược sĩ chọn catalog, duyệt mappings và rubric.
2. Hai người chấm 5 ca pilot, thảo luận bất đồng và khóa hướng dẫn.
3. Chấm độc lập phần dev còn lại; cải tiến cấu hình bằng dev.
4. Người quản lý gold giữ final ngoài đường truy cập của tuner.
5. Chấm final ẩn danh; phân xử lưu cả nhãn ban đầu.
6. Báo percent agreement và Cohen kappa cho nhãn loại trừ, kèm phân bố lớp; không chỉ một hệ số.

## 6. Thử hiểu nội dung với người dùng

5–8 người không chuyên thử prototype trên ca giả định đã kiểm chứng. Nhiệm vụ: xác định thuốc nào liên quan, nguồn nói gì, phần nào chưa biết, có được hiểu thiếu dữ liệu là an toàn không.
Ghi tỷ lệ trả lời đúng và lỗi diễn giải; mẫu nhỏ là usability pilot, không suy ra độ an toàn dân số. Nếu có người hiểu B0/association thành xác suất hoặc lời khuyên tự đổi thuốc, sửa UI rồi thử lại các ca tương ứng.

## 7. Checklist và bàn giao

- [ ] Catalog review và rubric có tên người duyệt.
- [ ] Case/source hashes, dev/final separation tests.
- [ ] Annotation độc lập, adjudication và metric script kiểm tra bằng fixture tính tay.
- [ ] Bộ final có ca thiếu nguồn và bất đồng.
- [ ] Coverage, availability và completeness đều được báo.
- [ ] Không ghi claim support khi không có claim.

Artifact dự kiến: gold_cases, expected_facts, annotations và gold_manifest; theo version, không sửa bản cuối sau khi chấm mà không ghi correction log.

