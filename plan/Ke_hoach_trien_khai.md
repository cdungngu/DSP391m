# Kế hoạch triển khai dự án — lộ trình sau phân tích

**DSP391m · Group 8** · _Cập nhật lần cuối: 2026-10-10_ · Trạng thái: **đề xuất, chưa chốt**

## 0 Cách đọc file này

File này trả lời ba câu hỏi: **làm gì trước, làm gì sau, và tại sao**. Nó tổng hợp hai nguồn:

- **Ý tưởng ban đầu** của nhóm: `docs/submission/Report_1_Introduction.docx`, `method_rp2.docx`, `report.pdf`.
- **Phân tích và đánh giá** ngày 08/10, cùng phần kiểm chứng lại ngày 10/10: `analysis/2026-10-08/Bao_cao_danh_gia_huong_trien_khai.md`. Đây là nơi chứa bằng chứng chi tiết, số liệu và nguồn [S01–S34].

Đây là **tài liệu sống**. Khi nhóm chốt hoặc đổi một quyết định, sửa file này và ghi vào *Nhật ký thay đổi* ở cuối. Trạng thái tổng của dự án và nhật ký quyết định nằm trong `CLAUDE.md`. Trong file này, mọi mục ghi **(đề xuất)** đều chưa được nhóm hoặc giảng viên xác nhận.

---

## 1 Tóm tắt một trang

**Hướng đi chính (đề xuất):** làm **A trước, sau đó B**. Nếu còn thời gian thì làm **đúng một** hướng mở rộng.

```
 GĐ0 Chốt phạm vi ──► GĐ1 Nền dữ liệu ──► GĐ2 Mốc A ──► GĐ3 Baseline B ──► GĐ4 Giải thích ──► GĐ5 Đánh giá ──► GĐ6 Báo cáo
  (trả lời 4 câu hỏi,   (ETL, split theo     (tra cứu       (dự đoán theo     (truy xuất có     (ablation,       (sửa claim,
   hỏi giảng viên)       cặp, chống rò rỉ)    bằng chứng,    cặp: B0→B1→B2)    nguồn, verifier,  seed, latency)   demo)
                                              demo sớm)                        abstain)
        │                     │                   │                │
     [cổng]                [cổng]              [cổng]           [cổng]
  phạm vi được duyệt   giao thức đánh giá   demo chạy được,   B0 + một trong
  (GĐ1 ETL được chạy   đã chốt; không giao  báo đúng phần     B1/B2 tái lập
   song song)          cặp; tách 2 chế độ   thiếu dữ liệu     qua 3 seed
                                                                   │
                                                                   └──► (tùy chọn, chọn MỘT) B3 GNN/TIP · cold-start · C HODDI · D nguồn cơ chế
```

- **A — Tra cứu và tổng hợp bằng chứng cho đơn thuốc.** Với mỗi cặp thuốc trong đơn, lấy các tác dụng phụ đã ghi nhận, gộp lại và trình bày có nguồn.
- **B — Dự đoán tác dụng phụ theo cặp bằng mô hình nhẹ, cộng giải thích có nguồn.** Đơn nhiều thuốc được tổng hợp từ các cặp.

**Ba lý do chính:**

1. **Dữ liệu Decagon chỉ có nhãn theo cặp.** Vì vậy không thể chứng minh "tác dụng phụ chỉ xuất hiện khi đủ cả 3 thuốc". Lời hứa nên là "dự đoán theo cặp, tổng hợp cho đơn".
2. **Tra cứu thuần (A) chỉ phủ một phần các cặp trong đơn.** Chỉ 30,6% cặp thuốc có nhãn. Với đơn 3 thuốc ngẫu nhiên, 57% có ít nhất một cặp có nhãn, nhưng chỉ khoảng 10% có nhãn cho cả 3 cặp. A trả lời được phần đã ghi nhận; B bổ sung bài toán dự đoán cho các nhãn và cặp chưa quan sát. Việc B cần thiết đến mức nào còn phụ thuộc yêu cầu môn học (GĐ0) và kết quả thực nghiệm.
3. **Nhánh suy luận cơ chế qua target/PPI thiếu dữ liệu.** Chỉ 284/645 thuốc có target, và chỉ khoảng 8,6% bộ 3 thuốc có đủ target. Nhánh này chỉ nên là *bằng chứng bổ sung khi có*, không phải xương sống của hệ thống.

---

## 2 Xuất phát điểm: ý tưởng ban đầu

Report 1 và method đặt ra bốn trụ cột:

