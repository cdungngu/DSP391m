# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **File này là tài liệu sống.** Dự án đang ở giai đoạn ý tưởng và phạm vi còn thay đổi. Trước khi làm việc, đọc mục **Trạng thái hiện tại** và **Nhật ký quyết định**. Sau mỗi phiên làm thay đổi phạm vi, dữ liệu, kiến trúc hoặc lệnh chạy, cập nhật file này theo **Quy tắc cập nhật** ở cuối.

## Dự án

DSP391m · Group 8 (Le Van Hung, Nguyen Vu Huy, Nguyen Chi Dung, Do Quoc An). Đề tài: dự đoán và giải thích tác dụng phụ khi dùng nhiều thuốc (polypharmacy side effects) bằng Graph RAG + LLM trên dữ liệu Decagon (BioSNAP, Stanford). Báo cáo nộp bằng tiếng Anh; ghi chú nội bộ và phân tích bằng tiếng Việt.

## Trạng thái hiện tại

_Cập nhật lần cuối: 2026-10-10_

- **Bối cảnh (chốt 2026-10-10):** đây là **dự án thật, không phải môn học**: không có cổng duyệt của giảng viên. Còn **6 tuần**; API LLM và GPU thuê ngoài khi cần; **có người bên dược** hỗ trợ (danh mục demo, duyệt mapping, gold set, chấm giải thích).
- **Hướng đã chốt (plan v2):** lõi là **A** (tra cứu bằng chứng Decagon) + **D** (cơ chế ChEMBL `action_type`, đoạn nhãn DailyMed, dược sĩ kiểm tra) + **B0** (dự đoán bằng đếm tần suất theo từng thuốc, **không huấn luyện**). **B2** (DistMult/SimplE) chỉ làm nếu qua **cổng M** cuối tuần 3 (plan mục 4.4). Không làm B1, GNN, HODDI. Chi tiết và lịch ở `plan/Ke_hoach_trien_khai.md`.
- **Giai đoạn:** GĐ1a xong (ETL, QA 32/32, cấu trúc 645/645). **Tiếp theo: GĐ1b** (vocabulary 963 nhãn, split theo cặp 70/10/20 seed 391, data view theo chế độ, 4 test rò rỉ). Giao thức đánh giá D1–D7 đã chốt ở plan mục 6.1.
- **Đang chờ dược sĩ:** danh mục demo khoảng 50 thuốc; xem khoảng 10 chất vô cơ/ion và 2 ánh xạ nghi sai trong `structure_coverage.json`.
- **Tài liệu cũ:** `docs/submission/*` vẫn mô tả thiết kế cũ. Không cần nộp lại; nếu dùng lại thì sửa theo plan mục 10.

## Nhật ký quyết định

Thêm dòng mới ở **đầu bảng**. Không xóa dòng cũ; nếu đảo ngược một quyết định thì thêm dòng mới ghi rõ "thay thế quyết định ngày …".

