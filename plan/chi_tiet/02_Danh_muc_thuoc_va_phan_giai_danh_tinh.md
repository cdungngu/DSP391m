> **HẾT HIỆU LỰC HƯỚNG DẪN (v2.1).** Giữ để truy vết lịch sử. Dùng [bộ dự đoán cặp v3](../du_doan_cap/00_Dieu_phoi_va_ra_soat.md) và [kế hoạch tổng](../Ke_hoach_trien_khai.md). Các cổng duyệt và thứ tự bên dưới không áp dụng cho lõi v3.

# 02 — Danh mục thuốc và phân giải danh tính

Ngày: 2026-10-17 · Chủ trì: dữ liệu + dược sĩ · Phụ thuộc: [01](01_Pham_vi_san_pham_va_hop_dong_dau_ra.md), [03](03_Snapshot_DataView_va_chong_ro_ri.md).

## 1. Hiện trạng và vấn đề

names.py dùng PubChem/related CID; lookup.resolve cho phép tên hoặc CID liên quan. ChEMBL có exact/connectivity và lựa chọn ứng viên theo max_phase. needs_review hiện chưa phải cổng chặn dùng alias. Báo cáo tên hiện ghi 271/645 chưa có tên hiển thị, gồm 253 pending và 18 none. Không tiếp tục gọi PubChem/NCBI theo lô để lấp thiếu; dùng cache và nguồn được phép truy cập.

Khớp connectivity không xác nhận đồng phân; parent mapping không xác nhận rằng mọi sản phẩm có cùng điều kiện sử dụng. Một tên thương mại có thể khác thành phần theo quốc gia.

## 2. Đầu vào và đầu ra

Đầu vào: drugs, drug_structures, drug_names, ứng viên ChEMBL và danh sách khoảng 50 hoạt chất dược sĩ chọn trong 645 thuốc.
Đầu ra có phiên bản: ingredients, products, aliases, mapping_candidates, review_decisions.

- Ingredient: ingredient_id, tên chuẩn/tiếng Việt, source IDs, dạng muối nếu có.
- Product: product_id, brand, country, route, formulation, ingredient_ids, nguồn xác nhận.
- Alias: chuỗi gốc/chuẩn hóa, owner ID, ngôn ngữ, source, review_id.
- Review: reviewer, thời điểm, quyết định approved/rejected/pending, reason, source_url/hash.

Tên thương mại thiếu thông tin thành phần/quốc gia chưa được đưa vào catalog công khai. Công khai từng đợt đã duyệt; không cần chờ đủ 50 để kiểm thử nội bộ.

## 3. Thuật toán phân giải

1. Chuẩn hóa Unicode NFC, khoảng trắng và case; giữ chuỗi gốc. Tìm không dấu chỉ để gợi ý.
2. Catalog ID hoặc alias approved khớp duy nhất → resolve.
3. Nhiều kết quả → trả candidates kèm hoạt chất, dạng, route, quốc gia; người dùng chọn.
4. Không khớp → fuzzy top 3 trên catalog đã duyệt; không tự chọn theo ngưỡng.
5. Product approved → khai triển ingredient_ids; gộp ingredient trùng nhưng giữ input contributions.
6. Mapping hóa học chưa duyệt chỉ hiển thị trên hàng đợi nội bộ; không trở thành alias của consumer.

Exact InChIKey tạo ứng viên ưu tiên, không thay thế kiểm tra sản phẩm. Connectivity chỉ tạo tập ứng viên. max_phase được phép dùng sắp hàng đợi, không là tiêu chí chứng minh danh tính.

## 4. Thiết kế duyệt

Dược sĩ duyệt danh mục theo lô 10 thuốc: tên, alias, parent/salt, route, products và nguồn. Ưu tiên 58 trường hợp bị gắn cờ cấu trúc và các chất nghi ánh xạ sai nếu chúng nằm trong danh mục. Giữ toàn bộ trong dataset nghiên cứu; catalog công khai có thể loại một mục và ghi lý do.

Hàng đợi CSV có cột: candidate_id, original_id, proposed_ingredient_id, match_type, source, ambiguity, decision, rationale, reviewer, reviewed_at. Import quyết định phải kiểm tra ID và source hash, không nhập hàng đã sửa nguồn mà không duyệt lại.

## 5. Thử nghiệm cải tiến

E02: baseline resolver hiện tại so với resolver catalog hai bước. Tập kiểm tra gồm mọi alias approved, ít nhất 20 tên gõ sai và 20 tình huống mơ hồ/khác muối/chế phẩm. Fixture giả định tách khỏi sản phẩm thật.
Metric: exact resolution accuracy, wrong-auto-resolution count, abstention rate, số thao tác xác nhận. Yêu cầu **0 tự khớp sai** trên tập duyệt; fuzzy tăng recall gợi ý nhưng không được giảm điều kiện này.

## 6. Checklist và nghiệm thu

- [ ] Xuất catalog candidate từ nguồn hiện có, không sửa source tables.
- [ ] Dược sĩ duyệt mọi mục sẽ xuất hiện công khai.
- [ ] Chuyển alias chưa duyệt sang resolver nội bộ.
- [ ] Test đồng danh, khác đồng phân, route, product nhiều hoạt chất, trùng hoạt chất và ngoài catalog.
- [ ] Bất kỳ catalog release nào có manifest, reviewer và rollback về phiên bản trước.
- [ ] UI không phân tích một tập con khi input chưa được xác nhận hết.

Nếu dược sĩ chưa có thời gian: chỉ demo bằng ID/hoạt chất đã duyệt; không giải quyết bằng cách bỏ cờ needs_review.

## 7. Nguồn và giới hạn

[ChEMBL web services](https://github.com/chembl/GLaDOS-docs/blob/master/web-services/chembl-data-web-services.md) mô tả molecule, molecule_form và parent. Dữ liệu này hỗ trợ ứng viên danh tính, không thay thế nguồn đăng ký chế phẩm tại Việt Nam. V1 không hứa phủ tên thương mại Việt Nam ngoài danh mục.
