# Kế hoạch triển khai dự án — lộ trình sau phân tích

**DSP391m · Group 8** · _Cập nhật lần cuối: 2026-10-10_ · Trạng thái: **đã chốt (v2)**, thay đổi tiếp theo ghi ở mục 13

## 0 Cách đọc file này

File này trả lời ba câu hỏi: **làm gì trước, làm gì sau, và tại sao**. Nó tổng hợp:

- **Ý tưởng ban đầu** của nhóm: `docs/submission/Report_1_Introduction.docx`, `method_rp2.docx`, `report.pdf`.
- **Phân tích và đánh giá** ngày 08/10 cùng phần kiểm chứng ngày 10/10: `analysis/2026-10-08/Bao_cao_danh_gia_huong_trien_khai.md` (bằng chứng chi tiết, nguồn [S01–S34]).
- **Các quyết định ngày 10/10** (mục 0.1) và thử nghiệm B0 (mục 4).

Đây là **tài liệu sống**. Khi đổi quyết định, sửa file này và ghi vào mục 13. Trạng thái tổng của dự án nằm trong `CLAUDE.md`.

### 0.1 Các quyết định đã chốt (2026-10-10)

| # | Quyết định | Nguồn |
|---|---|---|
| Q1 | Coi đây là **dự án thật, không phải môn học**: không có cổng duyệt của giảng viên; đích là sản phẩm dùng được và đánh giá trung thực | Người dùng |
| Q2 | Thời gian **6 tuần**. API LLM và GPU thuê ngoài khi cần, nên không phải ràng buộc cứng | Người dùng |
| Q3 | **Chưa huấn luyện mô hình ở giai đoạn đầu.** Chỉ huấn luyện nếu phân tích chi phí–lợi ích cho thấy đáng (mục 4) | Người dùng; Claude phân tích |
| Q4 | **Có người bên dược hỗ trợ**, nên nhánh nguồn cơ chế (D) được **nâng từ mở rộng lên lõi** | Người dùng |
| Q5 | Giao thức đánh giá D1–D7 (mục 6.1), cách xử lý thuốc bị gắn cờ, quy trình git | Claude chốt theo ủy quyền của người dùng |

---

## 1 Tóm tắt một trang

**Hướng đi:** xây sản phẩm **tra cứu và giải thích bằng chứng** (A) cộng **nguồn cơ chế có kiểm chứng của dược sĩ** (D) trước, **không huấn luyện mô hình**.

- Phần dự đoán cho cặp chưa có dữ liệu dùng **B0**: đếm tần suất theo từng thuốc. B0 không cần huấn luyện, nhưng đã có tín hiệu thật (AUROC 0,84 trong thử nghiệm).
- **Cuối tuần 3** có một cổng quyết định: chỉ huấn luyện B2 nếu đạt các tiêu chí ở mục 4.4.

```
 Tuần 1            Tuần 2              Tuần 3                    │ Tuần 4               Tuần 5        Tuần 6
 GĐ1b split +      GĐ2 demo tra cứu    GĐ4 giải thích: LLM +     │ Nhánh theo cổng M:   GĐ5 đánh giá  GĐ6 đóng gói
 data view +       (evidence mode)     verifier + abstain;       │ (a) huấn luyện B2    với gold set  demo, báo cáo,
 test rò rỉ        GĐ3 nguồn cơ chế    B0 cho cặp chưa có nhãn   │ (b) mở rộng bằng     của dược sĩ   data card
 (GĐ1a đã xong)    (ChEMBL, DailyMed)  gold set v1 của dược sĩ   │     chứng, giao diện
                                                         [CỔNG M]┘
```

**Ba lý do chính:**

