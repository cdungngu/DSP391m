# Đánh giá tính khả thi và hướng triển khai dự án tương tác đa thuốc

**DSP391m · Group 8 · Báo cáo nghiên cứu ngày 08 tháng 10 năm 2026**

## 1 Kết luận và quyết định đề xuất

**Đề tài khả thi nếu điều chỉnh lời hứa khoa học và tách rõ dự đoán với giải thích.** Phương án hiện tại có thể tạo một công cụ truy xuất bằng chứng cho đơn nhiều thuốc. Tuy nhiên, ba tệp Decagon không đủ để xác nhận tác dụng phụ mới do tổ hợp từ ba thuốc trở lên, mức độ khuếch đại, hay nguy cơ ở một bệnh nhân cụ thể. Giữ nguyên ba tầng kết luận trong bản methodology sẽ khiến kết quả khó bảo vệ dù giao diện chạy tốt.

Hướng đề xuất chính là **dự đoán tác dụng phụ theo cặp bằng mô hình nhẹ, sau đó dùng truy xuất đồ thị và tài liệu để giải thích có nguồn; tổng hợp các cặp khi người dùng nhập nhiều thuốc**. Đây là thay đổi phạm vi có chủ đích so với ý tưởng không huấn luyện mô hình. Nhóm vẫn giữ được Graph RAG và LLM, đồng thời có bài toán học máy, nhãn, baseline và thí nghiệm định lượng rõ ràng.

Nếu thời gian ngắn hoặc không muốn huấn luyện, chọn phiên bản **tra cứu và tổng hợp bằng chứng tương tác trong đơn thuốc**. Khi đó, đánh giá độ đúng của truy xuất, mức độ đầy đủ, độ trung thực của giải thích, độ phủ và thời gian đáp ứng. Không trình bày việc đọc lại cạnh đã biết như khả năng dự đoán mới.

HODDI phù hợp hơn Decagon để nghiên cứu tổ hợp nhiều thuốc, nhưng chưa nên chọn làm đường triển khai mặc định. Kiểm tra trực tiếp bản phát hành cho thấy cần xử lý thuốc lặp trong một tổ hợp, nhóm báo cáo qua thời gian và sự khác biệt rất lớn giữa phân phối thuốc của mẫu dương với mẫu âm nhân tạo. Chi tiết và phép thử chẩn đoán nằm ở mục 5.

### Những phát hiện ảnh hưởng trực tiếp đến quyết định

| Phát hiện đã kiểm tra | Hệ quả triển khai |
| --- | --- |
| CSV combo có 4.649.441 dòng, 645 thuốc, 1.317 nhãn; lọc nhãn có ít nhất 500 dòng còn 963 nhãn | Phải mô tả đúng bản dữ liệu thực dùng; không sao chép con số 964 từ bài gốc |
| Chỉ 284 trong 645 thuốc có target ở tệp hiện có | 56,0% thuốc thiếu cơ sở cho nhánh suy luận target |
| Bản targets-all vẫn chỉ phủ 284 thuốc của combo | Cần nguồn bổ sung thực sự hoặc cho phép từ chối giải thích cơ chế |
| HODDI v1 merged tải về có 111.072 dòng dương và 111.072 dòng âm | Bản phát hành này không đồng nhất với con số 109.744 của bài báo; cần cố định phiên bản và tập con |
| Quy tắc chỉ dùng độ phủ thuốc đạt 86,2% accuracy trong phép thử HODDI 3–5 thuốc | Điểm cao có thể phản ánh cách tạo mẫu âm; phải có baseline kiểm tra shortcut |
| Có liên kết sai và diễn giải quá mạnh trong literature review | Cần sửa tài liệu nền trước khi chọn baseline và tuyên bố đóng góp |

Các số trên là kết quả kiểm tra dữ liệu và phép thử chẩn đoán của đợt nghiên cứu này, không phải kết quả huấn luyện hệ thống dự kiến. Chưa thực hiện đánh giá chuyên gia dược, huấn luyện GNN, hay benchmark API LLM.

## 2 Phạm vi tài liệu và cách nghiên cứu

Đã đọc nội dung hai tài liệu `Report_1_Introduction.docx`, `method_rp2.docx`, toàn bộ `report.pdf`, 44 mục của sheet `LR` cùng sheet `Note` trong `literature-review.xlsx`. Các phiên bản báo cáo có nhiều nội dung trùng nhau; methodology và ba tầng đầu ra nhất quán giữa chúng. Đã xem hình và bảng của methodology để đối chiếu với văn bản. Thư mục `src/` hiện chưa có mã triển khai.

Đã quét toàn bộ ba CSV dữ liệu gốc, thay vì suy rộng từ vài dòng đầu: đếm thực thể, nhãn, cạnh, giá trị thiếu, trùng lặp, độ phủ giữa bảng và phân bố số target. Đã tải thêm hai tệp Decagon chính thức là targets-all và mono, cùng hai tệp merged của HODDI v1 tại commit `700d0dafc74810fae3d06b1871b20a0f1df60646`, để kiểm tra các hướng thay thế. Các tệp mới được để riêng trong thư mục nghiên cứu; dữ liệu ban đầu được giữ nguyên.

Đối chiếu nguồn gốc cho các công trình ảnh hưởng trực tiếp đến lựa chọn: Decagon, TIP, tensor factorization, KnowDDI, K-Paths, CBR-DDI, HODDI, DDI-Ben, DDIAgents và các nguồn dữ liệu. Đây là tổng quan tập trung phục vụ quyết định kỹ thuật, không phải systematic review có sàng lọc toàn bộ văn liệu. Những chỉ số của các mục khác trong bảng LR chưa được tái lập và không được dùng làm căn cứ khẳng định mô hình nào tốt nhất.

**Giả định lập kế hoạch:** nhóm có bốn thành viên theo tài liệu, khoảng 6–8 tuần làm việc, máy cá nhân và khả năng dùng một GPU khi cần. Thời hạn, RAM, GPU, ngân sách API và yêu cầu chấm điểm chưa được xác nhận. Vì vậy, báo cáo đưa cả phương án CPU và phương án có GPU; thời gian ở mục 12 là ước lượng công việc, không phải cam kết hiệu năng.

## 3 Định nghĩa bài toán trước khi chọn công nghệ

### 3.1 Bốn bài toán khác nhau đang bị gộp trong ý tưởng

**Tra cứu tương tác đã ghi nhận.** Với cặp A–B, tìm các tác dụng phụ và nguồn đã có. Nếu đưa trực tiếp cạnh A–B–tác dụng phụ vào prompt, câu trả lời chủ yếu đo khả năng truy xuất và tổng hợp. Đây vẫn là chức năng hữu ích nhưng nhãn đã hiện diện trong đầu vào.

**Dự đoán liên kết chưa quan sát.** Với A–B–e bị giữ lại khỏi dữ liệu huấn luyện, xếp hạng e hoặc dự đoán điểm cho bộ ba đó. Muốn đánh giá, phải loại nhãn test khỏi đồ thị, kho tài liệu phục vụ benchmark, ví dụ few-shot, cache và đường cạnh đảo. Decagon là nền tảng phù hợp cho bài toán cặp thuốc nhiều nhãn. [S01, S02]

**Tổng hợp đơn nhiều thuốc.** Với tập S gồm k thuốc, xem xét k(k−1)/2 cặp, gộp kết quả và giữ nguồn đóng góp của từng cặp. Chức năng nhận 3–10 thuốc không tự động tạo ra mô hình tương tác bậc cao. Đầu ra nên nói “bằng chứng và dự đoán theo cặp trong đơn”.

**Tương tác bậc cao thực sự.** Học quan hệ giữa toàn bộ tập S và biến cố e, rồi kiểm tra mô hình tập hợp có giá trị bổ sung so với mô hình chỉ dùng các thuốc đơn và các cặp. Nhãn đồng xuất hiện trong báo cáo chưa chứng minh một cơ chế chỉ xuất hiện khi có đủ S. Muốn tuyên bố tác động nhân quả còn cần thiết kế đối chứng, biến gây nhiễu và thông tin phơi nhiễm mà các CSV hiện tại không có. FDA cũng lưu ý báo cáo tự phát không xác lập quan hệ nhân quả hoặc tỷ lệ mắc biến cố. [S08]

### 3.2 Phát biểu phù hợp cho dự án chính

Đầu vào là một cặp thuốc đã chuẩn hóa, đầu ra là điểm xếp hạng các nhãn tác dụng phụ và giải thích có nguồn. Giao diện có thể nhận một đơn gồm nhiều thuốc, nhưng mỗi kết quả phải chỉ ra cặp nào đóng góp, là quan sát có sẵn hay dự đoán, và dữ liệu còn thiếu gì.

Tên tiếng Anh đề xuất: **Evidence Grounded Drug Interaction Prediction and Regimen Review**. Nếu chọn hướng không huấn luyện: **Evidence Grounded Polypharmacy Review with Graph and Document Retrieval**. Nếu chọn HODDI: **Robust Multi Drug Adverse Event Association Prediction under Temporal and Negative Sampling Shifts**.

Đóng góp có thể bảo vệ được nằm ở chất lượng giao thức đánh giá, xử lý thiếu dữ liệu, truy xuất tiết kiệm ngữ cảnh và kiểm tra mức hỗ trợ của nguồn. Chưa có cơ sở để tuyên bố “đầu tiên”, “dự đoán nhân quả” hoặc “sẵn sàng hỗ trợ quyết định lâm sàng”.

