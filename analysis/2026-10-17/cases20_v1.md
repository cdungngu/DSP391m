# Lô 20 ca val — b0_alpha0-db2b9c960215 vs distmult_d128-dbd218398318

Tạo 2026-10-17T07:07:03+00:00 · commit `b768afb1b4` · split hash `3362fa700fa27f78` · seed 391. Chỉ val; không dùng test.

**Quy tắc chọn:** (cố định trước khi xem ca):
- delta = NDCG@10(cand) − NDCG@10(base) theo từng cặp val (cặp không có nhãn quan sát bị loại).
- improve: delta lớn nhất; decline: delta nhỏ nhất (hòa: drug_a, drug_b tăng dần).
- low_degree: cặp có bậc train nhỏ hơn của hai thuốc nằm ở tertile thấp (ngưỡng tính trên cặp train), thứ tự
  hoán vị default_rng([seed, 1]); random: mọi cặp val, hoán vị default_rng([seed, 2]).
- Điền theo thứ tự improve → decline → low_degree → random; cặp đã chọn thì lấy cặp kế tiếp trong chính nhóm đó.

**Cách đọc:** Nhãn quan sát của Decagon là ground truth giả định; nhãn không quan sát trong top-10 không chứng minh sai. Ca để phát hiện nhãn bệnh nền, thuốc mơ hồ, dự đoán giống nhau và hiển thị gây hiểu sai; không phải đánh giá đúng/sai y khoa. ✓ = nhãn có quan sát trên val cho cặp này.

## improve-01: **vincristine** (`CID000005978`, bậc train 174, 23 target) + **sodium bicarbonate** (`CID000008953`, bậc train 182, 0 target; cấu trúc: multi_component)

Nhãn quan sát: 55 · bậc train nhỏ hơn: 174 · NDCG@10 0.069 → 1.000 (Δ +0.931) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | anaemia (`C0002871`) | 1.085 | ✓ xerosis (`C0259817`) | 13.277 |
| 2 | arterial pressure NOS decreased (`C0020649`) | 0.972 | ✓ contracture (`C0009917`) | 9.326 |
| 3 | body temperature increased (`C0015967`) | 0.934 | ✓ fib (`C0016059`) | 7.479 |
| 4 | sepsis (`C0243026`) | 0.870 | ✓ kidney transplant (`C0022671`) | 7.036 |
| 5 | neumonia (`C0032285`) | 0.854 | ✓ lung fibrosis (`C0034069`) | 3.678 |
| 6 | bone marrow failure (`C0030312`) | 0.816 | ✓ mitral valve disease NOS (`C0026265`) | 3.621 |
| 7 | heart rate increased (`C0039231`) | 0.806 | ✓ pleural fibrosis (`C0264545`) | 3.582 |
| 8 | ✓ Neutropenia (`C0027947`) | 0.792 | ✓ asystole (`C0018790`) | 3.139 |
| 9 | thrombocytopenia (`C0040034`) | 0.748 | ✓ nephrocalcinosis (`C0027709`) | 3.076 |
| 10 | kidney failure (`C0035078`) | 0.748 | ✓ hepatic necrosis (`C0151798`) | 2.962 |

Ghi chú người xem: _…_

## improve-02: **ketoconazole** (`CID000003823`, bậc train 127, 0 target) + **Olmesartan medoxomil** (`CID000130881`, bậc train 215, 2 target)

Nhãn quan sát: 25 · bậc train nhỏ hơn: 127 · NDCG@10 0.095 → 1.000 (Δ +0.905) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | arterial pressure NOS decreased (`C0020649`) | 0.909 | ✓ Vestibular disorder (`C0042594`) | 23.236 |
| 2 | pleural pain (`C0008033`) | 0.865 | ✓ Superficial thrombophlebitis (`C1510431`) | 16.112 |
| 3 | Pain (`C0030193`) | 0.863 | ✓ osteomalacia (`C0029442`) | 12.228 |
| 4 | ✓ dizziness (`C0012833`) | 0.856 | ✓ angiitis (`C0042384`) | 8.185 |
| 5 | Difficulty breathing (`C0013404`) | 0.844 | ✓ Phlebitis (`C0031542`) | 8.040 |
| 6 | asthenia (`C0004093`) | 0.837 | ✓ bronchial spasm (`C0006266`) | 6.055 |
| 7 | High blood pressure (`C0020538`) | 0.791 | ✓ glaucoma (`C0017601`) | 5.680 |
| 8 | emesis (`C0042963`) | 0.790 | ✓ arthritis (`C0003864`) | 5.650 |
| 9 | Fatigue (`C0015672`) | 0.789 | ✓ neuropathy peripheral (`C0031117`) | 5.498 |
| 10 | nausea (`C0027497`) | 0.789 | ✓ hypochloraemia (`C0085680`) | 5.098 |

