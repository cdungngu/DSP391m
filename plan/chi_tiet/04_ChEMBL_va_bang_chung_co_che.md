# 04 — ChEMBL và bằng chứng cơ chế

Ngày: 2026-10-17 · Chủ trì: dữ liệu + dược sĩ · Phụ thuộc [02](02_Danh_muc_thuoc_va_phan_giai_danh_tinh.md), [03](03_Snapshot_DataView_va_chong_ro_ri.md).

## 1. Hiện trạng và giới hạn cụ thể

chembl.py đã có phân trang, batch, exact/connectivity mapping, parent, mechanisms, targets và cập nhật tên. Cần hoàn thiện trước sử dụng:
- map_drugs chọn best candidate; chưa lưu toàn bộ bằng chứng quyết định.
- update_names thêm synonyms kể cả mapping connectivity; cờ review không ngăn resolver dùng.
- mechanisms nối symbol → gene bằng một giá trị đầu; chưa giữ đầy đủ accession protein.
- organism được lưu nhưng không lọc bản ghi trước mọi đường sử dụng.
- Báo cáo tổng độ phủ cơ chế không đồng nghĩa độ phủ cơ chế tương tác cặp.

Đây là nhận xét từ đọc mã, chưa phải kết quả chạy collector.

Cập nhật cuối phiên: mã thêm nhánh neutralized bằng sửa ký tự protonation cuối InChIKey thành N và coi mapping này không cần review. Thiết kế yêu cầu ghi transformation và xác minh cấu trúc/parent, không coi thao tác chuỗi là bằng chứng đủ để công bố alias. Mọi mapping trong consumer catalog vẫn phải có quyết định duyệt; bổ sung fixture protonation, ion không trung hòa được và đồng phân.

## 2. Đầu vào/đầu ra

Đầu vào: cấu trúc 645 thuốc, catalog duyệt, nguồn ChEMBL khóa version.
Đầu ra: mapping candidates và SingleDrugMechanism evidence theo contract 01. Giữ matched ID, parent ID, mec_id, target ID/type, organism, components/accessions, action_type, direct_interaction, refs, review_status và content_hash.

Tách coverage: khớp phân tử; có cơ chế; cơ chế người; target có accession; mapping đã duyệt; bằng chứng hỗ trợ một claim cặp. Báo riêng 645 thuốc và danh mục demo.

## 3. Pipeline

1. Query exact InChIKey và lưu ứng viên; fallback connectivity chỉ cho review.
2. Theo molecule hierarchy đến parent; không xóa ID hóa học ban đầu.
3. Lấy mechanism + target components + refs; phân loại protein đơn, family, complex, non-protein.
4. Giữ organism; chỉ quan hệ phù hợp người mới đi vào nhánh giải thích người, quan hệ khác là bối cảnh riêng.
5. Nối protein bằng accession có namespace/species. Gene symbol chỉ là candidate mapping; nhiều kết quả thì chưa nối.
6. Biên dịch evidence riêng cho từng quan hệ, không gộp action_type thiếu thành inhibitor.
7. Chỉ publish catalog-facing evidence qua review và manifest.

ChEMBL mechanism là thông tin cơ chế tác động; không mặc định phủ đầy đủ substrate/inhibitor/inducer của chuyển hóa thuốc. Cần nguồn bổ sung trực tiếp nếu tiền đề PK còn thiếu.

## 4. Quy tắc suy luận có giới hạn

Chia kết luận thành:
- Fact: “nguồn ghi A có action X trên target T”.
- Pair hypothesis: hai fact tạo một giả thuyết, chưa đủ khẳng định outcome.
- Pair statement: nguồn trực tiếp hoặc rule do dược sĩ duyệt có đủ tiền đề, điều kiện và kết luận.

Rule v1 có rule_id, required_relations, species, applicability, allowed_conclusion, supporting_reference, reviewer. Ví dụ cấu trúc A ức chế E + B là substrate E không tự suy ra một triệu chứng; nếu chỉ chứng minh khả năng thay đổi phơi nhiễm thì kết luận dừng ở đó. Không dùng PPI để bổ sung tiền đề dược động học còn thiếu.

## 5. Cải tiến thử nghiệm

E04 so sánh: facts riêng lẻ + LLM; facts có rule kiểm chứng; template trên facts. Giữ cùng nguồn/query/token budget. Dược sĩ chấm đúng quan hệ, đủ tiền đề, outcome overclaim và tỷ lệ đủ thông tin. Thử trên 20 ca dev có cả target chung nhưng không có kết luận tương tác.

Chỉ giữ rule khi từng rule có hồ sơ duyệt và không tạo overclaim trên các counterexample. Không báo hiệu quả chung từ một ví dụ đúng.

## 6. Checklist và nghiệm thu

- [ ] Lưu đủ candidates, accession, reference và provenance.
- [ ] Test salt/parent, connectivity ambiguity, missing action, protein family/complex, non-human target.
- [ ] Synonym chưa duyệt không đi vào consumer resolver.
- [ ] Test symbol trùng không chọn tùy tiện.
- [ ] Mọi claim cặp có nguồn trực tiếp hoặc rule + toàn bộ tiền đề được truy vết.
- [ ] Không có cơ chế trả insufficient, không gọi LLM bịa phần thiếu.
- [ ] Có báo cáo coverage thực trước khi ghi GĐ3 hoàn thành.

## 7. Nguồn và phương án dự phòng

[ChEMBL API và resources](https://github.com/chembl/GLaDOS-docs/blob/master/web-services/chembl-data-web-services.md). Giữ license theo snapshot; không coi cache API là nội dung tự tạo.
Nếu coverage thấp, tăng bằng chứng DailyMed trên catalog trước; chưa mở thêm KG lớn. Ước lượng hoàn thiện 2–3 ngày công cộng thời gian duyệt.