1. **Giá trị sản phẩm nằm ở bằng chứng, không nằm ở điểm số mô hình.** Nhãn Decagon là liên hệ thống kê từ báo cáo tự phát (FAERS/TWOSIDES) và rất chung chung (buồn nôn, thiếu máu...). Với người dùng là dược sĩ, một cảnh báo có nguồn (nhãn thuốc, cơ chế ChEMBL) đáng tin hơn một điểm dự đoán.
2. **B0 đã cho tín hiệu dự đoán mà không cần huấn luyện.** Huấn luyện B2 tốn khoảng 1 tuần công. Lợi ích có thể có (AP còn xa mức trần) nhưng chưa biết lớn đến đâu. Vì vậy quyết định được hoãn tới khi có dữ liệu thật để cân nhắc (mục 4).
3. **Có dược sĩ nên nhánh cơ chế (D) khả thi**, bù đúng điểm yếu lớn nhất của ý tưởng ban đầu: PPI không có dấu, 56% thuốc thiếu target, và LLM dễ bịa cơ chế.

---

## 2 Xuất phát điểm: ý tưởng ban đầu

| Trụ cột | Nội dung ban đầu |
|---|---|
| Graph RAG thuần | Truy xuất subgraph (drug → target → PPI → target → drug cùng cạnh tác dụng phụ đã biết), serialize thành text rồi đưa cho LLM. **Không huấn luyện mô hình**; GNN là future work. |
| Đơn k ≥ 3 thuốc | Hứa dự đoán tác dụng phụ cho đơn từ 3 thuốc trở lên. |
| Ba Tier đầu ra | Tier 1: known pairwise. Tier 2: amplified (target chung của ≥3 thuốc). Tier 3: newly emergent (bridge PPI). |
| LLM qua API | Một lần gọi API, ưu tiên độ trễ thấp; DDI-GPT làm baseline tham chiếu; cắt hub theo ngưỡng bậc. |

Ý tưởng này **có định hướng tốt**, và tinh thần "không huấn luyện, dùng truy xuất và LLM" **được giữ lại** ở v2. Vấn đề nằm ở chỗ **lời hứa vượt quá những gì dữ liệu cho phép chứng minh** (mục 3).

---

## 3 Phân tích đã thay đổi điều gì

### 3.1 Phát hiện, số liệu và hệ quả

| Phát hiện | Số liệu (đã kiểm chứng) | Hệ quả cho thiết kế |
|---|---|---|
| Nhãn chỉ có theo cặp | Mỗi cạnh combo nối đúng 2 thuốc | Không kiểm chứng được tương tác bậc 3. Lời hứa là "theo cặp, tổng hợp cho đơn". |
| Nhãn cặp thưa | 63.473 / 207.690 cặp có nhãn (30,6%). Đơn 3 thuốc ngẫu nhiên: 57% có ≥1 cặp có nhãn, khoảng 10% có đủ cả 3 cặp | Tra cứu chỉ phủ một phần. Cặp chưa có nhãn cần B0 (dự đoán) hoặc nguồn ngoài (D). |
| Thiếu target | 284/645 thuốc (44,0%) có target | Cần nguồn cơ chế khác (ChEMBL), và trả về "chưa đủ bằng chứng cơ chế" khi vẫn thiếu. |
| Tier 2 hầu như không kích hoạt | Đơn 3 thuốc: 8,6% có đủ target; 0,8% có target chung của ≥3 thuốc | Bỏ Tier 2. |
| PPI không có dấu | 715.612 cạnh, không có kích hoạt/ức chế | PPI chỉ là bối cảnh; chiều tác động lấy từ ChEMBL `action_type`. |
| Cấu trúc phân tử | 645/645 thuốc có SMILES và fingerprint; 58 thuốc bị gắn cờ | Không chặn mô hình nào; khoảng 10 chất vô cơ/ion cần dược sĩ xem (mục 6.1). |
| Số liệu khác bài gốc | 1.317 nhãn (963 nhãn khi lọc ≥500 dòng), 19.081 gene | Ghi đúng snapshot, không chép 964 / 19.085. |
| HODDI có shortcut | Quy tắc "thuốc đã thấy ở mẫu dương" đạt 86,9% accuracy | Không dùng HODDI. |
| DDI-GPT khác bài toán | Phân loại nhị phân cặp (theo bảng LR) | Chỉ là related work. |

### 3.2 Giữ, sửa và bỏ so với ý tưởng ban đầu