| Trụ cột | Nội dung ban đầu |
|---|---|
| Graph RAG thuần | Truy xuất subgraph (drug → target → PPI → target → drug cùng cạnh tác dụng phụ đã biết), serialize thành text rồi đưa cho LLM. **Không huấn luyện mô hình**; GNN là future work. |
| Đơn k ≥ 3 thuốc | Hứa dự đoán tác dụng phụ cho đơn từ 3 thuốc trở lên, xem đây là khoảng trống so với các phương pháp theo cặp. |
| Ba Tier đầu ra | Tier 1: known pairwise. Tier 2: amplified (target chung của ≥3 thuốc). Tier 3: newly emergent (bridge PPI giữa hai thuốc, chưa có nhãn). |
| LLM qua API | Một lần gọi API, ưu tiên độ trễ thấp; lấy DDI-GPT làm baseline tham chiếu. Cắt protein hub theo một ngưỡng bậc. |

Ý tưởng này **có định hướng tốt**: bài toán quan trọng, dữ liệu chuẩn, Graph RAG hợp lý, và việc kiểm tra path chống bịa đặt là một điểm hay. Vấn đề nằm ở chỗ **lời hứa vượt quá những gì dữ liệu cho phép chứng minh**.

---

## 3 Phân tích đã thay đổi điều gì

### 3.1 Phát hiện, số liệu và hệ quả

| Phát hiện | Số liệu (đã kiểm chứng) | Hệ quả cho thiết kế |
|---|---|---|
| Nhãn chỉ có theo cặp | Mỗi cạnh combo nối đúng 2 thuốc | Không có nhãn để kiểm chứng tương tác bậc 3. Đổi lời hứa thành "theo cặp, tổng hợp cho đơn". |
| Nhãn cặp rất thưa | 63.473 / 207.690 cặp có nhãn (30,6%); bộ 3 ngẫu nhiên: 57% có ≥1 cặp có nhãn, khoảng 10% có đủ cả 3 cặp | A chỉ phủ một phần: đơn 3 thuốc ngẫu nhiên có 57% trường hợp có ít nhất một cặp có nhãn (trung vị 24 dòng nhãn), nhưng chỉ khoảng 10% có đủ nhãn cho cả 3 cặp. B bổ sung phần dự đoán cho nhãn chưa quan sát. |
| Thiếu target | 284/645 thuốc (44,0%) có target; `targets-all` không cải thiện | Nhánh cơ chế phải hỗ trợ trả về "chưa đủ bằng chứng". |
| Tier 2 hầu như không kích hoạt | Đơn 3 thuốc: 8,6% có đủ target; 0,8% có target chung của ≥3 thuốc | Tier 2 không phải tính năng dùng được trên thực tế. |
| Target bất thường | `CID000000271` (calcium cation) có 2.840 target | Cần xử lý ngoại lệ và giới hạn số path. |
| PPI không có dấu | 715.612 cạnh, không có kích hoạt/ức chế; bậc trung vị 33, lớn nhất 2.519 | Một đường PPI không chứng minh được cơ chế; cắt hub cứng có thể làm mất protein quan trọng. |
| Số liệu khác bài gốc | 1.317 nhãn (963 nhãn nếu lọc ≥500 dòng), 19.081 gene | Báo cáo phải ghi đúng snapshot đang dùng, không chép con số 964 / 19.085 của bài gốc. |
| HODDI có shortcut | Một quy tắc chỉ dựa trên "thuốc đã thấy ở mẫu dương" đạt 86,9% accuracy (86,2% với 3–5 thuốc) | HODDI chưa dùng được làm đường chính; cần negative khó hơn. |
| DDI-GPT khác bài toán | Theo bảng LR: phân loại nhị phân 63.437 cặp dương / âm (chưa xác minh toàn văn) | Không so trực tiếp với bài toán 963 nhãn. Baseline đúng là Decagon, TIP và tensor factorization. |
| Literature review có lỗi | Nhiều link sai hoặc trỏ sang bài khác (mục 14 báo cáo đánh giá) | Sửa trước khi viết related work. |

### 3.2 Giữ, sửa và bỏ so với ý tưởng ban đầu