Ghi chú người xem: _…_

## improve-03: **CID000004052** (`CID000004052`, bậc train 269, 0 target; tên chờ duyệt; ChEMBL: none) + **mupirocin** (`CID000004264`, bậc train 83, 0 target; tên chờ duyệt; ChEMBL: connectivity)

Nhãn quan sát: 26 · bậc train nhỏ hơn: 83 · NDCG@10 0.139 → 1.000 (Δ +0.861) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | anaemia (`C0002871`) | 0.913 | ✓ Vestibular disorder (`C0042594`) | 30.762 |
| 2 | ✓ kidney failure (`C0035078`) | 0.872 | ✓ Superficial thrombophlebitis (`C1510431`) | 18.779 |
| 3 | arterial pressure NOS decreased (`C0020649`) | 0.847 | ✓ osteomalacia (`C0029442`) | 14.312 |
| 4 | nausea (`C0027497`) | 0.815 | ✓ Phlebitis (`C0031542`) | 8.508 |
| 5 | AFIB (`C0004238`) | 0.799 | ✓ angiitis (`C0042384`) | 8.420 |
| 6 | emesis (`C0042963`) | 0.756 | ✓ glaucoma (`C0017601`) | 7.651 |
| 7 | Pain (`C0030193`) | 0.747 | ✓ arthritis (`C0003864`) | 6.549 |
| 8 | High blood pressure (`C0020538`) | 0.739 | ✓ cholelithiasis (`C0008350`) | 6.446 |
| 9 | cellulitis (`C0007642`) | 0.737 | ✓ hypochloraemia (`C0085680`) | 5.807 |
| 10 | Pleural Effusion (`C0032227`) | 0.732 | ✓ bronchial spasm (`C0006266`) | 5.485 |

Ghi chú người xem: _…_

## improve-04: **azelastine** (`CID000002267`, bậc train 75, 7 target) + **Atrovent Hfa** (`CID000003746`, bậc train 287, 6 target; cấu trúc: charged)

Nhãn quan sát: 122 · bậc train nhỏ hơn: 75 · NDCG@10 0.173 → 1.000 (Δ +0.827) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | Pain (`C0030193`) | 1.174 | ✓ hair disease (`C0018500`) | 11.958 |
| 2 | neumonia (`C0032285`) | 1.063 | ✓ atrial ectopic beats (`C0033036`) | 9.204 |
| 3 | Back Ache (`C0004604`) | 1.049 | ✓ eyelid diseases (`C0015423`) | 9.141 |
| 4 | ✓ chest pain (`C0008031`) | 1.033 | ✓ hyperkeratosis (`C0870082`) | 8.822 |
| 5 | edema extremities (`C0085649`) | 1.016 | ✓ lichen planus (`C0023646`) | 8.629 |
| 6 | ✓ Difficulty breathing (`C0013404`) | 1.001 | ✓ Seroma (`C0262627`) | 7.924 |
| 7 | arterial pressure NOS decreased (`C0020649`) | 0.981 | ✓ Nail disorder (`C0027339`) | 7.489 |
| 8 | Aching joints (`C0003862`) | 0.979 | ✓ actinic keratosis (`C0022602`) | 6.831 |
| 9 | muscle spasm (`C0037763`) | 0.927 | ✓ seborrhoeic keratosis (`C0022603`) | 6.579 |
| 10 | Fatigue (`C0015672`) | 0.889 | ✓ diverticulosis (`C1510475`) | 5.943 |

Ghi chú người xem: _…_

## improve-05: **verapamil** (`CID000002520`, bậc train 285, 183 target; panel target rộng) + **loperamide(1+)** (`CID000003954`, bậc train 265, 161 target; cấu trúc: charged; ChEMBL: neutralized; panel target rộng)