| | Thành phần | Ghi chú |
|---|---|---|
| **Giữ** | Không huấn luyện ở giai đoạn đầu | B0 là phép đếm; B2 chỉ làm nếu qua cổng M |
| **Giữ** | Graph RAG + LLM qua API, một lần gọi | Thêm cache, template dự phòng, verifier |
| **Giữ** | Giao diện nhận 3–5 thuốc | Ghi rõ là "tổng hợp theo cặp" |
| **Giữ** | Kiểm tra path | Mở rộng thành verifier đầy đủ |
| **Sửa** | Ba Tier | Thành `status` (quan sát / dự đoán / thiếu dữ liệu) + `evidence_type` |
| **Sửa** | Cơ chế chỉ dựa trên target/PPI | Thêm ChEMBL (chiều tác động) và DailyMed (đoạn nhãn thuốc), dược sĩ kiểm tra |
| **Sửa** | Cắt hub theo ngưỡng cứng | Phạt mềm theo bậc, giới hạn số path |
| **Sửa** | "Clinical decision-support", "low latency" | "Research prototype"; latency là mục tiêu cần đo |
| **Bỏ** | "Amplified", "arising only from the combined regimen"; HODDI; GNN | Không chứng minh được, hoặc không đáng công trong 6 tuần |

---

## 4 Có nên huấn luyện mô hình không? — phân tích chi phí và lợi ích

### 4.1 Thử nghiệm B0 (2026-10-10)

Đây là phép thử **tạm thời** trên một lần chia 80/20 theo cặp (seed 0), **không** phải split chính thức. Chấm trên toàn bộ 963 nhãn cho 12.694 cặp test; tỷ lệ dương 7,45%.

| Phương pháp | Huấn luyện? | Macro AP | Macro AUROC | Micro AP |
|---|---|---|---|---|
| Độ phổ biến của nhãn (giống nhau cho mọi cặp) | Không | 0,074 | 0,500 | 0,226 |
| **B0: `f(A,e) + f(B,e)`**, với f là tỷ lệ cặp train của thuốc có nhãn e | **Không**, chỉ đếm | **0,270** | **0,837** | **0,351** |

**Đọc kết quả:**

- B0 đã có tín hiệu thật mà không cần huấn luyện: AUROC 0,84, AP gấp 3,6 lần mức ngẫu nhiên.
- AP 0,27 còn xa mức trần, nên một mô hình học **có thể** cải thiện, nhưng không biết được bao nhiêu nếu chưa thử.
- Tensor factorization báo AUROC 0,978 [S04] nhưng đo trên random edge split với mẫu âm lấy mẫu, nên **không so trực tiếp** được với con số trên.

### 4.2 Chi phí và lợi ích của từng lựa chọn

Công sức là **ước lượng**, chưa đo.

| Lựa chọn | Công sức | Tài nguyên | Lợi ích kỳ vọng | Giá trị cho sản phẩm |
|---|---|---|---|---|
| **B0** (đếm) | 0,5–1 ngày công | CPU, vài giây | Đã đo: AUROC 0,84 | Có điểm "dự đoán" cho cặp chưa có nhãn, và bằng chứng mức thuốc dễ giải thích ("A đi cùng e trong X% cặp") |
| **B2** DistMult/SimplE | 4–6 ngày công (lấy mẫu âm, train, tune, 3 seed) | CPU đủ; GPU giúp nhanh hơn | Chưa biết. Có thể tăng AP; đã được chứng minh mạnh trên random split | Xếp hạng tốt hơn, nhưng **khó giải thích**: embedding không cho lý do; vẫn chỉ là liên hệ thống kê |
| B1 fingerprint + logistic | 3–4 ngày công | CPU | Chưa biết; cho phép thuốc mới (cold-start) | Chỉ có giá trị nếu sản phẩm cần thuốc ngoài 645 thuốc |
| GNN/TIP | 1,5–2 tuần công | GPU | Biên lợi ích nhỏ so với B2 (theo văn liệu) | Thấp |
| A + D (không huấn luyện) | Khoảng 2,5 tuần công | CPU + API | Bằng chứng có nguồn, cơ chế có chiều tác động | **Cao nhất**: dược sĩ dùng và kiểm chứng được |

