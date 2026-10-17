# So sánh DSP391m với repo Pancasel/dsp (2026-10-17)

Repo được so: <https://github.com/Pancasel/dsp>, nhánh `main`, commit `0288b52`. Tôi chỉ đọc code và kết quả đã commit, không chạy code của repo đó. Các số đo của DSP391m nêu bên dưới chạy bằng [pancasel_scorer_val.py](pancasel_scorer_val.py), chỉ trên **val**, nên là thăm dò, không phải kết quả chọn model.

## 1. Hai repo giải hai bài toán khác nhau

| | Pancasel/dsp | DSP391m (v3) |
|---|---|---|
| Bài toán | App chat cảnh báo tác dụng phụ cho đơn ≥ 3 thuốc | Benchmark xếp hạng 963 nhãn cho một cặp thuốc |
| Đầu ra | Tier 1 (đã ghi nhận) / Tier 2 (protein đích chung) / Tier 3 (giả thuyết qua cầu PPI); tối đa 10 tác dụng phụ "nghiêm trọng" | Điểm 963 nhãn, top-k, các metric AP/NDCG |
| Mô hình | Luật + thống kê đếm, LLM giải thích (1 request, có validator) | B0 tần suất, DistMult |
| Dữ liệu | Dùng cả `bio-decagon-mono`; 1.317 nhãn ở UI | 963 nhãn (≥ 500 dòng), split cặp đóng băng 70/10/20 |
| Đánh giá | A1–A6, E1–E6, seed 0, không có CI | Evaluator chung, paired bootstrap, search đăng ký trước, khóa test |
| Sản phẩm | Streamlit, nhận biệt dược Việt Nam, tiếng Việt, đồ thị pyvis | Chưa có demo (plan 07) |

Hai repo bổ sung cho nhau: phía họ có nhiều thứ cho sản phẩm và giao diện, phía mình có giao thức đánh giá chặt hơn.

## 2. Điểm mạnh của Pancasel nên học hoặc tái dùng

- **Tên thuốc:** 645/645 thuốc có tên generic, cùng 87 dòng override có ghi bằng chứng. Ví dụ CID005311039 được đổi thành Caspofungin, trong khi bảng của mình còn để "Gaspofungin Impurity F"; Rapamycin được chuẩn hóa thành Sirolimus. Mình còn 129 tên pending và ít nhất 8 tên sai rõ. Có thể nhập bảng của họ làm **ứng viên có nguồn**, nhưng vẫn để trạng thái `needs_review`, vì đó là bảng do người hoặc agent sửa tay, chưa có dược sĩ duyệt. Một số synonym còn lẫn tạp chất ("Amikacin EP Impurity D" nằm dưới Kanamycin), nên không coi là đã duyệt.
- **Mức độ nghiêm trọng:** ánh xạ tên nhãn sang danh sách Important Medical Event của EMA (MedDRA), loại các nhãn kiểu chỉ định hoặc bệnh nền (ung thư, thai sản, bệnh mạn tính). Cách này giải quyết đúng vấn đề lô 20 ca của mình đã thấy (cụm nhãn thai sản ở decline-01, nhãn chung chung đứng đầu B0). Có thể dùng làm cờ hiển thị trong demo, không dùng làm nhãn huấn luyện.
- **Resolver và biệt dược Việt Nam:** 123 biệt dược, resolver được đánh giá (98,6% trên 71 input), không tự nhận khi chưa chắc. Hữu ích nếu demo nhận tên thay vì ID.
- **Kết quả âm được báo trung thực:** A2 cho thấy cầu protein gần như ngẫu nhiên (AUROC 0,54) và Tier 3 chỉ là giả thuyết. Kết quả này khớp với nhận định của mình về target/PPI.
- **Kiểm tra faithfulness (A1) và validator LLM (A4):** đầu ra được đối chiếu lại với CSV gốc. Đây là mẫu tốt nếu sau này làm nhánh RAG/LLM (plan 08).

## 3. Điểm cần cẩn thận ở Pancasel

- **A3 (AUROC 0,951) không so được với Decagon hay với mình.** Repo chia ngẫu nhiên 10% **cạnh** của từng nhãn, nên các nhãn khác của cùng cặp test vẫn nằm trong train. Mỗi dương đi với một cặp âm ngẫu nhiên, và phần lớn cặp âm là cặp chưa từng có dữ liệu (69% số cặp), tức là âm dễ. Baseline độ phổ biến đã đạt 0,908. Chính README của họ cũng ghi là "không kết luận là tốt hơn GCN". Không nên trích 0,951 như một kết quả dự đoán.
- **E4 (P@10 0,507):** leave-one-pair-out, chỉ trên các cặp mà cả hai thuốc có target, xếp trong 1.317 nhãn. Gần với P@10 của mình (B0 alpha0 đạt 0,501 trên val), nhưng khác tập cặp, khác vocab và gần như dùng toàn bộ dữ liệu làm train. Chỉ coi là tham chiếu.
- **Tier 2 "khuếch đại":** không xử lý panel target rộng. 83/284 thuốc có hơn 100 target và dùng chung panel khoảng 158 gene GPCR, nên "protein đích chung" sẽ bật hàng loạt. Code chỉ lọc hub PPI, không lọc panel. Ngoài ra, gọi là "khuếch đại" là một claim mà dữ liệu Decagon không chứng minh được (quyết định 2026-10-08).
- Một seed, không có CI; trọng số xếp hạng (recurrence, idf, serious…) đặt tay và được chỉnh theo A5 (26 ca kinh điển), nên A5 không phải tập đánh giá độc lập.

