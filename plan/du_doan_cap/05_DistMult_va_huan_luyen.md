# 05 — DistMult và thiết kế huấn luyện

Phụ thuộc G1: [02](02_Du_lieu_va_chong_ro_ri.md)–[04](04_Baseline_va_shortcut.md).
Đây là hạng mục lõi mới; không chờ catalog, DailyMed, LLM hoặc dược sĩ.

## Mô hình

Mỗi thuốc có vector z_d ∈ R^h, mỗi nhãn có r_e ∈ R^h.
s(A,B,e)=sum_j z_Aj * r_ej * z_Bj.
Vì phép nhân giao hoán, score đối xứng phù hợp cặp không thứ tự. Có (645+963)*h tham số, khoảng 103 nghìn khi h=64, 206 nghìn khi h=128, chưa tính optimizer. Không cần PPI hay ChEMBL để chạy.

Lựa chọn này dựa trên dạng bilinear của [Yang et al., ICLR 2015](https://arxiv.org/abs/1412.6575). Đây là baseline embedding nhỏ, không phải tái hiện toàn bộ [Decagon GNN](https://arxiv.org/abs/1802.00543). Không so trực tiếp metric bài báo với split của repo.

## Sampler train-only

Mỗi positive (A,B,e) lấy 5 nhãn e' chưa quan sát trên chính cặp train A,B; không thay A/B sang cặp held-out. Lọc positives bằng train matrix, không cần đọc nhãn toàn snapshot. Nhãn nằm trong vocab cố định 963. Lấy không hoàn lại trong nhóm 5 nếu đủ, nếu thiếu lấy số có thể và lưu số thực; nếu không có âm bỏ negative term và ghi count.

RNG riêng theo seed và epoch; chỉ số pair/label và trạng thái RNG được lưu khi resume. Các positive duyệt một lần mỗi epoch sau shuffle. Tránh vòng while vô hạn khi cặp có nhiều nhãn: dựng candidate complement hoặc rejection có giới hạn + fallback xác định.

Loss mỗi positive:
softplus(-s_pos) + mean_j softplus(s_neg_j).
Sau đó mean theo batch. Đây là cân bằng positive/negative terms, khác phép lấy mean chung 1 positive + 5 negatives; ghi loss_version để không trộn kết quả. Âm vẫn là giả định, sigmoid(logit) không được xuất như xác suất lâm sàng.

## Cấu hình khởi đầu và ngân sách

| Tham số | Giá trị thiết kế |
|---|---|
| Embedding dimension | 64 hoặc 128 |
| Learning rate | 0,01 hoặc 0,03 (sửa 2026-10-17; thiết kế cũ 0,001/0,003) |
| Optimizer | Adam, weight_decay=0 (sửa 2026-10-17; 1e-5 làm embedding sụp về 0) |
| Batch | 2.048 positive; mỗi positive 5 âm thay nhãn + 5 âm thay cặp train (sửa 2026-10-17) |
| Loss | softplus(-s_pos) + 0,5·mean âm thay nhãn + 0,5·mean âm thay cặp; loss_version pos_plus_half_label_half_pair_v1 |
| Epoch | Tối đa 50; patience 5 theo val macro AP |
| Early stop | Cải thiện >1e-4; hòa giữ checkpoint sớm hơn |
| Khởi tạo | Xavier uniform; seed ghi riêng |
| Search | 4 cấu hình seed391; cấu hình thắng thêm392,393 |

Đây là giá trị đề xuất, không phải hyperparameter đã chứng minh tối ưu. **Sửa protocol 2026-10-17 trước search:** lr, weight decay và sampler đổi sau thăm dò trên val ([chẩn đoán](../../analysis/2026-10-17/distmult_diagnostics.md)); đây là thăm dò phát triển phương pháp, phải công bố như vậy. Đăng ký vòng search: `results/experiments/2026-10-17_distmult_search_v1_registration.json`. Dùng PyTorch trong nhóm dependency training riêng; chọn/pin phiên bản tương thích Python và máy khi triển khai, không tự nâng môi trường ETL. Chạy CPU smoke test trước; đo epoch/validation để quyết định thiết bị. Giới hạn 5 ngày công cho phần huấn luyện/tuning; nếu chưa hoàn tất, báo thiếu bằng chứng ổn định và dùng B0 cho demo.

## Pipeline và checkpoint

Module đề xuất: models/distmult.py, training/sampler.py, training/trainer.py và CLI train. Tên này là thiết kế, chưa phải lệnh có sẵn.

1. Xác minh data readiness/hash; tạo config immutable.
2. Seed Python/NumPy/framework, ghi device và deterministic settings.
3. Train batch → kiểm finite loss/gradient → optimizer step.
4. Mỗi epoch score toàn val theo batch, evaluator trả macro AP.
5. Lưu best checkpoint, không chỉ last; early stop.
6. Load lại best rồi xuất scores qua chung adapter.

Checkpoint: weights, optimizer, epoch, RNG states, config, drug/CUI maps, source/split hashes, code identity, val history. Resume chỉ khi khớp; save/load kiểm numerical tolerance theo thiết bị. Không ghi đè best release đã dùng final.

## Nghiệm thu

- [x] Tính tay score và đối xứng; gradients hữu hạn.
- [x] Overfit fixture nhỏ chỉ để kiểm trainer, không tuyên bố chất lượng.
- [x] Sampler không positive collision, không truy cập val/test labels.
- [x] Dừng đúng patience; chọn best không phải epoch cuối.
- [x] Load checkpoint cho cùng scores; mismatch bị chặn.
- [x] Báo runtime, peak memory, số epoch thực và checkpoint mỗi seed.

Rủi ro chính: học lại tần suất, nhãn thiếu tạo false negatives, rank thấp không đủ biểu diễn, tuning overfit val. Giải quyết bằng baseline mạnh và protocol file06 trước khi thêm kiến trúc.

Kết quả 2026-10-17: code trainer/sampler/checkpoint và test đã có; runtime khoảng 11 giây/epoch (dim 64) trên M4 CPU. Cấu hình thiết kế (lr 0,001/0,003, chỉ âm thay nhãn) không học trên dữ liệu thật; xem [chẩn đoán](../../analysis/2026-10-17/distmult_diagnostics.md). Cần sửa lưới lr và sampler trước khi đăng ký search plan 06.
