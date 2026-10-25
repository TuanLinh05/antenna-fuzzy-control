# Anten hai trục V2 — linh kiện Thế Giới IC

Bản này thay V1 để mua linh kiện cơ khí tại **một cửa hàng: Thế Giới IC**. Chảo Ø160 mm, servo nâng **MG946R 180°**, stepper **SL42STH40-1684A**, dây **2GT-280 rộng 6 mm**, pulley kim loại 20T và rotor in 80T. File anten gốc và V1 được giữ nguyên.

Đây là bản cơ khí thử nghiệm để lắp động cơ và thực nghiệm điều khiển trong nhà. Chưa in hoặc thử tải thực tế. Cửa hàng chưa cung cấp đủ bản vẽ tai servo/tay tròn/pulley; **in mẫu thử và đo linh kiện nhận được trước khi in toàn bộ**. Chảo và đầu thu nhựa chưa có chức năng thu sóng thiên văn.

## Mở file nào

- `XEM_MO_HINH_3D.html`: xem offline trong Chrome/Edge; kéo chuột để xoay, cuộn để phóng to, chỉnh góc nâng và phương vị.
- `STL/`: chi tiết đã đặt hướng in, Z=0. In theo `printed_parts.csv`, tránh in thiếu chi tiết lặp.
- `3MF_plates/`: 4 bàn in 256×256 mm; mỗi file là một công việc riêng. File chứa hình học, **chưa có profile Bambu Studio, support hay G-code**.
- `STEP/ASSEMBLY_with_hardware_envelopes.step`: lắp tổng thể và bao hình danh định của linh kiện mua; không in nguyên cụm.
- `STEP/`: CAD mỗi chi tiết tại tọa độ lắp; có thể sửa trong phần mềm CAD.
- `DANH_SACH_MUA_THEGIOIIC.md`, `hardware_BOM.csv`: mã, link mua, lượng cần/lượng đề xuất, giá và tồn kho kiểm tra ngày 11/10/2026.
- `KIEM_TRA_OC_M4.md`: 20 mối ghép M4, kích thước lỗ/đầu ốc/đai ốc và các vị trí còn dùng M3/M2; kết quả đo trực tiếp STEP trong `m4_audit.json`.
- `build_model.py`: nguồn CadQuery. Sửa tham số trong nguồn rồi xuất và kiểm tra lại; chỉ sửa `parameters.json` sẽ không đổi hình học.

## Những thay đổi cơ khí

| Hạng mục | V2 |
|---|---|
| Chảo | Ø160 mm, f=80 mm, lòng sâu 20 mm, thành 2,4 mm |
| Đế | 208×146×8 mm, 4 chân in cao 10 mm |
| Trục nâng | Tâm Z=209 mm tính từ đáy tấm đế; cao 219 mm so với mặt bàn khi lắp chân |
| Servo | MG946R; cửa thân 41,5×21,4 mm, rãnh tai ±3 mm theo chiều dài thân |
| Gá servo | Hốc mở để bắt bằng M4×20, bỏ M4×55 |
| Stepper | Mã IC5255, thân dài 40 mm, trục Ø5 nhô 20 mm; mặt motor Z=58 mm |
| Dây đai | Vòng kín 2GT-280, 140 răng, bước 2 mm, rộng 6 mm |
| Pulley | Kim loại 20T + rotor in 80T, tỉ số 4:1 |
| Tâm pulley | 87,917 mm, motor chỉnh căng ±5 mm bằng rãnh trên mặt gá |
| Cao độ đai | Tâm vùng răng Z=73 mm; vùng răng rotor Z=69,5–76,5 mm |
| Rotor | Pulley và bàn xoay gộp thành 04, bỏ mối ghép cần đai ốc mỏng |
| Vòng bi | 4×608ZZ, Ø8×Ø22×7 mm |
| Trục | Cắt một thanh Ø8×200 thành 110, 40, 30 mm |
| Chặn trục | 2 vòng chặn kẹp in, M3×16; thêm spacer ngoài vòng bi nâng phải |
| Tay servo | Dùng tay tròn và vít tâm đi kèm đúng MG946R; M2 xuyên tay vào adapter, không in spline |

Không tự đổi dây sang 300 mm, đai hở hoặc 300XL; không đổi motor sang trục 4,5 mm. Xem mã chính xác trong danh sách mua. Tồn kho motor hiện chỉ có 1 chiếc, cần kiểm tra lại khi đặt hàng.

## Chi tiết cần in

