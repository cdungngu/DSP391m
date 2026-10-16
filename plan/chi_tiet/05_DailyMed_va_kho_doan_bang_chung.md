# 05 — DailyMed và kho đoạn bằng chứng

Ngày: 2026-10-17 · Chủ trì: dữ liệu + dược sĩ · Phụ thuộc [02](02_Danh_muc_thuoc_va_phan_giai_danh_tinh.md), [03](03_Snapshot_DataView_va_chong_ro_ri.md).

## 1. Hiện trạng đọc từ mã

dailymed.py có tìm SPL theo tên, chọn nhãn, tách section theo LOINC và find_mentions. Các điểm cần xử lý:
- search_spls chỉ lấy một trang 100 kết quả, chưa chứng minh danh sách đầy đủ.
- choose_spl dựa startswith và không có “ AND ”, không xác minh ingredient/route/formulation.
- fetch_spl_xml cache theo set_id; metadata search có thể khác version XML đã cache.
- _text làm phẳng bảng; parse_sections có thể lặp nội dung section lồng nhau.
- find_mentions bỏ qua nhóm thuốc và chỉ nhận từ dài ít nhất 4 ký tự.
- collect dừng khi rate limited nhưng các thuốc còn lại cần được ghi not_attempted; thiếu cache/XML lỗi cần trạng thái riêng.

Có test collector không đồng nghĩa nguồn phù hợp mọi thuốc trong catalog.

Đối chiếu cuối phiên: dailymed_report.json có 8 thuốc, 129 chunks; lookup đã có tích hợp đọc nguồn. Đây là coverage collector mẫu, chưa phải xác nhận chọn SPL/mapping đúng hoặc danh mục 50 thuốc đã duyệt.

## 2. Nguồn, đầu vào và artifact

Dùng catalog approved để tạo truy vấn; raw XML, response search và metadata lưu theo hash. SPL record có set_id, actual_xml_version, effective_time, published_date, title, ingredients, route, formulation, source_url. Đối chiếu version trong XML với metadata; lệch thì quarantine hoặc tải bản đúng, không gắn version mới lên nội dung cũ.

DailyMed có endpoint lịch sử và tải bản cũ theo SET ID/version. [Tài liệu chính thức](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm).
Nguồn là nhãn thuốc Hoa Kỳ; sự phù hợp với sản phẩm Việt Nam phải được xét bằng thành phần và điều kiện, không bằng tên thương mại giống nhau.

## 3. Chọn tài liệu

1. Phân trang đầy đủ có budget; nếu dừng sớm, status search_incomplete.
2. Parse ingredient/route/formulation từ tài liệu ứng viên.
3. Loại ứng viên khác thành phần; giữ mismatch reasons.
4. Xếp các ứng viên đúng phạm vi theo phiên bản và chất lượng nội dung; dược sĩ duyệt lựa chọn catalog ban đầu.
5. Có thể giữ nhiều SPL hợp lệ; nhóm near-duplicate nhưng không xóa nguồn bất đồng.
6. Trường hợp không xác định route: chọn đoạn không phụ thuộc route hoặc giữ điều kiện rõ.

Không dùng “ngày mới nhất” giữa hai set_id khác nhau để tự quyết rằng nội dung của một hãng phủ định hãng khác.

## 4. Chunking và truy vết

Lưu section code, title path, XPath/ordinal, parent_section, block type và text gốc. Section dài chia theo paragraph/list/table, mục tiêu 250–500 tokens; giới hạn 800, chỉ thêm heading/điều kiện cần thiết. Không cắt câu phủ định khỏi câu tác động.

Bảng phải giữ header + hàng + chú thích; không nối toàn bộ ô thành câu mơ hồ. Chunk ID bao gồm set_id, XML version và hash nội dung/vị trí. Section lồng nhau có ID duy nhất, dedup dựa structural path + content hash.

Văn bản được giữ nguyên tiếng Anh để đối chiếu; bản tiếng Việt là lớp diễn đạt, không thay nguồn gốc.

## 5. Retrieval theo tên và nhóm

Khớp tên chỉ tạo candidate. Cần kiểm tra câu nói về tương tác, phủ định, điều kiện và thuốc chủ thể. Nhóm “strong CYP…” cần membership evidence đã duyệt, không suy từ similarity tên hay LLM. Nếu thiếu membership, trả chưa đủ thông tin.

Kết quả không có mention không có nghĩa không tương tác: có thể nguồn dùng nhóm, chunk bị thiếu hoặc collector chưa chạy.

## 6. Thí nghiệm và tiêu chí

E05: chia đoạn cố định 400 tokens, overlap 50 so với structural chunking. Dùng cùng SPL và 20 dev queries; dược sĩ xác định đoạn đủ hỗ trợ trước. Đo evidence recall@10, mất điều kiện/phủ định, token tổng và duplicate rate.

Giữ structural mặc định; chỉ thay nếu phương án khác tăng recall mà không tăng mất điều kiện. Các bộ parser fixture phải bao gồm nested sections, bảng, references, XML namespace, version mismatch và lỗi mạng.

## 7. Checklist và cổng

- [ ] Sửa chọn SPL dựa metadata thực, bổ sung phân trang và status mỗi thuốc.
- [ ] Đóng băng raw/version, parser có fixture.
- [ ] Tạo coverage: đã thử/tải thành công/đúng mapping/có section DI/có evidence cặp.
- [ ] Dược sĩ duyệt nguồn cho mọi mục catalog công khai.
- [ ] Chạy offline tái tạo cùng chunk IDs.
- [ ] Không publish XML version sai hoặc nội dung mất bảng quan trọng.

Nguồn bị chặn: dùng cache hợp lệ và báo độ phủ thiếu; không đổi IP để né hạn chế. Ước lượng 2–4 ngày công cộng duyệt.