### 4.3 Kết luận

**Chưa huấn luyện ở tuần 1–3.** Ba lý do:

- (1) B0 đã đủ làm tín hiệu "dự đoán" ban đầu.
- (2) Phần giá trị nhất của sản phẩm (bằng chứng và cơ chế) không phụ thuộc vào mô hình.
- (3) Lợi ích của B2 chưa biết và chỉ là thống kê, trong khi chi phí khoảng một tuần công.

Quyết định huấn luyện được đặt ở **cổng M** cuối tuần 3, khi đã có dữ liệu thật để cân nhắc.

### 4.4 Cổng M (cuối tuần 3) — điều kiện để huấn luyện B2

Chỉ huấn luyện B2 ở tuần 4 khi **cả ba** điều kiện đều đạt:

1. **Lõi sản phẩm đúng tiến độ:** GĐ2, GĐ3 và GĐ4 đã qua cổng.
2. **Dự đoán thật sự được dùng:** dược sĩ xem top-10 dự đoán B0 của khoảng 20 cặp chưa có nhãn, và đánh giá rằng dự đoán có ích nhưng xếp hạng chưa tốt. Nếu dược sĩ thấy dự đoán thống kê không hữu ích dù xếp hạng tốt hơn, thì huấn luyện không đáng.
3. **Có khoảng 5 ngày công rảnh** ở tuần 4 mà không làm trễ GĐ5.

**Nếu làm B2:** chỉ giữ B2 khi nó vượt B0 về macro AP trên **val** ít nhất **+0,02**, nhất quán qua 3 seed. Nếu không, giữ B0. Đây cũng là một kết quả đáng báo cáo.

**Nếu không làm B2:** tuần 4 dùng để mở rộng bằng chứng (thêm thuốc vào danh mục demo, thêm phần nhãn DailyMed) và làm giao diện.

---

## 5 Các hướng và lựa chọn

| Hướng | Vai trò trong v2 | Lý do |
|---|---|---|
| **A** Tra cứu bằng chứng Decagon | **Lõi** | Rẻ, demo sớm, là nền cho mọi phần khác |
| **D** Nguồn cơ chế (ChEMBL, DailyMed) + dược sĩ | **Lõi** (trước đây là mở rộng) | Có dược sĩ; bù chỗ thiếu target và PPI không có dấu |
| **B0** Dự đoán bằng đếm | **Lõi** | Không cần huấn luyện; đã đo được tín hiệu |
| **B2** Mô hình học | **Có điều kiện** (cổng M) | Chi phí khoảng 1 tuần công, lợi ích chưa biết |
| B1, GNN/TIP, HODDI (C), nhiều agent (E) | **Không làm** | Không đáng công trong 6 tuần, hoặc dữ liệu có vấn đề |

---

## 6 Lộ trình theo giai đoạn

Mỗi giai đoạn chỉ bắt đầu khi **cổng** của giai đoạn trước đã đạt. Ngoại lệ: GĐ3 (nguồn cơ chế) có thể chạy song song với GĐ2 vì không phụ thuộc nhau.

### 6.1 Giao thức đánh giá (đã chốt)

