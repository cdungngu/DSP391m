# 10 — Verifier và xử lý thiếu bằng chứng

Ngày: 2026-10-17 · Chủ trì: giải thích · Phụ thuộc [01](01_Pham_vi_san_pham_va_hop_dong_dau_ra.md), [09](09_LLM_va_giai_thich_tieng_Viet.md).

## 1. Bài toán

Một citation tồn tại chỉ chứng minh truy xuất được record, không chứng minh record hỗ trợ câu. Một path có thật không chứng minh outcome. Verifier phải xử lý cả provenance và ý nghĩa, đồng thời không tuyên bố luật tự động chứng minh mọi phát biểu y khoa.

## 2. Input/output

verify(claims, bundle, policy) → verified_claims + rejected_claims + coverage + trace.
Trạng thái theo file 01: supported/contradicted/insufficient; reason_codes có citation_missing, wrong_subject, direction_mismatch, condition_dropped, scope_overreach, source_conflict, unreviewed_mapping, unverified_semantics.

Một claim nhiều mệnh đề được tách thành các đơn vị nguyên tử trước khi chấm. Không cho citation ở cuối đoạn mặc nhiên hỗ trợ toàn bộ đoạn.

## 3. Các lớp kiểm tra

1. **Schema:** field types, pair IDs thuộc query, evidence IDs tồn tại trong bundle.
2. **Nguồn:** version/hash khớp, mode đúng, catalog mapping approved, source thuộc snapshot.
3. **Quan hệ:** chủ thể và hướng đúng; đơn thuốc không được chuyển thành cặp; target/PPI không được gán outcome.
4. **Điều kiện:** route/dose/population/negation không bị mất; class mention có membership evidence.
5. **Ngữ nghĩa:** claim template từ fact approved có thể quyết định bằng cấu trúc. Free text cần đối chiếu nguồn; nếu checker chưa đủ chắc thì insufficient, không mặc định supported.
6. **Bất đồng:** nguồn mâu thuẫn được hiển thị như bất đồng có nguồn, không chọn thuận ý model.

Không dùng danh sách từ cấm như bằng chứng đầy đủ rằng câu đúng. Một câu không chứa “chắc chắn” vẫn có thể overclaim.

## 4. Hành vi sau kiểm tra

Publish claims supported. Claim contradicted/insufficient không vào card khẳng định; chuyển reason phù hợp sang missing/conflicting panel, không hiển thị nguyên văn kết luận sai.
Nếu tất cả bị loại, dùng template “chưa tìm được đủ bằng chứng trong các nguồn đã kiểm tra” kèm phạm vi nguồn. Nếu một phần đạt, giữ phần đó và báo phần thiếu. Không thay “không có target” bằng “không có tương tác”.

## 5. Thí nghiệm E10

V0 schema+ID; V1 thêm kiểm tra quan hệ/điều kiện bằng cấu trúc; V2 thêm NLI hoặc LLM judge cho free text. Một checker bổ sung là thí nghiệm riêng, không phá mục tiêu một lần gọi model sinh câu trả lời; chi phí/latency của judge được cộng đầy đủ.

Tập challenge gồm câu đúng và câu bị biến đổi có chủ đích: đảo thuốc, đổi inhibitor/agonist, bỏ “not”, đổi route, thêm outcome, dùng citation thật sai chủ thể. Dược sĩ xác nhận nhãn trước.
Metric: false-accept unsupported, false-reject supported, coverage và latency. Chỉ giữ V2 nếu giảm false-accept so V1 và giữ coverage mục tiêu; không dùng V2 làm gold.

## 6. Checklist và cổng

- [ ] Unit tests các reason_codes và multi-claim sentence.
- [ ] Citation đúng ID nhưng sai nội dung bị chặn.
- [ ] Mất một tiền đề rule không còn được kết luận.
- [ ] Verifier fallback deterministic khi model checker lỗi.
- [ ] Lưu trace nhưng consumer không thấy câu bị loại như lời khuyên.
- [ ] Đánh giá cả rejected outputs để không che giấu lỗi sinh.

Cổng: 0 citation không tồn tại/claim sai chủ thể được publish trong challenge suite; D7 đo trên bộ dev thật. Không diễn giải “0 lỗi trong bộ thử” thành đảm bảo đúng mọi trường hợp.