Có **20 loại STL**, tổng **31 chi tiết** kể cả 3 mẫu thử. Đánh số giữ gần V1 nên không có chi tiết 06 riêng.

| Chi tiết | Số lượng |
|---|---:|
| 01 đế; 02 trụ vòng bi; 03 gá stepper; 04 rotor; 07 dầm; 08/09 càng; 10 gá servo; 11 adapter; 12 chảo; 13 giá chảo; 15 đầu thu | Mỗi loại 1 |
| 05 spacer vòng trong | 3 |
| 14 thanh đỡ đầu thu | 3 |
| 18 vòng chặn trục kẹp | 2 |
| 19 chân đế | 4 |
| 21 đệm vít motor 1 mm | 4 |
| 16 mẫu lỗ vòng bi; 17 mẫu lỗ trục; 20 mẫu tai servo | Mỗi loại 1 |

## Vít cho từng mối lắp

Chiều dài vít tính từ dưới đầu vít; dùng **đầu trụ DIN912** theo mã trong BOM. V2 dùng vít có đầu để ép trục qua đai ốc, không cần mua vít không đầu. Các hốc đai ốc dùng loại lục giác thường; đai ốc mặt bích và tán keo không cùng kích thước.

Phần khung dùng M4×20 với lỗ xuyên **Ø4,4 mm**. 8 hốc đầu ốc dưới đế sâu 3,2 mm; đầu trụ cao 4 mm nhô 0,8 mm nên phải lắp 4 chân in cao 10 mm. Mối ghép gá servo vào càng trái không thêm vòng đệm để giữ đủ chiều dài ăn ren. V2 vẫn có các mối lắp M3/M2 theo bảng dưới.

| Mối lắp | Vít | Đai ốc |
|---|---|---|
| Trụ vào đế | 4×M4×20, đầu dưới đế | 4×M4 trên chân trụ |
| Gá stepper vào đế | 4×M4×20, đầu dưới đế | 4×M4 trên chân gá |
| Dầm vào rotor | 4×M4×20, đầu trên dầm | 4×M4 trong hốc dưới rotor |
| Càng vào dầm | 4×M4×20 | 4×M4 trong hốc dưới dầm |
| Gá servo vào càng trái | 4×M4×20, đầu ở đáy hốc mở X=-107 | 4×M4 trong càng trái |
| Motor vào gá | 4×M3×10 + 4 đệm in 21 | Ren motor; vít vào sâu danh định 3 mm |
| Tai servo vào gá | 4×M3×12 | 4×M3 sau tai servo |
| Chân đế | 4×M3×12, đầu trong hốc trên đế | 4×M3 trong hốc dưới chân |
| Hai vòng chặn kẹp | 2×M3×16 | 2×M3 trong vòng chặn |
| Ép trục vào rotor | 1×M3×12 | 1×M3 trong hub |
| Ép hai trục vào giá chảo | 2×M3×10 | 2×M3 trong tai giá chảo |
| Ép trục vào adapter servo | 1×M3×8 | 1×M3 trong adapter |
| Chảo vào giá chảo | 4×M3×20, đầu trên các bệ phẳng trong lòng chảo | 4×M3 trong hốc sau giá |
| Chân thanh đầu thu vào chảo | 3×M3×20, đầu tại bệ Z=29,2 | 3×M3 dưới bệ chảo |
| Thanh đầu thu vào hub | 3×M3×12 theo trục chảo, đầu ở mặt hub Z=88 | 3×M3 trong hốc đáy đầu thanh |
| Tay tròn servo vào adapter | 2×M2×10 xuyên hai lỗ đối xứng | 2×M2 đồng trong hốc adapter |
| Giữ tay tròn vào spline | Vít tâm đúng loại trong bộ servo | Không tự thay bằng vít metric chưa xác nhận |

Tổng lắp: 20×M4×20, 1×M3×8, 6×M3×10, 12×M3×12, 2×M3×16, 7×M3×20, 2×M2×10; 20 đai ốc M4, 24 M3, 2 M2. BOM mua đã làm tròn theo lượng tối thiểu và có dự phòng.

## Thử linh kiện và in trên A1