Nhãn quan sát: 94 · bậc train nhỏ hơn: 265 · NDCG@10 0.195 → 1.000 (Δ +0.805) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | Difficulty breathing (`C0013404`) | 0.945 | ✓ als (`C0002736`) | 4.938 |
| 2 | Fatigue (`C0015672`) | 0.880 | ✓ polymyositis (`C0085655`) | 4.902 |
| 3 | ✓ asthenia (`C0004093`) | 0.863 | ✓ hyperaesthesia (`C0020453`) | 3.597 |
| 4 | nausea (`C0027497`) | 0.858 | ✓ dermatomyositis (`C0011633`) | 3.269 |
| 5 | ✓ emesis (`C0042963`) | 0.852 | ✓ glucosuria (`C0017979`) | 2.680 |
| 6 | anaemia (`C0002871`) | 0.844 | ✓ haemorrhoids (`C0019112`) | 2.316 |
| 7 | diarrhea (`C0011991`) | 0.827 | ✓ burning sensation (`C0085624`) | 2.280 |
| 8 | neumonia (`C0032285`) | 0.817 | ✓ aching muscles (`C0231528`) | 2.257 |
| 9 | arterial pressure NOS decreased (`C0020649`) | 0.817 | ✓ bundle branch block right (`C0085615`) | 2.242 |
| 10 | heart rate increased (`C0039231`) | 0.736 | ✓ eating disorder (`C0013473`) | 2.222 |

Ghi chú người xem: _…_

## decline-01: **CID000060787** (`CID000060787`, bậc train 76, 0 target; tên chờ duyệt) + **Gaspofungin Impurity F** (`CID005311039`, bậc train 80, 0 target; ChEMBL: none)

Nhãn quan sát: 2 · bậc train nhỏ hơn: 76 · NDCG@10 1.000 → 0.000 (Δ -1.000) · top-10 trùng 2/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | ✓ thrombocytopenia (`C0040034`) | 0.920 | Caesarean Section (`C0007876`) | 1.013 |
| 2 | ✓ anaemia (`C0002871`) | 0.886 | multifocal leukoencephalopathy (`C0023524`) | 0.429 |
| 3 | body temperature increased (`C0015967`) | 0.828 | icterus (`C0022346`) | 0.217 |
| 4 | Aspartate Aminotransferase Increase (`C0151904`) | 0.793 | aspergillosis (`C0004030`) | -0.268 |
| 5 | Bleeding (`C0019080`) | 0.778 | still birth (`C0595939`) | -0.276 |
| 6 | abdominal pain (`C0000737`) | 0.763 | neonatal respiratory distress syndrome (`C0035220`) | -0.279 |
| 7 | sepsis (`C0243026`) | 0.643 | Bleeding (`C0019080`) | -0.415 |
| 8 | confusion (`C0009676`) | 0.621 | Hepatitis C (`C0019196`) | -0.560 |
| 9 | diarrhea (`C0011991`) | 0.617 | Acidosis (`C0001122`) | -0.638 |
| 10 | neumonia (`C0032285`) | 0.612 | diarrhea (`C0011991`) | -0.671 |

Ghi chú người xem: _…_

## decline-02: **clomiphene** (`CID000002800`, bậc train 17, 0 target) + **omeprazole** (`CID000004594`, bậc train 399, 1 target)

Nhãn quan sát: 25 · bậc train nhỏ hơn: 17 · NDCG@10 1.000 → 0.110 (Δ -0.890) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | ✓ Hypoventilation (`C0398353`) | 0.995 | ventricular septal defect (`C0018818`) | 7.365 |
| 2 | ✓ Fatigue (`C0015672`) | 0.808 | apraxia (`C0003635`) | 6.453 |
| 3 | ✓ muscle weakness (`C0151786`) | 0.751 | ✓ neck mass (`C0149736`) | 6.354 |
| 4 | ✓ confusion (`C0009676`) | 0.701 | birth defect (`C0000768`) | 6.211 |
| 5 | ✓ agitated (`C0085631`) | 0.671 | congenital heart disease (`C0152021`) | 6.071 |
| 6 | ✓ dizziness (`C0012833`) | 0.654 | abortion spontaneous (`C0000786`) | 5.616 |
| 7 | ✓ Feeling unwell (`C0231218`) | 0.649 | neonatal respiratory distress syndrome (`C0035220`) | 5.529 |
| 8 | ✓ tremor (`C0040822`) | 0.637 | blepharoptosis (`C0005745`) | 5.292 |
| 9 | ✓ Amnesia (`C0002622`) | 0.627 | autonomic instability (`C0262385`) | 4.738 |
| 10 | ✓ neuropathy peripheral (`C0031117`) | 0.620 | patent ductus arteriosis (`C0013274`) | 4.226 |