| Ngày | Quyết định / thay đổi | Lý do | Trạng thái |
|---|---|---|---|
| 2026-10-10 | **Chốt plan v2:** dự án thật (không cổng giảng viên), 6 tuần, có dược sĩ; lõi A + D + B0 không huấn luyện; B2 qua cổng M cuối tuần 3; bỏ B1/GNN/HODDI; chốt giao thức D1–D7; giữ mọi thuốc bị gắn cờ, dược sĩ xem lại | Thử nghiệm B0 (`analysis/2026-10-10/b0_pilot.json`): macro AP 0,270, AUROC 0,837 mà không cần huấn luyện; giá trị sản phẩm nằm ở bằng chứng có nguồn | Đã chốt (thay thế các dòng "Đề xuất" ngày 08/10 và 10/10 về B) |
| 2026-10-10 | Hoàn thành GĐ1a: package `dsp391m` (etl, quality, structures), `.venv` + `requirements.txt`, test pytest; Parquet không commit, manifest/QA/cache PubChem được commit | Bắt đầu nền dữ liệu song song GĐ0 như kế hoạch cho phép | Đã làm |
| 2026-10-10 | Sửa kế hoạch theo review: thêm giao thức đánh giá chung (mục 5.1), cách ly hai chế độ ở tầng dữ liệu, mapping cấu trúc cho B1, mốc bắt buộc B0 + một trong B1/B2; GĐ1a (ETL, manifest, QA) được chạy song song GĐ0 | Tránh bảng metric không so sánh được và rò rỉ nhãn qua lookup/cache | Đề xuất, chưa chốt |
| 2026-10-10 | Tạo `plan/Ke_hoach_trien_khai.md`: lộ trình A → B theo giai đoạn GĐ0–GĐ6, một nhánh mở rộng tùy chọn | Gom ý tưởng ban đầu và phân tích thành lộ trình có thứ tự và lý do | Đề xuất, chưa chốt |
| 2026-10-10 | Sắp xếp lại repo thành `data/`, `docs/`, `analysis/` và `src/`; thêm `README.md` hướng dẫn nhanh | Tách dữ liệu gốc, tài liệu nộp và hồ sơ phân tích để dễ tìm; cập nhật script và lệnh theo đường dẫn mới | Đã làm |
| 2026-10-10 | Tạo CLAUDE.md dạng tài liệu sống | Phạm vi còn thay đổi nhiều | Đã làm |
| 2026-10-08 | Đề xuất chuyển từ "RAG thuần cho k ≥ 3 thuốc" sang B (dự đoán theo cặp + giải thích), A làm mốc đầu | Chỉ 284/645 thuốc có target; Decagon chỉ có nhãn theo cặp; HODDI có shortcut ở mẫu âm | Đề xuất, chưa chốt |
| 2026-10-08 | Không lấy DDI-GPT làm baseline bắt buộc | DDI-GPT làm phân loại nhị phân cặp, khác bài toán 963 nhãn; thiếu code tái lập | Đề xuất |
| 2026-10-08 | Thay ba Tier bằng hai trường độc lập: `status` (quan sát / dự đoán / thiếu dữ liệu) và loại bằng chứng | "Amplified" và "newly emergent" không chứng minh được bằng dữ liệu hiện có | Đề xuất |

## Bố cục repo

- `data/decagon/`: ba CSV Decagon gốc (combo, targets, ppi). **Chỉ đọc, không sửa.**
- `docs/submission/`: tài liệu nộp (`.docx`, `.pdf`); chúng vẫn phản ánh thiết kế cũ như mô tả ở trên.
- `docs/literature/literature-review.xlsx`: bảng tổng quan tài liệu (sheet `LR`, `Note`). Có nhiều link sai đã được liệt kê ở mục 14 của báo cáo đánh giá; chưa sửa workbook.
- `analysis/2026-10-10/`: thử nghiệm B0 (`b0_pilot.py`, `b0_pilot.json`), dùng để quyết định chưa huấn luyện mô hình. Split 80/20 ở đây là tạm thời, **không** phải split chính thức.
- `analysis/2026-10-08/`: đợt kiểm toán dữ liệu và đánh giá hướng đi:
  - `Bao_cao_danh_gia_huong_trien_khai.md`: **bản gốc** của báo cáo đánh giá. File `.docx` được sinh từ file này bằng `build_report.py`; sửa `.md` rồi build lại, không sửa `.docx` bằng tay.
  - `audit_data.py`, `audit_external.py`, `probe_hoddi_shortcut.py`: các script kiểm toán chỉ đọc. Kết quả nằm trong `*.json` và `*.csv` cùng thư mục.
  - `sources/`: nguồn tải thêm (Decagon mono, targets-all, HODDI v1 tại commit `700d0da…`) và bản text của các báo cáo/literature review để đọc nhanh.
  - `qa/`: bản PDF và ảnh trang được render để kiểm tra bố cục tài liệu.
- `plan/Ke_hoach_trien_khai.md`: kế hoạch triển khai sống (lộ trình, giai đoạn, cổng, lịch, các chỗ cần sửa trong báo cáo nộp).
- `src/dsp391m/`: package triển khai (xem `src/README.md`). `paths.py` giữ mọi đường dẫn chuẩn và tên snapshot (`decagon_v1`).
- `data/processed/decagon_v1/`: đầu ra ETL. File `*.parquet` bị gitignore (sinh lại được); `manifest.json`, `qa_report.json`, `structure_coverage.json` được commit.
- `data/external/pubchem/`: cache nguyên văn phản hồi PubChem, được commit để chạy lại ở chế độ `--offline`.
- `tests/`: pytest; test đánh dấu `slow` chạy trên dữ liệu thật.

## Lệnh