| # | Quyết định | Đã chốt | Lý do |
|---|---|---|---|
| D1 | Vocabulary nhãn | **Danh sách cố định 963 nhãn** (≥500 dòng trên toàn snapshot), lưu thành file trước khi split | Trùng quy ước của Decagon; chỉ dùng tần suất nhãn, không dùng danh tính cặp test (công bố rõ) |
| D2 | Chia tập | Theo cặp, **70/10/20, seed 391**; mọi nhãn của một cặp nằm cùng split | Không giao cặp giữa các split |
| D3 | Chấm điểm | Mỗi cặp val/test được chấm trên **toàn bộ 963 nhãn**; nhãn vắng mặt là "âm giả định"; không lấy mẫu âm khi chấm | Một ma trận chấm chung cho mọi phương pháp |
| D4 | Cách diễn đạt kết quả | "Dự đoán nhãn cho cặp đã có báo cáo nhưng bị giữ lại", **không phải** dự đoán cho cặp chưa từng được ghi nhận | Cặp vắng mặt không có nhãn âm thật |
| D5 | Metric | **Macro AP** là chính; micro AP và macro AUROC là phụ; tách theo nhóm tần suất nhãn và theo thuốc có/không có target | AP phù hợp với ma trận thưa |
| D6 | Mô hình | **B0 bắt buộc; B2 theo cổng M**; không làm B1/GNN | Mục 4 |
| D7 | Ngưỡng nghiệm thu phần giải thích | Trên bộ dev: **claim support ≥ 90%** và **coverage ≥ 70%** (tạm thời; dược sĩ xác nhận sau pilot tuần 3, **trước** khi chạy đánh giá cuối) | Tránh chọn ngưỡng sau khi đã thấy kết quả |
| — | Validation và test | Chọn cấu hình chỉ trên val; test chạy **một lần** | Tránh tune trên test |
| — | Thuốc bị gắn cờ cấu trúc | **Giữ tất cả** trong dữ liệu, tra cứu và B0. Dược sĩ xem khoảng 10 chất vô cơ/ion và 2 ánh xạ nghi sai (CID 28112 lithium aluminum hydride, CID 6398525); kết quả ghi vào data card | Nhãn của các chất này vẫn là dữ liệu thật |

### GĐ1 — Nền dữ liệu

- **GĐ1a — xong 2026-10-10:** môi trường, ETL chỉ đọc, manifest, QA 32/32, cấu trúc phân tử 645/645.
- **GĐ1b — tuần 1:**
  - Lưu file vocabulary (D1); chia tập theo cặp (D2).
  - **Data view tách hai chế độ:**
    - *Evidence mode* đọc toàn bộ snapshot.
    - *Prediction mode* chỉ đọc nhãn train, đã loại cả val lẫn test.
    - Khóa cache gồm `mode`, `split_id` và `snapshot_hash`.
  - **4 test rò rỉ:**
    - (a) không có cặp nào giao giữa các split;
    - (b) không còn cạnh val/test trong dữ liệu train;
    - (c) prediction mode không truy xuất được nhãn val/test;
    - (d) không có cache hit chéo giữa hai chế độ.
  - **Vì sao vẫn cần dù chưa huấn luyện:** B0 cần split để được chấm trung thực, và giữ split sẵn để B2 có thể làm ngay nếu qua cổng M.
  - **Cổng:** 4 test đạt; hash khớp manifest.

### GĐ2 — Demo tra cứu (evidence mode), tuần 2

- **Thứ tự làm:**
  1. CLI nhận ID thuốc → tạo mọi cặp → lookup → gộp theo `effect_id`, giữ `contributing_pairs` → xuất theo **template**, có báo phần thiếu dữ liệu.
  2. Cho nhập bằng tên thuốc (dùng tên PubChem đã có).
  3. Thêm bối cảnh target/PPI có giới hạn.
- **Phân biệt ba trường hợp:**
  - Thuốc ngoài vocabulary: báo lỗi.
  - Cặp không có nhãn: `thiếu dữ liệu` cho riêng cặp đó.
  - Thuốc thiếu target: **giữ kết quả lookup**, chỉ đánh dấu phần cơ chế là thiếu.
- **Cổng:** demo chạy được với các đơn mẫu, báo đúng cả ba trường hợp.

