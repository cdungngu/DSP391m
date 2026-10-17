# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **File này là tài liệu sống.** Dự án đang ở giai đoạn ý tưởng và phạm vi còn thay đổi. Trước khi làm việc, đọc mục **Trạng thái hiện tại** và **Nhật ký quyết định**. Sau mỗi phiên làm thay đổi phạm vi, dữ liệu, kiến trúc hoặc lệnh chạy, cập nhật file này theo **Quy tắc cập nhật** ở cuối.

## Dự án

DSP391m · Group 8 (Le Van Hung, Nguyen Vu Huy, Nguyen Chi Dung, Do Quoc An). Đề tài hiện hành: dự đoán đa nhãn tác dụng phụ theo cặp thuốc trên dữ liệu Decagon (BioSNAP, Stanford). Lõi v3 là baseline + DistMult + đánh giá và demo nghiên cứu; Graph RAG/LLM là mở rộng. Báo cáo nộp bằng tiếng Anh; ghi chú nội bộ và phân tích bằng tiếng Việt.

## Trạng thái hiện tại

_Cập nhật lần cuối: 2026-10-17 (chuyển sang PC)_

> **Đang chuyển máy:** trên máy mới, đọc [plan/Huong_dan_tiep_tuc_tren_PC.md](plan/Huong_dan_tiep_tuc_tren_PC.md) trước tiên (cài đặt, xác minh, rồi phần 2: E1 residual).

- **Phạm vi hiện hành v3:** người dùng xác nhận mục tiêu dự đoán cặp và ít thời gian/nhân lực duyệt. [Kế hoạch tổng](plan/Ke_hoach_trien_khai.md) và [10 plan dự đoán cặp](plan/du_doan_cap/00_Dieu_phoi_va_ra_soat.md) thay hướng consumer A+D+B0/cổng M. Hai ID → xếp hạng 963 nhãn, không chuyển thành nhị phân có/không tương tác.
- **Đã có:** ETL, split/DataView, B0, smoothing alpha100, ChEMBL/DailyMed collectors và foundation contracts/releases/catalog/review/workbench. Kết quả trước phiên thiết kế: 61 test nhanh + 2 test thật đạt; xem [báo cáo thực thi](plan/Bao_cao_trien_khai_2026_10_17.md).
- **Đã triển khai v3 bước 1–5 (2026-10-17):** predictor contract, readiness, evaluator top-k/NDCG + paired bootstrap song song + final lock, baseline qua cùng giao thức, DistMult trainer có resume. 88 test nhanh đạt. Chưa chạy search plan 06, chưa lock/test, chưa demo.
- **Protocol DistMult đã sửa và đăng ký (2026-10-17):** wd 0 (wd 1e-5 của Adam làm embedding sụp về 0), sampler trộn 5 âm thay nhãn + 5 âm thay cặp train cân 0,5/0,5, lr {0,01; 0,03} × dim {64,128}. Mốc macro AP là B0 alpha100, mốc NDCG@10 là B0 alpha0; demo tạm dùng alpha0. Thăm dò trước đã nhìn val, phải công bố. Đăng ký: `results/experiments/2026-10-17_distmult_search_v1_registration.json`; chẩn đoán: [distmult_diagnostics.md](analysis/2026-10-17/distmult_diagnostics.md).
- **Search v1 xong (2026-10-17):** chọn d128 lr 0,01; ba seed macro AP 0,2852–0,2880, dưới alpha100 0,2890 (CI seed391 [−0,0074; +0,0013]); NDCG@10 0,412 so 0,526 của alpha0; micro AP 0,376 cao hơn mọi B0. **Không promote**; demo giữ B0 alpha0. Kết quả: `results/experiments/2026-10-17_search_v1_model_selection.json`.
- **Lô 20 ca val xong (2026-10-17):** B0 alpha0 vs DistMult; [tóm tắt](analysis/2026-10-17/cases20_review_notes.md), bảng từng ca `analysis/2026-10-17/cases20_v1.md`. Chờ người xem đợt 1.
- **Tiếp theo (người dùng chọn):** phần 2 = E1 residual DistMult trên B0 (plan 08, đăng ký trước, chạy trên PC) → lock/final → demo CLI. Chi tiết: [hướng dẫn chuyển máy](plan/Huong_dan_tiep_tuc_tren_PC.md).
- **Duyệt theo đợt:** một gói baseline/pilot và một gói bàn giao. Không chờ catalog 50 thuốc hoặc gold dược sĩ để huấn luyện bằng ID. Consumer safeguards giữ nguyên; không tự đổi pending thành approved.
- **Mở rộng:** ChEMBL features/residual chỉ có đối chứng sau lõi; DailyMed/RAG/LLM, đơn nhiều thuốc và consumer hoãn. Không tự khởi động lại khung sáu tuần trước; plan mới ước lượng 8–14 ngày công, cần đo runtime.
- **Tài liệu cũ:** plan/chi_tiet và bản tổng v2.1 lưu trữ hết hiệu lực hướng dẫn; docs/submission vẫn phản ánh thiết kế cũ, chỉ sửa khi tái sử dụng.