Ghi chú người xem: _…_

## decline-03: **isoniazid** (`CID000003767`, bậc train 139, 3 target) + **Rapamycin-d3** (`CID000005040`, bậc train 122, 0 target)

Nhãn quan sát: 41 · bậc train nhỏ hơn: 122 · NDCG@10 0.870 → 0.000 (Δ -0.870) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | ✓ anaemia (`C0002871`) | 0.948 | congenital heart disease (`C0152021`) | 3.381 |
| 2 | ✓ diarrhea (`C0011991`) | 0.768 | bronchiolitis (`C0006271`) | 3.170 |
| 3 | ✓ neumonia (`C0032285`) | 0.743 | brain abscess (`C0006105`) | 3.018 |
| 4 | ✓ body temperature increased (`C0015967`) | 0.738 | Lyell (`C0014518`) | 2.460 |
| 5 | ✓ emesis (`C0042963`) | 0.690 | Mycobacterium tuberculosis infection (`C0041296`) | 2.402 |
| 6 | ✓ thrombocytopenia (`C0040034`) | 0.673 | anaemia hypochromic (`C0002884`) | 2.218 |
| 7 | ✓ dehydration (`C0011175`) | 0.673 | obstructive uropathy (`C0178879`) | 2.174 |
| 8 | ✓ hyperglycaemia (`C0020456`) | 0.654 | Pneumocystis carinii pneumonia (`C0032305`) | 2.147 |
| 9 | Neutropenia (`C0027947`) | 0.626 | uterine bleeding (`C0042134`) | 2.080 |
| 10 | nausea (`C0027497`) | 0.617 | encephalitis (`C0014038`) | 2.045 |

Ghi chú người xem: _…_

## decline-04: **Mulfasin** (`CID000004138`, bậc train 94, 0 target) + **rofecoxib** (`CID000005090`, bậc train 315, 167 target; panel target rộng)

Nhãn quan sát: 104 · bậc train nhỏ hơn: 94 · NDCG@10 1.000 → 0.133 (Δ -0.867) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | ✓ Difficulty breathing (`C0013404`) | 1.019 | pyuria (`C0034359`) | 4.063 |
| 2 | ✓ anaemia (`C0002871`) | 1.013 | patent ductus arteriosis (`C0013274`) | 3.687 |
| 3 | ✓ arterial pressure NOS decreased (`C0020649`) | 0.917 | Chest wall pain (`C0008035`) | 2.708 |
| 4 | ✓ edema extremities (`C0085649`) | 0.915 | neonatal respiratory distress syndrome (`C0035220`) | 2.556 |
| 5 | ✓ nausea (`C0027497`) | 0.899 | atrial ectopic beats (`C0033036`) | 2.543 |
| 6 | ✓ abdominal pain (`C0000737`) | 0.888 | congenital heart disease (`C0152021`) | 2.351 |
| 7 | ✓ pleural pain (`C0008033`) | 0.885 | ventricular septal defect (`C0018818`) | 2.272 |
| 8 | ✓ edema (`C0013604`) | 0.871 | ✓ umbilical hernia (`C0019322`) | 2.247 |
| 9 | ✓ constipated (`C0009806`) | 0.868 | mitral valve disease NOS (`C0026265`) | 2.013 |
| 10 | ✓ neumonia (`C0032285`) | 0.804 | ✓ obesity (`C0028754`) | 2.011 |

Ghi chú người xem: _…_

## decline-05: **aspirin** (`CID000002244`, bậc train 351, 10 target) + **felodipine** (`CID000003333`, bậc train 219, 1 target)

Nhãn quan sát: 42 · bậc train nhỏ hơn: 219 · NDCG@10 0.864 → 0.000 (Δ -0.864) · top-10 trùng 1/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | ✓ Difficulty breathing (`C0013404`) | 1.044 | sick sinus syndrome (`C0037052`) | 4.376 |
| 2 | ✓ arterial pressure NOS decreased (`C0020649`) | 1.023 | Diabetic Retinopathy (`C0011884`) | 3.441 |
| 3 | ✓ anaemia (`C0002871`) | 1.020 | external ear infection (`C0029878`) | 3.091 |
| 4 | ✓ chest pain (`C0008031`) | 0.917 | hernia (`C0019270`) | 2.762 |
| 5 | ✓ heart attack (`C0027051`) | 0.915 | allergic rhinitis (`C0002103`) | 2.711 |
| 6 | ✓ Cardiac decompensation (`C0018802`) | 0.864 | AFIB (`C0004238`) | 2.665 |
| 7 | ✓ acute kidney failure (`C0022660`) | 0.863 | atrial flutter (`C0004239`) | 2.509 |
| 8 | neumonia (`C0032285`) | 0.827 | Hernia Inguinal (`C0019294`) | 2.352 |
| 9 | AFIB (`C0004238`) | 0.816 | colonic polyp (`C0009376`) | 2.326 |
| 10 | ✓ apoplexy (`C0038454`) | 0.811 | melanocytic naevus (`C0027962`) | 2.229 |