## 4 Kiểm toán dữ liệu Decagon trong dự án

### 4.1 Schema và số liệu thực tế

| Tệp | Schema gốc | Kết quả quét toàn bộ |
| --- | --- | --- |
| combo | STITCH 1, STITCH 2, Polypharmacy Side Effect, Side Effect Name | 4.649.441 dòng; 645 thuốc; 63.473 cặp không thứ tự; 1.317 nhãn |
| targets | STITCH, Gene | 18.690 cạnh; 284 thuốc; 3.648 gene |
| ppi | Gene 1, Gene 2 | 715.612 cạnh không thứ tự; 19.081 gene |

Không có ô thiếu, dòng trùng hoàn toàn hay cạnh tự nối trong ba bảng đã kiểm tra. Combo và PPI không có bản sao đảo chiều khi chuẩn hóa cặp không thứ tự. Tuy nhiên, dữ liệu không thiếu ở cấp ô không có nghĩa là đầy đủ ở cấp sinh học: 361 thuốc không xuất hiện trong bảng targets; 8 gene của targets không có trong PPI. Hợp các gene giữa targets và PPI là 19.089, khác thống kê đồ thị đã xử lý trong bài báo gốc.

Số liệu 645 thuốc, 19.085 protein và 964 loại tác dụng phụ trong báo cáo cũ là thống kê được dẫn từ nghiên cứu Decagon, không phải số đếm trực tiếp của ba tệp đang nằm trong dự án. Nên ghi riêng “thống kê bài gốc” và “thống kê snapshot sử dụng”. Ngưỡng ít nhất 500 dòng trên combo hiện tại cho ra 963 nhãn với 4.576.287 dòng; báo cáo phải ghi chính xác điều kiện này, không ép dữ liệu để khớp 964.

Schema combo không chứa số người dùng thuốc, liều, thời gian dùng, mức độ nặng, xác suất, nhóm bệnh nhân hay ngày xác nhận tương tác. Nó cũng không cung cấp nhãn âm đã xác nhận. Do đó, một cạnh không thể được dịch trực tiếp thành phần trăm nguy cơ hoặc mức độ nghiêm trọng.

### 4.2 Độ phủ target là điểm nghẽn lớn

Tỷ lệ thuốc trong combo có target là 284/645, tương đương 44,0%. Với nhóm đã có target, trung vị là 11 target mỗi thuốc, nhưng có ngoại lệ rất lớn: `CID000000271` có 2.840 target. Truy vấn PubChem cho CID 271 trả về Calcium Cation. Trường hợp này cho thấy cần phân biệt thực thể hóa học, hoạt chất và sản phẩm thuốc; không thể mặc định mọi cạnh STITCH là một đích điều trị chọn lọc. Phép kiểm tra PubChem và phản hồi được lưu trong hồ sơ nghiên cứu. [S19]

Đã thử giải pháp dễ nhất là tải `bio-decagon-targets-all`: có 131.034 cạnh, 1.774 thực thể hóa học và 7.795 gene, nhưng giao với 645 thuốc của combo vẫn chỉ là 284 thuốc. Vì vậy, việc thêm tệp này có thể tăng nội dung trong một số vùng đồ thị nhưng không tự khắc phục 361 thuốc thiếu target. Phải đo lại độ phủ sau khi ánh xạ ChEMBL hoặc DrugCentral, thay vì chỉ đếm tổng số cạnh của nguồn mới.

Đối với một thuốc thiếu target, hệ thống vẫn có thể truy xuất nhãn thuốc và tương tác đã ghi nhận. Nhánh giải thích cơ chế cần trả “chưa đủ bằng chứng target trong snapshot”, hoặc dùng bằng chứng văn bản đã kiểm chứng. Không tự dựng target từ trí nhớ LLM để lấp chỗ trống rồi coi đó là dữ liệu gốc.

### 4.3 Phép thử truy xuất nhiều thuốc

Đã lấy ngẫu nhiên đều 1.000 tổ hợp cho từng kích thước k, không lặp thuốc trong tổ hợp, seed 391. Đây là phép thử độ phủ và tải truy xuất trên không gian thuốc hiện có; không đại diện cho phân bố đơn thuốc thực tế.

| Số thuốc k | Đủ target cho mọi thuốc | Có target chung của ít nhất 3 thuốc | Trung vị số dòng nhãn theo cặp | Phân vị 95 số dòng nhãn |
| --- | --- | --- | --- | --- |
| 3 | 8,6% | 0,8% | 24 | 309,15 |
| 5 | 1,8% | 5,2% | 134,5 | 741,10 |
| 10 | 0,0% trong mẫu thử | 30,5% | 847 | 2.460,40 |

Các dòng nhãn ở đây được cộng qua từng cặp nên một tác dụng phụ có thể xuất hiện nhiều lần. Cần gộp theo effect_id trong phần tóm tắt nhưng vẫn giữ cặp đóng góp. Tỷ lệ 0,0% ở k = 10 chỉ là kết quả của 1.000 mẫu thử, không có nghĩa xác suất lý thuyết bằng không.

Quy tắc Tier 2 yêu cầu target chung của ít nhất ba thuốc sẽ hiếm khi kích hoạt cho đơn ba thuốc với dữ liệu hiện có. Ngược lại, với đơn dài, lượng cạnh nhãn đưa thẳng vào prompt có thể rất lớn. Hai vấn đề thiếu bằng chứng và quá nhiều ngữ cảnh cùng tồn tại.

### 4.4 PPI và nhãn cần được xử lý thế nào

Bậc PPI trung vị là 33, phân vị 95 là 285, phân vị 99 khoảng 525,4 và lớn nhất 2.519. Xóa mọi node trên một ngưỡng bậc có thể làm mất protein quan trọng; bậc lớn không chứng minh đó là housekeeping protein. Đề xuất dùng phạt mềm theo bậc, giới hạn số đường dẫn, giữ độ đa dạng nguồn và quan hệ, rồi đánh giá ablation thay vì chọn ngưỡng theo trực giác.

Một cặp có trung vị 53 nhãn và tối đa 540 nhãn. Các tên có thể không đồng nhất về cách viết, như “neumonia”, nên dùng CUI làm khóa, giữ nhãn gốc cho truy vết và bổ sung nhãn hiển thị được chuẩn hóa. Không gộp bệnh, triệu chứng và thuật ngữ tổng quát chỉ vì gần nhau trong embedding.

PPI không có dấu kích hoạt/ức chế, cường độ, mô hay thời điểm trong CSV này. Một đường nối protein là bằng chứng quan hệ cấu trúc; nó chưa nối đầy đủ đến một biến cố cụ thể. Nguồn BioSNAP mô tả mạng PP-Decagon gồm liên hệ vật lý và chức năng; tránh gọi toàn bộ cạnh là tương tác vật lý trực tiếp. [S03]

Tệp mono chính thức có 174.977 dòng, 639 thuốc, 10.184 nhãn, và phủ 639/645 thuốc combo. Nó hữu ích cho baseline và phân biệt bằng chứng đơn thuốc với cặp thuốc, nhưng không cung cấp độ lớn của hiệu ứng cộng gộp. Mono và combo có nguồn gốc liên quan; không dùng mono như bộ ngoại kiểm độc lập.

## 5 Đánh giá HODDI và hướng tương tác bậc cao

### 5.1 HODDI cung cấp gì

HODDI xây dựng tổ hợp thuốc và biến cố từ FAERS, sử dụng DrugBank ID và mã CUI; bài báo mô tả 109.744 bản ghi và mẫu âm được tạo bằng thay thuốc cùng biến cố ngẫu nhiên. Đây là dữ liệu phù hợp hơn để đặt bài toán quan hệ giữa một tập thuốc và biến cố, nhưng nhãn vẫn chịu giới hạn của báo cáo tự phát và cách tạo negative. [S07, S08]

Repository hiện lưu cả HODDI_v1 và HODDI_v2. Không trộn thống kê bài báo với các bản phát hành, thư mục GNN, HGNN hoặc tập con khác nhau. Các tệp CSV trong GitHub dùng Git LFS: tải qua raw có thể chỉ nhận một tệp con trỏ khoảng 130 byte. Đợt kiểm tra đã tải bytes dữ liệu thực của v1 merged và đối chiếu SHA256 của tệp dương với con trỏ LFS. Chưa kiểm toán toàn bộ v2, nên các kết luận số liệu dưới đây chỉ áp dụng cho v1 merged tại commit đã nêu. [S09]

### 5.2 Kết quả kiểm tra bản phát hành đã tải

| Thuộc tính | Mẫu dương | Mẫu âm |
| --- | --- | --- |
| Số dòng | 111.072 | 111.072 |
| Report ID phân biệt | 40.164 | 40.164 |
| Thuốc phân biệt | 2.506 | 12.293 |
| CUI phân biệt | 3.950 | 4.581 |
| Dòng có thuốc lặp trong danh sách | 26.065 | 18.890 |
| Tập thuốc phân biệt sau chuẩn hóa | 29.090 | 110.924 |
| Khoảng thời gian | 2014Q3–2024Q3 | 2014Q3–2024Q3 |

Sau khi bỏ thuốc lặp trong từng danh sách, mẫu dương có 816 dòng chỉ còn một thuốc. Các tổ hợp 3, 4, 5 thuốc lần lượt có 17.091, 12.065 và 10.303 dòng dương. Vì vậy, lọc “từ ba thuốc trở lên” phải thực hiện sau khi chuẩn hóa và loại phần tử lặp. Danh sách có ba phần tử chưa chắc có ba hoạt chất khác nhau.