| | Thành phần | Ghi chú |
|---|---|---|
| **Giữ** | Graph RAG trên Decagon | Vẫn là phần giải thích của hệ thống |
| **Giữ** | LLM qua API, một lần gọi | Thêm cache và đường trả kết quả theo template khi API lỗi |
| **Giữ** | Giao diện nhận 3–5 thuốc | Ghi rõ là "tổng hợp theo cặp" |
| **Giữ** | Kiểm tra path trong subgraph | Mở rộng thành verifier đầy đủ hơn (mục GĐ4) |
| **Sửa** | Ba Tier | Thành hai trường độc lập: `status` (quan sát / dự đoán / thiếu dữ liệu) và `evidence_type` |
| **Sửa** | Cắt hub theo ngưỡng cứng | Thành phạt mềm theo bậc, giới hạn số path, có ablation so sánh |
| **Sửa** | "Không huấn luyện mô hình" | Thêm mô hình nhẹ theo cặp (B0–B2) |
| **Sửa** | "Clinical decision-support" | Thành "research prototype" |
| **Sửa** | "Low latency" | Thành mục tiêu cần đo (p95) |
| **Sửa** | DDI-GPT làm baseline | Chuyển thành related work; baseline là các mô hình cùng bài toán |
| **Bỏ** | "Amplified effect", "arising only from the combined regimen" | Dữ liệu không thể chứng minh |

---

## 4 Các hướng có thể đi và lý do chọn

| Hướng | Làm gì | Chứng minh được | **Không** chứng minh được | Chi phí | Khi nào chọn |
|---|---|---|---|---|---|
| **A** Tra cứu bằng chứng | Lookup cạnh đã biết theo cặp, gộp cho đơn, LLM/template tóm tắt có nguồn | Truy xuất đúng, đầy đủ, giải thích trung thực | Dự đoán cái chưa biết | Thấp (CPU + API) | Luôn làm, là **mốc đầu tiên** |
| **B** Dự đoán theo cặp + giải thích | Mô hình nhẹ xếp hạng 963 nhãn cho cặp chưa thấy; giải thích có nguồn | Dự đoán trên nhãn giữ lại, có baseline và metric | Tương tác bậc cao, nhân quả | Trung bình (CPU, có thể thêm 1 GPU) | **Hướng chính** đề xuất |
| **C** Tổ hợp 3–5 thuốc trên HODDI | Mô hình tập hợp (DeepSets...) với negative khó và split theo thời gian | Liên hệ tổ hợp với biến cố được báo cáo | Hiệp đồng dược lý | Cao (làm sạch, negative, split) | Chỉ khi có thêm thời gian và muốn trọng tâm nghiên cứu |
| **D** Suy luận cơ chế có giới hạn | Thêm ChEMBL/DailyMed để có chiều tác động, áp dụng cho danh mục thuốc nhỏ | Giải thích sâu hơn | Phủ rộng | Cao (cần người đọc dược học) | Khi có người kiểm tra chuyên môn |
| **E** GNN lớn + nhiều LLM agent | Pipeline nghiên cứu phức tạp | — | Khó truy nguyên lỗi | Rất cao | Không nên làm ở đồ án này |

**Kết luận (đề xuất): B, với A làm mốc đầu.**

- **Vì sao A trước:** rẻ, có demo sớm, và là phương án dự phòng nếu B trễ. Khung đầu ra của A (schema, tổng hợp theo cặp, trình bày nguồn) được B dùng lại nguyên vẹn.
- **Vì sao không dừng ở A:** A có độ phủ không đầy đủ trên các cặp trong đơn (khoảng 69% cặp không có nhãn) và chỉ trả lời được những gì đã ghi nhận. B bổ sung một bài toán dự đoán nhãn chưa quan sát, có nhãn, baseline và metric. Mức độ cần thiết của B còn phụ thuộc yêu cầu môn học (GĐ0); nếu môn học không đòi hỏi huấn luyện, A cộng phần đánh giá giải thích vẫn là một đồ án hợp lệ.
- **Vì sao B chứ không phải C:** B có nhãn sạch, baseline đã có trong văn liệu, và chạy được trên CPU. C có rủi ro dữ liệu đã được đo (shortcut 86%), nên chỉ nên là nhánh phụ có cổng dừng rõ ràng.

---

## 5 Lộ trình theo giai đoạn

Mỗi giai đoạn chỉ bắt đầu khi **cổng** của giai đoạn trước đã đạt. Thứ tự này được chọn để **phần nào phụ thuộc thì làm sau, phần nào làm sai sẽ hỏng mọi thứ thì làm trước**. Ngoại lệ duy nhất: **GĐ1a được chạy song song với GĐ0**, vì nó không phụ thuộc vào quyết định phạm vi.

### GĐ0 — Chốt phạm vi

- **Mục tiêu:** biết chắc nhóm được phép và cần làm gì.
- **Việc chính:**
  1. Trả lời 4 câu hỏi mở: môn học có bắt buộc huấn luyện mô hình không; thời gian, phần cứng và ngân sách API; Report 1 đã nộp chưa; có người kiểm tra nội dung dược học không.
  2. Trình bày với giảng viên việc điều chỉnh phạm vi, kèm các số liệu ở mục 3.1.
  3. Chốt **giao thức đánh giá** ở mục 5.1. Phần này phải xong trước khi đóng băng split (GĐ1b).
