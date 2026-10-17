# Hướng dẫn tiếp tục trên PC (chuyển máy 2026-10-17)

Đối tượng: Claude Code (và người dùng) trên PC mới (i5-14600KF, 32 GB RAM, RTX 3070 Ti), sau khi pull repo từ GitHub. Mục tiêu là chạy tiếp **phần 2: thí nghiệm mở rộng E1 (residual DistMult trên B0)**, rồi phần 3 (lock + chấm test cuối). Đọc hết file này và [CLAUDE.md](../CLAUDE.md) trước khi chạy bất kỳ lệnh nào.

## 0. Đang ở đâu

Nhánh `gd1a-data-foundation`. Đã xong và đã commit:

| Việc | Kết quả | File |
|---|---|---|
| v3 bước 1–5: contract, readiness, evaluator, baseline, trainer | 94 test nhanh + 2 slow đạt | `src/dsp391m/`, `tests/` |
| Baseline val | popularity / B0 alpha0 / alpha100: macro AP 0,0749 / 0,2714 / 0,2890; NDCG@10 0,405 / 0,526 / 0,487 | `results/releases/baselines/2026-10-17_v1.json` |
| Search DistMult v1 (đăng ký trước) | chọn d128 lr 0,01; ba seed macro AP 0,2863 / 0,2852 / 0,2880; NDCG@10 khoảng 0,412; **không promote** | `results/experiments/2026-10-17_search_v1_model_selection.json`, [chẩn đoán](../analysis/2026-10-17/distmult_diagnostics.md) |
| Lô 20 ca val (B0 alpha0 vs DistMult) | B0 mạnh top-10 từng cặp; DistMult mạnh micro AP (0,376) và cụ thể hơn theo cặp | [tóm tắt](../analysis/2026-10-17/cases20_review_notes.md) |

Danh sách việc lúc chuyển máy (người dùng chọn chạy **phần 2**):

1. ~~Lô 20 ca val~~ (xong).
2. **E1 residual (plan 08)**: một thí nghiệm mở rộng duy nhất, đăng ký trước, làm **trước** khi lock test. ← làm tiếp
3. Lock bộ model và chấm test một lần (`dsp391m.final`).
4. Demo CLI (plan 07) với backend đã chọn (hiện là B0 alpha0), rồi báo cáo/bàn giao (plan 09).

Chưa có người duyệt hay dược sĩ. Theo plan 09 vẫn chạy tiếp: giữ ID, không diễn giải lâm sàng, ghi "chưa duyệt chuyên môn". Không coi im lặng là duyệt.

ID quan trọng (đều có trong `results/models/`, đã commit):

| Vai trò | model_release_id |
|---|---|
| B0 alpha0: backend demo, mốc NDCG@10 | `b0_alpha0-db2b9c960215` |
| B0 alpha100: mốc macro AP | `b0_alpha100-60eb89cd5f55` |
| Popularity | `b0_popularity-c9cb1df52e07` |
| DistMult d128 lr 0,01 seed 391 / 392 / 393 | `distmult_d128-dbd218398318` / `distmult_d128-b53b6970f80a` / `distmult_d128-78acee09798d` |

## 1. Cái gì có trong git, cái gì không

Có trong git (không cần sinh lại):

- CSV Decagon gốc. `bio-decagon-combo.csv` (233 MB) nằm trong **Git LFS**.
- Bảng ETL `data/processed/decagon_v1/*.parquet` và split đóng băng. Đã commit đúng byte mà manifest/split hash, nên **không chạy lại ETL**.
- Tên thuốc/gene, cache PubChem/NCBI, kết quả ChEMBL.
- Artifact model `results/models/` (khoảng 27 MB). Train lại trên máy khác sẽ ra trọng số khác, tức `model_release_id` khác, nên lock phải dùng các artifact này.
- Kết quả val, so sánh, đăng ký thí nghiệm, summary của các run.

Không có trong git (phải sinh lại hoặc không cần):

| Thiếu | Cách xử lý |
|---|---|
| `.venv/` | tạo mới (mục 2) |
| `results/scores/` (score cache val, 257 MB) | `dsp391m.evaluate --rescore` (mục 3) |
| `results/runs/**/*.pt` (checkpoint resume) | không cần; artifact suy luận đã nằm trong `results/models/` |
| `data/cache/` | không cần |