- **Trạng thái (2026-10-10): lõi đã xong.** `python -m dsp391m.lookup`. Phát hiện cần xử lý ở GĐ3–GĐ5:
  - **Xếp hạng tác dụng phụ chưa có lời giải tốt.** Theo số cặp thì nhãn chung chung lên đầu; theo mức trội so với tỷ lệ nền thì nhãn hiếm, có thể là nhiễu, lên đầu. Dược sĩ cần đánh giá cách xếp hạng trên gold set; nguồn DailyMed giúp ưu tiên các tương tác có ghi trong nhãn thuốc.
  - **Nhãn Decagon lẫn chỉ định và bệnh nền** (ví dụ hyperlipaemia ở cặp có simvastatin). Phần giải thích không được trình bày các nhãn này như tác dụng phụ do tương tác.
  - **Tên thuốc:** 374/645 có tên trực tiếp; 253 thuốc chờ PubChem hết giới hạn tốc độ; các tên suy ra từ CID liên quan cần dược sĩ duyệt.

### GĐ3 — Nguồn cơ chế và nhãn thuốc (D), tuần 2, song song GĐ2

- **Danh mục demo:** dược sĩ chọn khoảng **50 thuốc** thường dùng chung trong số 645 thuốc. Phần D làm sâu trên danh mục này trước khi mở rộng.
- **ChEMBL:** InChIKey (đã có) → `molecule_chembl_id` → mechanism (`target`, `action_type`: inhibitor, agonist...). Đây là quan hệ **có chiều** mà PPI không có. Đo độ phủ trên 645 thuốc và trên danh mục demo.
- **DailyMed:** tên hoạt chất → SPL `set_id` → các mục *Drug Interactions*, *Warnings*, *Adverse Reactions*, chia đoạn và giữ `set_id`, version, ngày. Đây là nguồn văn bản cho câu giải thích.
- **Dược sĩ kiểm tra:** mapping của danh mục demo, và các trường hợp mơ hồ (salt, ion, chế phẩm phối hợp).
- **Cổng:** độ phủ ChEMBL và DailyMed được đo; mapping của danh mục demo đã được dược sĩ duyệt.

### GĐ4 — Giải thích + dự đoán B0, tuần 3

- **Dự đoán:**
  - Viết bộ chấm điểm dùng chung (D3, D5).
  - Chấm B0 trên **val**; test giữ cho GĐ5.
  - Với cặp chưa có nhãn, B0 cho top-k ở `status = dự đoán`, kèm bằng chứng mức thuốc.
- **Loại bằng chứng, xếp theo độ mạnh:**
  1. Đoạn nhãn thuốc DailyMed nói trực tiếp về cặp hoặc nhóm thuốc;
  2. Cơ chế ChEMBL có chiều tác động;
  3. Nhãn Decagon đã quan sát;
  4. Bằng chứng mức thuốc của B0;
  5. Bối cảnh target/PPI (gắn nhãn "bối cảnh, không phải cơ chế").
- **LLM:**
  - Một lần gọi API với schema JSON; mỗi phát biểu trích ID bằng chứng; được phép trả "insufficient evidence".
  - Phần cơ chế mặc định là "chưa đủ bằng chứng", trừ khi có nguồn loại 1 hoặc 2.
- **Verifier:** ID có thật; quan hệ và chiều đúng; bằng chứng thuộc đúng chế độ và data view; không có câu khẳng định quá mức.
- **Gold set v1:** dược sĩ lập khoảng 20 trường hợp dev (tách riêng khỏi bộ đánh giá cuối).
- **Cổng:** đạt ngưỡng D7 trên bộ dev, sau đó đến **cổng M** (mục 4.4).

### GĐ4' — Tuần 4, theo kết quả cổng M

- **(a) Nếu qua cổng M:** huấn luyện B2 (lấy mẫu âm theo mục 6.1, tỷ lệ cố định trong config), so với B0 trên val qua 3 seed.
- **(b) Nếu không qua:** mở rộng bằng chứng ra thêm thuốc, thêm phần nhãn, làm giao diện web đơn giản.

### GĐ5 — Đánh giá, tuần 5

- **Gold set cuối:** dược sĩ lập khoảng **100 cặp + 30 đơn 3–5 thuốc**, phân tầng theo có/không nhãn Decagon, có/không target, có/không đoạn DailyMed. Hai người chấm độc lập (dược sĩ + một thành viên) với nhãn: supported / contradicted / insufficient / citation mismatch / overclaim.
- **Ba nhóm thí nghiệm:**
  1. **Dự đoán:** B0 (và B2 nếu có) trên **test**, chạy một lần.
  2. **Giải thích:** claim support, citation precision, coverage.
  3. **Vận hành:** p50/p95 latency, số token, chi phí, lỗi API.