1. Nhận các mã chính, kiểm tra Ø8 trục vào 608 nhẹ và không rơ quá mức; đo tai/tay servo. Ảnh MG946R của cửa hàng có tay tròn và vít tâm; nếu bộ nhận được thiếu, yêu cầu cửa hàng bổ sung đúng bộ phụ kiện.
2. In STL **16, 17, 20**, thêm **11 và 18** để thử tay servo/vòng chặn. Mẫu 16 có lỗ 22,0/22,2/22,4 mm; mẫu 17 có 8,0/8,2/8,4 mm. Mẫu 20 chỉ kiểm tra thân và tai, chưa xác nhận vị trí trục ra.
3. Adapter có rãnh M2 cho tâm lỗ tay tròn cách spline 6,5–10,5 mm. Cần ít nhất 2 lỗ đối xứng. Nếu lỗ nhựa nhỏ, mở lên 2,2 mm; giữ nguyên spline. CAD giả định tay dày 3 mm, Ø24 mm; kiểm tra độ dày thật và chiều dài vít, tránh vít cọ vỏ servo. Đai ốc M2 trong CAD dùng AF 4 mm và dày 2 mm, hốc sâu 2,8 mm.
4. Căn tâm servo đúng tâm 608 tại Z=209. Rãnh tai cho chỉnh ±3 mm. Vị trí dọc trục/hình tai là kích thước danh định, cần lắp thử adapter và trục 40 mm trước khi in cả khung; có thể sửa vị trí gá trong nguồn nếu phiên bản thực khác. Không ép khớp nối khi hai tâm lệch.
5. A1 nozzle 0,4 mm, scale **100%**; bắt đầu lớp 0,20 mm, 4–5 vòng thành, 5 lớp mặt trên/dưới, gyroid 30–40% cho khung. Rotor, adapter và vòng chặn: 6 vòng thành, 60–100% infill; rotor thử lớp 0,16 mm. Spacer/đệm 1 mm in 100%.
6. PLA dùng thử trong nhà; PETG có thể dùng cho gá và vòng chặn sau khi chỉnh dung sai. Chưa có profile in đã chạy thử. Vòng chặn kẹp nhựa cần kiểm tra sau khi siết và sau thời gian dùng; siết vừa đủ, không lấy nó làm bộ phận giữ tải nặng.
7. **Bật tree support cho chảo 12, gá stepper 03 và dưới đĩa rotor 04.** Rotor gộp có đĩa Ø96 nhô ra khỏi hub, cần support ở mặt dưới đĩa. Kiểm tra support dễ tháo, không khóa kín hốc đai ốc. Rà lại các mái rãnh hub, adapter và lỗ ngang trong Slice preview.
8. Brim 2–4 mm nếu cần; Auto Arrange lại nếu brim sát mép hoặc dính chi tiết khác. 3MF chỉ kiểm tra footprint chi tiết nằm trong 256×256; support/brim và vùng tránh đầu in phải kiểm tra trong Bambu Studio. In từng bàn, không chọn in tuần tự từng vật nếu chưa kiểm tra khoảng trống đầu in.
9. Đai thật phải vào răng rotor đều, không đội/kẹt; làm sạch ba via. Chưa kiểm chứng biên dạng GT2 in bằng chạy tải, nên thử rotor riêng và đai trước khi lắp khung.

## Lắp theo thứ tự