**Không chạy trên PC:** `dsp391m.etl`, `dsp391m.splits` (ghi đè manifest đã commit), `dsp391m.names`, `dsp391m.chembl`, `dsp391m.structures` không có `--offline` (IP cũ bị NCBI/PubChem chặn; dữ liệu đã có sẵn).

## 2. Cài đặt (Windows PowerShell; Linux/WSL ghi chú bên cạnh)

Cần: Git, **Git LFS**, **Python 3.12** (máy cũ dùng 3.12.4; `rdkit==2024.3.5` và `torch==2.5.1` có wheel cho Windows x64/3.12).

```powershell
git lfs install
git clone https://github.com/cdungngu/DSP391m.git
cd DSP391m
git checkout gd1a-data-foundation
git lfs pull
git status            # phải sạch
```

Combo CSV (LFS) chỉ cần cho `pytest -m slow` (chạy lại ETL vào thư mục tạm). Phần 2 và 3 không cần nó. Nếu tải LFS quá chậm (clone thử trên Mac bị kẹt hơn 15 phút), clone bằng `$env:GIT_LFS_SKIP_SMUDGE=1; git clone ...` (bash: `GIT_LFS_SKIP_SMUDGE=1 git clone ...`), bỏ `git lfs pull` và bỏ `pytest -m slow`. File combo khi đó chỉ là con trỏ LFS; không sửa và không commit nó.

Nếu đã clone từ trước: `git fetch` → `git checkout gd1a-data-foundation` → `git pull` → `git lfs pull`.

