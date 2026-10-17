> **HẾT HIỆU LỰC HƯỚNG DẪN (v2.1).** Giữ để truy vết lịch sử. Dùng [bộ dự đoán cặp v3](../du_doan_cap/00_Dieu_phoi_va_ra_soat.md) và [kế hoạch tổng](../Ke_hoach_trien_khai.md). Các cổng duyệt và thứ tự bên dưới không áp dụng cho lõi v3.

# 07 — Truy xuất đồ thị và văn bản

Ngày: 2026-10-17 · Chủ trì: retrieval · Phụ thuộc [03](03_Snapshot_DataView_va_chong_ro_ri.md)–[06](06_Chuan_hoa_nhan_va_xep_hang_ket_qua.md).

## 1. Hiện trạng

EvidenceIndex chỉ dùng evidence_view, trả nhãn theo cặp, target chung và một cạnh PPI giữa target hai thuốc. Đây chưa phải truy xuất đường dài tùy ý. Giữ baseline này; không tự tăng hop khi chưa đo chất lượng.

Kho văn bản mới cần lọc danh tính và applicability trước tìm kiếm. Một câu có tên cả hai thuốc chưa chắc hỗ trợ tương tác.

## 2. Interface và dữ liệu

retrieve(query, RunContext, RetrievalConfig) → EvidenceBundle theo file 01.
Query gồm canonical ingredients, pairs và câu hỏi cố định “bằng chứng tương tác theo cặp”; không chứa outcome thật bị giữ lại trong prediction evaluation.
Mọi candidate lưu source, matched entities, relation, lexical score, applicability, selected_reason hoặc dropped_reason.

Chỉ mục văn bản BM25 tạo từ heading + body; tìm bằng tên tiếng Anh/synonyms approved. Nhập tiếng Việt được map về ID trước, không dịch tự do query y khoa.

## 3. Pipeline và ngân sách mặc định

1. Lấy statements trực tiếp về cặp hoặc class-membership đã duyệt.
2. Tìm BM25 tối đa 20 candidate/cặp trong nguồn phù hợp.
3. Lấy cơ chế đơn thuốc có provenance để bổ sung; graph context tối đa 5 path/cặp từ baseline.
4. Dedup bằng content hash, giữ provenance list.
5. Chọn round-robin theo cặp có bằng chứng để tránh một cặp chiếm hết; tối đa 10 đoạn văn + 10 facts/path cho toàn đơn.
6. Đóng gói tối đa 6.000 input tokens cho evidence, cộng overhead prompt theo đo tokenizer; bỏ context yếu trước, không cắt giữa điều kiện.
7. Trả missing_data cho từng cặp không có bằng chứng phù hợp.

Đơn 5 thuốc có 10 cặp: budget không bảo đảm một đoạn cho mọi cặp. Báo cặp bị bỏ do budget khác cặp không có evidence. Không chọn bằng outcome thật trong benchmark.

## 4. Các cải tiến có điều kiện

E07a: baseline BM25 so với MMR trên candidates. MMR dùng cosine TF-IDF để phạt đoạn lặp, lambda thử {0,5; 0,7}; không cần embedding API ban đầu.
E07b: hybrid lexical+dense chỉ nếu error analysis cho thấy thiếu recall do cách diễn đạt; chọn một encoder qua pilot và khóa model/version, dùng reciprocal rank fusion, không cộng raw scores khác thang.

Mỗi thí nghiệm dùng cùng source snapshot, queries và token budget. Đo evidence recall@10, đủ điều kiện của nguồn, redundancy, p95, tokens. Giữ nếu recall tăng ít nhất 5 điểm phần trăm và p95 retrieval không quá 1 giây trên máy được ghi; nếu không đạt, giữ baseline. Đây là mục tiêu thử nghiệm.

## 5. Đồ thị và hiệu năng

Dùng lookup/sparse adjacency hiện có; chưa cần Neo4j. PPI degree penalty là heuristic, không là độ tin cậy y khoa. Chỉ mở rộng hai PPI hops ở thí nghiệm riêng khi gold có câu hỏi cần bối cảnh đó. Đường tìm được không tạo claim outcome nếu không có nguồn hỗ trợ.

## 6. Checklist và kiểm thử

- [ ] Fixture có negation, class mention, sai route, duplicate và nguồn bất đồng.
- [ ] Query không dùng hidden labels hoặc metadata từ test.
- [ ] Bundle chỉ chứa record có source version/hash.
- [ ] Cặp thiếu bằng chứng và cặp bị budget loại có reason khác nhau.
- [ ] Giữ heading/table footnote trong đoạn được chọn.
- [ ] Benchmark warm/cold index riêng, không dùng cache LLM để đo retrieval.

Cổng: trace giải thích được mọi lựa chọn; baseline tái lập offline; không source sai danh tính. Ước lượng 2–3 ngày công.
