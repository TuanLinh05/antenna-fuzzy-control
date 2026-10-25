# Anten V4 - 17HS1352-P4130 / LD-1501MG / MT6701

Ngày 25/10/2026. Bản sửa từ V3 theo cấu hình người dùng đã chấp nhận. Đơn vị CAD và file in: **mm**, xuất tỷ lệ **100%**.

**Đây là bộ CAD đã kiểm tra số, chưa in/lắp và chưa nghiệm thu điều khiển trên phần cứng.** Tỉ số răng và kích thước xuất được kiểm tra riêng với các giả thiết về linh kiện. Xem `BAO_CAO_KIEM_TRA_V4.md` để phân biệt kết quả đạt về hình học, ước lượng tải và phép đo còn thiếu.

## Mở bộ file

- `XEM_MO_HINH_3D.html`: trình xem offline, có phương vị/góc nâng và bật tắt linh kiện. Góc trong trình xem là chuyển động hình học.
- `STEP/ASSEMBLY_with_hardware_envelopes.step`: cả cụm, có bao kích thước linh kiện; không dùng cả cụm làm file in.
- `STL/`: từng chi tiết đã đặt hướng in ban đầu.
- `3MF_plates/`: năm bàn in A1, không kèm profile, support hoặc G-code.
- `preview/MT6701_underside.png`, `MT6701_dimensions.png`, `GT2_transmission_dimensions.png`: ảnh gá cảm biến và sơ đồ kích thước.
- `printed_parts.csv`: số lượng từng chi tiết in; `hardware_BOM.csv`: vít và linh kiện.
- `audit/`: kết quả kiểm tra độc lập. `parameters.json` và `build_model.py` là tham số/nguồn chính.

## Thay đổi chính

1. Motor đổi sang 17HS1352-P4130: thân dài 34 mm, mặt khung 42 mm, tâm lỗ M3 31 mm. Mô hình lấy trục Ø5 mm, chiều dài nhô **20 mm** để kiểm tra trường hợp ngắn hơn trong thông tin bán hàng. Chưa xác minh trục thực là Ø5 hay 4,5 mm; phải đo trước khi chọn lỗ pulley.
2. Giữ pulley kim loại GT2 **20T**, rotor in **80T**, đai kín **GT2-280-2GT, rộng 6 mm**. Tỉ số đúng 4:1 theo số răng. Khoảng cách tâm danh định **87,9173 mm**, motor trượt ±5 mm để căng đai.
3. Servo đổi sang LD-1501MG, cửa gá rộng 21,6 mm và lỗ tai có thể chỉnh. Dùng **đĩa tròn đi kèm servo** như người dùng xác nhận; adapter in bắt vào đĩa, không thay spline.
4. Bỏ encoder quang và khớp nối 6–8 mm. MT6701 đặt dưới **trục anten sau đai**; nam châm quay cùng trục, PCB đứng yên.
5. Thêm cầu gá cố định, carrier chỉnh XYZ và đầu kẹp trục giữ nam châm Ø4 x2 mm. Chân đế giảm từ 90 xuống 55 mm vì không còn encoder quang dài.
6. Thêm dưỡng lỗ bo, dưỡng nam châm, dưỡng trục motor và dưỡng mặt gá NEMA17. Mẫu gá MT6701 cũ được tham khảo tại `reference/`, không phải phần cần in để lắp cụm mới.

## In thử trước

In riêng các file sau trước khi in toàn bộ năm bàn:

| Chi tiết | Mục đích |
|---|---|
| `26_MT6701_PCB_fit_gauge.stl` | Luồn đủ bốn vít M2 qua bo và dưỡng, không ép bo cong |
| `27_4mm_magnet_fit_gauge.stl` | Chọn hốc 4,0 / 4,1 / 4,2 mm theo nam châm nhận được và sai số máy in |
| `20_LD1501MG_mount_fit_gauge.stl` | Kiểm tra thân/tai servo và khả năng căn trục |
| `28_motor_shaft_fit_gauge.stl` | Đối chiếu trục motor 4,5 / 5,0 mm; thước cặp vẫn là phép đo chính |
| `30_NEMA17_mount_fit_gauge.stl` | Thử mặt motor, boss định tâm và bốn vít M3 |
| `16_608_fit_coupon.stl`, `17_shaft_fit_coupon.stl`, `23_D_shaft_fit_gauge.stl` | Kiểm tra bi, trục Ø8 và mặt D như V3 |

Không scale toàn bộ chi tiết để sửa riêng một lỗ. Chỉnh tham số lỗ hoặc bù dung sai trong slicer sau khi đo. Hướng STL là điểm bắt đầu; phải slice và xem support/bridge/brim, đặc biệt cầu gá 22 và giá servo. 3MF chưa phải xác nhận in thành công.

## Lắp bộ truyền và motor