- **Vì sao đứng đầu:** câu trả lời quyết định làm B hay chỉ làm A, và có cần sửa Report 1 không.
- **Sản phẩm:** dòng quyết định trong `CLAUDE.md`; cập nhật trạng thái của file này.
- **Cổng:** phạm vi được nhóm và giảng viên chấp nhận; mục 5.1 chuyển từ "đề xuất" sang "đã chốt".

### 5.1 Giao thức đánh giá — chốt trước khi đóng băng split

Đây là các mặc định **(đề xuất)**. Mục đích là để B0, B1 và B2 được chấm trên **cùng một** tập và cùng một quy tắc; nếu không, bảng AP/AUROC sẽ không so sánh được.

| Quyết định | Đề xuất | Lý do |
|---|---|---|
| Vocabulary nhãn | **Danh sách cố định 963 nhãn** (≥500 dòng trên toàn snapshot), chốt và lưu thành file trước khi split. Báo cáo thêm, ở dạng phân tích độ nhạy, số nhãn khi áp ngưỡng chỉ trên train | Trùng quy ước của Decagon và tensor factorization nên so sánh được với văn liệu. Danh sách chỉ dùng tần suất nhãn, không dùng danh tính cặp test; phải công bố rõ việc này |
| Tập cặp đánh giá chính | Các cặp có ít nhất một nhãn trong 963 nhãn. Chia 70/10/20 theo cặp | Đây là những cặp có nhãn đã ghi nhận; mọi nhãn của một cặp nằm cùng một split |
| Nhãn chưa quan sát khi **chấm điểm** | Với mỗi cặp val/test, chấm **toàn bộ 963 nhãn**. Nhãn có ghi nhận là 1; nhãn vắng mặt là 0, gọi là **"âm giả định"**, không phải "an toàn". **Không** lấy mẫu âm khi chấm | Mọi baseline được chấm trên cùng một ma trận cố định, không phụ thuộc cách mỗi mô hình lấy mẫu |
| Nhãn chưa quan sát khi **huấn luyện** | B0: đếm trên train. B1: BCE đa nhãn đầy đủ trên các cặp train, ô vắng mặt là âm giả định. B2: lấy mẫu âm bằng cách thay nhãn (hoặc một thuốc) của bộ ba dương, lọc bỏ các bộ ba dương đã biết trong train, **tỷ lệ cố định trong config** (khởi đầu 1:1, thử 1:5 trên val) | Mỗi mô hình huấn luyện theo cách phù hợp với nó, nhưng tất cả đều được chấm bằng một bộ chấm điểm chung |
| Metric | Macro AP (trên các nhãn có ít nhất 1 dương trong test), micro AP, AUROC; kèm kết quả theo nhóm tần suất nhãn và theo thuốc có / không có target | AP phù hợp với ma trận nhãn thưa |
| Dùng validation và test | Chọn mô hình và hyperparameter **chỉ** trên val. Test chạy **một lần** khi đã khóa cấu hình | Tránh tune trên test |
| Cặp hoàn toàn chưa ghi nhận (khoảng 69% còn lại) | **Không** đưa vào metric chính. Khi báo cáo phải ghi rõ: kết quả chính là "dự đoán nhãn cho cặp đã có báo cáo nhưng bị giữ lại", **không phải** khả năng dự đoán cho cặp chưa từng được ghi nhận. Nếu muốn, có thể thêm thí nghiệm phụ "cặp có được báo cáo hay không" và nêu rõ đây là bài toán positive–unlabeled | Cặp vắng mặt không có nhãn âm thật nên không thể chấm như thể có |

### GĐ1 — Nền dữ liệu

**GĐ1a — bắt đầu ngay, song song với GĐ0:**

- Dựng môi trường (`requirements` khóa phiên bản) và khung `src/`.
- ETL **chỉ đọc** ba CSV Decagon gốc, xuất Parquet, kèm manifest SHA256. Tái dùng logic đếm và kiểm tra trong `analysis/2026-10-08/audit_data.py`.
- Định nghĩa schema; kiểm tra chất lượng dữ liệu (số đếm, trùng lặp, độ phủ). Kết quả phải khớp mục *Sự thật về dữ liệu* trong `CLAUDE.md`.
- **Ánh xạ ID sang cấu trúc phân tử** (phụ thuộc của B1): STITCH CID → PubChem CID → SMILES và InChIKey qua PUG REST, có cache, rồi parse bằng RDKit.
  - Báo độ phủ: bao nhiêu thuốc có cấu trúc và tạo được fingerprint.
  - Liệt kê các trường hợp mơ hồ (salt, ion, ví dụ CID 271) và các trường hợp không parse được.
  - Lấy luôn tên thuốc để hiển thị.