- **Ablation (cùng model API):** LLM không truy xuất; Graph RAG đơn giản theo ý tưởng gốc; chỉ Decagon; Decagon + ChEMBL + DailyMed + verifier.

### GĐ6 — Đóng gói, tuần 6

- Demo (CLI hoặc web đơn giản), data card, cập nhật tài liệu (mục 10). Báo cáo phải khớp đúng các thí nghiệm đã chạy.

---

## 7 Lịch 6 tuần (ước lượng)

| Tuần | Việc | Điều kiện kết thúc |
|---|---|---|
| 1 | GĐ1b; dược sĩ chọn danh mục demo và xem các thuốc bị gắn cờ | 4 test rò rỉ đạt; có danh mục demo |
| 2 | GĐ2 (demo tra cứu) ‖ GĐ3 (ChEMBL, DailyMed) | Demo báo đúng phần thiếu; độ phủ D đã đo |
| 3 | GĐ4: bộ chấm điểm, B0, LLM, verifier, gold set v1 | Đạt D7 trên dev; **quyết định cổng M** |
| 4 | (a) B2 hoặc (b) mở rộng bằng chứng và giao diện | Theo nhánh đã chọn |
| 5 | GĐ5: gold set cuối, đánh giá, ablation | Bảng kết quả kèm độ bất định |
| 6 | GĐ6: đóng gói | Demo và tài liệu khớp thí nghiệm |

---

## 8 Phân công gợi ý (4 thành viên + dược sĩ)

| Vai trò | Phụ trách |
|---|---|
| Dữ liệu và mapping | GĐ1b, ChEMBL/DailyMed mapping, data card |
| Truy xuất và dự đoán | Lookup, B0, bộ chấm điểm, B2 nếu có |
| Giải thích | Chọn bằng chứng, prompt, verifier |
| Sản phẩm và đánh giá | API LLM, cache, demo, harness đo latency và metric |
| **Dược sĩ** | Danh mục demo, duyệt mapping, gold set, chấm giải thích, xét cổng M |

Người viết prompt không tự chấm toàn bộ phần giải thích.

---

## 9 Tiêu chí thành công

Đây là mục tiêu nghiệm thu, chưa phải kết quả.

- **Giải thích (chính):** claim support ≥ 90% và coverage ≥ 70% trên gold set cuối. Bản đầy đủ phải giảm số claim không có nguồn hỗ trợ so với Graph RAG đơn giản.
- **Dự đoán:** báo B0 trên test theo D3–D5. Nếu có B2, chỉ giữ khi vượt B0 theo mục 4.4.
- **Vận hành:** p95 lookup dưới 1 giây; p95 toàn pipeline dưới 15 giây.
- **Không bao giờ:** hiển thị citation không tồn tại, biến "thiếu dữ liệu" thành "an toàn", hay trình bày dự đoán thống kê như cơ chế.

---

## 10 Tài liệu cần cập nhật cho khớp hướng mới

Vì đây là dự án chứ không phải môn học, các báo cáo cũ trong `docs/submission/` không cần nộp lại. Nhưng nếu dùng lại để giới thiệu dự án, cần sửa:

| Ý cũ | Sửa thành |
|---|---|
| Dự đoán cho đơn ≥3 thuốc | Theo cặp, tổng hợp bằng chứng cho đơn 3–5 thuốc |
| DDI-GPT làm baseline | Related work |
| Ba Tier | `status` + `evidence_type` |
| Cơ chế từ target/PPI | ChEMBL + DailyMed có dược sĩ kiểm tra; PPI là bối cảnh |
| "Clinical decision-support", "minimal latency" | "Research prototype"; latency đo bằng p95 |
| 645 / 19.085 / 964 | Thống kê của snapshot (mục 3.1) |
| Related work | Thêm K-Paths, CBR-DDI, tensor factorization, DDI-Ben; sửa các link sai trong LR |

