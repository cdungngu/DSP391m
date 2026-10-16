# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **File này là tài liệu sống.** Dự án đang ở giai đoạn ý tưởng và phạm vi còn thay đổi. Trước khi làm việc, đọc mục **Trạng thái hiện tại** và **Nhật ký quyết định**. Sau mỗi phiên làm thay đổi phạm vi, dữ liệu, kiến trúc hoặc lệnh chạy, cập nhật file này theo **Quy tắc cập nhật** ở cuối.

## Dự án

DSP391m · Group 8 (Le Van Hung, Nguyen Vu Huy, Nguyen Chi Dung, Do Quoc An). Đề tài: dự đoán và giải thích tác dụng phụ khi dùng nhiều thuốc (polypharmacy side effects) bằng Graph RAG + LLM trên dữ liệu Decagon (BioSNAP, Stanford). Báo cáo nộp bằng tiếng Anh; ghi chú nội bộ và phân tích bằng tiếng Việt.

## Trạng thái hiện tại

_Cập nhật lần cuối: 2026-10-17_

- **Bối cảnh (chốt 2026-10-10):** đây là **dự án thật, không phải môn học**: không có cổng duyệt của giảng viên. Còn **6 tuần**; API LLM và GPU thuê ngoài khi cần; **có người bên dược** hỗ trợ (danh mục demo, duyệt mapping, gold set, chấm giải thích).
- **Hướng đã chốt (plan v2):** lõi là **A** (tra cứu bằng chứng Decagon) + **D** (cơ chế ChEMBL `action_type`, đoạn nhãn DailyMed, dược sĩ kiểm tra) + **B0** (dự đoán bằng đếm tần suất theo từng thuốc, **không huấn luyện**). **B2** (DistMult/SimplE) chỉ làm nếu qua **cổng M** cuối tuần 3 (plan mục 4.4). Không làm B1, GNN, HODDI. Chi tiết và lịch ở `plan/Ke_hoach_trien_khai.md`.
- **Giai đoạn:** GĐ1, GĐ2 xong. **B0 trên val chính thức xong** (`results/val/`). **GĐ3 đang làm:** module ChEMBL (cơ chế + bổ sung tên) và DailyMed (đoạn nhãn) đã có và tích hợp vào `lookup`; DailyMed mới chạy trên 8 thuốc mẫu, chờ danh mục demo của dược sĩ. **Tiếp theo:** hoàn tất GĐ3 theo danh mục demo, rồi GĐ4 (LLM + verifier).
- **Đang chờ dược sĩ:** danh mục demo khoảng 50 thuốc; xem khoảng 10 chất vô cơ/ion và 2 ánh xạ nghi sai trong `structure_coverage.json`.
- **Tài liệu cũ:** `docs/submission/*` vẫn mô tả thiết kế cũ. Không cần nộp lại; nếu dùng lại thì sửa theo plan mục 10.

## Nhật ký quyết định

Thêm dòng mới ở **đầu bảng**. Không xóa dòng cũ; nếu đảo ngược một quyết định thì thêm dòng mới ghi rõ "thay thế quyết định ngày …".