**GĐ1b — sau khi GĐ0 và mục 5.1 đã chốt:**

- Ghi file vocabulary 963 nhãn; chia tập theo cặp 70/10/20 với seed cố định. Dựng đồ thị và feature huấn luyện **sau** khi chia.
- **Cách ly hai chế độ ở tầng truy cập dữ liệu:**
  - *Evidence mode* đọc toàn bộ snapshot.
  - *Prediction mode* chỉ nhận một "data view" được dựng từ split: chỉ chứa nhãn của train, đã loại **cả val lẫn test**.
  - Code dự đoán và code giải thích **không được** import bảng lookup đầy đủ.
  - Khóa cache gồm `mode`, `split_id` và `snapshot_hash`. Cache của evidence mode không bao giờ được đọc trong prediction mode.
- Test tự động phải kiểm tra:
  - (a) không có cặp nào giao giữa các split;
  - (b) không còn cạnh val/test trong đồ thị train;
  - (c) bộ truy xuất của prediction mode không trả về được nhãn nào của cặp val/test;
  - (d) không có cache hit chéo giữa hai chế độ.
- **Vì sao ở đây:** mọi phần sau đều đọc từ đây. Chia tập muộn, hoặc để hai chế độ dùng chung bảng lookup và cache, là nguồn rò rỉ nhãn khó phát hiện nhất.
- **Sản phẩm:** `src/` có ETL, mapping, split, data view, test; data card ngắn (bao gồm độ phủ cấu trúc).
- **Cổng:** cả 4 test (a)–(d) đạt; hash khớp manifest; đã biết độ phủ cấu trúc.

### GĐ2 — Mốc A: tra cứu bằng chứng (evidence mode)

- **Mục tiêu:** demo end-to-end đầu tiên.
- **Việc chính, theo thứ tự:**
  1. CLI nhận **ID thuốc** → tạo mọi cặp → lookup → gộp theo `effect_id`, giữ `contributing_pairs` và nguồn → xuất theo **template** (không LLM), có báo phần thiếu dữ liệu.
  2. Thêm tên thuốc để nhập và hiển thị.
  3. Thêm bằng chứng target/PPI khi có (giới hạn số path, phạt mềm theo bậc).
  4. Cuối cùng mới thêm **một lần gọi LLM qua API** với schema JSON cố định, mỗi phát biểu trích ID bằng chứng.
- **Phân biệt rõ ba trường hợp, không gộp chung:**

  | Trường hợp | Đầu ra |
  |---|---|
  | Thuốc ngoài vocabulary hoặc tên mơ hồ | Báo lỗi hoặc yêu cầu chọn lại; không xử lý thuốc đó |
  | Cặp không có nhãn đã ghi nhận | `status = thiếu dữ liệu` cho cặp đó; các cặp khác vẫn trả kết quả |
  | Thuốc thiếu target | **Giữ nguyên kết quả lookup**; chỉ ghi vào `missing_data` rằng phần **bằng chứng cơ chế** bị thiếu |

- **Vì sao ở đây:** có sản phẩm chạy được sớm để kiểm tra pipeline và schema. Đây là phương án dự phòng nếu GĐ3–4 trễ, và B sẽ dùng lại schema của bước này.
- **Sản phẩm:** CLI demo; schema đầu ra (`drug_pair`, `effect_id`, `status`, `evidence_ids`, `explanation`, `missing_data`, `contributing_pairs`, …).
- **Cổng:** demo chạy được với các đơn mẫu, và báo đúng phần thiếu dữ liệu ở cả ba trường hợp trên.

### GĐ3 — Baseline dự đoán theo cặp (bắt đầu B)

- **Mục tiêu:** dự đoán 963 nhãn cho các cặp bị giữ lại, theo giao thức ở mục 5.1.
- **Bước đầu tiên:** viết **bộ chấm điểm dùng chung**. Bộ này nhận ma trận điểm (cặp × 963 nhãn) và trả về mọi metric. Mọi mô hình đều đi qua nó.
- **Mốc bắt buộc: B0 + một trong B1/B2.** Mô hình còn lại làm sau, khi mốc này đã chạy ổn.
  - **B0:** tần suất nhãn, và **baseline theo từng thuốc** `score(A,B,e) = f(A,e) + f(B,e)` học từ train.
  - **B2 (đề xuất làm trước):** DistMult hoặc SimplE đã đối xứng hóa, embedding 64–128 chiều. Lý do làm trước: chỉ cần ID thuốc, không phụ thuộc vào phần mapping cấu trúc.
  - **B1:** Morgan fingerprint, ghép `(u+v, |u−v|, u⊙v)`, rồi logistic đa nhãn. Chỉ cam kết lịch cho B1 khi độ phủ cấu trúc ở GĐ1a đã đủ. Thuốc thiếu cấu trúc dùng điểm của B0 làm dự phòng; báo kết quả trên toàn bộ test và riêng trên phần có cấu trúc.