- **ChEMBL đã chạy xong (2026-10-17):** khớp 599/645 thuốc (470 chính xác, 20 dạng trung hòa, 109 theo connectivity cần duyệt, 46 không khớp); 271 thuốc có cơ chế, 218 có cơ chế trên người (212 có accession), 0 mapping đã duyệt. Tên thuốc: 374 từ CID gốc + 129 từ ChEMBL, còn 129 pending và 13 không có. Gói duyệt `data/review/2026-10-17_foundation_v2` (645 ứng viên catalog, 129 đoạn, 0 approved). `http.request` thử lại 5xx; ChEMBL `BATCH=20`.

## Nhật ký quyết định

Thêm dòng mới ở **đầu bảng**. Không xóa dòng cũ; nếu đảo ngược một quyết định thì thêm dòng mới ghi rõ "thay thế quyết định ngày …".

| Ngày | Quyết định / thay đổi | Lý do | Trạng thái |
|---|---|---|---|
| 2026-10-17 | Chuyển sang PC: commit bảng ETL `decagon_v1/*.parquet` và `results/models/`; `.gitattributes` `* -text`; `evaluate --rescore` dựng lại score cache; trainer chạy được trên Windows; phần 2 là E1 residual | Train lại hoặc ETL trên nền tảng khác có thể lệch byte/hash và đổi model_release_id; CRLF làm lệch hash | Đã commit; E1 chưa đăng ký |
| 2026-10-17 | Thêm `dsp391m.cases` và xuất lô 20 ca val theo quy tắc plan 06 (B0 alpha0 vs DistMult seed391) | Gói duyệt đợt 1 | Đã xuất; chưa có ghi chú người xem |
| 2026-10-17 | Search DistMult v1 theo đăng ký: chọn d128 lr 0,01; không đạt promotion (0/4 điều kiện metric); backend demo B0 alpha0 | Quy tắc plan 06 đã khóa trước khi chạy | Đã chạy; chưa chấm test |
| 2026-10-17 | Sửa protocol DistMult trước search (thay dòng "Chờ quyết" cùng ngày): wd 0, sampler trộn cân loss, lr {0,01; 0,03}; guardrail NDCG so alpha0 (≥ 0,5208), macro AP so alpha100; demo tạm alpha0; numpy 2.5.3 được pin sau khi venv sạch tái lập giống hệt | Chẩn đoán wd (norm embedding → 0), đối chứng sampler cân loss (+0,054 macro AP, −0,074 NDCG); review người dùng | Đã đăng ký và chạy |
| 2026-10-17 | Triển khai v3 bước 1–5; review thêm: compare chỉ val, tách config_id/model_release_id, lock cần worktree sạch, last/best checkpoint, bootstrap song song (kết quả không phụ thuộc số worker) | Theo plan đã duyệt và review 5 điểm | Đã làm; 88 test |
| 2026-10-17 | Phát hiện: alpha100 thắng macro AP (+0,0175) nhưng thua NDCG@10 (−0,039) và mọi metric theo cặp; DistMult theo plan 05 kẹt ở saddle; âm chỉ thay nhãn không dạy macro AP | Paired bootstrap 1.000 resample; thăm dò val | Chờ quyết: baseline tham chiếu cho guardrail NDCG, lưới lr, sampler |
| 2026-10-17 | Đồng bộ README, src/README và báo cáo thực thi 17/10 với v3 (báo cáo thành lịch sử); đo train support cho plan 02 | Các file này còn mô tả Graph RAG/consumer là hướng chính | Đã làm; chưa có data_readiness.json chính thức |
| 2026-10-17 | **v3 thay thế phạm vi A+D+B0/cổng M ngày 10/10 và v2.1 ngày 17/10:** lõi dự đoán cặp đa nhãn, baseline + DistMult + evaluator; 10 plan mới, hai đợt xem kết quả | Người dùng thiếu thời gian/nhân lực duyệt và muốn trở lại bài toán gốc; giữ consumer safeguards ở nhánh riêng | Đã thiết kế, chưa triển khai các phần mới; 15 plan cũ được đánh dấu lịch sử |
| 2026-10-17 | Chạy xong ChEMBL: 599/645 khớp, 271 có cơ chế (218 người); tên thêm 129 thuốc; gói duyệt foundation_v2 | Lượt trước dừng vì HTTP 500; thêm retry 5xx, giảm lô xuống 20 | Đã làm; mapping và cơ chế chờ dược sĩ duyệt |
| 2026-10-17 | Triển khai foundation consumer, immutable releases, review workflow và smoothing B0; alpha100 đạt val macro AP 0,288953 so 0,271431 baseline | Thực thi từng bước bộ plan, không tự duyệt dữ liệu | 63 tests đạt; chờ catalog/gold; smoothing mới là val experiment |
| 2026-10-17 | Thêm 15 plan chi tiết, cập nhật plan tổng v2.1; consumer dùng catalog duyệt, B0 chỉ nghiên cứu; cơ chế đơn thuốc không tự chứng minh claim cặp | Người dùng đã chọn phạm vi; giữ lõi và thử cải tiến có đối chứng | Thiết kế đã viết; chưa nghiệm thu code theo bộ plan mới |
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
- `plan/du_doan_cap/`: 10 plan hiện hành v3; điều phối 00, evaluator 03, DistMult 05, bàn giao 09.
- `plan/chi_tiet/`: 15 plan v2.1 lịch sử, đã có banner hết hiệu lực; bản tổng cũ ở `plan/Ke_hoach_trien_khai_v2_1_lich_su.md`.
- `src/dsp391m/`: package triển khai (xem `src/README.md`). `paths.py` giữ mọi đường dẫn chuẩn và tên snapshot (`decagon_v1`).
- `data/processed/decagon_v1/`: đầu ra ETL. Parquet của `decagon_v1` được commit (khoảng 9 MB, đúng byte manifest đã hash; không chạy lại ETL trên máy khác); snapshot mới vẫn bị gitignore. `manifest.json`, `qa_report.json`, `structure_coverage.json` được commit.
- `data/processed/decagon_v1/splits/pair_70-10-20_s391/`: split **đã đóng băng** (vocab, phân chia cặp, manifest có hash), được commit. Muốn đổi thì tạo `split_id` mới, không ghi đè.
- `data/cache/`: cache theo chế độ (gitignore).
- `data/processed/decagon_v1/drug_names.parquet`, `gene_names.parquet`: bảng tên lấy từ API ngoài, được commit.
- `data/external/ncbi/`: cache symbol gene (đã cắt gọn), được commit.
- `data/external/pubchem/`: cache nguyên văn phản hồi PubChem, được commit để chạy lại ở chế độ `--offline`.
- `tests/`: pytest; test đánh dấu `slow` chạy trên dữ liệu thật; `test_distmult.py` tự bỏ qua khi chưa cài torch.
- `results/`: `readiness/`, `val/<model_release_id>/`, `val/comparisons/`, `releases/baselines/`, `runs/<run_id>/` được commit; `models/` cũng được commit (artifact đã fit; train lại ra ID khác); `scores/` (dựng lại bằng `--rescore`) và `*.pt` bị gitignore; `final/` chỉ ghi qua `dsp391m.final`.
- `analysis/2026-10-17/`: chẩn đoán DistMult và baseline v3.