Ghi chú người xem: _…_

## low_degree-01: **miconazole** (`CID000004189`, bậc train 81, 62 target) + **morphine** (`CID000004253`, bậc train 361, 0 target; tên chờ duyệt; ChEMBL: connectivity)

Nhãn quan sát: 55 · bậc train nhỏ hơn: 81 · NDCG@10 0.303 → 0.779 (Δ +0.476) · top-10 trùng 1/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | neumonia (`C0032285`) | 1.099 | ✓ angiopathy (`C0042373`) | 5.042 |
| 2 | anaemia (`C0002871`) | 1.011 | ✓ dysphasia (`C0973461`) | 3.812 |
| 3 | thrombocytopenia (`C0040034`) | 0.971 | ✓ carotid artery stenosis (`C0007282`) | 3.383 |
| 4 | arterial pressure NOS decreased (`C0020649`) | 0.967 | ✓ hemiplegia (`C0018991`) | 3.344 |
| 5 | ✓ diarrhea (`C0011991`) | 0.876 | neumonia (`C0032285`) | 2.712 |
| 6 | ✓ acute kidney failure (`C0022660`) | 0.856 | ✓ palsies (`C0522224`) | 2.691 |
| 7 | ✓ Difficulty breathing (`C0013404`) | 0.841 | ✓ Chest infection (`C0149725`) | 2.687 |
| 8 | body temperature increased (`C0015967`) | 0.784 | Bacterial infection (`C0004623`) | 2.570 |
| 9 | ✓ confusion (`C0009676`) | 0.753 | lobar pneumonia (`C0032300`) | 2.514 |
| 10 | sepsis (`C0243026`) | 0.722 | ✓ aspiration pneumonia (`C0032290`) | 2.461 |

Ghi chú người xem: _…_

## low_degree-02: **DL-Thyroxine** (`CID000000853`, bậc train 408, 0 target) + **nitrazepam** (`CID000004506`, bậc train 107, 0 target)

Nhãn quan sát: 50 · bậc train nhỏ hơn: 107 · NDCG@10 0.000 → 0.000 (Δ +0.000) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | arterial pressure NOS decreased (`C0020649`) | 0.724 | epilepsy (`C0014544`) | 2.144 |
| 2 | nausea (`C0027497`) | 0.695 | attempted suicide (`C0038663`) | 1.814 |
| 3 | neumonia (`C0032285`) | 0.674 | status epilepticus (`C0038220`) | 1.709 |
| 4 | anaemia (`C0002871`) | 0.672 | psychoses (`C0033975`) | 1.655 |
| 5 | body temperature increased (`C0015967`) | 0.666 | Lyell (`C0014518`) | 1.523 |
| 6 | edema (`C0013604`) | 0.646 | sleep disorder (`C0851578`) | 1.521 |
| 7 | emesis (`C0042963`) | 0.631 | galactorrhea (`C0235660`) | 1.520 |
| 8 | Difficulty breathing (`C0013404`) | 0.580 | schizophrenia (`C0036341`) | 1.510 |
| 9 | constipated (`C0009806`) | 0.569 | carcinoid syndrome (`C0024586`) | 1.405 |
| 10 | Anorexia (`C0003123`) | 0.567 | cognitive disorder (`C0009241`) | 1.337 |

Ghi chú người xem: _…_

## low_degree-03: **diazepam** (`CID000003016`, bậc train 356, 33 target) + **CID000004451** (`CID000004451`, bậc train 41, 0 target; tên chờ duyệt)