Không thấy trùng khóa `(tập thuốc đã sắp xếp, CUI)` trong từng lớp hay giao khóa giữa hai lớp trong snapshot này. Nhưng không thể chia ngẫu nhiên theo dòng: nhiều biến cố thuộc cùng report_id, và mẫu âm có liên hệ với báo cáo dương gốc. Với chẩn đoán chia train đến 2021Q4 và test từ 2023Q1, có 116 source report ID xuất hiện ở cả hai giai đoạn. Nên nhóm theo report/case có thể xác định được, loại giao nhau, và nếu có FAERS case/version gốc thì xử lý cả bản cập nhật.

**Bất cân xứng đáng chú ý:** 9.792 thuốc chỉ xuất hiện ở lớp âm; 91.498/111.072 dòng âm chứa ít nhất một thuốc vắng mặt trong toàn bộ lớp dương. Đây là kiểm tra phân bố toàn bộ snapshot để tìm nguy cơ shortcut, không phải một mô hình được phép nhìn test khi huấn luyện.

### 5.3 Phép thử shortcut chỉ học từ giai đoạn huấn luyện

Để kiểm tra thực tế, đã xây một quy tắc không dùng hóa học, protein, CUI hay cơ chế: dự đoán dương nếu mọi thuốc trong tổ hợp từng xuất hiện ở mẫu dương của train. Train dùng thời gian đến 2021Q4; 2022 được để ngoài phép thử; test từ 2023Q1 và loại các dòng có source report ID đã xuất hiện trong train. Với nhánh 3–5 thuốc, lọc bằng số thuốc phân biệt trước khi chia.

| Phạm vi | Dòng train | Dòng test sau loại giao source ID | Accuracy | Balanced accuracy |
| --- | --- | --- | --- | --- |
| Toàn bộ kích thước tổ hợp | 180.508 | 25.712 | 86,89% | 86,89% |
| Chỉ 3–5 thuốc phân biệt | 66.580 | 9.014 | 86,21% | 86,18% |

Kết quả này là chẩn đoán cấu trúc dataset, không phải khả năng dự đoán biến cố trên bệnh nhân và không phải tái lập benchmark chính thức HODDI. Nó cho thấy một mô hình phức tạp có thể đạt điểm cao nhờ nhận diện thuốc ít xuất hiện ở lớp dương. Không được suy từ đây rằng mọi kết quả của tác giả đều vô hiệu; cần kiểm tra chính tập con, cách split và baseline mà họ dùng.

### 5.4 Nếu nhóm vẫn muốn làm tương tác từ ba thuốc

Đặt bài toán là **dự đoán liên hệ tổ hợp thuốc với biến cố được báo cáo**, giới hạn 3–5 thuốc trong giai đoạn đầu. Chọn v1 đã kiểm toán hoặc kiểm toán lại v2 trước khi dùng. Lưu source ID, thời gian, canonical regimen và nguồn của negative.

Đánh giá song song bộ negative do tác giả cung cấp và một giao thức mới dùng negative khó hơn, lấy từ cùng không gian thuốc, gần tương đương tần suất thuốc, kích thước tổ hợp và tần suất biến cố. Có thể giữ nguyên tổ hợp và thay biến cố, hoặc giữ biến cố và thay một thuốc tương tự. Tất cả vẫn là nhãn chưa quan sát, không phải bằng chứng an toàn; cần báo cáo độ nhạy theo nhiều cách tạo negative và lọc va chạm với positive đã biết theo giao thức minh bạch.

Baseline tối thiểu gồm tần suất thuốc/biến cố, quy tắc độ phủ ở trên, mô hình bag-of-drugs, tổng hợp điểm cặp, DeepSets và một hypergraph model nếu còn nguồn lực. DeepSets mã hóa từng thuốc rồi tổng hợp bằng phép cộng hoặc trung bình bất biến thứ tự, sau đó kết hợp embedding của biến cố. So sánh với Set Transformer khi cần tương tác giữa phần tử; không cần bắt đầu bằng GNN nhiều tầng.

Chỉ kết luận mô hình tập hợp học thêm tín hiệu khi nó vượt baseline cặp trên test theo thời gian và test tổ hợp chưa thấy, với negative đã kiểm soát. Giá trị tăng thêm về dự đoán vẫn chưa chứng minh hiệp đồng dược lý. Ước lượng nhân quả bậc ba cần thêm dữ liệu so sánh các tổ hợp con, liều và bệnh nền; đây là hướng dài hạn.

## 6 Phản biện từng thành phần của phương án hiện tại

### 6.1 Truy xuất nhiều thuốc là khả thi nhưng chưa phải bằng chứng bậc cao

Hợp target của nhiều thuốc là thao tác tập hợp rõ ràng. Tuy nhiên, phát biểu “target chung của ba thuốc là tín hiệu pairwise không thể cung cấp” cần sửa: nếu giữ danh tính target trong các giao đôi, có thể tìm lại giao ba. Điểm mới ở đây là cách tổ chức truy vấn và tổng hợp; muốn chứng minh tương tác bậc cao phải có mô hình và nhãn bổ sung.

Độ phức tạp không chỉ phụ thuộc k. Đơn 5 thuốc có 10 cặp, 10 thuốc có 45 cặp, nhưng mỗi cặp có nhiều target và nhiều đường PPI. Cần phân biệt “hai hop giữa protein” với tổng chiều dài đường drug–protein–protein–drug; hai mô tả này không có cùng số cạnh.

### 6.2 PPI không đủ để suy ra cơ chế tác dụng phụ cụ thể

Đồ thị hiện tại thiếu những mắt xích như tác động agonist/antagonist, substrate/inhibitor/inducer, nồng độ, tissue, pathway–phenotype và bằng chứng gắn với một outcome. Hai thuốc cùng target có thể cùng chiều, đối chiều hoặc cạnh tranh; dữ liệu unsigned không xác định tình huống nào xảy ra.

Ví dụ sơ đồ giả định “A ức chế enzyme E, B là cơ chất của E” chỉ có ý nghĩa khi hai quan hệ và chiều tác động đều được nguồn xác nhận. Cạnh A–E và B–E chung chung không tương đương ví dụ đó. Nguồn cơ chế nên ưu tiên ChEMBL/DrugCentral và nhãn thuốc, dùng PPI làm bối cảnh bổ sung. [S21, S22, S27]

### 6.3 Ba tầng đầu ra cần thay đổi

| Tầng cũ | Vấn đề | Cách diễn đạt và dữ liệu cần có |
| --- | --- | --- |
| Known pairwise effect | “Độc lập với các thuốc khác” là kết luận quá mạnh | “Có liên hệ theo cặp được ghi nhận”; chỉ rõ nguồn và ngày |
| Amplified effect | Target chung không xác lập khuếch đại hoặc mức độ nặng | “Giả thuyết hội tụ cơ chế”; cần chiều tác động và bằng chứng liên quan outcome |
| Newly emergent effect | Đường nối hai thuốc không chứng minh tác động chỉ có khi đủ cả đơn | “Dự đoán chưa quan sát” hoặc “giả thuyết chưa đủ bằng chứng”; không gọi bậc cao nếu chưa kiểm định |

Nên thay thang tầng bằng hai thuộc tính độc lập: **trạng thái kết quả** (quan sát, dự đoán, chưa đủ dữ liệu) và **loại bằng chứng** (nhãn thuốc, tài liệu được tuyển chọn, association dataset, cơ chế, đường PPI). Mức nghiêm trọng chỉ hiển thị nếu có nguồn cho chính mức đó; độ tin cậy của mô hình không phải mức độ nặng.

### 6.4 Kiểm tra đường dẫn chỉ là một lớp kiểm tra

Một path tồn tại chứng minh rằng các cạnh đã được truy xuất, không chứng minh câu giải thích đúng. LLM vẫn có thể đảo chiều quan hệ, gán sai tác dụng của protein, suy ra triệu chứng không được nguồn hỗ trợ hoặc dùng một cạnh tương quan như bằng chứng nhân quả.

Kiểm tra tối thiểu gồm: entity ID có thật; relation và chiều đúng; path liền mạch; snapshot và split được phép; câu kết luận không vượt nội dung nguồn; nguồn trực tiếp nói về outcome hay chỉ cho bối cảnh. Nếu không có lời giải thích cơ chế đủ tốt, giữ điểm dự đoán ở trạng thái “chưa giải thích được” hoặc abstain theo giao thức, thay vì âm thầm bỏ hết các dự đoán khó rồi báo accuracy trên phần còn lại. Luôn báo cả độ phủ câu trả lời và độ đúng trên phần được trả lời.

### 6.5 Cắt hub và lựa chọn ngữ cảnh

Giữ toàn bộ target trực tiếp có thể làm prompt lớn với ngoại lệ 2.840 target. Lưu đầy đủ bằng chứng trong kho, nhưng chỉ đưa top đường dẫn vào prompt theo điểm tin cậy nguồn, liên quan query/outcome, độ dài, độ đa dạng và phạt bậc. Công thức điểm ban đầu là heuristic cần tuning trên validation, không được diễn giải thành xác suất.

