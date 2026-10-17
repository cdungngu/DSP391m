> **HẾT HIỆU LỰC HƯỚNG DẪN (v2.1).** Giữ để truy vết lịch sử. Dùng [bộ dự đoán cặp v3](../du_doan_cap/00_Dieu_phoi_va_ra_soat.md) và [kế hoạch tổng](../Ke_hoach_trien_khai.md). Các cổng duyệt và thứ tự bên dưới không áp dụng cho lõi v3.

# 08 — B0 và giao thức dự đoán

Ngày: 2026-10-17 · Chủ trì: dự đoán · Phụ thuộc [03](03_Snapshot_DataView_va_chong_ro_ri.md).

## 1. Hiện trạng và ý nghĩa kết quả

models/b0.py và evaluate.py đã có; test_evaluate.py tồn tại. Artifact [B0 val](../../results/val/b0_per_drug.json) ghi 6.347 cặp × 963 nhãn, macro AP 0,2714308716; micro AP 0,3507798529; macro AUROC 0,8360128228. Đó là kết quả lưu sẵn, không chạy lại trong phiên viết plan.

Split chính thức giữ cặp có nhãn; không chứng minh generalization sang mọi cặp chưa từng báo cáo. Macro AP đo xếp hạng cặp theo nhãn, không trực tiếp chứng minh top-10 outcome của mỗi đơn hữu ích.

## 2. Định nghĩa và hợp đồng score

N_d = số cặp train phân biệt chứa d; n_de = số cặp đó có e.
p_e = số cặp train có e / số cặp train.
f(d,e)=n_de/N_d; nếu N_d=0 dùng p_e.
score(A,B,e)=f(A,e)+f(B,e), thuộc [0,2], **không phải xác suất**.

ScoreResult giữ effect CUI/order, score, per-drug counts/denominators, model_config_hash, split_hash. Không gọi n_de/N_d là tỷ lệ người dùng thuốc bị biến cố. Chỉ research serializer được trả record này.

## 3. Giao thức chính giữ nguyên

D1–D5: vocab 963 cố định, pair split 70/10/20 seed391, score toàn ma trận, vắng nhãn là assumed negative, macro AP chính. Chính sách xử lý label không có dương: loại khỏi macro AP và báo số label; AUROC chỉ có hai lớp. Khi không có label hợp lệ trả null có reason, không NaN JSON.

Kiểm tra thứ tự bằng effect_cui/effect_idx, không chỉ label_idx số học. Bootstrap theo cặp; dùng cùng resample indices khi so hai model. Lưu seed và số bootstrap. 100 resamples hiện có là sơ bộ; báo cuối dùng 1.000 nếu tài nguyên cho phép, không dùng CI làm chứng minh clinical efficacy.

## 4. Thí nghiệm E08

- Popularity và per_drug là baseline bắt buộc.
- Smoothing: f_alpha=(n_de+alpha*p_e)/(N_d+alpha); thử alpha={0,5,20,100}. Alpha0 phải khớp B0 hiện có, kể cả fallback N_d=0.
- Chọn theo macro AP val; hòa trong 0,001 chọn alpha nhỏ hơn. Báo paired bootstrap delta, không chỉ hai CI riêng.
- Bổ sung mean AP theo từng cặp, Precision@10/Recall@10/NDCG@10 với observed labels; gọi rõ metrics này vẫn chịu nhãn thiếu.
- Phân tầng degree thuốc thấp/cao và có/không target.
- So sánh 963 với 959 nhãn trên cùng validation như sensitivity analysis; không thay split hoặc benchmark chính.

B0 có tham số được chọn trên val vẫn là estimator thống kê có model selection; không gọi là “không học gì từ dữ liệu”.

## 5. Kiểm thử bắt buộc

- [ ] Fixture tính tay 3–4 thuốc/nhãn: counts, denominators, popularity và fallback.
- [ ] Đảo A/B giữ score; input indices không tồn tại bị từ chối.
- [ ] Train-only labels; thay val/test không đổi fitted B0.
- [ ] Column reorder theo CUI bị phát hiện; empty/one-class evaluation có trạng thái đúng.
- [ ] AP xử lý ties khớp sklearn; bootstrap tái lập theo seed.
- [ ] Lưu results theo run_id, không ghi đè val artifact cũ khi thử cấu hình mới.

## 6. Cổng và trình tự

Bổ sung contracts/tests → val-only sensitivity → chọn baseline cấu hình → khóa config → chuyển [13](13_Cong_M_va_B2_co_dieu_kien.md). Không chạy test trong bước này. Chất lượng điểm chưa đủ để hiển thị B0 trong consumer; lựa chọn người dùng đã giữ nó ở chế độ nghiên cứu.

Ước lượng 1–2 ngày công; không cần GPU. Không cần chạy lại val đã có chỉ để cập nhật ngày.