Nhãn quan sát: 10 · bậc train nhỏ hơn: 41 · NDCG@10 0.064 → 0.000 (Δ -0.064) · top-10 trùng 1/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | Pain (`C0030193`) | 0.885 | Hepatitis C (`C0019196`) | 1.790 |
| 2 | Difficulty breathing (`C0013404`) | 0.868 | ketoacidosis (`C0220982`) | 1.623 |
| 3 | dizziness (`C0012833`) | 0.849 | Caesarean Section (`C0007876`) | 1.322 |
| 4 | nausea (`C0027497`) | 0.839 | dizziness (`C0012833`) | 1.263 |
| 5 | pleural pain (`C0008033`) | 0.838 | insomnia (`C0917801`) | 1.180 |
| 6 | anaemia (`C0002871`) | 0.811 | macrocytosis (`C0085662`) | 1.177 |
| 7 | confusion (`C0009676`) | 0.800 | drug withdrawal (`C0152128`) | 1.121 |
| 8 | diarrhea (`C0011991`) | 0.794 | abortion spontaneous (`C0000786`) | 1.081 |
| 9 | Hypoventilation (`C0398353`) | 0.779 | HIV disease (`C0019693`) | 1.013 |
| 10 | ✓ abdominal pain (`C0000737`) | 0.773 | patent ductus arteriosis (`C0013274`) | 0.994 |

Ghi chú người xem: _…_

## low_degree-04: **CID000002631** (`CID000002631`, bậc train 86, 0 target; tên chờ duyệt; cấu trúc: charged; ChEMBL: neutralized) + **CID000003937** (`CID000003937`, bậc train 376, 1 target; tên chờ duyệt)

Nhãn quan sát: 59 · bậc train nhỏ hơn: 86 · NDCG@10 0.775 → 0.218 (Δ -0.557) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | ✓ sepsis (`C0243026`) | 0.929 | hydroureter (`C0521620`) | 3.278 |
| 2 | ✓ body temperature increased (`C0015967`) | 0.857 | hypernatraemia (`C0020488`) | 2.537 |
| 3 | ✓ Difficulty breathing (`C0013404`) | 0.853 | patent ductus arteriosis (`C0013274`) | 2.471 |
| 4 | kidney failure (`C0035078`) | 0.827 | neonatal respiratory distress syndrome (`C0035220`) | 2.128 |
| 5 | ✓ anaemia (`C0002871`) | 0.800 | agranulocytoses (`C0001824`) | 1.924 |
| 6 | ✓ arterial pressure NOS decreased (`C0020649`) | 0.798 | ✓ Excess potassium (`C0020461`) | 1.919 |
| 7 | ✓ acute kidney failure (`C0022660`) | 0.785 | ✓ leucocytosis (`C0023518`) | 1.918 |
| 8 | ✓ edema (`C0013604`) | 0.778 | Lyell (`C0014518`) | 1.877 |
| 9 | neumonia (`C0032285`) | 0.765 | ✓ rhabdomyolysis (`C0035410`) | 1.783 |
| 10 | confusion (`C0009676`) | 0.745 | Acute Respiratory Distress Syndrome (`C0035222`) | 1.704 |

Ghi chú người xem: _…_

## low_degree-05: **metformin** (`CID000004091`, bậc train 317, 0 target) + **Erlotinib** (`CID000176870`, bậc train 97, 38 target)

Nhãn quan sát: 38 · bậc train nhỏ hơn: 97 · NDCG@10 0.420 → 0.365 (Δ -0.055) · top-10 trùng 2/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | Difficulty breathing (`C0013404`) | 1.105 | ✓ dry skin (`C0151908`) | 2.232 |
| 2 | anaemia (`C0002871`) | 0.989 | coughing blood (`C0019079`) | 1.844 |
| 3 | ✓ diarrhea (`C0011991`) | 0.964 | Acne (`C0702166`) | 1.765 |
| 4 | ✓ dehydration (`C0011175`) | 0.959 | Neutropenia (`C0027947`) | 1.763 |
| 5 | ✓ Fatigue (`C0015672`) | 0.906 | mucositis oral (`C0038362`) | 1.746 |
| 6 | neumonia (`C0032285`) | 0.899 | ✓ diarrhea (`C0011991`) | 1.647 |
| 7 | asthenia (`C0004093`) | 0.898 | cutaneous candidiasis (`C0006846`) | 1.633 |
| 8 | arterial pressure NOS decreased (`C0020649`) | 0.830 | Anorexia (`C0003123`) | 1.484 |
| 9 | ✓ Pain (`C0030193`) | 0.808 | ✓ dehydration (`C0011175`) | 1.442 |
| 10 | ✓ Cough (`C0010200`) | 0.767 | ild (`C0206062`) | 1.432 |

