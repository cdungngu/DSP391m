# 04 — Baseline và kiểm tra mô hình chỉ học tần suất

Phụ thuộc: [03](03_Danh_gia_va_khoa_test.md). Tái sử dụng models/b0.py và b0_experiment.py.

## Mốc đã có

Val macro AP: popularity khoảng 0,0749; B0 gốc 0,271431; smoothing alpha100 0,288953. Alpha chọn từ {0,5,20,100}, ưu tiên alpha nhỏ nhất trong 0,001 so tốt nhất. Đây là val, chưa phải final test. [Artifact smoothing](../../results/experiments/2026-10-17_b0_smoothing_v1.json) chưa có paired CI hoặc per-pair top-k.

## Định nghĩa để tái lập

N là số cặp train; N_d là số cặp train chứa d; n_de là số cặp đó có nhãn e; p_e=n_e/N.
f_alpha(d,e)=(n_de+alpha*p_e)/(N_d+alpha).
Nếu N_d=0 dùng p_e, kể cả alpha=0.
B0(A,B,e)=f_alpha(A,e)+f_alpha(B,e), thuộc [0,2].

Popularity trả p_e cho mọi cặp. B0 dùng thông tin từng thuốc, không có thành phần riêng về cách phối hợp hai thuốc. Vì vậy thắng B0 giúp kiểm tra lợi ích mô hình quan hệ, nhưng chưa chứng minh học cơ chế sinh học.

## Công việc cụ thể

1. Đưa popularity, alpha0 và alpha100 qua cùng Predictor adapter.
2. Gắn config/alpha vào model ID và hash; tránh mọi alpha cùng tên b0_per_drug gây ghi đè.
3. Bổ sung các metric của file03 trên cùng val, cùng ID order.
4. Lưu baseline release và scores dùng paired comparison.
5. Phân tầng train degree thấp/trung/cao, nhãn hiếm/trung/phổ biến và target coverage.
6. Chọn 20 cặp error-analysis bằng quy tắc file06, không chọn toàn case đẹp.

Không mở lại lưới alpha chỉ vì alpha100 nằm biên rồi thử mãi. Lưới đã chạy là ngân sách baseline hiện tại; mọi mở rộng sau đó phải ghi như thí nghiệm riêng trước final.

## Phân tích shortcut

So top-10 của cặp với top-10 từng thuốc và popularity: overlap cao + ít cải thiện trên B0 gợi ý mô hình chủ yếu học tần suất. Báo AP/NDCG theo degree thấp để tránh kết luận từ các thuốc nhiều báo cáo. So delta từng nhãn; nhãn bệnh nền/chỉ định giữ nguyên benchmark nhưng ghi ví dụ đáng ngờ, không gọi chúng là ground truth cơ chế.

Thí nghiệm phụ rẻ: hoán vị partner trong một tập truy vấn val cố định, chỉ như diagnostic độ nhạy score; không chấm các cặp mới bằng nhãn cặp cũ. Kết quả score thay đổi không tự chứng minh tương tác được học.

## Nghiệm thu

- [ ] Alpha0 tái tạo số cũ trong tolerance ghi rõ.
- [ ] Popularity và B0 đối xứng, fit train-only, fallback đúng.
- [ ] Bảng val mới có macro/micro AP, per-pair AP, top-k, CI delta.
- [ ] Artifact không ghi đè E08 cũ; metadata đủ nguồn/split/alpha.
- [ ] Không dùng CI đã lưu cho B0 gốc như CI của alpha100.

Bàn giao: baseline comparison và model release làm đối chứng mạnh nhất. B0 alpha100 là baseline tham chiếu mặc định cho quyết định DistMult.