---

## 11 Rủi ro chính

| Rủi ro | Cách xử lý |
|---|---|
| Rò rỉ nhãn | Data view theo chế độ; khóa cache gồm mode và split; 4 test tự động |
| Độ phủ ChEMBL/DailyMed thấp | Làm sâu trên danh mục demo trước; báo coverage theo từng thuốc; trả "chưa đủ bằng chứng" thay vì đoán |
| Mapping tên thuốc sai (salt, chế phẩm phối hợp) | Dược sĩ duyệt danh mục demo; lưu các trường hợp chưa phân giải |
| LLM bịa cơ chế | Schema, verifier, abstain, cơ chế mặc định là "chưa đủ" |
| Dược sĩ không đủ thời gian | Gold set nhỏ trước (20 trường hợp), mở rộng dần; chấm theo đợt |
| Tiếc vì không huấn luyện | Cổng M có tiêu chí rõ; split sẵn sàng để làm B2 ngay |
| Chi phí API | Pilot 50–100 query, cache, giới hạn số lần retry |

---

## 12 Việc cần làm ngay (tuần 1)

- [x] GĐ1a: môi trường, ETL, QA, cấu trúc phân tử.
- [x] Chốt quyết định Q1–Q5 và giao thức D1–D7.
- [x] **Claude:** GĐ1b, gồm vocabulary, split 70/10/20 seed 391, data view theo chế độ, 4 test rò rỉ. *(Xong 2026-10-10: 44.430/6.347/12.695 cặp; vocab chỉ tính trên train còn 959 nhãn, chênh 4 nhãn, chưa đo ảnh hưởng lên metric.)*
- [x] Sửa 3 lỗi bảo vệ dữ liệu theo review (metadata trong prediction view, ghi đè split, xác minh khi đọc split). Bước đánh giá tiếp theo: **B0 trên val chính thức**; test giữ cho GĐ5.
- [ ] **Dược sĩ:** chọn khoảng 50 thuốc cho danh mục demo; xem khoảng 10 chất vô cơ/ion và 2 ánh xạ nghi sai trong `data/processed/decagon_v1/structure_coverage.json`.
- [ ] **Nhóm:** gán người cho 4 vai trò ở mục 8; sửa các link sai trong `docs/literature/literature-review.xlsx`.

---

## 13 Nhật ký thay đổi của kế hoạch

| Ngày | Thay đổi |
|---|---|
| 2026-10-10 | GĐ2 lõi hoàn thành (tra cứu, gộp, bối cảnh target/PPI, 3 trường hợp thiếu dữ liệu, p95 228 ms). Ghi nhận vấn đề xếp hạng và nhãn lẫn chỉ định; tên thuốc còn thiếu 253. |
| 2026-10-10 | Sửa GĐ1b theo review: metadata của prediction view chỉ tính trên train; split không ghi đè được; xác minh checksum và snapshot khi đọc split; khóa cache gồm split_hash. |
| 2026-10-10 | GĐ1b hoàn thành; split `pair_70-10-20_s391` đóng băng và commit. |
| 2026-10-10 | **v2.** Chốt Q1–Q5 (dự án thật, 6 tuần, chưa huấn luyện, có dược sĩ). Thử nghiệm B0: macro AP 0,270, AUROC 0,837, không cần huấn luyện. Lõi đổi thành A + D + B0; B2 có điều kiện qua cổng M cuối tuần 3; bỏ B1, GNN, HODDI. Giao thức D1–D7 đã chốt. Lịch 6 tuần viết lại. |
| 2026-10-10 | GĐ1a hoàn thành: QA 32/32, cấu trúc 645/645. |
| 2026-10-10 | Sửa theo review: giao thức đánh giá chung, tách GĐ1a/GĐ1b, cách ly hai chế độ, mapping cấu trúc, GĐ4 giữ `status = dự đoán`. |
| 2026-10-10 | Tạo kế hoạch đầu tiên (v1, đề xuất). |