Môi trường: Python 3.12 trong `.venv` của dự án, phiên bản khóa trong `requirements.txt` (có RDKit). `build_report.py` cần thêm `python-docx`.

```bash
# Cài đặt lần đầu
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -e .

# GĐ1a: ETL -> QA -> mapping cấu trúc (chạy theo thứ tự; QA thoát mã 1 nếu có kiểm tra thất bại)
.venv/bin/python -m dsp391m.etl
.venv/bin/python -m dsp391m.quality
.venv/bin/python -m dsp391m.structures --offline   # bỏ --offline để gọi PubChem khi thiếu cache

# Test: nhanh (mặc định), trên dữ liệu thật, hoặc một test
.venv/bin/pytest
.venv/bin/pytest -m slow
.venv/bin/pytest tests/test_etl.py::test_tables_are_canonical

# Kiểm toán lại dữ liệu Decagon gốc (quét toàn bộ combo ~233 MB, mất vài chục giây)
python3 analysis/2026-10-08/audit_data.py
# Kiểm toán nguồn bổ sung (cần drug_target_coverage.csv do audit_data.py sinh ra)
python3 analysis/2026-10-08/audit_external.py
# Phép thử shortcut của HODDI
python3 analysis/2026-10-08/probe_hoddi_shortcut.py
# Build lại .docx của báo cáo đánh giá từ bản .md
python3 analysis/2026-10-08/build_report.py
```

Các script trong `analysis/` dùng `Path(__file__)` nên chạy được từ bất kỳ thư mục nào. Chưa có linter. Khi logic ETL thay đổi kết quả, đổi `SNAPSHOT` trong `paths.py` thay vì ghi đè snapshot cũ; nếu đổi số đếm kỳ vọng, sửa `EXPECTED` trong `quality.py` cùng mục *Sự thật về dữ liệu* bên dưới.

## Sự thật về dữ liệu (đã kiểm chứng trên snapshot trong `data/decagon/`)

Khi viết báo cáo, phân biệt **"thống kê bài gốc Decagon"** (645 thuốc, 19.085 protein, 964 nhãn, 4.651.131 cạnh) với **"thống kê snapshot sử dụng"** dưới đây. Không chỉnh dữ liệu cho khớp con số của bài gốc.

- **combo:** 4.649.441 dòng; 645 thuốc; 63.473 cặp không thứ tự (30,6% trên 207.690 cặp có thể có); 1.317 nhãn CUI. Lọc nhãn có ≥500 dòng còn 963 nhãn (cùng quy ước với bài tensor factorization). Không có cạnh trùng, cạnh đảo chiều hay cạnh tự nối. Không có nhãn âm, liều, mức độ nặng hay xác suất: cặp vắng mặt nghĩa là **chưa quan sát**, không phải an toàn.
- **targets:** chỉ **284/645** thuốc của combo có target. Trung vị 11 target mỗi thuốc, nhưng `CID000000271` (calcium cation) có 2.840 target. File `targets-all` chính thức cũng không tăng độ phủ này.
- **ppi:** 715.612 cạnh không hướng, 19.081 gene; bậc trung vị 33, lớn nhất 2.519. Cạnh không có dấu (kích hoạt/ức chế) và gồm cả liên hệ chức năng, nên không gọi chung là "tương tác vật lý trực tiếp".
- Bộ 3 thuốc ngẫu nhiên: khoảng 8,6% có đủ target cho cả 3 thuốc. Về nhãn theo cặp: 57% có ít nhất một cặp có nhãn, 43% không cặp nào có nhãn, khoảng 10% có nhãn cho cả 3 cặp. Với đơn 5 thuốc: 86% có ít nhất một cặp có nhãn. (Đo ngày 2026-10-10, 5.000 mẫu, seed 391.) Tra cứu theo cặp chỉ phủ một phần; nhánh cơ chế thiếu dữ liệu ở đa số truy vấn.
- **B0 (thử nghiệm, split tạm 80/20 seed 0):** chấm toàn ma trận 12.694 cặp × 963 nhãn (tỷ lệ dương 7,45%): độ phổ biến của nhãn đạt macro AP 0,074; B0 `f(A,e)+f(B,e)` đạt macro AP 0,270, macro AUROC 0,837, micro AP 0,351.
- **Cấu trúc phân tử** (PubChem, 2026-10-10): 645/645 thuốc combo có SMILES và RDKit tạo được Morgan fingerprint. 58 thuốc bị gắn cờ (`charged`, `multi_component`, `tiny`): phần lớn là dạng ion hóa hợp lệ của thuốc (penicillin dạng carboxylate, amoni bậc 4), nhưng có nhóm cần xem tay vì không phải hoạt chất đặc hiệu (calcium cation, NaCl, KCl, sulfate ion, nitric oxide, lithium aluminum hydride, CID 6398525). Không có InChIKey trùng. Danh sách đầy đủ trong `data/processed/decagon_v1/structure_coverage.json`.
- Tên tác dụng phụ có lỗi chính tả (ví dụ "neumonia"). Dùng CUI làm khóa và giữ tên gốc để truy vết.
- Nạp combo bằng `dtype='category'` để tiết kiệm RAM. Không dựng toàn bộ 4,6 triệu cạnh thành object NetworkX; dùng bảng tra cứu hoặc ma trận thưa.

