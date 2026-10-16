# Báo cáo triển khai — 17/10/2026

## 1. Kết quả thực hiện

Đã bắt đầu **triển khai mã**, không chỉ viết thêm plan. Hoàn thành luồng nền có thể kiểm thử: chuẩn bị dữ liệu chờ duyệt → nhập quyết định duyệt → phát hành catalog/corpus có checksum → nhận diện đầy đủ đơn → trả câu template từ bằng chứng đã duyệt → chặn claim không được hỗ trợ.

**Chưa hoàn thành toàn bộ 15 plan.** Người dùng xác nhận chưa có danh mục được dược sĩ duyệt. Vì vậy chưa nghiệm thu consumer trên dữ liệu thật, chưa có gold set và chưa qua cổng M. Những bước này không được đánh dấu xong bằng fixture.

## 2. Các bước đã triển khai

| Bước | Mã/artifact | Kết quả |
|---|---|---|
| Contracts | contracts.py | RunContext kiểm tra purpose/mode/split; EvidenceRecord, Claim; consumer serializer dùng allowlist |
| Catalog | catalog.py | Xuất candidates, nhập review có provenance/source hash; chỉ resolve approved; tên mơ hồ/fuzzy không tự chọn |
| Chế phẩm | catalog.py | Khai triển thành hoạt chất đã duyệt; giữ route, nhận diện trùng; kiểm tra 2–5 hoạt chất |
| Releases | releases.py | Hash nội dung, xác minh nguồn, phát hành atomic không ghi đè |
| Template/verifier | review.py | Không phân tích tập con khi còn input chưa rõ; chỉ publish nguyên văn câu tiếng Việt đã duyệt, giữ điều kiện |
| Chuẩn bị duyệt | workbench.py | 645 ứng viên thuốc, 129 đoạn DailyMed; tất cả pending, không tự chọn 50 thuốc hoặc tự ký duyệt |
| B0 | models/b0.py, b0_experiment.py | Thêm smoothing alpha, kiểm tra index/đối xứng; chạy E08 chỉ trên val |
| Evaluator | evaluate.py | So thứ tự nhãn bằng CUI/ID, metric không xác định trả null; xử lý nhóm không có nhãn hợp lệ |

Các đường lookup cũ được giữ; luồng consumer mới là CLI riêng. Không coi luồng CLI template này là web UI đã hoàn tất.

## 3. Kết quả B0 trên validation

Split chính thức, 6.347 cặp × 963 nhãn; dùng cùng nhãn và ma trận chấm:

| Alpha | Macro AP |
|---|---:|
| 0 — baseline | 0,271431 |
| 5 | 0,274061 |
| 20 | 0,279489 |
| 100 | 0,288953 |

Alpha 100 được chọn theo quy tắc nhỏ nhất nằm trong 0,001 so mức tốt nhất của **bốn cấu hình đã thử**. Tăng tuyệt đối khoảng **0,01752 macro AP** so B0 gốc. Đây là kết quả chọn cấu hình trên val, chưa có paired bootstrap cho mức tăng, chưa chấm test, chưa đo top-k theo cặp và không phải xác suất nguy cơ lâm sàng. Chưa thay baseline đã công bố hay triển khai cho consumer.

Artifact bất biến: [kết quả E08](../results/experiments/2026-10-17_b0_smoothing_v1.json). Artifact ghi git commit tại lúc chạy nhưng mã mới còn trong working tree; tái lập cần giữ cả working tree/diff của phiên này, chưa coi commit đó chứa toàn bộ mã thí nghiệm.

## 4. Kiểm thử đã chạy

- `.venv/bin/pytest -q`: **61 passed**, 2 slow tests deselected; không còn cảnh báo Mean of empty slice.
- `.venv/bin/pytest -q -m slow`: **2 passed**, 61 deselected; kiểm tra dữ liệu và split thật.
- 19 test mới được thêm cho foundation/workbench/evaluator; tổng số test chạy thành công là 63.
- Kiểm tra: pending không resolve; input chưa rõ không bị bỏ; product chỉ dùng ingredient approved; alias mơ hồ; source hash sai; publication ghi đè; source bị sửa; cache đổi theo context; citation thật sai câu/chủ thể/điều kiện; dữ liệu nghiên cứu không thành claim consumer.

Các unit test dùng quyết định duyệt **giả lập ghi rõ fixture**. Không có quyết định dược sĩ thật được tạo. Kiểm tra dữ liệu thật không huấn luyện hoặc chấm model trên tập test cuối.

## 5. Gói bàn giao để dược sĩ duyệt

Thư mục [data/review/2026-10-17_foundation_v1](../data/review/2026-10-17_foundation_v1):