So sánh ít nhất ba cách: không cắt trong giới hạn budget; cắt ngưỡng bậc như ý tưởng gốc; xếp hạng có phạt mềm và đa dạng hóa. K-Paths là prior work gần về truy xuất đường đi đa dạng cho LLM nên cần đưa vào related work và baseline retrieval. [S10]

### 6.6 API LLM và độ trễ

Chuyển sang API giúp giảm yêu cầu chạy LLM tại máy nhóm, nhưng không đảm bảo nhanh hơn mô hình cục bộ. Độ trễ còn phụ thuộc truy xuất, số token, mạng, hàng đợi và độ dài câu trả lời. Chọn một lần gọi cho phần tổng hợp, cache theo tập thuốc đã chuẩn hóa, graph snapshot, model ID và prompt version. Có đường trả kết quả theo template khi API lỗi hoặc hết ngân sách.

Chưa có phép đo latency hoặc hóa đơn thực tế trong đợt nghiên cứu này. Mọi mục tiêu p95 ở kế hoạch là tiêu chí kỹ thuật cần đo, không phải thành tích sẵn có.

## 7 Những hướng đã có và bài học cho lựa chọn mô hình

### 7.1 Mô hình dự đoán nhẹ đáng làm trước

Nghiên cứu tensor factorization của Lloyd và cộng sự báo cáo SimplE với median AUROC 0,978 và AUPRC 0,971 trên 963 nhãn, đồng thời cho thấy huấn luyện có thể rất nhanh trong cấu hình của họ. Tuy nhiên, nghiên cứu giữ lại ngẫu nhiên 10% cạnh theo nhãn; đây không phải đánh giá thuốc hoàn toàn mới. Thời gian khoảng bốn phút sau hai epoch cũng không bao gồm toàn bộ tìm siêu tham số. Dùng DistMult hoặc SimplE làm baseline nhẹ, không sao chép chỉ số đó thành kỳ vọng của dự án. [S04]

DistMult thuận tiện cho nhãn cặp đối xứng; mô hình có hướng như SimplE cần đối xứng hóa điểm khi endpoint là tác dụng phụ không thứ tự. Embedding chỉ dựa trên ID phù hợp cho thuốc đã thấy nhưng không tự suy rộng sang thuốc mới. Muốn cold-start, thêm fingerprint hoặc embedding phân tử và kiểm tra thật trên entity split.

TIP là phương án GNN đáng cân nhắc khi muốn kết hợp PPI, drug–target và DDI mà không tái dựng nguyên pipeline Decagon cũ. Các cải thiện tốc độ và AUPRC trong TIP là kết quả trong thiết lập tác giả, không là so sánh công bằng với API LLM ở dự án này. [S05]

### 7.2 Truy xuất và giải thích không còn là khoảng trống mới hoàn toàn

KnowDDI học subgraph cho cặp thuốc và cung cấp đường giải thích. K-Paths dùng truy xuất đường đi không cần huấn luyện để phục vụ LLM hoặc GNN. CBR-DDI đưa thêm các ca lịch sử và cơ chế vào suy luận. Những công trình này làm cho tuyên bố “thêm LLM để giải thích” hoặc “dùng path để giảm nhiễu” chưa đủ thành đóng góp mới. [S10, S11, S12]

DDI-GPT là tài liệu liên quan nhưng repository công khai mô tả web server và gửi suy luận tới cluster. Chưa xác nhận được từ repository này một pipeline huấn luyện đầy đủ có thể chạy ngay. Truy cập toàn văn bioRxiv trong đợt kiểm tra gặp lỗi; do đó không xác nhận lại toàn bộ chỉ số và backbone mà sheet LR ghi. Không lấy DDI-GPT làm baseline bắt buộc nếu thiếu checkpoint hoặc code tái lập. [S06]

DDIAgents 2026 có bản ghi arXiv hợp lệ; phương pháp công bố chính là luồng ngữ cảnh động theo cơ chế. Dòng LR mô tả hạn chế của nó là lịch trình cộng tác cố định cần sửa hoặc dẫn bằng chứng cụ thể. DrugReason tập trung drug repurposing; chỉ dùng làm tham khảo cách suy luận, không coi chỉ số của nó là benchmark trực tiếp cho tác dụng phụ. [S13, S14]

### 7.3 Chất lượng split có thể quan trọng hơn thêm kiến trúc

DDI-Ben nghiên cứu suy giảm hiệu năng khi phân phối thuốc thay đổi và cung cấp thiết lập theo thời gian phê duyệt. Điều này củng cố việc phải báo riêng unseen pair, unseen drug và biến đổi dữ liệu, thay vì chỉ một random split. Không so trực tiếp AUROC của bài toán nhị phân, multi-class cơ chế và multi-label tác dụng phụ. [S15]

Khuyến nghị thứ tự thử: baseline tần suất → fingerprint cộng logistic/MLP → DistMult/SimplE → GNN nhẹ khi baseline đã ổn định. Nếu mục tiêu là sản phẩm tra cứu, đầu tư vào nguồn và chất lượng giải thích có thể hữu ích hơn một GNN lớn chưa có đánh giá đúng.

## 8 So sánh các phương án triển khai

Các mức khả thi dưới đây là đánh giá kỹ thuật dựa trên dữ liệu đã kiểm tra và giả định nguồn lực ở mục 2, không phải điểm số đã đo.

| Phương án | Đầu ra có thể bảo vệ | Nguồn lực và trở ngại | Khi nên chọn |
| --- | --- | --- | --- |
| A Graph và document RAG cho đơn thuốc | Bằng chứng tương tác đã ghi nhận và tóm tắt có nguồn | CPU và API; cần corpus tốt cùng bộ kiểm tra giải thích | Còn ít thời gian; ưu tiên ứng dụng |
| B Mô hình dự đoán cặp nhẹ cộng giải thích | Xếp hạng tác dụng phụ trên nhãn giữ lại; tổng hợp theo cặp trong đơn | CPU hoặc một GPU; cần split sạch và negative rõ ràng | Khuyến nghị chính cho đồ án khoa học dữ liệu |
| C Mô hình tập hợp trên HODDI | Liên hệ tổ hợp 3–5 thuốc với biến cố được báo cáo | Làm sạch, negative khó, temporal/group split và baseline mạnh | Có thêm thời gian và muốn trọng tâm nghiên cứu |
| D Hệ suy luận cơ chế PK và PD có giới hạn | Tra cứu cơ chế và cảnh báo trong một phạm vi thuốc được tuyển chọn | Nguồn signed relation, nhãn thuốc và người kiểm tra chuyên môn | Muốn giải thích sâu, chấp nhận phạm vi hẹp |
| E GNN lớn cộng nhiều LLM agents | Pipeline nghiên cứu phức tạp | Nhiều phụ thuộc, chi phí và khó truy nguyên sai số | Chưa nên là mốc đầu tiên |

**Lựa chọn B giữ cân bằng tốt nhất** giữa phần học máy, khả năng demo, dữ liệu sẵn có và đánh giá. A là mốc hoàn thành sớm cũng là phương án dự phòng. C nên là nhánh riêng có điều kiện tiếp tục; không ghép toàn bộ vào một đồ án rồi thiếu thời gian kiểm chứng. D có thể làm tốt hơn A về độ sâu giải thích nếu nhóm có người đọc tài liệu dược học.

Một đóng góp thực nghiệm phù hợp cho B là: “Truy xuất theo loại bằng chứng và khả năng từ chối có giảm các khẳng định không được hỗ trợ so với LLM thuần và Graph RAG đơn giản, trong khi giữ chất lượng xếp hạng tác dụng phụ không?” Câu hỏi này đo được bằng ablation và bộ gán nhãn kiểm tra, không đòi hỏi chứng minh phát hiện cơ chế sinh học mới.

## 9 Nguồn dữ liệu và cách kết nối cụ thể

### 9.1 Bộ dữ liệu tối thiểu cho phương án B

**Decagon combo, PPI, targets và mono.** Dùng combo làm bảng nhãn; PPI/target chỉ làm đặc trưng hoặc bằng chứng khi có. Dùng mono làm baseline hoặc đặc trưng phụ có kiểm soát nguồn. Cố định SHA256 và vocabulary. Nguồn tải chính thức cung cấp các tar.gz; tệp đã có trong dự án không cần tải lại. [S01]

**PubChem.** Lấy tên, synonym, cấu trúc SMILES và InChIKey qua PUG REST. Chạy theo batch, cache phản hồi và ghi ID gốc. Ví dụ đã thử thành công: endpoint `/rest/pug/compound/cid/271,2173,3345/property/Title,InChIKey,CanonicalSMILES/JSON`. Phản hồi hiện dùng trường `ConnectivitySMILES`, vì vậy parser cần kiểm tra schema thay vì giả định tên trường trả về giống tên được yêu cầu. [S19]

Không áp dụng cắt tiền tố CID một cách mù quáng cho mọi phiên bản STITCH. Kiểm tra quy ước flat/stereo, salt, charge, parent compound, synonym và InChIKey. Một chemical ID có thể tương ứng dạng ion hoặc dạng không chuẩn với tên hoạt chất người dùng nhập. Cần bảng alias có provenance và danh sách trường hợp chưa phân giải.

**Nhãn thuốc qua DailyMed.** Dùng SPL XML, giữ set_id, version, ngày, tiêu đề mục và đoạn nguồn. Chọn các mục liên quan tương tác và dược lý, chia đoạn theo cấu trúc nhãn; truy xuất bằng tên hoạt chất và nội dung câu hỏi. Đây là nguồn thích hợp cho giải thích được ghi nhận, nhưng nội dung có thể nói trực tiếp về cặp test, nên corpus của thí nghiệm dự đoán phải có quy tắc che nhãn riêng. API và bulk download được NLM công bố. [S27]