- **Vì sao trước GNN:** các nhãn phổ biến nhất trong Decagon rất chung chung (hạ huyết áp, thiếu máu, buồn nôn...). Giả thuyết cần kiểm tra là phần lớn tín hiệu đến từ từng thuốc riêng lẻ. Nếu mô hình phức tạp không vượt được B0 thì đó là một kết quả đáng báo cáo, không phải thất bại. Tensor factorization đã được báo cáo là nhanh và mạnh trên đúng 963 nhãn này [S04]. Lưu ý: chỉ số của tác giả đo trên random split, không phải pair split.
- **Sản phẩm:** bảng kết quả trên val (để chọn mô hình) và một lần chạy test cuối.
- **Cổng:** B0 + một mô hình tái lập được qua 3 seed; hyperparameter đã khóa trước khi chạy test.

### GĐ4 — Giải thích có nguồn cho dự đoán (prediction mode)

- **Mục tiêu:** đặt điểm dự đoán của B cạnh bằng chứng liên quan, và **nói rõ bằng chứng hỗ trợ được đến đâu**.
- **Nguyên tắc:** một path hợp lệ trong đồ thị chỉ chứng minh quan hệ trong đồ thị, **không** đủ để nói "cặp này gây tác dụng phụ e".
  - Vì vậy kết quả luôn giữ `status = dự đoán`.
  - Trường cơ chế mặc định là **"chưa đủ bằng chứng giải thích cơ chế"**, trừ khi có nguồn trực tiếp nói về đúng outcome đó. Nguồn như vậy chỉ có ở nhánh mở rộng D.
- **Các loại bằng chứng của bản đầu** (chỉ lấy từ data view của train):
  1. Bằng chứng mức thuốc: A (hoặc B) đi cùng e trong bao nhiêu cặp train. Đây cũng là tín hiệu của B0.
  2. Các cặp train tương tự có nhãn e.
  3. Bối cảnh target/PPI khi có, gắn nhãn rõ là "bối cảnh, không phải cơ chế".
- **Việc chính:**
  - Truy xuất có budget: 10–20 path, khoảng 4.000–8.000 input token. Đây là điểm khởi đầu để đo, chưa phải giá trị tối ưu.
  - Không dùng nhãn val/test để chọn path.
  - Verifier kiểm tra: ID có thật; quan hệ và chiều đúng; path liền mạch; bằng chứng thuộc đúng data view; không có câu nào khẳng định quá mức.
  - Cho phép abstain.
- **Vì sao sau GĐ3:** cần có điểm dự đoán thật để giải thích, và cần tách rõ lợi ích đến từ mô hình hay từ phần giải thích.
- **Cổng:** trên một bộ dev khoảng 20 trường hợp (tách khỏi bộ đánh giá cuối), đo **tỷ lệ phát biểu được nguồn hỗ trợ** và **coverage**, đạt mức tối thiểu đã thống nhất từ trước. Chỉ demo chạy được thì chưa đủ để qua cổng.

### GĐ5 — Đánh giá

- **Ba nhóm thí nghiệm, đo riêng:**
  1. **Dự đoán:** macro AP, micro AP, AUROC; kết quả tách theo nhóm tần suất nhãn và theo thuốc có / không có target.
  2. **Truy xuất và giải thích:** citation precision, claim support, abstention coverage. Bộ gán nhãn tay khoảng 50 cặp, hai người chấm độc lập.
  3. **Vận hành:** p50/p95 latency, số token, lỗi API.
- **Ablation:**
  - Với cùng model API: LLM không truy xuất, Graph RAG đơn giản theo ý tưởng gốc, và bản có verifier.
  - So sánh cắt hub cứng với phạt mềm theo bậc.
- **Báo cáo:** mean ± std qua 3 seed; bootstrap theo cặp.

### GĐ6 — Báo cáo và demo

- Sửa các claim trong báo cáo nộp theo mục 9; viết data card và model card; đóng gói demo.
- Báo cáo phải khớp đúng các thí nghiệm đã chạy, không trình bày mục tiêu như kết quả.

### Mở rộng — chỉ chọn MỘT, sau khi GĐ3 đạt cổng