1. Lắp trục và hai bi 608, vòng đệm chỉ tì vào vòng trong bi. Giữ trục đồng tâm và quay tay nhẹ trước khi gắn đai.
2. Rotor 80T và các mối truyền mô-men vẫn dùng mặt D theo V3. Giũa đúng vùng được chỉ định; không giũa phần chạy trong bi. Đầu kẹp nam châm chỉ đi theo góc trục, không truyền mô-men kéo chảo.
3. Motor treo dưới cầu gá 03, mặt trước ở z=58 mm. Bốn M3x10 qua đệm in 1 mm và tấm gá 6 mm, ăn vào motor danh định 3 mm; kiểm tra chiều sâu ren thật để không chạm bên trong motor.
4. Pulley 20T và rotor 80T có phần răng cùng cao độ; đai rộng 6 mm nằm giữa hai vành. Pulley thương mại cần thân/hub nằm trong bao cao độ 64–78 mm được dựng. Chọn đúng lỗ trục thực, không dùng vòng lót in mỏng 0,25 mm để chữa sai Ø4,5/Ø5.
5. Đặt tâm motor gần 87,9173 mm, luồn đai khi motor ở phía trong rãnh rồi kéo ra để căng vừa. Không kéo đến tận đầu +5 mm với đai 280 mm; đó là biên hành trình chỉnh, không phải độ căng làm việc.
6. Quay tay toàn hành trình, kiểm tra răng ăn đai, mép đai không cọ và vít pulley bám đúng mặt phẳng trục. Hình học đường bước đúng không thay thế thử ăn răng/độ căng trên bản in.

Với 1,8°/bước và vi bước 1/16: 12.800 xung/vòng anten; 0,028125°/xung lệnh; 30°/s cần khoảng 1.066,7 Hz, motor quay 20 rpm. Đây là độ chia lệnh, không phải độ chính xác góc đã đo.

## Lắp nam châm và MT6701

1. Kẹp chi tiết 25 lên **8 mm cuối trục Ø8**, đầu trục ở z=-14 mm, đỉnh chi tiết ở z=-6 mm. Siết M3x16 vừa đủ để đầu kẹp không trượt. Ưu tiên vít/ê-cu phi từ gần nam châm khi có sẵn; kiểm tra sai số góc sau khi lắp đủ vít.
2. Hốc nam châm danh định Ø4,2 x2,2 mm. Dùng lớp keo phù hợp, giữ **mặt nam châm ngang mặt đáy hốc tại z=-20 mm**; 0,2 mm phía sau dành cho dung sai/keo. Không mặc nhiên ép nam châm vào đáy rồi lấy khe theo mặt nhựa. Phải kiểm tra giữ chắc trước khi chạy.
3. Cầu 22 bắt vào bốn lỗ dưới đế x=±36, y=±18 bằng M3x16. Chân cầu không được ép vào ê-cu; bản V4 đã kiểm tra khoảng trống vít và ê-cu.
4. Bốn M3x25 từ dưới sàn cầu hướng lên làm trụ chỉnh cao. Mỗi trụ dùng một ê-cu dưới carrier và một ê-cu trên để đỡ/khóa carrier. Căn bốn điểm cùng cao, siết đều vừa tay.
5. Lắp PCB lên carrier 24 bằng bốn **M2x8** và ê-cu M2 trượt trong hốc dưới. Lỗ vít và hốc ê-cu cùng có khoảng chỉnh; kiểm tra bo nằm phẳng. Không giả định vít M2 sẽ luồn được lỗ PCB có sai số; thử dưỡng trước, không ép mạnh.
6. Mặt IC hướng lên nam châm. Mô hình giả định PCB dày 1,6 mm, IC cao 1,7 mm và IC nằm ở tâm bo. **Căn theo tâm IC thực**, không chỉ tâm hình vuông PCB. Carrier dịch XY ±1,5 mm; lỗ bo còn có khoảng chỉnh riêng. Nếu chip lệch hơn phạm vi này, đổi tham số theo số đo.
7. **Ưu tiên hàn dây mềm trực tiếp hoặc dùng header vuông góc cho dây ra bên hông.** Bao linh kiện trên mặt bo ở vùng header chỉ cao tối đa 3 mm; không dùng đầu pin đứng dài chĩa vào đầu giữ nam châm. Phần đuôi hàn dưới bo không dài quá 1,5 mm. Nếu module đã hàn đầu cắm hướng khác, kiểm tra lại khoảng hở trước khi lắp; không kẹp bo vào chân hàn.
8. Khe danh định từ **mặt nam châm đến mặt trên IC** là **1,0 mm**. Chiều cao carrier thay đổi 1,5 mm cho phép đặt khe 0,5–2,0 mm theo các chiều cao giả định. Đo thực tế vì chiều cao IC, lớp keo và chiều dày PCB có thể khác.
9. Nam châm bộ cảm biến Ø4 x2 mm nhỏ hơn nam châm tham chiếu trong datasheet. Khe đúng chưa tự chứng minh từ trường và độ chính xác đạt. Đọc góc khi quay chậm đủ vòng, thử tại các góc chuẩn, kiểm tra độ lặp lại, lỗi qua 0/360° và ảnh hưởng của motor khi cấp điện.

Mốc 18 x18 mm được suy từ mô tả mới: 23 -2*(1,5 +2/2)=18 mm. Mẫu gá cũ dùng 17,5 mm là số lắp thử. Bộ mới đã kiểm tra vít và ê-cu tại các pitch 17,5 /18 /19 mm; số đo thật vẫn quyết định việc căn bo.