- `catalog_candidates.json`: ứng viên và source hash.
- `evidence_candidates.json`: đoạn gốc, ID, source/version và content hash.
- `sources.json`: checksum các tệp nguồn thực.
- `review_instructions.json`: các trường cần chuẩn bị cho review/gold.

Mỗi file là envelope `{"payload": ..., "content_hash": ...}`. **Không sửa trực tiếp envelope đã xuất**; quyết định duyệt ghi thành JSON riêng rồi import. Chưa có 50 thuốc duyệt: danh sách 645 là hàng đợi, không phải catalog công khai.

### Quyết định catalog

Tạo một mảng JSON; mỗi phần tử lấy ingredient_id/source_hash từ candidate. Cần có display_name_vi, aliases đã xem, review_status, reviewer, reviewed_at, rationale và review_source. Chỉ đưa tên thương mại khi đã kiểm chứng sản phẩm; products mặc định rỗng. Không sao chép toàn bộ synonyms chưa xem thành aliases approved.

```bash
.venv/bin/python -m dsp391m.catalog import-decisions \
  --candidates data/review/2026-10-17_foundation_v1/catalog_candidates.json \
  --decisions /duong/dan/catalog_decisions.json \
  --out data/review/catalog_approved_v1.json
```

### Quyết định bằng chứng

Mỗi phần tử cần evidence_id và content_hash của candidate; subjects là hai ingredient ID đã duyệt, phải chứa thuốc gốc của nhãn; statement_vi, conditions đầy đủ, review_status, reviewer, reviewed_at và rationale. Người duyệt phải kiểm tra đoạn gốc và sự phù hợp, không chỉ xem có tên hai thuốc.

```bash
.venv/bin/python -m dsp391m.workbench publish-corpus \
  --catalog data/review/catalog_approved_v1.json \
  --drafts data/review/2026-10-17_foundation_v1/evidence_candidates.json \
  --decisions /duong/dan/evidence_decisions.json \
  --out data/review/corpus_approved_v1.json
.venv/bin/python -m dsp391m.review TEN_HOAC_ID_A TEN_HOAC_ID_B \
  --catalog data/review/catalog_approved_v1.json \
  --corpus data/review/corpus_approved_v1.json
```

Các lệnh trên là hướng dẫn sau duyệt, **chưa chạy với dữ liệu được duyệt thật**. Khi nguồn đã thay đổi, xuất packet mới và duyệt theo hash mới. SourceManifest hiện dùng đường dẫn tuyệt đối máy này; chuyển máy cần tạo/kiểm tra lại manifest, chưa hỗ trợ relocation tự động.

## 6. Trạng thái đối với từng plan

| Plan | Trạng thái sau phiên |
|---|---|
| 00 Điều phối | Có báo cáo mã/test/artifact và điểm chờ |
| 01 Contracts | Đã triển khai phần cần cho template consumer; chưa toàn bộ JSON schema/giao diện |
| 02 Danh tính | Có export/import/resolver; **chờ danh mục và duyệt thực** |
| 03 Snapshot | Có immutable releases/source checks/context cache key; chưa migration toàn collector/cache hiện hữu |
| 04 ChEMBL | Kế thừa mã cũ; các sửa mapping/accession/rule trong plan chưa hoàn thành |
| 05 DailyMed | Xuất 129 đoạn vào packet pending; chưa sửa toàn parser/SPL selection |
| 06 Xếp hạng | Chưa chạy E06, cần gold |
| 07 Retrieval | Template dùng exact reviewed pair statements; chưa BM25/MMR/hybrid |
| 08 B0 | Smoothing và val đã chạy; paired CI/top-k/sensitivity 959 chưa làm |
| 09 LLM | Chưa gọi API; template đã có, chưa provider adapter/LLM pilot |
| 10 Verifier | Có verifier bảo thủ cho câu đã duyệt; chưa kiểm tra ngữ nghĩa free text hoặc source conflicts tự động |
| 11 Gold | Có hướng dẫn trường dữ liệu; **chưa gold thật/chấm dược sĩ** |
| 12 Giao diện | CLI consumer đã có; web/latency/usability chưa làm |
| 13 B2 | Chưa qua cổng M, không huấn luyện |
| 14 Final | Chưa khóa đánh giá cuối; không chạy final test |

## 7. Bước tiếp theo

Đường triển khai gần nhất: hoàn thiện collector ChEMBL/DailyMed theo plan04–05, đưa catalog/source review qua G0/G1, rồi retrieval/template trên danh mục thật. Sau đó thêm LLM/verifier, web và dev gold. Các phần phụ thuộc gold/duyệt không thể được nghiệm thu trung thực khi chưa có người duyệt.

Không có thay đổi dữ liệu Decagon gốc, không xóa kết quả cũ, không deploy công khai và không tạo chi phí API trong phiên này.