## Lệnh

Môi trường: Python 3.12 trong `.venv` của dự án, phiên bản khóa trong `requirements.txt` (có RDKit, numpy 2.5.3); huấn luyện cần thêm `requirements-train.txt` (torch 2.5.1). `build_report.py` cần thêm `python-docx`.

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
# v3: kiểm tra dữ liệu trước huấn luyện (ghi bất biến, không ghi đè)
.venv/bin/python -m dsp391m.readiness --out results/readiness/NEW_ID.json
# Chấm một baseline trên val (popularity | b0_alpha0 | b0_alpha100); test luôn bị từ chối ở đây
.venv/bin/python -m dsp391m.evaluate --model b0_alpha100
# So sánh ghép cặp trên val (ID lấy từ results/models/); 1.000 resample khoảng 19 phút
.venv/bin/python -m dsp391m.compare --base b0_alpha0-db2b9c960215 --cand b0_alpha100-60eb89cd5f55 --bootstrap 1000
# DistMult (cần .venv/bin/pip install -r requirements-train.txt); thư mục --out phải mới, hoặc --resume
.venv/bin/python -m dsp391m.training.trainer --dim 64 --lr 0.01 --seed 391 --negatives mixed --weight-decay 0 --out results/runs/NEW_RUN_ID
# Máy mới: dựng lại score cache val từ artifact đã commit, rồi so metric với run đã commit
.venv/bin/python -m dsp391m.evaluate --rescore b0_alpha0-db2b9c960215 distmult_d128-dbd218398318 ...
.venv/bin/python analysis/2026-10-17/verify_transfer.py
# Lô ca val để xem thủ công (không ghi đè)
.venv/bin/python -m dsp391m.cases --base b0_alpha0-db2b9c960215 --cand distmult_d128-dbd218398318 --out results/val/error_analysis/NEW.json --markdown analysis/NGAY/NEW.md
# Search đã đăng ký (4 cấu hình + 2 seed + compare), không chấm test
.venv/bin/python analysis/2026-10-17/run_distmult_search_v1.py
# Test cuối: chỉ sau khi chọn model trên val và commit sạch (lock từ chối worktree bẩn)
.venv/bin/python -m dsp391m.final lock --models ID ... --reference ID --selection "..." --out results/final/locks/NEW.json
.venv/bin/python -m dsp391m.final run --lock results/final/locks/NEW.json --run-id NEW_RUN
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
- **Train support (đo 2026-10-17, `prediction_view`):** cả 645 thuốc có cặp train (bậc trung vị 117, 31 thuốc dưới 10 cặp); 0 cặp val/test chứa thuốc chưa học; 963/963 nhãn có dương trong train; trung vị 52 nhãn mỗi cặp train, tối đa 505. DistMult không cần fallback thuốc lạnh trên split này.
- **Split chính thức `pair_70-10-20_s391`:** 63.472 cặp có nhãn trong vocab, chia 44.430 / 6.347 / 12.695 (1 cặp chỉ có nhãn ngoài vocab bị loại). Prediction view còn 3.198.361 dòng nhãn train. Nếu chỉ tính ngưỡng ≥500 dòng trên train (ngưỡng nhân 0,7) thì vocab còn 959 nhãn: chênh 4 nhãn, **chưa đánh giá ảnh hưởng đến metric** (muốn kết luận thì so sánh hai vocab trên cùng val). Tỷ lệ dương của val: 7,49%.
- **Tên thuốc** (`names_report.json`): 374/645 thuốc có tên ngay từ CID gốc. CID gốc của Decagon thường là dạng flat hoặc ion (ví dụ CID 2173 là anion của ampicillin) nên không có tên; khi đó lấy tên từ CID cha hoặc CID cùng connectivity có nhiều synonym nhất (ampicillin → CID 6249). Mọi tên lấy theo cách này có `needs_review` (có thể nhầm đồng phân lập thể). PubChem chặn IP (HTTP 429) sau khoảng 1.000 request liên tiếp; đến 2026-10-12 NCBI chuyển hướng mọi request từ IP này tới trang **abuse** (`misuse.ncbi.nlm.nih.gov`). **Không gọi PubChem/NCBI theo lô lớn nữa**; dùng `--offline`. ChEMBL đã bổ sung 129 tên ngày 17/10; tổng 503 có tên, 129 pending và 13 không có tên. Các số PubChem ở đầu đoạn là lịch sử trước bổ sung. 3.648/3.648 gene target có symbol NCBI.
- **Hạn chế của nhãn Decagon thấy qua demo:** nhãn lẫn chỉ định và bệnh nền của nhóm bệnh nhân (hyperlipaemia xuất hiện ở mọi cặp có simvastatin), tên nhãn đôi khi lạ (C0011860 có tên "Mod"). Xếp theo số cặp đẩy nhãn chung chung lên đầu; xếp theo mức trội đẩy nhãn hiếm, có thể là nhiễu. Chưa có cách xếp hạng đã kiểm chứng; cần dược sĩ và nguồn GĐ3.
- **B0 trên val chính thức** (`results/val/`, 6.347 cặp × 963 nhãn, tỷ lệ dương 7,49%): popularity macro AP 0,0749; **per-drug macro AP 0,2714** (CI bootstrap percentile [0,2703; 0,2797], lệch lên do cặp lặp khi lấy mẫu), micro AP 0,3508, macro AUROC 0,8360. Theo nhóm: nhãn hiếm/trung bình/phổ biến 0,178/0,246/0,391; cặp có 0/1/2 thuốc có target 0,266/0,274/0,305.
- **Baseline v3 trên val** (evaluator schema 2, `results/releases/baselines/2026-10-17_v1.json`): popularity / B0 alpha0 / alpha100: macro AP 0,0749 / 0,2714 / 0,2890; NDCG@10 0,405 / 0,526 / 0,487; pair AP 0,270 / 0,355 / 0,324. Score float32 lệch macro AP dưới 1e-7 so float64.
- **Runtime trên Apple M4:** chấm một model val khoảng 20 giây; compare 1.000 resample: 1 worker khoảng 24 phút, 6 worker khoảng 8,4 phút; DistMult khoảng 11 giây/epoch (dim 64), 16 giây/epoch (dim 128), peak RSS khoảng 1,9 GB. Môi trường: numpy 2.5.3 (đã pin; venv sạch tái lập giống hệt baseline và trainer, xem `results/env/2026-10-17_verification.md`). DistMult trộn âm khoảng 25–35 giây/epoch; một run d128 khoảng 13–15 phút (22–27 epoch), peak RSS khoảng 2,1 GB.
- **Target Decagon dạng panel rộng:** 83/284 thuốc có target có hơn 100 target và gần như dùng chung một panel khoảng 158 gene GPCR (Jaccard trung vị 0,88; 20 thuốc có bộ target giống hệt nhau; gồm cả atenolol, amitriptyline, salbutamol, calcium ion). Target của các thuốc này không đặc hiệu: `lookup` gắn `low_specificity` và không diễn giải "target chung".
- **DailyMed** (8 thuốc mẫu, 129 đoạn): tìm được tương tác thật mà nhãn Decagon không nói được (nhãn fluoxetine: kéo dài thời gian bán thải của diazepam; nhãn omeprazole: diazepam là cơ chất CYP2C19). Nhãn chọn tự động có thể là nhãn OTC không có mục Drug Interactions (aspirin). Chỉ khớp tên thuốc nguyên từ, chưa bắt được cách nhắc theo nhóm ("strong CYP3A4 inhibitors").
- **Độ trễ GĐ2** (300 đơn ngẫu nhiên, k = 3/5/10): tải chỉ mục 0,7 giây; truy vấn p50 15 ms, p95 228 ms, tối đa 687 ms. Đạt mục tiêu p95 tra cứu dưới 1 giây.
- **Cấu trúc phân tử** (PubChem, 2026-10-10): 645/645 thuốc combo có SMILES và RDKit tạo được Morgan fingerprint. 58 thuốc bị gắn cờ (`charged`, `multi_component`, `tiny`): phần lớn là dạng ion hóa hợp lệ của thuốc (penicillin dạng carboxylate, amoni bậc 4), nhưng có nhóm cần xem tay vì không phải hoạt chất đặc hiệu (calcium cation, NaCl, KCl, sulfate ion, nitric oxide, lithium aluminum hydride, CID 6398525). Không có InChIKey trùng. Danh sách đầy đủ trong `data/processed/decagon_v1/structure_coverage.json`.
- **Tên thuốc `needs_review=False` chưa chắc hiển thị được** (`cases20_global_checks.py`, 2026-10-17): 19/420 có dạng không phù hợp, ít nhất 8 sai rõ (đồng vị `Rapamycin-d3`, `Tacrolimus-13C,D2`; bốn tên "Impurity"; `loperamide(1+)`, `dantrolene(1-)`). Demo luôn hiện ID kèm tên.
- **Top-10 trên val:** B0 alpha0 chỉ dùng 220 nhãn khác nhau ("arterial pressure NOS decreased" ở 81% cặp); DistMult dùng 961 nhãn, nhãn hiếm hơn, NDCG@10 = 0 ở 11,6% cặp so 3,4%.
- Tên tác dụng phụ có lỗi chính tả (ví dụ "neumonia"). Dùng CUI làm khóa và giữ tên gốc để truy vết.
- Nạp combo bằng `dtype='category'` để tiết kiệm RAM. Không dựng toàn bộ 4,6 triệu cạnh thành object NetworkX; dùng bảng tra cứu hoặc ma trận thưa.