### 9.2 Nguồn bổ sung theo nhu cầu

| Nguồn | Trường và khóa cần lấy | Vai trò | Điều kiện sử dụng |
| --- | --- | --- | --- |
| RxNorm và RxNav | RXCUI, ingredient, synonym, trạng thái concept | Chuẩn hóa tên và chế phẩm về hoạt chất | API RxNorm vẫn hữu ích; dịch vụ DDI của RxNav đã ngừng từ 02/01/2024 [S20] |
| ChEMBL | molecule_chembl_id, target_chembl_id, action_type, mechanism, cấu trúc | Bổ sung target và chiều tác động | Dữ liệu CC BY-SA 3.0; lọc species và nguồn; endpoint mechanism không phủ mọi hợp chất [S22] |
| DrugCentral | drug ID, INN, cấu trúc, target, activity, reference | Thay thế hoặc bổ sung nguồn cơ chế | Có tệp cấu trúc và drug–target tải công khai; xác minh license của snapshot dùng [S21] |
| Reactome | stable pathway ID, gene hoặc UniProt, evidence | Nối protein tới pathway có chú giải | Chỉ lấy Homo sapiens; pathway membership không tự chứng minh outcome [S23] |
| STRING | protein ID, score, loại bằng chứng | PPI có điểm tin cậy thay cho cạnh trần | Chọn rõ mạng functional hay physical; khóa phiên bản [S24] |
| DDInter 2.0 | ID thuốc, cặp, severity, cơ chế và reference khi có | Bộ ca giải thích hoặc tác vụ severity riêng | CC BY-NC-SA 4.0; trang tải đã kiểm tra, thử tải CSV mẫu gặp timeout [S16, S17, S18] |
| HODDI | report_id, DrugBankID list, CUI, time, label | Nhánh tổ hợp từ ba thuốc | Dùng bytes LFS thật; cố định v1/v2; kiểm toán và tái thiết kế negative [S07, S09] |
| FAERS gốc | CASEID, PRIMARYID, drug role, reaction, therapy, indication | Xử lý version và thử nghiệm báo cáo theo thời gian | Nhiều công làm sạch; báo cáo tự phát không có mẫu số phơi nhiễm [S08] |
| PrimeKG | typed nodes, typed edges, source | KG rộng cho thử nghiệm mở rộng | Lọc chỉ subgraph cần thiết và loại quan hệ làm lộ nhãn; không import toàn bộ ngay [S25] |

DDInter web có các mô tả phong phú nhưng chưa kiểm tra bytes CSV trong đợt này; không giả định tệp tải chứa toàn bộ đoạn giải thích của giao diện. Đọc schema thực trước khi chốt nó làm corpus chính. Trạng thái tải và sự đầy đủ của từng trường là tiêu chí của tuần đầu.

### 9.3 Các phụ thuộc không nên đặt trên đường triển khai bắt buộc

**DrugBank full XML.** Trang phát hành kiểm tra ngày 08/10/2026 thông báo tạm dừng toàn bộ academic downloads. Nếu nhóm chưa có bản tải hợp lệ, không lập kế hoạch yêu cầu tải được ngay. Dùng nguồn có sẵn và ChEMBL/DrugCentral/PubChem; xem lại quyền sử dụng từng nguồn trước khi phân phối bản dữ liệu hợp nhất. [S26]

**UMLS và MedDRA.** Có mã CUI trong CSV không đồng nghĩa được phân phối toàn bộ từ điển. Nếu cần tên, mapping hoặc ontology đầy đủ, kiểm tra quyền truy cập và hạn chế của từng vocabulary. Giai đoạn đầu giữ mã cùng tên có sẵn, bổ sung mapping được phép và đánh dấu chưa ánh xạ. [S29]

**SIDER.** Có thể bổ sung thông tin tác dụng phụ đơn thuốc; phải phân biệt version, licensing và quan hệ nguồn với Decagon. Đợt này đã tải mono từ Decagon nên chưa cần thêm SIDER chỉ để tăng số nguồn. [S28]

**OGB ogbl-ddi.** Hữu ích cho link prediction nhị phân nhưng không thay thế trực tiếp bộ nhãn 963 hoặc 1.317 tác dụng phụ. Nếu chuyển sang OGB phải đổi câu hỏi nghiên cứu và metric, không gọi đó là tái lập tác vụ Decagon. [S33]

### 9.4 Schema hợp nhất đề xuất

Dùng bảng `drug` có khóa nội bộ ổn định, ID nguồn, tên chuẩn, parent, cấu trúc và trạng thái mapping. Bảng `drug_alias` giữ tên nhập, hệ ID, phương pháp map và lý do chưa chắc chắn. Bảng `protein` giữ namespace gene/protein, species và mapping đã kiểm tra. Không join gene symbol trực tiếp nếu có Entrez/UniProt rõ hơn; lưu các quan hệ một–nhiều.

Bảng `evidence` lưu subject, predicate, object hoặc outcome, source, source_record_id, URL, thời điểm snapshot, đoạn nguồn và trạng thái kiểm chứng. Bảng `pair_label` giữ cặp đã sắp thứ tự và CUI. Với HODDI, thêm `regimen_event` gồm canonical set, report/case group, time, label và negative-generation method. Provenance cần được giữ đến câu trả lời cuối.

Không hợp nhất severity của DDInter, nhãn tác dụng phụ Decagon và loại cơ chế DrugBank thành một nhãn duy nhất. Đây là các endpoint khác nhau; có thể dùng để hỗ trợ giải thích, nhưng đánh giá dự đoán phải theo một định nghĩa đầu ra cố định.

## 10 Thiết kế kỹ thuật đề xuất

### 10.1 Luồng xử lý

Nhập danh sách thuốc → chuẩn hóa hoạt chất và xác nhận trường hợp mơ hồ → tạo cặp không thứ tự → truy xuất bằng chứng đã ghi nhận và chạy mô hình điểm riêng → chọn đường dẫn cùng đoạn tài liệu → tổng hợp một lần bằng LLM hoặc template → kiểm tra schema và từng phát biểu → trả kết quả cùng nguồn và phần thiếu dữ liệu.

Hai chế độ cần được cấu hình tách biệt. **Evidence mode** được phép sử dụng tương tác đã ghi nhận cho chính cặp hỏi. **Prediction evaluation mode** dùng đồ thị và corpus đã loại bằng chứng tiết lộ nhãn test theo giao thức. Mọi cache phải chứa mode và split ID; không dùng kết quả của evidence mode cho benchmark.

### 10.2 ETL và lưu trữ

Python xử lý ETL; pandas hoặc Polars cho bảng, Parquet để lưu dữ liệu đã xử lý, DuckDB hoặc SQLite cho lookup theo cặp và nguồn. Sparse adjacency hoặc adjacency list cho PPI. NetworkX thuận tiện cho subgraph nhỏ, nhưng không nên mặc định đưa toàn bộ 4,6 triệu cạnh đa nhãn thành Python objects khi chỉ cần lookup.

Neo4j là tùy chọn nếu nhóm cần Cypher hoặc trực quan hóa graph, không phải điều kiện để có Graph RAG. Embedding database cũng không bắt buộc ban đầu: có thể bắt đầu bằng BM25 trên nhãn thuốc đã chia đoạn, sau đó thêm dense retrieval khi benchmark cho thấy ích lợi. Các lựa chọn này là kiến trúc đề xuất, cần khóa phiên bản thư viện lúc dựng môi trường.

Tạo manifest cho dữ liệu gốc, dữ liệu xử lý, từ điển, nguồn bổ sung và split. Một thí nghiệm phải xác định được các hash này, seed, model configuration và prompt version. Tránh quy trình notebook thủ công khiến bảng nhãn và graph không cùng snapshot.

### 10.3 Các baseline và mô hình học

**B0 tần suất.** Xếp hạng theo tần suất nhãn trong train, thêm baseline mức độ phổ biến của thuốc hoặc độ bậc. Đây là đối chứng rẻ để biết mô hình có vượt phân bố phổ biến không.

**B1 đặc trưng hóa học.** Morgan fingerprint hoặc embedding phân tử đã cố định. Với embedding u và v, dùng ghép `(u + v, |u − v|, u ⊙ v)` để giữ tính bất biến thứ tự. Huấn luyện logistic hoặc MLP đa nhãn; chuẩn hóa và fit mọi bộ biến đổi chỉ trên train. Với fingerprint thưa, logistic theo nhãn là baseline dễ kiểm tra; MLP dùng masked/sampled loss nếu không coi mọi ô vắng là âm chắc chắn.

**B2 factorization.** DistMult với score `sum(z_A × r_e × z_B)` cho cặp đối xứng; hoặc SimplE đối xứng hóa. Khởi đầu embedding 64/128 chiều, huấn luyện minibatch trên triplet với negative đã lọc và ghi rõ cách sampling. Dùng sigmoid như điểm phân loại trên phân phối thí nghiệm; không gọi là xác suất lâm sàng.

**B3 có graph.** Chỉ thêm R-GCN/TIP hoặc encoder drug–target khi B1/B2 và giao thức đã chạy ổn. Phải xử lý thuốc không có target, ví dụ bằng molecular feature và mask nguồn. Ablation giữ nguyên dữ liệu và split để tách lợi ích topology khỏi việc thêm dữ liệu.