## 4. Phát hiện cho DSP391m: bộ chấm của họ thắng macro AP trên val của mình

Cùng split `pair_70-10-20_s391`, cùng evaluator, đếm chỉ trên train, 6.347 cặp val × 963 nhãn:

| Bộ chấm | Macro AP | Micro AP | Pair AP | P@10 | NDCG@10 |
|---|---:|---:|---:|---:|---:|
| Pancasel `graph`: 1e6·[cả hai thuốc có nhãn] + count_A + count_B | **0,3183** | 0,3697 | 0,3376 | 0,4752 | 0,4977 |
| Pancasel `graph_norm`: count / tổng cạnh của thuốc | 0,1774 | 0,2737 | **0,3649** | **0,5086** | **0,5330** |
| B0 alpha0 (backend demo) | 0,2714 | 0,3508 | 0,3546 | 0,5009 | 0,5258 |
| B0 alpha100 (mốc macro AP) | 0,2890 | 0,3131 | 0,3237 | 0,4637 | 0,4869 |
| DistMult d128 seed 391 | 0,2863 | 0,3759 | 0,2983 | 0,4041 | 0,4128 |
| Ablation: count thô | 0,2822 | 0,3548 | 0,3261 | 0,4729 | 0,4956 |
| Ablation: chỉ bậc A × bậc B (mọi nhãn như nhau) | 0,1704 | 0,1548 | 0,0749 | 0,1098 | 0,1341 |
| **Ablation: B0 alpha0 × (bậc A + bậc B)** | **0,3164** | **0,3834** | 0,3546 | 0,5009 | 0,5258 |

Bậc = số cặp train của thuốc.

Diễn giải:

- B0 của mình chuẩn hóa theo số cặp của thuốc. Cách đó **xóa tín hiệu bậc**: thuốc có nhiều cặp thì mỗi cặp của nó có nhiều nhãn hơn. Macro AP xếp hạng các cặp *trong một nhãn*, nên rất nhạy với tín hiệu này. Riêng bậc thôi (cùng một điểm cho mọi nhãn) đã đạt macro AP 0,170, gấp đôi popularity.
- Nhân B0 alpha0 với `bậc A + bậc B` chỉ đổi thang điểm giữa các cặp. Thứ tự nhãn trong từng cặp giữ nguyên, nên NDCG@10 không đổi (0,5258), trong khi macro AP tăng +0,045 và micro AP vượt cả DistMult. **Đánh đổi macro AP và NDCG mà mình thấy giữa alpha0, alpha100 và DistMult phần lớn đến từ việc thiếu tín hiệu bậc của cặp, không phải đánh đổi bắt buộc.**
- Hệ quả: các mốc hiện tại (alpha100 cho macro AP) là baseline yếu hơn mức nên có. DistMult "ngang alpha100" thực ra thua một baseline đếm đơn giản khoảng 0,03 macro AP.
- Cảnh báo: các số này **đã nhìn val** và chưa có CI. Biến thể nhân bậc được nghĩ ra sau khi xem kết quả, dù không có tham số nào để chỉnh. Nếu dùng, phải đăng ký như một baseline mới trước khi lock; test vẫn chưa mở nên test sẽ cho ước lượng không lệch.

## 5. Đề xuất (chờ người dùng quyết)

1. Đăng ký **B0 alpha0 × bậc cặp** làm baseline/ứng viên mới (một dòng code trong `models/b0.py`, không có tham số), cùng paired compare 1.000 resample với alpha0, alpha100 và DistMult trên val. Theo plan 08, việc này dùng luôn suất "một mở rộng" thay cho E1, hoặc nếu muốn giữ E1 thì E1 nên lấy base là biến thể này. Hai lựa chọn này cần người dùng chọn trước khi đăng ký.
2. Báo cáo phải ghi rằng một baseline đếm đơn giản (lấy từ repo của bạn cùng nhóm) mạnh hơn các mốc ban đầu, và search DistMult v1 đã được so với mốc yếu hơn.
3. Demo: nhập tên thuốc của Pancasel làm ứng viên (có nguồn, `needs_review`) và nhãn IME làm cờ "nghiêm trọng". Không đổi trạng thái thành đã duyệt.
4. Không dùng A3 0,951 hay Tier 2 "khuếch đại" của họ trong báo cáo chung nếu chưa đổi giao thức.