Ghi chú người xem: _…_

## random-01: **cimetidine** (`CID000002756`, bậc train 165, 15 target) + **granisetron** (`CID000003510`, bậc train 117, 24 target)

Nhãn quan sát: 63 · bậc train nhỏ hơn: 117 · NDCG@10 0.695 → 0.354 (Δ -0.341) · top-10 trùng 2/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | emesis (`C0042963`) | 1.146 | optic atrophy (`C0029124`) | 2.587 |
| 2 | ✓ diarrhea (`C0011991`) | 1.058 | ADH inappropriate (`C0021141`) | 2.438 |
| 3 | ✓ Neutropenia (`C0027947`) | 1.036 | ✓ Neutropenia (`C0027947`) | 2.366 |
| 4 | ✓ nausea (`C0027497`) | 1.030 | ✓ neoplasia (`C0027651`) | 2.080 |
| 5 | arterial pressure NOS decreased (`C0020649`) | 1.000 | ✓ lung neoplasm malignant (`C0242379`) | 2.015 |
| 6 | ✓ Fatigue (`C0015672`) | 0.992 | haematochezia (`C0018932`) | 2.014 |
| 7 | ✓ thrombocytopenia (`C0040034`) | 0.977 | Bleeding gums (`C0017565`) | 2.011 |
| 8 | ✓ anaemia (`C0002871`) | 0.974 | colonic obstruction (`C0235328`) | 1.936 |
| 9 | ✓ pleural pain (`C0008033`) | 0.944 | erythema (`C0041834`) | 1.897 |
| 10 | ✓ Pain (`C0030193`) | 0.930 | ✓ anaemia (`C0002871`) | 1.792 |

Ghi chú người xem: _…_

## random-02: **amiodarone** (`CID000002156`, bậc train 165, 21 target; tên chờ duyệt; cấu trúc: charged; ChEMBL: neutralized) + **CID000003161** (`CID000003161`, bậc train 241, 0 target; tên chờ duyệt; ChEMBL: connectivity)

Nhãn quan sát: 50 · bậc train nhỏ hơn: 165 · NDCG@10 0.608 → 0.217 (Δ -0.391) · top-10 trùng 3/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | ✓ arterial pressure NOS decreased (`C0020649`) | 1.198 | AFIB (`C0004238`) | 2.218 |
| 2 | AFIB (`C0004238`) | 1.134 | ✓ Cardiac decompensation (`C0018802`) | 2.143 |
| 3 | neumonia (`C0032285`) | 1.063 | bundle branch block right (`C0085615`) | 1.941 |
| 4 | ✓ Difficulty breathing (`C0013404`) | 1.009 | Pleural Effusion (`C0032227`) | 1.917 |
| 5 | ✓ Cardiac decompensation (`C0018802`) | 0.947 | kidney failure (`C0035078`) | 1.823 |
| 6 | ✓ asthenia (`C0004093`) | 0.898 | ✓ chronic obstructive airway disease (`C0024117`) | 1.812 |
| 7 | kidney failure (`C0035078`) | 0.868 | ventricular fibrillation (`C0042510`) | 1.779 |
| 8 | anaemia (`C0002871`) | 0.853 | tachycardia ventricular (`C0042514`) | 1.639 |
| 9 | ✓ chest pain (`C0008031`) | 0.850 | haematoma (`C0018944`) | 1.558 |
| 10 | ✓ emesis (`C0042963`) | 0.837 | atrioventricular block (`C0004245`) | 1.545 |

Ghi chú người xem: _…_

## random-03: **Tacrolimus-13C,D2** (`CID000005372`, bậc train 249, 0 target; ChEMBL: connectivity) + **CID005381226** (`CID005381226`, bậc train 120, 6 target; tên chờ duyệt; ChEMBL: none)