Kiểm tra xuống dòng: `.gitattributes` có `* -text` nên Git không đổi LF sang CRLF. Nếu clone trước commit này với `core.autocrlf=true`, chạy `git rm --cached -r -q .` rồi `git reset --hard` để checkout lại. Nếu file text bị đổi CRLF, hash trong manifest/lock sẽ lệch và loader sẽ từ chối (fail closed).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-train.txt   # đã gồm -r requirements.txt
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -c "import numpy, torch, rdkit; print(numpy.__version__, torch.__version__)"
```

Kết quả phải là numpy `2.5.3`, torch `2.5.1` (bản CPU là đúng). Linux/WSL: thay `.venv\Scripts\python` bằng `.venv/bin/python`. Mọi lệnh trong CLAUDE.md viết dạng `.venv/bin/python`; trên Windows đổi thành `.venv\Scripts\python`.

**GPU:** các run đã đăng ký dùng `device: cpu`, và E1 cũng giữ CPU để so được với DistMult. Không cài torch CUDA cho các run chính. i5-14600KF có 6P+8E nhân: dùng `--threads 6` (hoặc 8) cho trainer và để `--workers` mặc định (6) cho bootstrap.

Nếu `pip install` lỗi vì một gói không có wheel Windows, không đổi version tùy ý. Thử WSL2 Ubuntu (Python 3.12) trước. Nếu vẫn phải đổi pin, ghi lại trong `results/env/` theo cách của `2026-10-17_verification.md`, chạy lại mục 3 và cho người dùng biết.

## 3. Xác minh máy mới (bắt buộc trước khi làm phần 2)

```powershell
.venv\Scripts\pytest                         # 94 test nhanh, phải đạt hết
.venv\Scripts\python -m dsp391m.readiness --out results\readiness\pc_check.json
.venv\Scripts\python -m dsp391m.evaluate --rescore b0_popularity-c9cb1df52e07 b0_alpha0-db2b9c960215 b0_alpha100-60eb89cd5f55 distmult_d128-dbd218398318 distmult_d128-b53b6970f80a distmult_d128-78acee09798d distmult_d128-48ebb0762217 distmult_d128-5449a82c8b23 distmult_d64-56446f8ff89d distmult_d64-5f8f829ce880 distmult_d64-c4b527f2d6b7
.venv\Scripts\python analysis\2026-10-17\verify_transfer.py   # mỗi dòng phải là OK
.venv\Scripts\pytest -m slow                 # chạy ETL vào thư mục tạm (cần LFS combo), vài phút
```

Kỳ vọng:

- Readiness: 645 thuốc có cặp train, 0 cặp val/test chứa thuốc chưa học, 963/963 nhãn có dương. Xóa `pc_check.json` sau khi xem; không commit file này, vì `results/readiness/2026-10-17_v1.json` là bản chính thức.
- `verify_transfer.py`: macro AP B0 alpha0 0,271431, alpha100 0,288953, DistMult seed391 0,286290. Lệch tối đa ≤ 1e-5 so với kết quả trên Mac (BLAS trên x86 có thể lệch ở chữ số cuối với DistMult; B0 phải lệch 0).

Nếu lỗi:

| Lỗi | Nguyên nhân thường gặp |
|---|---|
| `SplitIntegrityError` hoặc `IntegrityError` khi nạp view | parquet chưa đúng byte: chưa `git lfs pull`, CRLF, hoặc lỡ chạy ETL. Dùng `git status`, `git checkout -- data/` |
| `IntegrityError` artifact | `results/models/` bị sửa hoặc thiếu; checkout lại |
| `os.link` lỗi | ổ đĩa không phải NTFS (FAT/exFAT, ổ mạng). Clone vào ổ NTFS |
| Đường dẫn quá dài | `git config --global core.longpaths true`, clone gần gốc ổ (ví dụ `C:\dev\DSP391m`) |
| Bootstrap treo hoặc lỗi spawn | chạy qua `python -m ...` như lệnh mẫu, không import trong REPL; thử `--workers 1` để cô lập |

Sau khi xác minh xong, chạy `git status` (chỉ được có file trong `results/scores/`, vốn đã bị ignore) rồi báo người dùng: số test, bảng `verify_transfer`, thời gian rescore.

## 4. Phần 2: E1 residual DistMult trên B0

Nguồn: [plan 08 mục E1](du_doan_cap/08_Mo_rong_va_thi_nghiem.md). Câu hỏi nghiên cứu: phần tương tác DistMult học thêm có cải thiện so với prior từng thuốc của B0 không. Lý do thử: B0 alpha0 mạnh NDCG@10 (0,526), DistMult mạnh micro AP và ngang alpha100 về macro AP.

### 4.1 Hỏi người dùng một câu trước khi đăng ký

Base của offset là **B0 alpha0** (khuyến nghị: là backend demo và mạnh top-10) hay alpha100? Không có câu trả lời thì dùng alpha0 và ghi rõ trong registration.

### 4.2 Công thức (cố định, không mở grid)

- `F` = ma trận tần suất train của B0 base đã fit (645 × 963, đọc từ artifact `results/models/<base>/`, không fit lại).
- `b0(A,B,e) = F[A,e] + F[B,e]` (score_kind `frequency_sum`, nằm trong [0, 2]).
- `p0 = clip(b0/2, 1e-4, 1 − 1e-4)`; `offset = logit(p0)`. Đây là biến đổi số học để làm offset, **không** phải xác suất đã hiệu chuẩn.
- `s(A,B,e) = offset(A,B,e) + DistMult(A,B,e)`. B0 đóng băng; chỉ embedding DistMult được học.
- Mọi thứ khác giữ như search v1: dim 128, lr 0,01, Adam, wd 0, Xavier, batch 2048, sampler `mixed` (5 âm thay nhãn + 5 âm thay cặp train, loss 0,5/0,5, `loss_version` giữ nguyên), max 50 epoch, patience 5, min_delta 1e-4, chọn epoch theo val macro AP, CPU.
- Offset phải tính cho **cả âm**: âm thay nhãn dùng `(A,B,e')`, âm thay cặp dùng `(A',B',e)`. Tính bằng gather từ `F` trên batch, không dựng tensor 44k × 963.
- Seeds 391, 392, 393.

### 4.3 Đăng ký trước khi chạy (commit riêng)

Tạo `results/experiments/<ngày>_residual_e1_registration.json` qua `dsp391m.releases.publish`, theo mẫu `2026-10-17_distmult_search_v1_registration.json`, gồm:

- `experiment: "residual_e1"`, base `model_release_id` và `weights_sha256` của base, công thức ở 4.2, config cố định, seeds, `code_commit_at_registration`, `no_test`.
- Quy tắc promotion giống search v1: cả 3 seed có macro AP > alpha100; delta trung bình ≥ 0,005; cận dưới CI95 paired (seed 391, 1.000 resample, seed 391) > 0; mean NDCG@10 ≥ 0,5208 (alpha0 − 0,005). Thêm so sánh mô tả với DistMult seed391 `distmult_d128-dbd218398318` (không phải điều kiện promotion).
- Quy tắc dừng: chạy đúng một lần; không đạt thì ghi kết quả âm và **không thử biến thể khác** (không đổi clip, lr, dim, trọng số offset).
- Ghi trung thực: các quan sát dẫn tới E1 (lô 20 ca, search v1) đã nhìn val; E1 là thí nghiệm phát triển phương pháp trên val.

Commit registration (cùng code nếu code đã xong và có test) **trước** khi chạy run thật.

### 4.4 Code cần thêm (gợi ý vị trí, theo phong cách repo)

- `src/dsp391m/models/residual.py` (hoặc mở rộng `models/distmult.py`): module có buffer `F` (float32, không học) cộng offset vào score của DistMult; `score_all(a, b)` = offset [n, 963] + bilinear. Predictor có `name` dạng `residual_d128`, `score_kind = "offset_plus_bilinear_logit"`, config gồm `base_model_release_id` và `base_weights_sha256`, nên base khác thì `config_id` và `model_release_id` khác. Artifact npz gồm embedding **và** `F`, để `model_release_id` hash cả hai. `save`/`load` kiểm identity giống `DistMultPredictor`.
- `training/trainer.py`: thêm `TrainConfig.offset: str | None = None` (`--offset <base_release_id>`). Khi có offset thì dựng model residual, nạp `F` qua `B0.load` từ `results/models/<base>` (kiểm identity cùng view), và áp offset trong `loss` cho dương, âm nhãn và âm cặp. Resume kiểm cả offset. `to_dict` phản ánh trường mới; DistMult cũ phải giữ nguyên `config_id`. Nếu thêm trường làm đổi hash của config cũ, chỉ thêm khóa khi khác None.
- `final._loader`: thêm loại `residual`.
- `evaluate.rescore` dùng `_loader`, nên tự hỗ trợ khi `_loader` có loại mới.
- Test (`tests/test_residual.py`, `pytest.importorskip("torch")`, fixture `snap`):
  - embedding bằng 0 thì score bằng đúng offset, và thứ hạng nhãn trong từng cặp trùng thứ hạng B0 (logit đơn điệu, trừ chỗ clip gây hòa);
  - đối xứng A/B;
  - offset trong loss của âm thay cặp dùng cặp âm chứ không dùng cặp dương;
  - `F` chỉ từ train: hoán đổi nhãn held-out không đổi score (giống test trong `test_readiness.py`);
  - save → load cho cùng score; base khác thì `model_release_id` khác; identity lệch thì bị chặn;
  - `config_id` của DistMult không offset không đổi so với trước (so với giá trị cố định của config d128 lr 0,01 seed 391, đọc từ `results/models/distmult_d128-dbd218398318/model.json`).

### 4.5 Chạy

Viết `analysis/<ngày>/run_residual_e1.py` theo mẫu `analysis/2026-10-17/run_distmult_search_v1.py`: mỗi seed là một tiến trình trainer riêng, tái dùng run đã xong, sau đó compare seed391 với alpha100, alpha0 và DistMult seed391 (1.000 resample), áp quy tắc đã đăng ký và ghi `results/experiments/<ngày>_residual_e1_selection.json` bất biến.

```powershell
.venv\Scripts\python -m dsp391m.training.trainer --dim 128 --lr 0.01 --seed 391 --negatives mixed --weight-decay 0 --offset b0_alpha0-db2b9c960215 --threads 6 --out results\runs\<ngày>_residual_e1_s391
```

Ước tính trên PC: mỗi seed khoảng 8–15 phút (Mac M4: 13–15 phút với DistMult d128); 3 seed cộng 3 compare (mỗi compare khoảng 6–8 phút với 6 worker) tổng khoảng 1–1,5 giờ. Chạy nền và theo dõi log, không poll liên tục.

### 4.6 Ghi kết quả

- Thêm mục 7 vào [distmult_diagnostics.md](../analysis/2026-10-17/distmult_diagnostics.md) (hoặc file phân tích mới trong `analysis/<ngày>/`): bảng 3 seed, CI, kết luận promote hay không, và kết quả âm nếu có.
- CLAUDE.md: Trạng thái hiện tại, một dòng Nhật ký quyết định ở đầu bảng, Lệnh (`--offset`, `--rescore`), Sự thật về dữ liệu (runtime PC).
- Plan 08: đánh dấu E1 đã chạy và ghi kết quả. Nếu promote, sửa `FALLBACK_POLICY`/backend demo trong plan 06/07 theo quy tắc. Không promote thì demo giữ B0 alpha0.
- Commit, rồi `git push`.

## 5. Phần 3: lock và chấm test (sau E1, một lần duy nhất)

1. Bộ model khóa (đề xuất): popularity, B0 alpha0, B0 alpha100, DistMult 3 seed, E1 3 seed.
2. **Reference:** `final.run` chỉ so mọi model với **một** reference. Plan 06 dùng alpha100 làm mốc macro AP và alpha0 làm mốc NDCG. Nếu cần CI so với cả hai, sửa runner để nhận nhiều reference **trước** khi lock (có test), commit, rồi mới lock. Hỏi người dùng nếu chưa rõ; mặc định là alpha100.
3. Worktree phải sạch (trừ `results/`). Thứ tự bắt buộc: `final lock` → `final run` → **rồi mới** commit lock và kết quả. Lock ghi commit HEAD; nếu commit lock trước khi run, HEAD đổi và runner sẽ từ chối.

```powershell
.venv\Scripts\python -m dsp391m.final lock --models <ID ...> --reference b0_alpha100-60eb89cd5f55 --selection "search v1 + E1 theo đăng ký; demo B0 alpha0" --out results\final\locks\<ngày>_v1.json
.venv\Scripts\python -m dsp391m.final run --lock results\final\locks\<ngày>_v1.json --run-id <ngày>_final_v1
```

4. Test mở đúng một lần. Lỗi kỹ thuật thì chạy lại bằng `--retry-of` và `--reason`. Mọi thay đổi thuật toán sau khi xem test chỉ là thăm dò, không sửa kết quả chính.

## 6. Phần 4 (sau test): demo và bàn giao

- Demo CLI theo [plan 07](du_doan_cap/07_Suy_luan_va_demo.md), backend B0 alpha0 (trừ khi E1 promote): hiện ID kèm tên; đánh dấu tên `needs_review` hoặc tên có dạng lỗi (đồng vị, "Impurity", ion: xem `analysis/2026-10-17/cases20_global_checks.py`); gắn cờ "nhãn chung" cho nhãn nằm trong top-10 của hơn 50% cặp val; không hiện phần trăm nguy cơ; ghi "điểm xếp hạng nghiên cứu, cặp vắng nhãn không có nghĩa là an toàn".
- Bàn giao theo [plan 09](du_doan_cap/09_Ban_giao_va_duyet_theo_dot.md): data card, model card, toàn bộ kết quả kể cả thí nghiệm âm, hạn chế "chưa có duyệt chuyên môn".

## 7. Nguyên tắc không được phá (tóm tắt CLAUDE.md)

- Nhãn chỉ đọc qua `dsp391m.dataview`; chỉ evaluator gọi `load_eval_targets`; **test chỉ qua `dsp391m.final`**.
- Output là release bất biến (`releases.publish`), không ghi đè; thư mục `--out` phải mới.
- Đăng ký trước khi chạy; kết quả đã nhìn val phải ghi là thăm dò phát triển phương pháp.
- Không tự đổi trạng thái pending thành approved; không dựng target/cơ chế từ trí nhớ.
- Commit sau mỗi bước có nghiệm thu (test đạt), message tiếng Anh, ghi chú/phân tích tiếng Việt. Cập nhật CLAUDE.md trong cùng phiên.
- Dừng và hỏi người dùng khi: cần đổi version gói, cần đổi quy tắc đã đăng ký, E1 có dấu hiệu lỗi pipeline (loss NaN, macro AP = popularity), hoặc trước khi chạy `final run`.