## Nguyên tắc thiết kế đã thống nhất trong phân tích

Các nguyên tắc này dễ bị vi phạm khi viết code mới:

- **Tách hai chế độ chạy.** *Evidence mode* được dùng cạnh đã biết của chính cặp đang hỏi. *Prediction evaluation mode* phải loại mọi bằng chứng làm lộ nhãn test (cạnh đồ thị, corpus, ví dụ few-shot, cache). Cache phải ghi kèm mode và split ID.
- **Chia tập trước, rồi mới dựng đồ thị huấn luyện, feature hay embedding.** Thiết lập chính là chia theo cặp đã chuẩn hóa: mọi nhãn của một cặp nằm cùng một split.
- **Không huấn luyện trước cổng M.** B0 (đếm) là phần dự đoán mặc định. Chỉ thêm B2 khi qua cổng M (plan mục 4.4), và chỉ giữ B2 khi vượt B0 ít nhất +0,02 macro AP trên val, qua 3 seed.
- **Thứ tự độ mạnh của bằng chứng:** đoạn nhãn DailyMed > cơ chế ChEMBL có chiều > nhãn Decagon đã quan sát > bằng chứng mức thuốc của B0 > bối cảnh target/PPI. Phần cơ chế mặc định là "chưa đủ bằng chứng", trừ khi có một trong hai loại nguồn đầu.
- LLM đóng vai trò **giải thích hoặc tổng hợp**, không phải bộ dự đoán được chấm điểm. Mỗi phát biểu phải trích ID bằng chứng, và được phép trả "insufficient evidence".
- Điểm tổng hợp cho đơn nhiều thuốc phải ghi là "điểm tổng hợp theo cặp", không phải xác suất lâm sàng. Không dùng noisy-OR như xác suất thật.
- Không tự dựng target hay cơ chế từ trí nhớ của LLM để lấp chỗ dữ liệu thiếu.

## Quy tắc cập nhật file này

Cập nhật **trong cùng phiên** với thay đổi, không để dồn:

| Khi nào | Sửa mục nào |
|---|---|
| Nhóm chốt hoặc đổi phạm vi, phương án, baseline | Thêm dòng vào *Nhật ký quyết định*; sửa *Trạng thái hiện tại* |
| Đổi lộ trình, xong một giai đoạn hoặc đổi lịch | Sửa `plan/Ke_hoach_trien_khai.md` (kể cả nhật ký ở cuối file) và giai đoạn hiện tại trong *Trạng thái hiện tại* |
| Trả lời được một câu hỏi mở | Xóa khỏi *Câu hỏi mở* và ghi kết quả vào *Nhật ký quyết định* |
| Thêm code, môi trường, test hoặc script mới vào `src/` | Cập nhật *Lệnh* (cài đặt, chạy, test một case) và *Bố cục repo* nếu cấu trúc thay đổi |
| Phát hiện mới về dữ liệu, hoặc số liệu cũ sai | Sửa *Sự thật về dữ liệu*, ghi rõ nguồn hoặc script đã kiểm chứng |
| Báo cáo nộp được sửa cho khớp hướng mới | Gỡ ghi chú "Lệch giữa tài liệu" tương ứng |

Luôn đổi ngày ở dòng "Cập nhật lần cuối". Giữ file ngắn gọn: chi tiết dài đặt trong `analysis/`, ở đây chỉ dẫn đường dẫn. Thông tin nào đã lỗi thời thì xóa hoặc đánh dấu "thay thế", không để mâu thuẫn tồn tại.
