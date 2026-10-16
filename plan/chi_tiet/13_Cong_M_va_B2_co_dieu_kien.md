# 13 — Cổng M và B2 có điều kiện

Ngày: 2026-10-17 · Chủ trì: nhóm + dược sĩ · Phụ thuộc [08](08_B0_va_giao_thuc_du_doan.md) và cổng dev của [11](11_Gold_set_va_quy_trinh_duoc_si.md), [12](12_Giao_dien_va_van_hanh.md).

## 1. Quyết định và phạm vi

B2 chưa được cho phép chạy mặc định. B0 đã nằm trong chế độ nghiên cứu, nên giá trị B2 phải là giá trị nghiên cứu cụ thể, không viện lý do “cần cho người dùng phổ thông”.

Biên bản cổng ghi decision_date, approver, artifact_refs, ba điều kiện, công việc bị thay thế và go/no_go. Thiếu một điều kiện → no_go; không tự coi quá hạn là đồng ý.

## 2. Ba điều kiện giữ từ kế hoạch tổng

1. Lõi A+D, giải thích và demo đã qua dev gate; mapping công khai được duyệt.
2. Dược sĩ xem top-10 của khoảng 20 cặp chưa có nhãn, ghi usefulness/ranking concern theo rubric. Đây là đánh giá giá trị nghiên cứu, không ground truth cho accuracy.
3. Còn tối đa 5 ngày công không làm trễ gold/final.

Nếu no_go: ưu tiên mapping, nguồn và lỗi UX. Không bắt đầu B1/GNN/HODDI thay thế.

## 3. Thiết kế B2 khi go

Chọn **DistMult** trước vì endpoint cặp đối xứng. Embedding thuốc và nhãn; score=sum(z_A*r_e*z_B). Cùng vocab/split/evaluator B0, không dùng molecular/source features mới trong phép so chính.

Loss: logistic với minibatch positives và assumed negatives được sample. Negative giữ cặp và thay effect; loại mọi positive đã biết trong snapshot bằng bộ tạo benchmark riêng, chỉ truyền bộ mẫu cho trainer. Đây là lọc nhãn benchmark dùng chung, không cho trainer truy cập held-out labels trực tiếp. Công bố rõ giao thức này; không gọi negatives là an toàn.

Mặc định ratio5; train batches có seed; validation chấm toàn 963 nhãn, không sampling. Lưu positive/negative sampling config/hash. Nếu dùng hard negatives phải là thí nghiệm phụ, không thay giao thức giữa các model.

## 4. Budget và chọn cấu hình

Tối đa 4 cấu hình: dim{64,128} × learning_rate{0,001;0,003}; Adam, batch2048, L2=1e-5, tối đa50 epochs; early stop patience5 bằng macro AP val. Đây là cấu hình khởi đầu đề xuất, không phải tối ưu đã biết.
Chọn bằng seed391; cấu hình thắng chạy thêm seeds392,393. Cố định cấu hình trước final. Mọi thay đổi sau pilot phải ghi config mới; dừng khi hết 5 ngày công.

So cả B0 gốc và B0 được chọn trong E08. Điều kiện giữ: **cả ba seed** đạt macro AP val tăng≥0,02 so baseline B0 đã khóa; báo mean/std, paired bootstrap và top-k. Không dùng AUROC đẹp để bỏ qua điều kiện AP. Nếu không đạt, giữ B0.

## 5. Tích hợp và kiểm thử

- [ ] Mô hình score cặp đối xứng bằng test số học.
- [ ] Sampler không có positive collision, không tự nối, label trong vocab.
- [ ] Trainer không đọc load_eval_targets(test); early stop chỉ val.
- [ ] Checkpoint kèm seed/config/split/vocab hash và load test.
- [ ] Test set chưa được chạy để chọn hyperparameter.
- [ ] B2 chỉ đổi research score backend; consumer không thay đổi.

## 6. Nguồn và giới hạn

[Fast Polypharmacy Side Effect Prediction Using Tensor Factorisation](https://arxiv.org/html/2404.11374v2) là lý do cân nhắc factorization, không là cam kết số đo trên split này. Không so trực tiếp kết quả random edge/sampled negatives của bài với pair split/full-matrix hiện tại.

Bàn giao: gate decision, val comparison, checkpoint nếu đạt, model card và quyết định giữ/bỏ. Nếu no_go, biên bản cũng là đầu ra hoàn chỉnh của bài toán.

