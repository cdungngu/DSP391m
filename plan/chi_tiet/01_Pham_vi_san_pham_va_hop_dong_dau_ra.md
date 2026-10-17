> **HẾT HIỆU LỰC HƯỚNG DẪN (v2.1).** Giữ để truy vết lịch sử. Dùng [bộ dự đoán cặp v3](../du_doan_cap/00_Dieu_phoi_va_ra_soat.md) và [kế hoạch tổng](../Ke_hoach_trien_khai.md). Các cổng duyệt và thứ tự bên dưới không áp dụng cho lõi v3.

# 01 — Phạm vi sản phẩm và hợp đồng đầu ra

Ngày: 2026-10-17 · Chủ trì: sản phẩm · Trạng thái: thiết kế v1.
Điều phối: [00](00_Dieu_phoi_va_phu_thuoc.md). File này là nơi định nghĩa contract; các file khác tham chiếu, không tạo enum khác.

## 1. Bài toán và hiện trạng

lookup.py nhận 2–10 thuốc, có thể tiếp tục với thuốc đã nhận diện dù còn unresolved. Đầu ra observed/no_data chỉ nói về Decagon. Nó chưa phải hợp đồng cho người dùng phổ thông hoặc bằng chứng đa nguồn.

Web v1 nhận **2–5 hoạt chất phân biệt**, tối ưu luồng 3–5. CLI nghiên cứu giữ 2–10. Nếu còn đầu vào mơ hồ, web chưa chạy review toàn đơn; trả danh sách cần chọn. Không âm thầm bỏ thuốc. Chế phẩm được khai triển thành hoạt chất đã duyệt; vượt 5 hoạt chất thì yêu cầu thu hẹp, không cắt bớt.

## 2. Phạm vi kết quả

Ba khu vực: (a) thông tin tương tác có nguồn và đúng điều kiện; (b) thông tin chưa đủ/nguồn bất đồng; (c) chi tiết nguồn. Thống kê Decagon và B0 ở màn hình nghiên cứu riêng. PPI không trực tiếp xuất hiện như cảnh báo.

Không thu thập bệnh sử hoặc liều để tạo khuyến nghị cá nhân trong v1. Nếu nguồn phụ thuộc liều/đường dùng mà đầu vào không có, kết quả phải giữ điều kiện đó hoặc đánh dấu applicability chưa xác nhận. Không khẳng định đã đánh giá đủ mọi yếu tố của người dùng.

## 3. Contracts v1

Mỗi record có schema_version=1. ID nghiệp vụ là chuỗi ổn định; drug_idx chỉ dùng bên trong snapshot.

| Contract | Trường bắt buộc và ý nghĩa |
|---|---|
| ResolvedDrug | input_token, ingredient_id, display_name_vi, source_ids, resolution_status, review_id; product_id và route có thể null |
| RunContext | purpose: consumer_review/research_explanation/prediction_eval; data_mode: evidence/prediction; snapshot_hash, split_hash nullable, catalog_version, corpus_version, config_hash |
| EvidenceRecord | evidence_id, evidence_type, subjects, relation, object_or_outcome nullable, source_url, source_record_id, source_version, content_hash, text_or_structured_fact, applicability, review_status |
| EvidenceBundle | query_id, canonical_pairs, context, evidence_records, missing_data, retrieval_trace_id |
| Claim | claim_id, pair_ids, text_vi, claim_type, evidence_ids, conditions, support_status, reason_codes |
| ReviewResult | context, input_resolution, pair_results, claims, missing_data, coverage, execution_status, timing |
| RunManifest | run_id, code_commit, dirty_diff_hash nullable, config_hash, input_hashes, created_at_utc, seed, artifact_paths |

evidence_type: curated_statement / drug_label / single_drug_mechanism / observed_association / drug_frequency / ppi_context.
support_status: supported / contradicted / insufficient. citation mismatch và overclaim là reason_codes, không phải các trạng thái loại trừ lẫn nhau.
review_status: pending / approved / rejected. Không đồng nhất approved mapping với approved claim.

Mỗi pair_result có ba trường riêng:
- observation_status: observed / not_observed, chỉ áp dụng nguồn association;
- evidence_status: supported / conflicting / insufficient;
- prediction_status: not_requested / scored / unavailable, chỉ nghiên cứu.

execution_status: needs_resolution / completed / partial / failed. partial là thiếu thành phần hoặc fallback, không là mức rủi ro. Consumer serializer không xuất trường score B0.

## 4. Luồng và ví dụ giả định

Nhập sản phẩm P và hoạt chất B → P được duyệt gồm A → tạo cặp A–B → chọn nguồn phù hợp → verifier → trả claim. Nếu nguồn chỉ nói “ở đường dùng X”, conditions phải giữ X. Nếu chưa biết route, câu không được biến thành “A và B chắc chắn tương tác”.

Ví dụ fixture không phải dữ kiện y khoa:

```json
{"schema_version":1,"execution_status":"completed",
 "claims":[{"claim_id":"fixture-c1","pair_ids":["fixture-A:B"],
 "text_vi":"Nguồn mô tả tương tác trong điều kiện X.",
 "claim_type":"interaction_statement","evidence_ids":["fixture-e1"],
 "conditions":["X"],"support_status":"supported","reason_codes":[]}],
 "missing_data":[{"scope":"pair","reason":"route_not_confirmed"}]}
```

Claim có thể chưa có effect CUI; không ép mọi câu DailyMed vào 963 nhãn.

## 5. Thiết kế triển khai và tương thích

Tạo lớp service nhận catalog IDs + RunContext, trả ReviewResult. Giữ lookup CLI cũ qua adapter; thêm consumer adapter, không sửa ý nghĩa observed của output cũ âm thầm. Dùng typed models và validation tại ranh giới collector/service/LLM. Không cần REST server riêng ở v1; Streamlit gọi service Python.

## 6. Kiểm thử và nghiệm thu

- [ ] Thuốc mơ hồ, lặp hoạt chất, chế phẩm phối hợp, ngoài danh mục đều có hành vi rõ.
- [ ] Serializer consumer không chứa B0/model_score, kể cả lồng trong evidence.
- [ ] Nguồn không có dữ liệu khác với fetch thất bại; thiếu target không xóa nhãn quan sát.
- [ ] CLI cũ vẫn chạy với fixture; consumer giới hạn 2–5 được kiểm tra sau khai triển.
- [ ] Contract có JSON examples cho completed, partial, needs_resolution và failed.

Thay đổi contract phải tăng version khi phá tương thích. Những trường thuộc UI không được thay đổi nghĩa dữ liệu nghiên cứu.

## 7. Phương án thay thế và quyết định

Không mở chat tự do trong v1: danh mục chọn giúp kiểm chứng đúng danh tính. Sau pilot, chỉ mở text entry dưới dạng tìm trong catalog; không gọi LLM để tự quyết định thuốc. Cổng mở rộng là không có mapping sai ở bộ kiểm tra danh mục và không bỏ sót input.
