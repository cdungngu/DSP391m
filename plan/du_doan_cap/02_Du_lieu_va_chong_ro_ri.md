# 02 — Dữ liệu, split và chống rò rỉ

Phụ thuộc: [01](01_Bai_toan_va_hop_dong.md). Tái sử dụng etl.py, splits.py, dataview.py, releases.py.

## Dữ liệu đủ để bắt đầu

| Thành phần | Hiện có | Vai trò |
|---|---|---|
| Decagon combo | 645 thuốc, 1.317 nhãn, 63.473 cặp | Nhãn quan sát gốc |
| Benchmark cố định | 963 nhãn, 63.472 cặp | Một cặp chỉ có nhãn ngoài vocab không tham gia |
| Train / val / test | 44.430 / 6.347 / 12.695 cặp | pair_70-10-20_s391 |
| Train positives | 3.198.361 dòng | Fit B0 và DistMult |
| Target Decagon | 284/645 thuốc | Phân tầng, chưa là feature lõi |
| ChEMBL | 599 khớp; 271 có cơ chế; 218 cơ chế người | Mở rộng độc lập |
| Mapping đã duyệt | 0 | Không chặn benchmark bằng ID |

Không tải thêm nguồn để bắt đầu. Giữ raw và split đã đóng băng. Một ID hóa học đáng ngờ vẫn thuộc benchmark; gắn cờ khi phân tích, không sửa ID hay loại âm thầm.

## Ranh giới dữ liệu

1. Mọi fit/count/sampler chỉ đọc prediction_view qua split đã xác minh.
2. Evaluator đọc val/test qua load_eval_targets; model chỉ nhận cặp cần score.
3. Counts, degree, ngưỡng phân tầng, chuẩn hóa feature đều tính từ train.
4. Không lookup nhãn của cặp val/test, không dùng DailyMed/LLM/retrieval làm feature lõi.
5. Lưu ID order và CUI order cùng model; kiểm tra chính xác khi nạp, không chỉ kiểm tra shape.
6. Cache tách purpose, snapshot, split, config và model hash. Observation lookup không dùng chung cache feature.

## Vocab cố định và sensitivity

963 nhãn được chọn từ snapshot đầy đủ theo quy ước lịch sử; đây là sự phụ thuộc của bước chọn vocab vào toàn dữ liệu, cần công bố, không gọi pipeline hoàn toàn train-only từ bước chọn vocab. Fit mô hình vẫn train-only.

Tập 959 nhãn theo ngưỡng train là sensitivity tùy chọn. Giữ nguyên cặp, công bố số cặp mất toàn nhãn và mẫu số metric; không so các macro AP khác không gian nhãn như cùng benchmark. Bảng chính tiếp tục 963.

## Gói dữ liệu cho trainer

- drug_index: original_id, drug_idx, train_pair_degree, flags.
- label_index: effect_cui, effect_idx, label_idx, n_train_positive.
- train_pairs + positive label lists, hoặc CSR boolean.
- manifests: source hashes, split hash, vocabulary hash, preprocessing version.
- evaluation pairs không chứa cột nhãn, counts toàn snapshot hoặc membership source bị nhầm thành feature.

Dense train boolean khoảng 42,8 triệu ô; có thể dùng CSR để tiết kiệm. Không dựng Python object cho từng cạnh trong NetworkX. Dữ liệu labels và scores xử lý theo batch; toàn bộ 207.690 cặp không cần được score sẵn cho demo.

## Kiểm tra trước huấn luyện

- [x] Không trùng canonical pair giữa train/val/test; không self-pair.
- [x] Hash split/vocab đúng; schema và ID order đúng.
- [x] Thống kê train_degree=0, nhãn train_positive=0 và phân bố số nhãn mỗi cặp.
- [x] Hoán đổi nhãn held-out không đổi B0 fit hoặc train batches.
- [x] Train sampler không import lookup hay đọc raw combo để lọc nhãn toàn snapshot.
- [x] Khi source/hash sai, fail closed; không fallback sang snapshot khác.
- [x] Ghi báo cáo data_readiness với counts, phạm vi và các ngoại lệ.

Đo sơ bộ 2026-10-17 (chưa phải báo cáo readiness): 645/645 thuốc có cặp train, 0 cặp val/test chứa thuốc chưa học, 963/963 nhãn có dương trong train. Nếu kết quả này giữ nguyên trong data_readiness.json thì nhánh fallback B0 của file01 không phát sinh.

Bàn giao: data_readiness.json có version, tests chống leakage và manifest đầu vào. Đây là điều kiện G0/G1; không cần duyệt 645 danh tính thuốc bằng tay.

