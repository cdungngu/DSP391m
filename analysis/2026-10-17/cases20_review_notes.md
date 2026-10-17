# Lô 20 ca val — tóm tắt cho đợt duyệt 1 (2026-10-17)

So sánh **B0 alpha0** (`b0_alpha0-db2b9c960215`, backend demo) với **DistMult d128 lr 0,01 seed 391** (`distmult_d128-dbd218398318`, không được promote). Chỉ val; không dùng test. Bảng từng ca: [cases20_v1.md](cases20_v1.md). Dữ liệu đầy đủ: `results/val/error_analysis/2026-10-17_cases20_v1.json`. Kiểm tra toàn val: `cases20_global_checks.py`.

Quy tắc chọn đã cố định trong `src/dsp391m/cases.py`: 5 ca NDCG@10 tăng nhiều nhất, 5 ca giảm nhiều nhất, 5 ca bậc train thấp (tertile dưới, hoán vị seed 391), 5 ca ngẫu nhiên. Không có ca trùng, nên không phải bù.

## Quan sát (kỹ thuật, chưa phải nhận định chuyên môn)

1. **Hai model khác nhau về kiểu danh sách.** B0 dùng 220 nhãn khác nhau cho top-10 trên toàn val; "arterial pressure NOS decreased" có ở 81% cặp, anaemia 69%. DistMult dùng 961 nhãn, trung vị tần suất train của nhãn top-10 là 0,106 so 0,371 của B0. B0 gần như danh sách chung theo tần suất; DistMult cụ thể hơn theo cặp nhưng trượt nhiều hơn (NDCG@10 = 0 ở 11,6% cặp so 3,4%).
2. **Chênh lệch theo ca rất cực đoan.** Nhóm improve: DistMult trúng 10/10 nhãn quan sát, B0 1–2/10 (ví dụ vincristine + sodium bicarbonate). Nhóm decline: DistMult 0–2/10, B0 8–10/10 (aspirin + felodipine, clomiphene + omeprazole). Trung bình thì B0 tốt hơn ở top-10 (NDCG@10 0,526 so 0,413).
3. **Cụm nhãn lạ.** decline-01: DistMult xếp đầu Caesarean Section, still birth, neonatal respiratory distress, có vẻ là một cụm nhãn đi cùng nhau trong dữ liệu (bệnh cảnh bệnh nhân/thai kỳ) chứ không phải tác dụng phụ của cặp. Đúng dạng nhãn bệnh nền đã ghi trong CLAUDE.md; cần người có chuyên môn xem.
4. **Nhãn chung chung ở B0.** B0 đẩy các nhãn phổ biến (huyết áp giảm, thiếu máu, khó thở, buồn nôn) lên đầu cho gần mọi cặp; điểm cao không có nghĩa là đặc thù cho cặp.
5. **Tên thuốc cờ "ok" vẫn sai dạng.** 19/420 tên `needs_review=False` không phù hợp hiển thị, ít nhất 8 sai rõ: `Rapamycin-d3`, `Tacrolimus-13C,D2` (đồng vị), bốn tên "Impurity" (ví dụ `Gaspofungin Impurity F` cho CID005311039), `loperamide(1+)`, `dantrolene(1-)`. Demo phải hiện kèm ID và không coi `needs_review=False` là đã duyệt.
6. **Thuốc chưa có tên** (CID000004052, CID000060787, CID000002631, …) xuất hiện ở 7/20 ca; một số ca nhóm low_degree có cả hai thuốc chỉ có ID.

## Câu hỏi cho người xem (đợt 1)

- Với 3–5 ca, nhãn top-10 nào là bệnh nền/chỉ định thay vì tác dụng phụ của cặp? Chỉ ghi vào cột "Ghi chú người xem"; không gán đúng/sai cho từng nhãn.
- Hiển thị demo: có nên ẩn hoặc đánh dấu nhãn xuất hiện ở > 50% cặp (kiểu "arterial pressure NOS decreased") không?
- Có chấp nhận dùng ID thay tên cho các thuốc tên lỗi trong demo, chờ duyệt sau không?

Không coi phần xem này là duyệt mapping hay kiểm định lâm sàng (plan 09).