1. Lắp 4 chân 19 bằng M3×12 từ trên đế. Nhét các đai ốc trong rotor, dầm, càng và giá chảo trước khi các mặt bị che.
2. Lắp hai 608 vào trụ 02 từ hai đầu (Z=8–15 và 59–66); chỉ ép vòng ngoài. Bắt trụ và gá stepper vào đế bằng M4×20.
3. Luồn trục phương vị 110 mm, đáy trục tại khoảng Z=0. Từ dưới lên: vòng chặn in Z=-2–6, spacer Z=6–8, vòng bi dưới, vòng bi trên, spacer Z=66–68, rotor Z=68–105. Kẹp trục bằng M3×12 ở hub. Chỉnh vòng chặn để hết rơ dọc nhưng vòng bi quay nhẹ, không siết preload mạnh. Hốc Ø32 dưới đế chừa không gian cho vòng chặn/đầu vít; chân đế nâng cụm khỏi mặt bàn.
4. Lắp motor với 4 đệm 21 và M3×10; kiểm tra motor cho phép vít vào sâu 3 mm. Gắn pulley 20T và đai khi khung trên chưa lắp. Căn tâm vùng răng pulley ở Z=73 mm; hub pulley có thể xuống trong lỗ thông tâm của gá nếu cần. Trục 20 mm và bao hình pulley trong CAD khớp danh định; đo chiều dọc trục pulley thực, giữ hub nằm trên phần trục hữu ích và không cọ boss motor. Căng vừa đủ rồi siết motor theo rãnh.
5. Bắt dầm 07 vào rotor, rồi hai càng 08/09 vào dầm. Càng có lỗ gá servo ở bên trái. Lắp 608 nâng từ mặt ngoài mỗi càng.
6. Bắt giá 13 vào chảo bằng M3×20. Lắp thanh 14 bằng M3×20; lắp các đai ốc ở đáy đầu thanh trước khi đưa vào rãnh hub 15, rồi bắt M3×12 từ mặt trên hub. Các góc thanh là 90°, 210°, 330°.
7. Đặt chảo giữa hai càng. Trục trái dài 40 mm ở X=-114..-74; trục phải 30 mm ở X=77..107. Kẹp vào mặt phẳng nông trên trục bằng M3×10. Bên phải có spacer **X=97..99**, sau đó vòng chặn **X=99..107**. Spacer chỉ tì vòng trong 608; không ép vòng chặn trực tiếp lên cả vòng ngoài. Giữ khe hở giá chảo–càng khoảng 2 mm, cụm quay tay phải nhẹ.
8. Bắt gá servo 10 bằng 4 M4×20 từ các hốc mở; không luồn vít dài xuyên cả gá. Cho servo về giữa hành trình, lắp đúng tay tròn/vít tâm đi kèm. Lắp adapter vào tay bằng hai M2 xuyên + đai ốc. Căn đồng trục và cao độ trước khi kẹp adapter lên trục nâng.
9. Thử từ góc nhỏ, tốc độ thấp; tăng hành trình dần. CAD kiểm tra 0–180° theo mẫu rời rạc; khi chạy thật bắt đầu khoảng 5–175° rồi hiệu chỉnh theo servo, tránh ép chặn cơ khí. Chừa vòng dây servo mềm và giới hạn phương vị ban đầu ±170°; chưa có slip ring, gá home hoặc encoder.

## Điều khiển và giới hạn kiểm chứng

Với stepper 1,8° và tỉ số 4:1: 0,45°/bước đầy, 0,028125°/vi bước ở 1/16. Đây là độ chia lệnh, không phải độ chính xác đã đo. Driver cần giới hạn dòng phù hợp với 1,68 A/pha; servo cần nguồn đủ dòng đúng điện áp phiên bản thực, cùng mass với bộ điều khiển. Phần điện, firmware và bo điều khiển chưa được chọn hoặc kiểm chứng trong bộ cơ khí này.

Kiểm tra giao khối cụm trong `assembly_validation.json`; kiểm tra đầu vít, thân vít và đai ốc danh định trong `fastener_validation.json`. Ren trong motor và lỗ dự kiến mở trên tay servo là mối lắp chủ ý được loại khỏi kiểm tra. Các mẫu góc rời rạc không thay thế thử quay thực hoặc phép chứng minh thể tích quét liên tục. Dây đai là bao hình đường bước, không có từng răng; dây điện và spline không được mô phỏng.

STL kiểm tra kín, chiều mặt nhất quán, một thành phần liên thông, thể tích dương; 3MF kiểm tra đủ số lượng, không chồng footprint và nằm trong bàn in. Chưa thử độ bền lớp in, độ rơ, mô-men liên tục, độ chính xác hướng, độ bền vòng chặn nhựa hoặc chức năng RF.

PDF bài tập gốc mô tả motor DC, tỉ số N=150 và điều khiển điện áp. Cơ cấu stepper 4:1 hiện tại cần mô hình điều khiển và mô tả thực nghiệm riêng trong báo cáo.

## Tạo lại bộ file

CadQuery/trimesh/numpy đặt tại `D:/HK261/NMDKTM/tmp/cad_runtime`, không đóng gói runtime vào ZIP. Chạy `build_model.py`, sau đó `validate_assembly.py`, `validate_fasteners.py`, `audit_m4.py`, `make_preview.py`, cuối cùng `package_delivery.py`. Không giao bản mới nếu các kiểm tra báo FAIL. Một số kích thước vẫn là hằng số trong nguồn; đổi servo/vòng bi phải rà lại toàn bộ vị trí lắp, không chỉ đổi tên tham số.

Nguồn chính: các trang sản phẩm được liên kết trong danh sách mua; [Bambu A1](https://bambulab.com/pl/a1/tech-specs) cho bàn in; [rbuckland / droftarts](https://github.com/rbuckland/openscad.parametric-pulley) cho biên dạng GT2 in. Kích thước không được cửa hàng công bố đầy đủ đã ghi rõ là danh định và cần đo thực.