Chọn model bằng validation, khóa hyperparameter trước test, chạy ba seed cho các mô hình chính. Không bắt buộc dùng mọi kiến trúc trong bảng LR. Một mô hình đơn giản được đánh giá đúng có giá trị hơn nhiều baseline chưa kiểm soát điều kiện.

### 10.4 Retrieval có budget

Lọc entity chính xác trước, lấy bằng chứng trực tiếp cho cặp và các quan hệ target có loại rõ, sau đó mở rộng PPI với giới hạn đường đi. Đối với tài liệu, lấy đoạn theo thuốc và outcome; BM25 kết hợp embedding là bước mở rộng nếu cần. Khi đánh giá dự đoán, không dùng outcome thật bị giữ lại để chọn đường dẫn hoặc truy vấn tài liệu.

Đề xuất khởi đầu tối đa 10–20 đường dẫn và 6–10 đoạn nguồn cho một truy vấn đã gộp; ngân sách khoảng 4.000–8.000 input tokens. Đây là điểm khởi đầu để đo trade-off, không phải giá trị tối ưu. Có thể dùng diversity/MMR để tránh nhiều đoạn nói cùng một điều. Dữ liệu gốc vẫn được giữ trong kho để người xem mở chi tiết.

Tách loại evidence: observed association, curated interaction statement, target action, pathway context, PPI path. Không cho đường PPI yếu đẩy mất đoạn nhãn thuốc trực tiếp. Dùng fallback văn bản cho thuốc thiếu target và trả coverage trên từng thuốc.

### 10.5 LLM và schema câu trả lời

LLM nhận dữ liệu có ID, lời hướng dẫn ngắn và output schema cố định. Yêu cầu trích evidence IDs cho từng phát biểu, cho phép trả “insufficient evidence”, giới hạn danh sách outcome ở vocabulary hoặc candidate set đã xác định. Không yêu cầu viết một chuỗi suy luận dài; cần giải thích ngắn có thể đối chiếu nguồn.

Một record đầu ra nên có `drug_pair`, `effect_id`, `status`, `model_score`, `score_scope`, `evidence_ids`, `explanation`, `unsupported_steps`, `missing_data`, `source_snapshot` và `model_version`. `severity` để trống nếu nguồn không cung cấp. Ở regimen level, thêm `contributing_pairs` và `aggregation_method`.

Với đơn nhiều thuốc, điểm lớn nhất giữa các cặp có thể dùng làm heuristic xếp hạng. Công thức noisy-OR `1 − product(1 − p_pair)` đòi hỏi giả định phụ thuộc rất mạnh và pair probabilities có ý nghĩa; không dùng nó như xác suất biến cố của đơn khi chưa hiệu chỉnh bằng nhãn regimen. Giao diện phải gọi đây là điểm tổng hợp theo cặp.

### 10.6 Kiểm tra câu trả lời và xử lý thất bại

Parser kiểm tra JSON, tên và ID; verifier kiểm tra citation/path; bộ luật phát hiện từ ngữ khẳng định quá mức; một tập gán nhãn thủ công đánh giá ý nghĩa. Có thể thêm mô hình entailment như lớp phụ, nhưng không coi điểm của một LLM judge là chân lý.

Các tình huống phải có đầu ra xác định: thuốc ngoài vocabulary, tên mơ hồ, chế phẩm nhiều hoạt chất, thuốc trùng, thiếu target, thiếu nguồn trực tiếp, nguồn bất đồng, API timeout và cache cũ. Nếu chỉ thiếu giải thích cơ chế, vẫn phân biệt với trường hợp hoàn toàn không có bằng chứng tương tác. Nếu từ chối trả lời, phải nói rõ phần nào thiếu và được tính vào metric coverage.

## 11 Giao thức thực nghiệm và tiêu chí thành công

### 11.1 Tách ba nhóm đánh giá

| Nhóm thí nghiệm | Đối tượng cần đo | Metric chính |
| --- | --- | --- |
| Dự đoán nhãn chưa quan sát | Điểm mô hình cho cặp và tác dụng phụ | Macro AP, micro AP, AUROC bổ sung, Precision hoặc Recall tại K |
| Truy xuất và giải thích | Nguồn đúng, câu được nguồn hỗ trợ, độ bao phủ | Recall bằng chứng, citation precision, claim support, contradiction, abstention coverage |
| Vận hành hệ thống | Khả năng dùng được và chi phí | Mapping coverage, p50/p95 latency, input/output tokens, lỗi API, RAM |

Ghi rõ AP là average precision hay diện tích dưới đường PR tính bằng nội suy; không dùng lẫn hai tên khi so với bài khác. Không ưu tiên accuracy cho ma trận nhãn thưa. Brier score, calibration curve hoặc ECE chỉ mô tả phân phối đánh giá đã tạo; tập cân bằng bằng negative sampling không cho xác suất mắc ở dân số.

### 11.2 Split và chống rò rỉ

**Thiết lập phụ để so với văn liệu:** giữ lại triplet ngẫu nhiên theo nhãn, báo rõ cặp có thể vẫn tồn tại trong train qua outcome khác. Kết quả này đo hoàn thành nhãn của cặp đã có thông tin, không phải cặp hoàn toàn mới.

**Thiết lập chính:** chia theo cặp đã canonicalize, ví dụ 70/10/20; mọi nhãn và cạnh đảo của một cặp ở cùng split. Thuốc có thể đã thấy nhưng cặp test chưa thấy. Tạo graph huấn luyện sau khi chia, không xóa cạnh sau khi đã tính feature hoặc embedding từ graph đầy đủ.

**Thiết lập mở rộng:** giữ lại một hoặc cả hai thuốc; chỉ mô hình có đặc trưng ngoại sinh mới có cơ chế cold-start hợp lý. Nếu dùng molecular similarity/cluster split, lưu cách dựng cluster và không tune trên test. Không gọi một mô hình ID-only là inductive chỉ vì chạy được với token UNK.

Đối với HODDI, nhóm theo source report/case, quản lý positive và negative phát sinh từ cùng nguồn, dùng mốc thời gian rõ. Báo riêng tổ hợp đã thấy/chưa thấy, thuốc đã thấy/chưa thấy và độ phủ nhãn ở test. Hạn chế label vocabulary dựa trên train hoặc dùng danh sách benchmark cố định đã công bố trước; không lựa chọn nhóm nhãn tốt nhất dựa vào test.

Ngoài graph, kiểm tra rò rỉ trong mono, embedding đã huấn luyện trước, các bảng tổng hợp, nhãn thuốc nói thẳng về cặp test, ví dụ prompt và cache. Với LLM nền, không thể loại hoàn toàn khả năng nhớ dữ liệu công khai; cần báo đây là giới hạn, thêm đối chứng che tên khi phù hợp và phân biệt đánh giá năng lực truy xuất với dự đoán chưa biết.

### 11.3 Negative và đơn vị thống kê

Decagon vắng cạnh là chưa quan sát. Khi tạo negative, loại positive đã biết theo giao thức đã đăng ký, giữ nguyên quy tắc giữa các model và báo tỷ lệ negative. Thử cả negative ngẫu nhiên và negative khó cùng mức phổ biến; không dùng negative khác nhau cho từng baseline. Nếu khai thác nhãn test để lọc false negative, chỉ làm trong bộ tạo benchmark dùng chung và công bố rõ, không đưa thông tin đó vào feature hoặc chọn model.

Confidence interval nên bootstrap theo cặp hoặc theo report/regimen group thay vì coi hàng triệu nhãn liên quan là mẫu độc lập. Báo mean và độ lệch chuẩn qua seed, kết quả theo nhóm tần suất nhãn và theo thuốc có/không có target. Một mức tăng rất nhỏ không đủ thuyết phục nếu chỉ có một seed và không có khoảng bất định.

### 11.4 Baseline cho phần LLM

So sánh cùng model API, cùng tập query và budget: LLM không retrieval; document RAG; graph RAG đơn giản theo ý tưởng; graph cộng document có lựa chọn evidence và verifier; template không LLM. Tách ablation của prediction model khỏi ablation của explanation để xác định lợi ích đến từ đâu.

Lập bộ khoảng 100–150 cặp và 30–50 đơn tổng hợp cho kiểm tra giải thích, phân tầng theo đủ/thiếu target, bằng chứng mạnh/yếu, tên mơ hồ và nguồn bất đồng. Đơn tổng hợp chỉ đánh giá cách tổng hợp bằng chứng theo cặp, không là nhãn bậc cao. Hai người độc lập đọc từng claim và nguồn, thống nhất trường hợp bất đồng; nếu không có người có chuyên môn dược, chỉ gọi đây là kiểm tra hỗ trợ của nguồn, chưa xác nhận cơ chế lâm sàng.

Các nhãn gán tay nên gồm supported, contradicted, insufficient, citation mismatch và overclaim. LLM judge có thể hỗ trợ chọn trường hợp cần xem nhưng không tự chấm mình làm metric duy nhất. Đo tính ổn định khi đảo thứ tự thuốc hoặc bỏ một đoạn evidence; việc câu trả lời thay đổi không tự chứng minh nhân quả.

### 11.5 Tiêu chí tiếp tục và tiêu chí dừng

Tuần đầu phải có schema, hash, thống kê và coverage; mọi tên trong danh mục demo phải map đúng hoặc bị đánh dấu mơ hồ. Trước huấn luyện phải có kiểm tra không giao cặp/report giữa split và không còn cạnh test trong training graph.

