# 03 — Snapshot, DataView và chống rò rỉ

Ngày: 2026-10-17 · Chủ trì: dữ liệu · Phụ thuộc contract [01](01_Pham_vi_san_pham_va_hop_dong_dau_ra.md).

## 1. Hiện trạng

splits.py xác minh checksum và từ chối ghi đè split; DataView prediction lọc train và tính lại metadata. Cache có mode/split/snapshot. Tuy nhiên các nguồn mới, tên đã duyệt, prompt, model và verifier chưa được biểu diễn đầy đủ trong khóa. Collector hiện ghi vào snapshot processed, nên cần phân biệt dữ liệu lõi đóng băng với nguồn bổ sung.

Không tạo lại split pair_70-10-20_s391 chỉ để phù hợp thiết kế mới.

## 2. Kiến trúc nguồn và quyền truy cập

- Raw Decagon chỉ đọc; snapshot lõi và split giữ nguyên.
- Nguồn ngoài lưu raw response + fetch metadata bất biến; normalized corpus tạo version mới.
- Catalog duyệt là release riêng, phụ thuộc hash nguồn mapping.
- RunContext chọn source manifest trước khi nạp chỉ mục.
- consumer_review/research_explanation dùng evidence data; prediction_eval dùng prediction data.
- Evaluator là nơi duy nhất đọc held-out labels. Corpus DailyMed/ChEMBL không đi vào score B0/B2 của benchmark chính.

Phần giải thích một dự đoán dùng corpus đầy đủ phải ghi là thí nghiệm giải thích có nguồn sau dự đoán, không cộng điểm đó vào predictive performance. Nếu muốn retrieval tham gia dự đoán, tạo protocol riêng và đánh giá nguồn có thể lộ nhãn, kể cả câu nói theo nhóm thuốc.

## 3. Manifest và khóa cache

SourceManifest gồm source_name, source_version, fetched_at, URL/query, raw hashes, normalized hashes, parser_version, license_url, catalog_review_version, completeness/status. Tính corpus_hash từ nội dung đã chuẩn hóa và manifest; không chỉ từ thời gian.

Cache key = hash của RunContext + canonical ingredient IDs + điều kiện đầu vào + retrieval_config + model ID/version + prompt_hash + verifier_version + output_schema_version.
Canonicalization không xóa route/formulation. Cùng hoạt chất nhưng route khác không được dùng chung kết quả nếu nguồn có điều kiện.

Ghi artifact qua tệp tạm rồi atomic rename; hash được xác minh trước publish. Cache hỏng coi là miss có log, không dùng kết quả cũ chưa xác minh.

## 4. Thay đổi API dự kiến

Giữ evidence_view/prediction_view và Cache hiện có. Thêm SourceManifest/RunContext ở lớp service; truyền context vào retrieval và cache adapter. Không để collector tự chọn split hay LLM truy cập trực tiếp parquet.

Đối với test fixtures có snapshot nhỏ, truyền đường dẫn nguồn rõ thay vì dùng global production directory. ReviewResult chứa đủ version để tái tạo câu trả lời.

## 5. Kiểm thử

- [ ] Các test split hiện có tiếp tục đạt sau tích hợp.
- [ ] Thay catalog/corpus/prompt/model/verifier làm cache miss.
- [ ] Thứ tự nhập thuốc khác nhau cho cùng ingredients/conditions dùng cùng semantic key.
- [ ] Evidence mode không chia cache với prediction mode.
- [ ] Nhãn val/test không xuất hiện trong features/metadata train hoặc evidence bundle của benchmark.
- [ ] Partial fetch không được publish thành corpus complete.
- [ ] Bản nguồn cũ vẫn đọc được sau refresh; chạy offline tái lập được bundle.

## 6. Phương án thay thế và quyết định

Dùng file manifest + Parquet/JSON ở v1; chưa cần hệ quản trị version dữ liệu lớn. SQLite có thể dùng cho chỉ mục evidence, nhưng nguồn chuẩn vẫn là artifact có hash. Nếu tăng số nguồn, thử catalog DB sau khi profiling chứng minh file lookup là nút thắt.

## 7. Công việc và cổng

1. Liệt kê nguồn hiện có và điểm ghi đè.
2. Tạo loader nguồn theo manifest và migration adapter đọc dữ liệu cũ.
3. Bổ sung khóa cache và kiểm tra integrity.
4. Chạy fixtures leakage; publish manifest nguồn đầu tiên.

Cổng đạt khi một query có thể tái tạo offline từ run manifest và thử hoán đổi nguồn bị phát hiện. Ước lượng 1–2 ngày công, không bao gồm tải/duyệt nguồn.