| Ngày | Quyết định / thay đổi | Lý do | Trạng thái |
|---|---|---|---|
| 2026-10-17 | GĐ3: `http.py` (gọi API lịch sự, dùng chung), `chembl.py` (khớp InChIKey → dạng trung hòa → connectivity; cơ chế có `action_type`; bổ sung tên), `dailymed.py` (đoạn nhãn theo LOINC, tìm tên thuốc B trong mục Drug Interactions của thuốc A); `lookup` hiển thị cơ chế ChEMBL, target ChEMBL chung có chiều, đoạn nhãn DailyMed, và gắn cờ target Decagon dạng panel rộng (>100 target) | Bù chỗ PPI không có chiều và target Decagon nhiễu; NCBI chặn PubChem nên lấy tên qua ChEMBL | Đã làm |
| 2026-10-16 | Bộ chấm điểm dùng chung `evaluate.py` + B0 (`models/b0.py`) trên val chính thức; test chỉ chạy với `--final` | Theo D3–D5; giữ test cho GĐ5 | Đã làm |
| 2026-10-10 | Hoàn thành lõi GĐ2: `names.py` (tên thuốc qua PubChem synonyms + CID liên quan, symbol gene NCBI), `lookup.py` (tra cứu theo cặp, gộp theo tác dụng phụ với cặp đóng góp và evidence ID, bối cảnh target/PPI phạt mềm theo bậc, tách 3 trường hợp thiếu dữ liệu). Xếp hạng mặc định: số cặp đóng góp, hòa thì nhãn hiếm trước; `--sort enrichment` là tùy chọn | Demo cho thấy cả hai cách xếp hạng đều có điểm yếu; nhãn Decagon lẫn chỉ định và bệnh nền (ví dụ hyperlipaemia đi cùng simvastatin) | Đã làm |
| 2026-10-10 | Sửa GĐ1b theo review: prediction view bỏ metadata tính trên toàn snapshot (`effects.n_rows` → `n_rows_train`, `drugs.in_combo` → `in_train`); `splits.run` không ghi đè split đã có (cùng tham số thì chỉ xác minh, khác thì `SplitExistsError`); mọi nơi đọc split qua `load_verified_split` (checksum file và snapshot, nếu sai thì `SplitIntegrityError`); khóa cache gồm `split_hash`; 6 test hồi quy | Review phát hiện metadata val/test lọt vào prediction view, split "đóng băng" vẫn ghi đè được, và loader không xác minh file | Đã làm |
| 2026-10-10 | Hoàn thành GĐ1b: `splits.py` (vocab 963, split 70/10/20 seed 391, commit file split), `dataview.py` (evidence/prediction view, `load_eval_targets`, `Cache` khóa theo chế độ), `tests/test_leakage.py` | Đóng băng split để B0 được chấm trung thực và B2 có thể làm ngay nếu qua cổng M | Đã làm |
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
- `data/processed/decagon_v1/splits/pair_70-10-20_s391/`: split **đã đóng băng** (vocab, phân chia cặp, manifest có hash), được commit. Muốn đổi thì tạo `split_id` mới, không ghi đè.
- `data/cache/`: cache theo chế độ (gitignore).
- `data/processed/decagon_v1/drug_names.parquet`, `gene_names.parquet`: bảng tên lấy từ API ngoài, được commit.
- `data/external/ncbi/`: cache symbol gene (đã cắt gọn), được commit.
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
# Tên thuốc và gene (gọi PubChem/NCBI, có cache; --offline chỉ dùng cache). Nếu báo CHƯA XONG thì chạy lại sau
.venv/bin/python -m dsp391m.names
# GĐ2: tra cứu bằng chứng cho đơn thuốc (tên, STITCH ID hoặc PubChem CID; --json để xuất JSON)
.venv/bin/python -m dsp391m.lookup aspirin simvastatin omeprazole fluoxetine --top 10
# GĐ3: ChEMBL (cơ chế + tên; chậm, khoảng 10 giây mỗi request, có cache) và DailyMed (chỉ theo danh mục nhỏ)
.venv/bin/python -m dsp391m.chembl
.venv/bin/python -m dsp391m.dailymed --file demo_drugs.txt
# Chấm điểm trên val (test chỉ khi đã khóa cấu hình: --split test --final)
.venv/bin/python -m dsp391m.evaluate --model b0_per_drug
# GĐ1b: vocabulary + split (đã đóng băng và commit; chạy lại chỉ để kiểm tra hash, không ghi đè bằng tham số khác)
.venv/bin/python -m dsp391m.splits

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
- **Split chính thức `pair_70-10-20_s391`:** 63.472 cặp có nhãn trong vocab, chia 44.430 / 6.347 / 12.695 (1 cặp chỉ có nhãn ngoài vocab bị loại). Prediction view còn 3.198.361 dòng nhãn train. Nếu chỉ tính ngưỡng ≥500 dòng trên train (ngưỡng nhân 0,7) thì vocab còn 959 nhãn: chênh 4 nhãn, **chưa đánh giá ảnh hưởng đến metric** (muốn kết luận thì so sánh hai vocab trên cùng val). Tỷ lệ dương của val: 7,49%.
- **Tên thuốc** (`names_report.json`): 374/645 thuốc có tên ngay từ CID gốc. CID gốc của Decagon thường là dạng flat hoặc ion (ví dụ CID 2173 là anion của ampicillin) nên không có tên; khi đó lấy tên từ CID cha hoặc CID cùng connectivity có nhiều synonym nhất (ampicillin → CID 6249). Mọi tên lấy theo cách này có `needs_review` (có thể nhầm đồng phân lập thể). PubChem chặn IP (HTTP 429) sau khoảng 1.000 request liên tiếp; đến 2026-10-12 NCBI chuyển hướng mọi request từ IP này tới trang **abuse** (`misuse.ncbi.nlm.nih.gov`). **Không gọi PubChem/NCBI theo lô lớn nữa**; dùng `--offline`. Phần tên còn thiếu dự kiến lấy từ ChEMBL (tra theo InChIKey) ở GĐ3. 3.648/3.648 gene target có symbol NCBI.
- **Hạn chế của nhãn Decagon thấy qua demo:** nhãn lẫn chỉ định và bệnh nền của nhóm bệnh nhân (hyperlipaemia xuất hiện ở mọi cặp có simvastatin), tên nhãn đôi khi lạ (C0011860 có tên "Mod"). Xếp theo số cặp đẩy nhãn chung chung lên đầu; xếp theo mức trội đẩy nhãn hiếm, có thể là nhiễu. Chưa có cách xếp hạng đã kiểm chứng; cần dược sĩ và nguồn GĐ3.
- **B0 trên val chính thức** (`results/val/`, 6.347 cặp × 963 nhãn, tỷ lệ dương 7,49%): popularity macro AP 0,0749; **per-drug macro AP 0,2714** (CI bootstrap percentile [0,2703; 0,2797], lệch lên do cặp lặp khi lấy mẫu), micro AP 0,3508, macro AUROC 0,8360. Theo nhóm: nhãn hiếm/trung bình/phổ biến 0,178/0,246/0,391; cặp có 0/1/2 thuốc có target 0,266/0,274/0,305.
- **Target Decagon dạng panel rộng:** 83/284 thuốc có target có hơn 100 target và gần như dùng chung một panel khoảng 158 gene GPCR (Jaccard trung vị 0,88; 20 thuốc có bộ target giống hệt nhau; gồm cả atenolol, amitriptyline, salbutamol, calcium ion). Target của các thuốc này không đặc hiệu: `lookup` gắn `low_specificity` và không diễn giải "target chung".
- **DailyMed** (8 thuốc mẫu, 129 đoạn): tìm được tương tác thật mà nhãn Decagon không nói được (nhãn fluoxetine: kéo dài thời gian bán thải của diazepam; nhãn omeprazole: diazepam là cơ chất CYP2C19). Nhãn chọn tự động có thể là nhãn OTC không có mục Drug Interactions (aspirin). Chỉ khớp tên thuốc nguyên từ, chưa bắt được cách nhắc theo nhóm ("strong CYP3A4 inhibitors").
- **Độ trễ GĐ2** (300 đơn ngẫu nhiên, k = 3/5/10): tải chỉ mục 0,7 giây; truy vấn p50 15 ms, p95 228 ms, tối đa 687 ms. Đạt mục tiêu p95 tra cứu dưới 1 giây.
- **Cấu trúc phân tử** (PubChem, 2026-10-10): 645/645 thuốc combo có SMILES và RDKit tạo được Morgan fingerprint. 58 thuốc bị gắn cờ (`charged`, `multi_component`, `tiny`): phần lớn là dạng ion hóa hợp lệ của thuốc (penicillin dạng carboxylate, amoni bậc 4), nhưng có nhóm cần xem tay vì không phải hoạt chất đặc hiệu (calcium cation, NaCl, KCl, sulfate ion, nitric oxide, lithium aluminum hydride, CID 6398525). Không có InChIKey trùng. Danh sách đầy đủ trong `data/processed/decagon_v1/structure_coverage.json`.
- Tên tác dụng phụ có lỗi chính tả (ví dụ "neumonia"). Dùng CUI làm khóa và giữ tên gốc để truy vết.
- Nạp combo bằng `dtype='category'` để tiết kiệm RAM. Không dựng toàn bộ 4,6 triệu cạnh thành object NetworkX; dùng bảng tra cứu hoặc ma trận thưa.

## Nguyên tắc thiết kế đã thống nhất trong phân tích

Các nguyên tắc này dễ bị vi phạm khi viết code mới:

- **Tách hai chế độ chạy.** *Evidence mode* được dùng cạnh đã biết của chính cặp đang hỏi. *Prediction evaluation mode* phải loại mọi bằng chứng làm lộ nhãn test (cạnh đồ thị, corpus, ví dụ few-shot, cache). Trong code: chỉ đọc nhãn qua `dsp391m.dataview` (`prediction_view` cho benchmark); chỉ bộ chấm điểm gọi `load_eval_targets`; cache qua `dataview.Cache`. Split chỉ được đọc qua `splits.load_verified_split`. Trong prediction view, **mọi metadata suy ra từ nhãn phải tính lại trên train**; khi thêm cột hoặc bảng mới, thêm test vào `tests/test_split_integrity.py`. Nguồn ngoài (DailyMed, ChEMBL) nói trực tiếp về cặp val/test cũng phải bị che trong prediction mode.
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