Mô hình chỉ được nâng cấp khi baseline đã chạy tái lập. Nếu mô hình phức tạp không vượt baseline nhẹ qua nhiều seed, dùng baseline nhẹ và tập trung vào đánh giá nguồn. Nếu HODDI không qua kiểm tra negative hoặc group split, dừng nhánh bậc cao và chuyển về A/B.

Mục tiêu kỹ thuật ban đầu có thể đặt p95 lookup cục bộ dưới 1 giây, p95 toàn pipeline dưới 15 giây và giảm claim không có hỗ trợ so với graph RAG đơn giản trên bộ đánh giá cố định. Đây là mục tiêu nghiệm thu đề xuất cần đo. Nên đặt trước mức chất lượng tối thiểu cùng người hướng dẫn, không chọn sau khi nhìn kết quả. Giao diện không được hiển thị citation không tồn tại hoặc biến thiếu dữ liệu thành kết luận “an toàn”.

## 12 Nguồn lực và lộ trình thực hiện

### 12.1 Phạm vi tối thiểu và phạm vi mở rộng

Mốc tối thiểu gồm ETL và manifest, lookup theo cặp, chuẩn hóa một danh mục demo được kiểm tra, một baseline dự đoán nhẹ, một phương pháp giải thích có nguồn và bộ đánh giá. Cho phép nhập 3–5 thuốc ở giao diện nhưng ghi rõ tổng hợp theo cặp. Không đặt tái lập nhiều paper, fine-tune LLM và HODDI vào cùng mốc bắt buộc.

Với máy CPU, ưu tiên A và một bản B thu gọn với fingerprint/logistic hoặc factorization; benchmark thời gian trên sample trước khi chạy toàn bộ. RAM 16 GB là điểm khởi đầu thực dụng cho ETL nếu dùng dtype tiết kiệm, chunk và sparse. Đây là ước lượng; graph Python chứa mọi cạnh có thể đòi hỏi nhiều hơn. GPU 12–16 GB hữu ích cho MLP/GNN vừa phải nhưng không cần cho phần truy xuất; cloud notebook là phương án thử, không giả định phiên chạy miễn phí luôn sẵn.

Một tensor dày cho 207.690 cặp và 963 nhãn chứa khoảng 200 triệu ô, gần 0,8 GB chỉ riêng float32, chưa có gradient hoặc bản sao. Vì vậy dùng sparse labels, minibatch hoặc sampled loss. Đừng suy tài nguyên huấn luyện từ dung lượng CSV 233 MB.

### 12.2 Kế hoạch sáu tuần cho phương án B

| Tuần | Công việc | Điều kiện kết thúc |
| --- | --- | --- |
| 1 | Khóa bài toán, dữ liệu, mapping, split; sửa related work | Manifest và data card; biết rõ phần thiếu; qua kiểm tra leakage |
| 2 | B0 và B1/B2; lookup không LLM | Có baseline tái lập, metric và báo cáo lỗi |
| 3 | Corpus nhãn thuốc, retrieval theo pair và evidence | Có bộ query cố định và nguồn truy vết |
| 4 | LLM/template, schema, verifier, abstention | Demo end-to-end và xử lý tình huống lỗi |
| 5 | Ba seed, ablation, kiểm tra explanation và latency | Bảng kết quả có uncertainty và phân nhóm |
| 6 | Tổng hợp, sửa claim, data/model card, đóng gói demo | Báo cáo và demo khớp đúng thí nghiệm |

Nếu có tám tuần, thêm cold-start hoặc nhánh HODDI sau khi qua tiêu chí ở mục 11; chỉ chọn một mở rộng lớn. Với 2–3 tuần, chọn A, tập trung corpus nhỏ được kiểm chứng, evaluator và demo thay vì huấn luyện nhiều model.

Phân công gợi ý cho bốn người: dữ liệu/mapping; mô hình/split; retrieval/explanation; API/demo/evaluation harness. Cả nhóm cùng kiểm tra bộ giải thích để tránh một người viết prompt rồi tự chấm toàn bộ. Đây là đề xuất vai trò, chưa gán trách nhiệm cho thành viên cụ thể.

### 12.3 Chi phí API và tái lập

Không cần chọn model API đắt nhất ngay. Chạy pilot 50–100 query trên hai cấu hình, đo accuracy nhiệm vụ, hỗ trợ nguồn, latency và token; chọn bằng validation. Giữ model ID cụ thể, parameters và response thô để tái kiểm tra.

Công thức ngân sách là số query nhân với chi phí input tokens và output tokens theo biểu giá tại lúc chạy, cộng các lượt retry và evaluator. Ví dụ 300 query, ba cấu hình, một lượt mỗi cấu hình, trung bình 6.000 input và 800 output tokens sẽ tạo khoảng 5,4 triệu input cùng 0,72 triệu output tokens. Đây là phép tính planning, chưa phải hóa đơn hay báo giá nhà cung cấp. Chỉ chạy benchmark lớn sau pilot và giới hạn số retry.

## 13 Rủi ro chính và cách xử lý

| Rủi ro | Dấu hiệu trong dự án | Cách xử lý và phương án dự phòng |
| --- | --- | --- |
| Nhãn không khớp lời hứa bậc cao | Decagon chỉ có cặp | Đổi endpoint; HODDI là nhánh riêng |
| Thiếu target | 361/645 thuốc không có target | Thêm nguồn có provenance; fallback văn bản; báo coverage |
| Nhầm thực thể | Salt, ion, tên thương mại, chế phẩm phối hợp | Mapping nhiều tầng; lưu unresolved; kiểm tra thủ công danh mục demo |
| Graph path không đủ cho outcome | PPI unsigned và thiếu phenotype | Giới hạn claim; ưu tiên nguồn trực tiếp; gán insufficient |
| Rò rỉ nhãn | Cạnh test, alias, corpus, cache | Split trước feature; kiểm tra evidence theo mode và snapshot |
| Negative quá dễ | HODDI có nhiều thuốc chỉ ở lớp âm | Baseline shortcut, matched negatives, sensitivity analysis |
| Điểm số khó so sánh | Nhị phân, multi-class, multi-label trộn nhau | Cùng endpoint, split, negative và metric cho mọi baseline |
| Phụ thuộc nguồn không tải được | DrugBank academic paused; DDInter tải mẫu timeout | Dùng nguồn đang có; ChEMBL/DrugCentral/DailyMed; giới hạn scope |
| LLM trả lời quá chắc | Tự suy severity hoặc cơ chế | Schema, claim check, abstention và template fallback |
| Thí nghiệm vượt nguồn lực | GNN lớn, nhiều agents, quá nhiều model | Mốc A rồi B; chỉ một mở rộng sau baseline |

## 14 Những chỉnh sửa cần đưa vào báo cáo ý tưởng

Thay “predicts adverse effects for regimens of three or more drugs” bằng mô tả đúng endpoint đã chọn. Phân biệt kết quả lookup với prediction, thay ba Tier bằng trạng thái bằng chứng, bỏ các diễn giải “independent”, “amplified” và “arising only from the combined regimen” nếu không có thiết kế kiểm chứng tương ứng.

Sửa phần dữ liệu theo số đếm snapshot ở mục 4, thêm bước mapping ID và data coverage thay cho nhận định các bảng tự join là đã đủ sạch. Thay “clinical decision-support framework” bằng “research prototype for drug interaction prediction and evidence review” trong phạm vi hiện tại. Chuyển tuyên bố low latency thành mục tiêu cần đo.

Thêm protocol split, negative sampling, nguồn văn bản, chống leakage, baseline không LLM và kiểm tra claim. K-Paths, CBR-DDI, tensor factorization và DDI-Ben cần nằm trong nhóm đối chiếu trực tiếp. Không dùng kết quả drug repurposing để chứng minh hiệu quả của hệ dự đoán tác dụng phụ.

### Các lỗi hoặc điểm chưa xác nhận trong literature review

| Vị trí sheet LR | Vấn đề phát hiện | Hành động |
| --- | --- | --- |
| Hàng 25 cột K | Tensor factorization trỏ tới bài DSN-DDI | Dùng DOI 10.1093/bioinformatics/btae706 hoặc arXiv 2404.11374 [S04] |
| Hàng 42 cột K | HODDI trỏ tới arXiv 2406.00118 là ADEP | Thay bằng arXiv 2502.06274 [S07, S31] |
| Hàng 41 cột K | MGDN trỏ tới arXiv 2010.11711 là MIRACLE | Xác minh lại bài MGDN; chưa dùng chỉ số ở hàng này [S32] |
| Hàng 39 cột B và K | Link ACL có tên Learning to Describe for Predicting Zero-shot Drug-Drug Interactions | Sửa title/authors và kiểm tra lại phương pháp; chưa giữ nhãn PromptDDI [S30] |
| Hàng 7 cột J | Mô tả DDIAgents là lịch trình cố định | Điều chỉnh theo dynamic context flow của nguồn gốc [S13] |
| Hàng 31 cột K | Tên đường dẫn về nhận diện nhân tế bào ung thư không khớp DPSP | Xác minh lại nguồn trước khi trích chỉ số |
| Hàng 6 cột D | PolyLLM ghi 2024 trong khi bài đã tìm là năm 2025 | Kiểm tra metadata và repository đúng trước khi trích [S34] |
| Hàng 2 cột I và J | DDI-GPT có nhiều số liệu và kết luận latency | Toàn văn chưa truy cập được ở đợt này; không coi các số đó là đã xác minh [S06] |