## Servo nâng

Giữ góc nâng bằng vòng vị trí nội bộ của LD-1501MG. Chưa có cảm biến nâng gửi số đo về STM32. Servo dùng đĩa tròn thật, adapter 11 có lỗ/rãnh M2 theo bán kính 6,5–10,5 mm, tâm có đường đưa dụng cụ vào vít giữ đĩa. Nếu cần mở lỗ M2 trên đĩa, tháo đĩa khỏi servo trước và kiểm tra mép vật liệu; không khoan xuyên vào servo.

Cửa gá rộng 21,6 mm cho thân công bố 20,04 mm. Rãnh đã kiểm tra cho pitch tai 45 /47,6 /50 mm và khoảng cách ngang 8 /10 /12 mm. Cao độ trục ra và lỗ đĩa thực chưa được đo; **in dưỡng 20 và căn đồng trục trước khi siết**. Có bốn đệm tai servo 0,5 mm. Trục chảo được bi đỡ, tránh ép lệch trục servo.

Ban đầu dùng phạm vi lệnh servo 45–135°, đo góc chảo bằng thước/chuẩn ngoài và lập bảng hiệu chuẩn. Hành trình hình học 0–180° trong CAD không xác nhận servo chạy an toàn đủ hành trình dưới tải. Tốc độ ramp góc nâng phải đồng bộ giữa mô phỏng và firmware khi chỉnh phần điều khiển.

## Điện và phạm vi đáp ứng bài toán

- Nguồn 12 V/5 A cấp TB6600 loại hỗ trợ 12 V. Buck riêng tạo khoảng 7 V cho LD-1501MG; nhánh MCU/logic theo thiết kế board 5 V/3,3 V, không đưa 7 V vào chân MCU.
- Dòng 1,3 A của motor là thông tin ảnh sản phẩm, chưa đo. Chọn DIP theo cách ghi peak/RMS của TB6600 thực tế. Dùng driver giới hạn dòng, không nối trực tiếp 12 V vào cuộn có điện trở công bố 2,1 ohm.
- STM32F103 đủ cho cấu trúc vòng mờ phương vị hiện có ở mức mã tính toán đã kiểm tra trên máy tính. **Firmware F103 cũ đọc encoder AB/2400 count, chưa có driver MT6701; chưa được coi là firmware dùng ngay cho V4.** Phải đổi lớp đọc góc, xử lý timeout/wrap/mốc và kiểm tra thời gian trên chip.
- Có thể dùng I²C2 PB10/PB11 nếu đúng biến thể F103 và module hỗ trợ. Nguồn module/pull-up phải giữ mức giao tiếp phù hợp 3,3 V. Không suy pinout tuyệt đối chỉ từ ảnh.
- Dây cảm biến đứng yên dưới đế; dây servo đi theo phần quay, có vòng chùng và chặn kéo. Chưa có slip ring hoặc home cứng. Dùng hành trình phương vị ±150° sau khi kiểm tra dây thật.
- Ước lượng tải và nguồn cho thấy cấu hình có triển vọng đáp ứng chảo Ø160 mm trong nhà. Chưa có đặc tuyến mô-men chạy motor, thử nhiệt/nguồn, số đo từ trường hoặc dữ liệu bám góc thật để xác nhận vọt lố ≤2%, sai số ≤0,5° hay tốc độ thực ≤30°/s.

Thử trước ở 5–10°/s, tăng dần sau khi góc MT6701 có đúng chiều. Dùng test case trong `../../Review_2026-10-24/test_matrix.csv`, điều chỉnh theo V4. Không demo bằng chặn trục; lỗi cảm biến/heartbeat có thể thử bằng phần mềm. Không cần RF để bảo vệ phần điều khiển góc.

## Tái tạo và kiểm tra

Runtime CadQuery/trimesh hiện ở `D:/HK261/NMDKTM/tmp/cad_runtime`, nguồn ưu tiên nạp đường dẫn này. Thứ tự chạy:

```text
python build_model.py
python validate_assembly.py
python validate_fasteners.py
python audit_m4.py
python validate_interfaces.py
python validate_loads.py
python make_preview.py
python make_dimension_views.py
python finalize_v4.py
```

Có thể chạy các validator đọc hình học độc lập đồng thời sau khi build xong; `audit_m4.py` phải chạy sau `validate_fasteners.py`. Không chạy build trong lúc validator đang đọc các file xuất. `validate_loads.py` ghi tham số mô phỏng riêng trong `audit/`, không ghi đè tham số/kết quả MATLAB V3.

Nguồn chính: [MT6701 Rev.1.8](https://www.magntek.com.cn/upload/pdf/202407/MT6701_Rev.1.8.pdf), [Hiwonder LD-1501MG](https://www.hiwonder.com/products/pan-tilt), ảnh motor và module do người dùng cung cấp. Hình dạng rãnh GT2 kế thừa mã V3; chất lượng ăn răng thực tế cần kiểm tra với đai và bản in.
