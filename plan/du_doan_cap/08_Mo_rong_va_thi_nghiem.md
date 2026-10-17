# 08 — Mở rộng có kiểm soát sau bài toán lõi

Không là phụ thuộc của [05](05_DistMult_va_huan_luyen.md) hoặc [09](09_Ban_giao_va_duyet_theo_dot.md). Chỉ nhận tối đa một nhánh sau khi có kết quả baseline/DistMult và ngân sách còn lại.

## Đánh giá các hướng

| Hướng | Giá trị có thể có | Khó khăn | Quyết định v3 |
|---|---|---|---|
| Residual DistMult trên B0 | Kiểm tra phần bổ sung ngoài tần suất | Thêm loss/selection; chưa biết lợi ích | Ưu tiên nếu DistMult gần B0 |
| ChEMBL feature | Thêm thông tin cơ chế đơn thuốc | Thiếu coverage, mapping nhiễu | Phân tích trước, feature sau |
| Molecular fingerprints | Tương đồng cấu trúc, hướng thuốc mới | Dữ liệu ion/chất bất thường; cần split mới | Hoãn |
| GNN/PPI | Khai thác mạng sinh học | Target thiếu và panel rộng; nhiều tuning | Không thuộc lõi |
| DailyMed + RAG + LLM | Giải thích có nguồn | Duyệt claim và mapping tốn công | Giữ cache/code, hoãn sản phẩm |
| Binary DDI | UI dễ hiểu | Không có nhãn âm an toàn | Không suy ra từ Decagon vắng nhãn |
| Drug cold-start | Kiểm tra thuốc chưa học | DistMult ID không xử lý được | Protocol riêng về sau |

## E1 — Residual, một thí nghiệm mới có giới hạn

Nếu còn ngân sách trước final: p0=clip(B0_score/2,1e-4,1-1e-4), s=logit(p0)+DistMult(A,B,e).
p0 là biến đổi số học phục vụ offset, không phải xác suất được hiệu chuẩn. B0 được fit chỉ train và đóng băng. Giữ cùng sampler/loss/split; dùng dimension/lr đã chọn từ DistMult, không mở grid mới. So với cả B0 và DistMult.

Câu hỏi: phần tương tác học thêm có cải thiện ngoài prior từng thuốc không? Nếu không, dừng; không thử chuỗi biến thể vô hạn. Đăng ký E1 trước chạy và bổ sung lock nếu được chọn; sau final mọi thử nghiệm là exploratory.

## E2 — ChEMBL, ưu tiên audit tự động

Hiện 470 exact, 20 neutralized, 109 connectivity, 46 unmatched; 599 matched không đồng nghĩa 599 có cơ chế. Chỉ 271 có cơ chế và 218 có cơ chế trên người; giao giữa exact và human mechanisms cần tính, không lấy 218 làm coverage exact.

Bước rẻ: xuất bảng giao match_type × human mechanism × accession × train degree; phân tầng lỗi mô hình. Không cần duyệt từng dòng để dùng bảng thống kê nghiên cứu.

Nếu thử features: primary dùng exact InChIKey + human target accession có nguồn, action_type chuẩn hóa; mask thiếu. Connectivity/neutralized chưa xác minh để ngoài primary, chỉ sensitivity riêng. Dùng sparse indicators (accession, action_type), không dùng câu mô tả tương tác cặp từ corpus. Encoder và chuẩn hóa chỉ fit train; lưu vocabulary feature/hash. Không thay canonical Decagon IDs bằng ChEMBL parent IDs.

So model có/không features trên cùng toàn bộ cặp val, missing feature là zero + mask. Giữ các cặp thiếu feature, báo phân tầng. Không gọi cơ chế của từng thuốc là bằng chứng trực tiếp cho outcome cặp.

## Duyệt ít nhưng đúng chỗ

Nếu chuyên gia chỉ tham gia một lần, ưu tiên một bảng trường hợp mơ hồ có ảnh hưởng demo và các kết luận định viết trong báo cáo. Không yêu cầu duyệt 645 thuốc/129 chunks cho lõi. Không có người duyệt thì giữ ID và bỏ diễn giải cơ chế, benchmark vẫn tiếp tục.

Nguồn tham khảo phương pháp: [Decagon](https://arxiv.org/abs/1802.00543), [DistMult](https://arxiv.org/abs/1412.6575). Đây là định hướng thiết kế; lợi ích của E1/E2 phải đo trong repo, không suy từ kết quả bài báo.

Nghiệm thu mở rộng: registry trước chạy, source hashes, ablation cùng protocol, thêm tests leakage phù hợp và báo cả kết quả âm. Không biến nhánh mở rộng thành điều kiện bàn giao lõi.