Bảng LR là bản ghi nghiên cứu của nhóm, không phải nguồn sơ cấp. Một liên kết sai không chứng minh toàn bộ nội dung hàng sai, nhưng làm mất khả năng truy nguyên. Đợt này chỉ lập danh sách sửa; chưa thay đổi workbook gốc.

## 15 Quyết định triển khai sau báo cáo

**Tiến hành phương án B với A làm mốc đầu tiên.** Giới hạn lời hứa ở dự đoán nhãn cặp và tổng hợp bằng chứng trong đơn, đặt chất lượng đánh giá và giải thích làm trọng tâm. Giữ PPI khi có ích qua ablation; không xem nó là điều kiện bắt buộc cho mọi câu trả lời.

Chỉ chuyển trọng tâm sang C nếu nhóm chủ động chọn nghiên cứu tổ hợp 3–5 thuốc, có thêm thời gian cho kiểm toán negative và đánh giá theo report/thời gian. Khi đó, nên xem độ bền trước thay đổi negative sampling là một phần câu hỏi nghiên cứu; chưa hứa tìm ra biến cố chỉ xuất hiện vì cả tổ hợp.

Ba quyết định còn cần nhóm chốt là thời gian và phần cứng, mức độ yêu cầu huấn luyện của môn học, và có người kiểm tra nội dung dược học hay không. Các phần ETL, mapping, baseline, corpus và giao thức trong báo cáo đủ cụ thể để bắt đầu sau khi lựa chọn phạm vi.

## Phụ lục A Hồ sơ kiểm tra có thể tái lập

Thư mục `analysis/2026-10-08` chứa mã audit, thống kê JSON, phân bố nhãn CSV, độ phủ target và các nguồn bổ sung. Chạy các script từ project root bằng Python có pandas và numpy; các script chỉ đọc dữ liệu nguồn và ghi kết quả riêng.

- `audit_data.py`: kiểm toán ba CSV gốc và lấy mẫu tổ hợp seed 391.
- `audit_external.py`: kiểm toán targets-all, mono và HODDI v1 merged.
- `probe_hoddi_shortcut.py`: phép thử temporal với quy tắc độ phủ thuốc học từ train.
- `data_audit.json`, `external_data_audit.json`, `hoddi_shortcut_probe.json`: kết quả đầy đủ, gồm hash và số đếm.
- `effect_frequencies.csv`, `drug_target_coverage.csv`: bảng đối chiếu nhãn và thuốc.

SHA256 combo là `60bd3d071345473236f56638ebb732c3c964f0fd3468fdd29a444bcc1bf80d35`. Hash các tệp còn lại nằm trong JSON. HODDI dương có hash `03078648bd1376e480bb56f1dad34cbee03ef09b1b04af43d6df47e3b1b9294e`, trùng Git LFS pointer tại commit đã khóa. Nguồn công khai có thể cập nhật sau ngày nghiên cứu; cần dùng đúng snapshot khi tái lập.

Giới hạn của kiểm tra: chưa xác minh từng cạnh sinh học, chưa đánh giá clinical outcome, chưa huấn luyện các model đề xuất, chưa kiểm toán toàn bộ HODDI v2, chưa chứng minh tải đủ schema DDInter. Các thử nghiệm độ phủ dùng tổ hợp ngẫu nhiên; không nên suy chúng thành tần suất kê đơn ngoài thực tế.

## Phụ lục B Tài liệu và nguồn dữ liệu

Các nguồn dưới đây được kiểm tra trong đợt nghiên cứu ngày 08/10/2026. Nguồn dữ liệu cục bộ và phép tính độc lập được phân biệt với kết quả tác giả công bố. Những mục ghi “repository” hoặc “metadata” không có nghĩa đã tái lập toàn bộ nghiên cứu.

- [S01] Stanford SNAP. Decagon và các tệp tải chính thức. https://snap.stanford.edu/decagon/
- [S02] Zitnik, Agrawal, Leskovec. Modeling polypharmacy side effects with graph convolutional networks. 2018. https://arxiv.org/abs/1802.00543
- [S03] Stanford BioSNAP. Danh mục và thống kê các mạng. https://snap.stanford.edu/biodata/
- [S04] Lloyd, Liu, Gaunt. Fast Polypharmacy Side Effect Prediction Using Tensor Factorisation. 2024, bản v2. https://arxiv.org/html/2404.11374v2
- [S05] Xu, Sang, Lu. Tri-graph Information Propagation for Polypharmacy Side Effect Prediction. 2020. https://arxiv.org/abs/2001.10516
- [S06] DDI-GPT repository và liên kết bài gốc. https://github.com/Mew233/ddigpt ; DOI https://doi.org/10.1101/2024.12.06.627266 . Toàn văn gặp lỗi truy cập trong đợt này.
- [S07] Wang và cộng sự. HODDI. 2025, toàn văn v1. https://arxiv.org/html/2502.06274v1
- [S08] FDA. FAERS Public Dashboard FAQ. https://fis.fda.gov/extensions/FPD-FAQ-OCAC/FPD-FAQ-OCAC.html ; thông tin dữ liệu https://www.fda.gov/drugs/drug-approvals-and-databases/fda-adverse-event-reporting-system-faers-database
- [S09] TIML Group. HODDI repository. https://github.com/TIML-Group/HODDI/tree/700d0dafc74810fae3d06b1871b20a0f1df60646
- [S10] Abdullahi và cộng sự. K-Paths. KDD 2025; metadata v3 và phương pháp v1. https://arxiv.org/abs/2502.13344 ; https://arxiv.org/html/2502.13344v1
- [S11] Liu và cộng sự. Case-Based Reasoning Enhances the Predictive Power of LLMs in Drug-Drug Interaction. Preprint 2025. https://arxiv.org/html/2505.23034v1
- [S12] Wang, Yang, Yao. Accurate and interpretable drug-drug interaction prediction enabled by knowledge subgraph learning. Communications Medicine, 2024. https://www.nature.com/articles/s43856-024-00486-y
- [S13] Shen và cộng sự. DDIAgents. Preprint tháng 6/2026. https://arxiv.org/html/2606.31085v1
- [S14] Liu và cộng sự. DrugReason. Metadata preprint tháng 9/2026. https://arxiv.org/abs/2609.06779
- [S15] Shen và cộng sự. Benchmarking drug–drug interaction prediction methods a perspective of distribution changes. 2025. https://pmc.ncbi.nlm.nih.gov/articles/PMC12579548/ ; code https://github.com/LARS-research/DDI-Bench
- [S16] DDInter 2.0. Bài mô tả cơ sở dữ liệu. https://pmc.ncbi.nlm.nih.gov/articles/PMC11701621/
- [S17] DDInter 2.0. Trang tải. https://ddinter2.scbdd.com/download/
- [S18] DDInter 2.0. Điều khoản dữ liệu. https://ddinter2.scbdd.com/terms/
- [S19] PubChem. PUG REST. https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
- [S20] NLM. RxNorm và RxNav. https://www.nlm.nih.gov/research/umls/rxnorm/index.html ; thông báo DDI API https://lhncbc.nlm.nih.gov/RxNav/index.html
- [S21] DrugCentral. Tệp tải và license. https://www.drugcentral.org/download ; https://www.drugcentral.org/privacy
- [S22] EMBL EBI. ChEMBL và tài liệu web service. https://www.ebi.ac.uk/chembldb/ ; https://github.com/chembl/GLaDOS-docs/blob/master/web-services/chembl-data-web-services.md
- [S23] Reactome. Dữ liệu tải và điều khoản theo loại tài nguyên. https://reactome.org/download-data ; https://www.reactome.org/about/news/97-updated-license-agreement
- [S24] STRING. API, loại mạng và phiên bản. https://en.string-db.org/help/api/ ; https://string-db.org/cgi/download
- [S25] Chandak và cộng sự. Building a knowledge graph to enable precision medicine. Scientific Data, 2023. https://www.nature.com/articles/s41597-023-01960-3
- [S26] DrugBank. Trang phát hành và trạng thái academic downloads. https://go.drugbank.com/releases/latest
- [S27] NLM DailyMed. Web services. https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm ; danh sách SPL https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2/spls_api.cfm
- [S28] SIDER. Downloads. https://sideeffects.embl.de/download/
- [S29] NLM và ICH. UMLS mapping access và MedDRA. https://www.nlm.nih.gov/pubs/techbull/mj26/brief/mj26_snomed_meddra.html ; https://admin.ich.org/page/meddra
- [S30] ACL Anthology. Learning to Describe for Predicting Zero-shot Drug-Drug Interactions. 2023. https://aclanthology.org/2023.emnlp-main.918/
- [S31] Kobraei và cộng sự. ADEP. 2024. https://arxiv.org/abs/2406.00118
- [S32] MIRACLE. Multi-view Graph Contrastive Representation Learning for Drug-Drug Interaction Prediction. https://arxiv.org/abs/2010.11711
- [S33] Open Graph Benchmark. Link property prediction và ogbl-ddi. https://ogb.stanford.edu/docs/linkprop/
- [S34] Zhou và Xie. PolyLLM polypharmacy side effect prediction via LLM-based SMILES encodings. 2025. https://pmc.ncbi.nlm.nih.gov/articles/PMC12351685/