| Nhánh | Điều kiện vào | Điều kiện dừng |
|---|---|---|
| B3 GNN/TIP | B0, B1 và B2 ổn định, còn ≥2 tuần | Không vượt B2 qua nhiều seed thì giữ B2 |
| Cold-start (thuốc mới) | Muốn kiểm tra khả năng tổng quát hóa sang thuốc chưa thấy | Chỉ mô hình có feature ngoại sinh (fingerprint) mới được gọi là inductive |
| C HODDI 3–5 thuốc | Nhóm chủ động chọn trọng tâm nghiên cứu | Không qua được kiểm tra negative hoặc group split thì dừng, quay về B |
| D Nguồn cơ chế (ChEMBL, DailyMed) | Có người đọc dược học | Mapping thuốc không đạt trên danh mục demo thì thu hẹp phạm vi |

---

## 6 Lịch thời gian (ước lượng, chưa phải cam kết)

**Phương án chính, 6 tuần:**

| Tuần | Giai đoạn | Điều kiện kết thúc |
|---|---|---|
| 0 (ngay) | GĐ0 | Phạm vi được duyệt; mục 5.1 đã chốt |
| 1 | GĐ1a (song song GĐ0), rồi GĐ1b | Manifest, độ phủ cấu trúc; giao thức 5.1 chốt; split và 4 test rò rỉ đạt |
| 2 | GĐ2 + bộ chấm điểm + B0 | Demo A báo đúng phần thiếu dữ liệu; B0 chạy qua bộ chấm điểm |
| 3 | GĐ3 | B0 + một trong B1/B2 tái lập được qua 3 seed |
| 4 | GĐ4 (+ mô hình B còn lại nếu kịp) | Đạt ngưỡng claim support và coverage trên bộ dev |
| 5 | GĐ5 | Bảng kết quả kèm độ bất định |
| 6 | GĐ6 | Báo cáo và demo khớp thí nghiệm |

**Biến thể:**

- **Chỉ có 2–3 tuần:** làm GĐ1 rút gọn, rồi GĐ2 (A), rồi đánh giá phần truy xuất và giải thích. Bỏ phần huấn luyện mô hình.
- **Có 8 tuần:** lịch 6 tuần, cộng **một** nhánh mở rộng ở tuần 7–8.

---

## 7 Phân công gợi ý (4 vai trò, chưa gán tên)

| Vai trò | Phụ trách |
|---|---|
| Dữ liệu và mapping | GĐ1, vocabulary, PubChem, data card |
| Mô hình và split | Split, B0–B2, chạy seed |
| Truy xuất và giải thích | Path retrieval, prompt, verifier |
| API, demo và đánh giá | Gọi LLM, cache, demo, harness đo latency và metric |

Cả nhóm cùng chấm bộ giải thích, để tránh tình trạng một người viết prompt rồi tự chấm.

---

## 8 Tiêu chí thành công và tiêu chí dừng

Đây là các mục tiêu nghiệm thu **(đề xuất)**, cần đo, chưa phải kết quả. Nên thống nhất mức tối thiểu với giảng viên **trước khi** nhìn kết quả.

- **Dự đoán:** mô hình bắt buộc (B1 hoặc B2) vượt B0 về macro AP trên test pair split, qua 3 seed, chấm bằng bộ chấm điểm dùng chung theo mục 5.1. Kết quả chỉ được diễn giải là "dự đoán nhãn cho cặp đã có báo cáo nhưng bị giữ lại".
- **Giải thích:** bản có verifier giảm số claim không có nguồn hỗ trợ so với Graph RAG đơn giản trên cùng bộ đánh giá. Luôn báo **cả** tỷ lệ claim được hỗ trợ lẫn coverage; không được loại bớt các trường hợp khó để nâng tỷ lệ.
- **Vận hành:** p95 lookup cục bộ dưới 1 giây; p95 toàn pipeline dưới 15 giây.
- **Quy tắc nâng cấp:** chỉ thêm mô hình phức tạp hơn khi mô hình trước đã tái lập được.
- **Quy tắc dừng:** mô hình phức tạp không vượt baseline nhẹ thì dùng baseline nhẹ và tập trung vào chất lượng giải thích.
- **Không bao giờ:** hiển thị citation không tồn tại, hoặc biến "thiếu dữ liệu" thành kết luận "an toàn".

---

## 9 Những gì cần sửa trong báo cáo nộp (Report 2/3)