## Nguyên tắc thiết kế đã thống nhất trong phân tích

Các nguyên tắc này dễ bị vi phạm khi viết code mới:

- **Tách hai chế độ chạy.** *Evidence mode* được dùng cạnh đã biết của chính cặp đang hỏi. *Prediction evaluation mode* phải loại mọi bằng chứng làm lộ nhãn test (cạnh đồ thị, corpus, ví dụ few-shot, cache). Trong code: chỉ đọc nhãn qua `dsp391m.dataview` (`prediction_view` cho benchmark); chỉ bộ chấm điểm gọi `load_eval_targets`; cache qua `dataview.Cache`. Split chỉ được đọc qua `splits.load_verified_split`. Trong prediction view, **mọi metadata suy ra từ nhãn phải tính lại trên train**; khi thêm cột hoặc bảng mới, thêm test vào `tests/test_split_integrity.py`. Nguồn ngoài (DailyMed, ChEMBL) nói trực tiếp về cặp val/test cũng phải bị che trong prediction mode.
- **Chia tập trước, rồi mới dựng đồ thị huấn luyện, feature hay embedding.** Thiết lập chính là chia theo cặp đã chuẩn hóa: mọi nhãn của một cặp nằm cùng một split.
- **DistMult là thí nghiệm lõi v3 sau kiểm tra dữ liệu/evaluator.** Không chờ catalog hay duyệt chuyên môn. Đối chứng B0 alpha100; quy tắc promotion, ngân sách và ba seed ở plan/du_doan_cap/06_Thuc_nghiem_va_chon_model.md. Chọn bằng val, khóa checkpoint trước test; không đạt thì giữ B0 demo.
- **Bằng chứng phải phù hợp với claim:** nguồn trực tiếp về cặp, cơ chế đơn thuốc và association là các loại khác nhau, không phải thứ tự sức mạnh tuyệt đối. ChEMBL action_type không tự chứng minh tương tác cặp hoặc outcome. Consumer chỉ xuất claim đã kiểm chứng; B0 và thống kê Decagon ở chế độ nghiên cứu.
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
