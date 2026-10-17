# Chẩn đoán DistMult và baseline v3 — 2026-10-17

Thăm dò trên **val**, không phải run chọn model và không chấm test. Mọi số đo trên Apple M4 16 GB, CPU, torch 2.5.1 (4 thread), numpy 2.5.3. Script nằm cùng thư mục; chạy từ thư mục gốc repo bằng `.venv/bin/python analysis/2026-10-17/<file>.py`.

## 1. Baseline qua evaluator v3 (val, 6.347 cặp × 963 nhãn)

| Model | Macro AP | Micro AP | Pair AP | P@5 | R@10 | NDCG@10 |
|---|---:|---:|---:|---:|---:|---:|
| popularity | 0,0749 | 0,2263 | 0,2704 | 0,4124 | 0,0792 | 0,4053 |
| B0 alpha0 | 0,2714 | 0,3508 | 0,3546 | 0,5428 | 0,1077 | 0,5258 |
| B0 alpha100 | 0,2890 | 0,3131 | 0,3237 | 0,5027 | 0,0959 | 0,4869 |

Paired bootstrap 1.000 resample (seed 391), alpha100 − alpha0: macro AP **+0,0175** [+0,0152; +0,0192]; NDCG@10 **−0,0389** [−0,0412; −0,0365]; pair AP −0,0309; micro AP −0,0377. Smoothing kéo nhãn hiếm về popularity: tốt cho xếp hạng cặp trong từng nhãn (macro AP), xấu cho xếp hạng nhãn trong từng cặp (demo). Release: `results/releases/baselines/2026-10-17_v1.json`.

Shortcut top-10: B0 alpha0 có 92% nhãn top-10 nằm trong hợp top-10 của hai thuốc đơn lẻ; alpha100 trùng popularity 72%.

## 2. DistMult theo đúng plan 05 không học

Runtime probe (`results/runs/2026-10-17_probe_d64`, `_d128`): một epoch mất khoảng 11 giây (dim 64; sampler 5,2 giây, train 5,5 giây, val 0,5 giây) và khoảng 16 giây (dim 128); peak RSS khoảng 1,9 GB. Loss đứng yên ở 1,3863 = 2·ln 2, val macro AP 0,0749 = popularity.

| Thử nghiệm (script) | Kết quả |
|---|---|
| Khởi tạo lớn hơn (`diag_init.py`) | Score lớn hơn, loss không xuống dưới 1,386 sau 400 bước |
| Bias theo nhãn (`diag_bias.py`) | Loss giảm, macro AP vẫn 0,0749: bias không giúp xếp hạng cặp trong nhãn |
| lr 0,01 / 0,03, 8 epoch, wd 1e-5 (`diag_lr.py`) | Thoát saddle; chững ở macro AP khoảng 0,11 / 0,177 |
| lr 0,03, wd 1e-5 + âm thay cặp, không cân loss (`diag_pairneg.py`) | Macro AP 0,241 sau 3 epoch (chỉ thay nhãn: 0,176); NDCG@10 0,429 so 0,453 |

Giải thích ban đầu (lr quá nhỏ) đã được **thay** bởi mục 4: nguyên nhân chính là weight decay của Adam. Về sampler: chỉ thay nhãn có thể chưa phù hợp với mục tiêu xếp hạng theo nhãn; tham số dùng chung vẫn có thể học khác biệt giữa các cặp, nên kết quả chưa chứng minh nguyên nhân tuyệt đối. Bản thử ở `diag_pairneg.py` cộng thêm nguyên một term âm (tổng trọng số âm 2), nên đã gây nhiễu; xem đối chứng cân loss ở mục 5.

## 3. (Lịch sử) Câu hỏi trước plan 06

Lưới lr và sampler của plan 05 phải đổi trước khi đăng ký search 4 cấu hình; các thăm dò này đã nhìn val nên phải công bố như thăm dò thiết kế. Chưa thử: số epoch dài với âm thay cặp, tỷ lệ hai loại âm, weight decay.

## 4. Weight decay là nguyên nhân sụp về 0 (`diag_weight_decay.py`)

lr 0,001, dim 64, 1 epoch, cùng seed. Với Adam, `wd·θ` (1,1e-4) cùng bậc gradient dữ liệu (3,2e-4) ngay bước 0; Adam chuẩn hóa tổng nên embedding bị kéo về 0 (norm thuốc 10,8 → 0,05 ở bước 500 → 0), gradient dữ liệu tiêu biến, model không học. wd = 0: norm tăng lên 64, loss 1,050, val macro AP 0,169 sau một epoch. Không đổi sang AdamW trong thí nghiệm này. Kết luận: khóa wd = 0.

## 5. Đối chứng sampler có cân loss (`diag_sampler_control.py 0.01`)

Cùng seed 391, lr 0,01, dim 64, wd 0, 5 epoch; tổng trọng số âm bằng 1 ở cả hai.

| Sampler | Macro AP | Pair AP | NDCG@10 | Giây/epoch |
|---|---:|---:|---:|---:|
| Chỉ thay nhãn | 0,2087 | 0,3282 | 0,4858 | 15 |
| Trộn 0,5/0,5 | 0,2624 | 0,2895 | 0,4119 | 28 |

Âm thay cặp tăng macro AP +0,054 nhưng giảm NDCG@10 −0,074: đánh đổi thật giữa hai mục tiêu. Theo quyết định người dùng, khóa sampler trộn cho search (macro AP là metric chọn). Cả hai còn dưới mốc B0 sau 5 epoch.