| Câu hoặc ý cũ | Sửa thành |
|---|---|
| "predicts … adverse effects for regimens of three or more drugs" | Dự đoán theo cặp, tổng hợp bằng chứng cho đơn 3–5 thuốc |
| "Taking DDI-GPT as the baseline reference" | DDI-GPT là related work (bài toán nhị phân); baseline là tần suất, fingerprint và tensor factorization |
| Ba Tier (known / amplified / emergent) | `status` + `evidence_type` |
| "Training a GNN … is out of scope" | Có mô hình nhẹ theo cặp; GNN là mở rộng tùy chọn |
| "clinical decision-support framework" | "research prototype for drug interaction prediction and evidence review" |
| "minimal inference latency" | Mục tiêu latency đo bằng p95 |
| 645 thuốc / 19.085 protein / 964 nhãn | Ghi riêng "thống kê bài gốc" và "thống kê snapshot": 1.317 nhãn, 963 nhãn sau khi lọc, 19.081 gene |
| Cắt hub theo ngưỡng | Phạt mềm theo bậc, có ablation |
| Related work | Thêm K-Paths, CBR-DDI, tensor factorization, DDI-Ben; sửa các link sai trong LR |

**Cách trình bày gợi ý:** gọi đây là *"điều chỉnh phạm vi dựa trên kiểm toán dữ liệu"* và đưa bảng ở mục 3.1 vào báo cáo. Việc tự phát hiện giới hạn của dữ liệu rồi điều chỉnh cho phù hợp là điểm cộng về phương pháp, không phải điểm trừ.

---

## 10 Rủi ro chính

| Rủi ro | Cách xử lý |
|---|---|
| Giảng viên không chấp nhận đổi phạm vi | Giữ giao diện đa thuốc và Graph RAG; trình bày B như phần bổ sung dựa trên số liệu kiểm toán |
| Rò rỉ nhãn giữa train và val/test | Split trước khi tạo feature; prediction mode chỉ đọc data view của train; khóa cache gồm mode và split; 4 test tự động ở GĐ1b |
| Mỗi baseline được chấm một kiểu | Giao thức 5.1 chốt trước; một bộ chấm điểm dùng chung |
| Thiếu cấu trúc phân tử cho B1 | Đo độ phủ ở GĐ1a; làm B2 trước; B1 dùng B0 làm dự phòng |
| Thiếu target ở 56% thuốc | Giữ kết quả lookup và dự đoán; chỉ đánh dấu phần bằng chứng cơ chế là thiếu; báo coverage theo từng thuốc |
| LLM trả lời quá chắc chắn | Schema cố định, verifier, cho phép abstain, có template dự phòng |
| Mô hình phức tạp không vượt baseline | Chấp nhận baseline nhẹ; báo cáo đây là một phát hiện |
| Thời gian không đủ | A là mốc đã hoàn thành; chỉ làm một nhánh mở rộng |
| Chi phí API | Chạy pilot 50–100 query, có cache, giới hạn số lần retry |

---

## 11 Việc cần làm ngay (tuần này)

- [ ] Cả nhóm thống nhất trả lời 4 câu hỏi mở (GĐ0).
- [ ] Gặp giảng viên, trình bày bảng ở mục 3.1 và đề xuất đổi phạm vi.
- [ ] Sửa các link sai trong `docs/literature/literature-review.xlsx` (danh sách ở mục 14 báo cáo đánh giá).
- [ ] Chốt giao thức đánh giá ở mục 5.1 (vocabulary, tập cặp, nhãn chưa quan sát, quyền đọc dữ liệu của từng chế độ).
- [ ] **GĐ1a, làm ngay song song:** dựng `src/` và môi trường; ETL chỉ đọc, manifest, schema, kiểm tra chất lượng dữ liệu; đo độ phủ cấu trúc phân tử qua PubChem.
- [ ] Chỉ đóng băng split (GĐ1b) sau khi hai mục trên đã chốt.
- [ ] Cập nhật `CLAUDE.md` và file này sau khi chốt.

---

## 12 Nhật ký thay đổi của kế hoạch

| Ngày | Thay đổi |
|---|---|
| 2026-10-10 | Sửa theo review: thêm mục 5.1 (giao thức đánh giá chung, xử lý nhãn chưa quan sát, vocabulary cố định); tách GĐ1a (chạy song song GĐ0) và GĐ1b (cách ly hai chế độ, 4 test rò rỉ); thêm bước mapping cấu trúc cho B1; mốc bắt buộc là B0 + một trong B1/B2 (đề xuất B2 trước); GĐ4 giữ `status = dự đoán`, cổng đo claim support và coverage; tách thiếu target khỏi ngoài vocabulary; sửa lập luận về độ phủ của A theo số đo mới (đơn 3 thuốc: 57% có ≥1 cặp có nhãn). |
| 2026-10-10 | Tạo kế hoạch đầu tiên, tổng hợp từ Report 1/method và báo cáo đánh giá 08/10 cùng phần kiểm chứng 10/10. Toàn bộ ở trạng thái đề xuất. |