Nhãn quan sát: 60 · bậc train nhỏ hơn: 120 · NDCG@10 0.389 → 0.139 (Δ -0.250) · top-10 trùng 0/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | anaemia (`C0002871`) | 0.902 | Mycobacterium tuberculosis infection (`C0041296`) | 2.336 |
| 2 | thrombocytopenia (`C0040034`) | 0.774 | ✓ encephalitis (`C0014038`) | 2.255 |
| 3 | kidney failure (`C0035078`) | 0.774 | Bacteraemia (`C0004610`) | 2.239 |
| 4 | ✓ acute kidney failure (`C0022660`) | 0.724 | brain abscess (`C0006105`) | 2.188 |
| 5 | ✓ arterial pressure NOS decreased (`C0020649`) | 0.719 | glomerulonephritis (`C0017658`) | 2.132 |
| 6 | Neutropenia (`C0027947`) | 0.715 | pneumonia staphylococcal (`C0032308`) | 1.999 |
| 7 | ✓ abdominal pain (`C0000737`) | 0.703 | Arthritis bacterial (`C0003874`) | 1.923 |
| 8 | ✓ nausea (`C0027497`) | 0.693 | cryptococcosis (`C0010414`) | 1.849 |
| 9 | ✓ emesis (`C0042963`) | 0.686 | eosinophilic pneumonia (`C1527407`) | 1.746 |
| 10 | Pleural Effusion (`C0032227`) | 0.683 | Lyell (`C0014518`) | 1.688 |

Ghi chú người xem: _…_

## random-04: **morphine** (`CID000004253`, bậc train 361, 0 target; tên chờ duyệt; ChEMBL: connectivity) + **CID000005512** (`CID000005512`, bậc train 240, 0 target; tên chờ duyệt)

Nhãn quan sát: 159 · bậc train nhỏ hơn: 240 · NDCG@10 0.371 → 0.915 (Δ +0.543) · top-10 trùng 1/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | ✓ neumonia (`C0032285`) | 1.109 | ✓ metabolic alkalosis (`C0220983`) | 4.404 |
| 2 | arterial pressure NOS decreased (`C0020649`) | 1.055 | ✓ pain pelvic (`C0030794`) | 3.000 |
| 3 | anaemia (`C0002871`) | 0.962 | ✓ faecal incontinence (`C0015732`) | 2.454 |
| 4 | abdominal pain (`C0000737`) | 0.935 | ✓ multiple sclerosis (`C0026769`) | 2.447 |
| 5 | ✓ nausea (`C0027497`) | 0.922 | hypokalaemia (`C0020621`) | 2.394 |
| 6 | diarrhea (`C0011991`) | 0.914 | ✓ neumonia (`C0032285`) | 2.348 |
| 7 | Pain (`C0030193`) | 0.899 | ✓ Bacteraemia (`C0004610`) | 2.288 |
| 8 | Difficulty breathing (`C0013404`) | 0.863 | ✓ carotid artery stenosis (`C0007282`) | 2.264 |
| 9 | ✓ Fatigue (`C0015672`) | 0.856 | ✓ Hypomagnesaemia (`C0151723`) | 2.257 |
| 10 | asthenia (`C0004093`) | 0.846 | ✓ cholecystitis (`C0008325`) | 2.210 |

Ghi chú người xem: _…_

## random-05: **brimonidine** (`CID000002435`, bậc train 165, 158 target; panel target rộng) + **hydroxychloroquine** (`CID000003652`, bậc train 217, 0 target)

Nhãn quan sát: 24 · bậc train nhỏ hơn: 165 · NDCG@10 0.064 → 0.000 (Δ -0.064) · top-10 trùng 2/10

| # | b0_alpha0-db2b9c960215 | điểm | distmult_d128-dbd218398318 | điểm |
|---:|---|---:|---|---:|
| 1 | chest pain (`C0008031`) | 0.976 | glaucoma (`C0017601`) | 2.389 |
| 2 | anaemia (`C0002871`) | 0.953 | apoplexy (`C0038454`) | 1.957 |
| 3 | arterial pressure NOS decreased (`C0020649`) | 0.888 | basal cell carcinoma (`C0007117`) | 1.905 |
| 4 | Difficulty breathing (`C0013404`) | 0.863 | disseminated lupus erythematosus (`C0024141`) | 1.772 |
| 5 | neumonia (`C0032285`) | 0.854 | connective tissue disease (`C0009782`) | 1.752 |
| 6 | abdominal pain (`C0000737`) | 0.845 | hay fever (`C0018621`) | 1.617 |
| 7 | asthenia (`C0004093`) | 0.831 | High blood pressure (`C0020538`) | 1.554 |
| 8 | apoplexy (`C0038454`) | 0.825 | Infection Urinary Tract (`C0042029`) | 1.528 |
| 9 | High blood pressure (`C0020538`) | 0.806 | lung neoplasms (`C0024121`) | 1.519 |
| 10 | ✓ dizziness (`C0012833`) | 0.806 | Raynauds phenomenon (`C0034735`) | 1.502 |

Ghi chú người xem: _…_

