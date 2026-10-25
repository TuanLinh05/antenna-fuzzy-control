# Rà soát và hướng triển khai anten hai trục

Ngày 24/10/2026. Đọc tài liệu này trước khi dùng cấu hình V3 cho phần cứng hiện có.

**Cập nhật 25/10/2026:** người dùng đã chấp nhận đổi stepper sang 17HS1352-P4130 và dùng đĩa tròn đi kèm LD-1501MG. [CAD V5 và báo cáo mới](../3D%20Print/Antenna_V5_Reinforced/README_START_HERE.md) là nguồn cấu hình cơ khí hiện hành, đã gia cố gá servo và mở khung MT6701 để dễ thao tác; các đoạn nhắc STP bên dưới là lịch sử rà soát ngày 24/10. Cấu hình mới được lưu ở `actual_hardware.json`; chưa có thử phần cứng.

## 1. Kết luận và phạm vi

**Phương án người dùng chọn sau trao đổi: STM32F103 + TB6600 cấp 12 V + MT6701 đo trực tiếp trục phương vị; LD-1501MG cấp khoảng 7 V và dùng vòng vị trí bên trong servo.** Đây là cơ cấu hai trục với một vòng điều khiển mờ bên ngoài ở phương vị. Bài DC trong PDF là nguồn ý tưởng thiết kế/đánh giá, không phải các thông số của mô hình thực.

Người dùng đã xác nhận:

| Hạng mục | Phần cứng thực tế | Hồ sơ V3 đang giả định |
|---|---|---|
| MCU | STM32F103; chưa xác nhận biến thể board | F103C8T6 |
| Động cơ phương vị | Shinano Kenshi STP-43D2073-01 | SL42STH40-1684A |
| Driver | Dự định đổi DM542-05 sang TB6600 hỗ trợ 12 V | TB6600 |
| Động cơ nâng | Hiwonder LD-1501MG | MG946R |
| Cảm biến góc | Có sẵn MT6701, dự định lắp trên trục phương vị; nâng không thêm cảm biến | Encoder phương vị 600 P/R, giải mã x4 |
| Nguồn dự kiến | 12 V, 5 A; hạ áp khoảng 7 V cho servo | 12 V cho driver; 5 V cho servo |

Tên đề tài phù hợp cấu hình đã chọn: **“Điều khiển mờ góc phương vị trên mô hình anten hai trục”**. Phương vị là một tọa độ; tọa độ còn lại là góc nâng. Nếu giữ tên đề tài rộng hơn, cần ghi rõ chỉ phương vị dùng bộ mờ thiết kế bên ngoài.

Yêu cầu giảng viên về dùng mờ cho cả hai trục chưa được xác nhận. Cấu hình hiện chọn dùng một MT6701 và không cần mua cảm biến nâng ở giai đoạn này. Vẫn cần kiểm tra góc nâng bằng thước/chuẩn đo ngoài để hiệu chuẩn servo dưới tải chảo. Phương án hai vòng mờ ở mục 6.2 là hướng mở rộng nếu sau này yêu cầu môn học thay đổi.

## 2. Đối chiếu bài tham khảo

PDF `../Bài tập Điều khiển góc phương vị của antenna.pdf` mô tả một trục dẫn động DC, đầu vào điện áp ±12 V, hộp số N=150. Từ đề tính được J=7,25 kg.m² và B=3,125 N.m.s/rad. Chuỗi góc đặt là 60°, 150°, 30°, 90°, đổi mỗi 12 s, trong 48 s. Chỉ tiêu gồm vọt lố ≤2%, sai số xác lập bằng 0 theo lý tưởng, tốc độ ≤30°/s và thời gian xác lập nhanh.

Giữ lại cách lập sai số, chọn tập mờ, xây luật, mô phỏng bước/đảo chiều/nhiễu và đánh giá định lượng. Với mô hình thực, đầu ra điều khiển phương vị là vận tốc/tần số STEP; đầu ra nâng là lệnh góc mã hóa bằng độ rộng xung. Điện áp bus 12/24 V là điều kiện cấp nguồn, không tương đương tín hiệu điều khiển u(t) của đề DC.

Nhánh DC có thể để phụ lục minh họa học thuật. Phần chính của báo cáo phải dùng STP-43D2073-01, TB6600 và LD-1501MG với thông số được xác minh/nhận dạng. Không bắt buộc giữ chuỗi 48 s hoặc hành trình 150° của đề tham khảo cho buổi demo phần cứng.

## 3. Những điểm đã kiểm tra trong mã hiện có

| Phát hiện | Ý nghĩa và việc cần làm |
|---|---|
| `Simulation/simulate_prototype.m` đã có mô hình hai quán tính motor–đai–tải, encoder trục ra, lượng tử xung và ma sát | Đây là nền tảng có ích; thông số vẫn thuộc cấu hình cũ và phần lớn chưa đo. |
| Chỉ phương vị dùng Sugeno; nâng dùng PI nội bộ giả định | Chưa đủ để kết luận “điều khiển mờ hai trục”. Thêm đo góc nâng và vòng mờ bên ngoài nếu giữ tên đề tài hai trục. |
| Firmware tính góc từ TIM2/2400 count/vòng; thực tế có MT6701 chưa tích hợp | Cần thay lớp đọc encoder bằng giao tiếp phù hợp MT6701, hiệu chuẩn và xử lý vòng qua 0/360°. Không giữ nguyên hệ số 2400 count/vòng khi đọc góc tuyệt đối 14 bit. |
| Mô phỏng ramp góc servo 25°/s; firmware ánh xạ trực tiếp `el_goal` ra PWM | Đáp ứng nâng mô phỏng chưa đại diện cho luồng lệnh trên board. Cần cùng một bộ tạo lệnh/giới hạn tốc độ ở hai nơi. |
| `pass_tracking` chỉ chấm phương vị | Sai số nâng có được tính nhưng không quyết định đạt/trượt; cần bộ tiêu chí riêng cho từng trục và tổng hệ. |
| `score_steps.m` cố định mốc 0/12/24/36 s và góc 60/150/30/90° | Chưa dùng trực tiếp để chấm bước nhỏ, góc âm hoặc chuỗi demo khác. Cần suy ra đoạn thử từ kịch bản tham số hóa. |
| `prototype_scenarios.csv` có `pass=1` cho vòng hở, quan sát quá tải và ca phát hiện lỗi | Cột này không có nghĩa mọi ca đều bám góc đạt. Phải đọc `tracking_requirements_met`, `expected_fault`, `stress_observation`. |
| Baseline PD hiện có nằm ở nhánh DC | Chưa chứng minh lợi ích của mờ trên prototype. Cần so P/PD và mờ trên cùng mô hình stepper, cùng bộ giới hạn và cùng nhiễu. |
| Telemetry 5 Hz chỉ có phương vị, không lưu file; cửa sổ giữ 80 dòng | Đủ quan sát sơ bộ; thiếu dữ liệu để chấm hai trục, lặp lại phép thử và nhìn các đỉnh nhanh. Cần ghi log. |
| Đầu vào mờ thứ hai là vận tốc đo lấy dấu âm | Với góc đặt hằng, bằng đạo hàm sai số. Với góc đặt chuyển động, không được gọi chung là đạo hàm sai số nếu chưa thêm vận tốc đặt. |

Phép thử mất 5% xung hiện tại là loại bỏ lệnh xung trong mô hình. Nó kiểm tra khả năng bù sai lệch vị trí, chưa đại diện đầy đủ hiện tượng rotor mất đồng bộ do quá tải. Các ca kẹt/nhả kẹt và tải xung được giữ làm thử giới hạn trong mô phỏng; không dùng việc chặn trục bằng tay để demo.

## 4. Nguồn và linh kiện cần bổ sung

### 4.1 Nguồn

Người dùng đã chọn đổi sang TB6600 để giữ nguồn 12 V. Module TB6600 DFRobot công bố dải 9–42 VDC [S10], phù hợp 12 V. Cần kiểm tra dải điện áp, dòng pha và bảng DIP trên đúng module mua được. TB6600 là driver điều khiển dòng cuộn dây; nguồn 12 V cấp vào driver, không phải driver ổn áp ra 12 V cho motor.

Không cần thêm nguồn 24 V theo phương án TB6600 hiện chọn. Nguồn 12 V/5 A là ngân sách đầu vào; phải đo sụt áp và công suất tổng khi stepper và servo chạy đồng thời trước khi kết luận đủ tải. Cấu hình DM542-05 trước đây được thay thế; các tham chiếu DM542 [S1, S2] chỉ để truy vết lý do đổi driver.

Hiwonder công bố LD-1501MG dùng **6–8,4 V**, PWM chu kỳ 20 ms, xung danh định 500–2500 µs cho 0–180°. Nguồn sản phẩm nêu dòng kẹt 2,4–3 A [S3, S4]. Nhánh hạ áp **khoảng 7 V đã đo/điều chỉnh** phù hợp dải này. Buck cần chịu được dòng đỉnh khoảng 3 A cùng dự trữ và kiểm tra nhiệt/sụt áp; nhãn dòng tối đa không tự bảo đảm khả năng chạy thực. Không cấp servo bằng 5 V theo cấu hình MG946R cũ hoặc đưa trực tiếp 12 V vào servo.

Sơ đồ cấp nguồn đề xuất:

```text
12 V/5 A ------------------------> TB6600 --> stepper
         --> buck ~7 V, đủ dòng --> LD-1501MG
         --> buck 5 V -----------> board F103 theo thiết kế nguồn của board
                                  --> 3,3 V --> cảm biến và MCU
5 V logic --> bộ đệm phù hợp -----> PUL/DIR của driver (theo manual đúng mẫu)
```

Chung mass ở phần tín hiệu cần tham chiếu chung. Không dùng nhánh servo 7 V thay cho logic opto 5 V, hoặc đưa điện áp nguồn servo vào chân STM32. Giữ phương án transistor/buffer cho STEP/DIR nhưng xác minh mức tín hiệu, dòng opto, cực tính cạnh STEP và thời gian DIR theo đúng module TB6600; chọn dòng theo motor và cách đấu cuộn, chưa thể chốt DIP khi thiếu thông số STP.

### 4.2 Cảm biến góc

**Cần bổ sung phản hồi góc.** Đếm STEP là vị trí lệnh; cơ cấu có thể rơ, đàn hồi hoặc mất bước. Servo LD-1501MG kiểu PWM cũng không cung cấp số đo góc cho STM32 qua dây tín hiệu điều khiển này.

Dùng **MT6701 có sẵn đo trực tiếp trục phương vị sau đai**. Datasheet công bố dữ liệu góc số 14 bit, chia danh định 360/16384≈0,022° [S5]. Đây là độ chia, không phải sai số đo đảm bảo. Nam châm quay cùng trục, PCB cảm biến cố định trên đế. Căn tâm nam châm với tâm cảm biến và dùng nam châm hai cực từ hóa theo đường kính; không thay tùy ý bằng nam châm từ hóa theo chiều dày.

- Phương vị: đo trục anten **sau bộ truyền đai**, không chỉ trục motor.
- Nâng: không thêm cảm biến thường trực theo lựa chọn hiện tại; dùng thước/chuẩn đo ngoài khi hiệu chuẩn và kiểm tra dưới tải. Chưa có dữ liệu đo liên tục gửi về STM32 ở trục này.
- Có thể đọc MT6701 qua I²C, ví dụ I²C2 PB10/PB11 nếu đúng chip/board và các chân còn trống; PB6 vẫn dành PWM servo. Cần xác nhận module thực hỗ trợ chế độ giao tiếp và mức nguồn đã chọn.
- Giao tiếp tuyệt đối cần xử lý góc qua mốc 0/360°, đặt offset cơ khí và chiều quay. Góc tuyệt đối cảm biến chưa tự tương ứng hướng Bắc địa lý.
- Datasheet nêu khe từ mặt nam châm tới mặt IC 0,5–2 mm, điển hình 1 mm [S5]. Đo theo mặt IC thay vì mặt PCB; độ lệch tâm, loại nam châm và vật kim loại xung quanh vẫn cần kiểm tra khi lắp thực.
- Nếu đã chọn encoder AB trục ra thì vẫn có thể dùng, nhưng phải đổi độ chia cho đúng encoder và đặt mốc sau bật nguồn. Firmware hiện tại chỉ có lớp đọc AB ở phương vị; chưa có driver MT6701 hoặc vòng nâng.

Không cần mua thêm AS5600 hoặc MT6701 thứ hai cho phạm vi hiện chọn. Một cảm biến phương vị đủ cho một vòng mờ bên ngoài; không đủ cho chứng minh vòng mờ cả hai trục.

### 4.3 Stepper và cơ khí

Chưa tìm được datasheet gốc đáng tin cậy cho đúng STP-43D2073-01 trong lần tra cứu này. **Không gán lại dòng 1,68 A, mô-men 0,12/0,4 N.m hay quán tính rotor từ SL42STH40.** Cần ảnh nhãn, số dây, kích thước và phép đo điện trở cuộn; góc bước và dòng pha lấy từ nhãn/tài liệu đúng mã hoặc kiểm tra phù hợp.

Nếu motor thực có sáu dây, phải xác định hai nhóm cuộn và điểm giữa bằng đo điện trở trước khi chọn đấu nửa cuộn hay toàn cuộn với TB6600. Chế độ đấu làm thay đổi điện trở, điện cảm và dòng cho phép [S7]. Không suy ra màu dây, cách đấu hoặc dòng DIP từ tên NEMA17.

Đo đường kính/trục nhô, bánh răng sẵn có, tâm lỗ gá, chiều dài thân; kiểm tra gắn pulley GT2 20T. Với LD-1501MG, đo tai gá, độ cao tâm trục, tay servo và vít tâm trước khi dùng gá MG946R cũ. Cần cập nhật CAD, khối lượng/quán tính và chạy lại kiểm tra lắp sau thay động cơ. Kết quả kiểm tra va chạm V3 cũ chưa xác nhận được lắp linh kiện mới.

## 5. Mô hình toán phù hợp

### 5.1 Mức tối thiểu để thiết kế điều khiển

Quy ước rõ `q_az` là góc tương đối từ mốc gá, `q_el` là góc nâng của hướng chảo. Góc servo và góc nâng liên hệ bằng offset/dấu/tỉ số cơ khí đã hiệu chuẩn. Lệnh Z đặt mốc gá bằng tay, không tự cho hướng Bắc địa lý. Nếu cần phương vị từ Bắc, phải căn hướng chuẩn riêng.

Với bộ truyền giữ nguyên n=80/20=4:

```text
Delta_q_out = alpha_fullstep / (microstep * n)
f_STEP = abs(omega_command_deg_s) / Delta_q_out_deg
```

Ví dụ **chỉ khi** xác nhận alpha=1,8°, microstep=16, n=4: độ chia lệnh là 0,028125°; 10°/s cần khoảng 355,6 Hz; 30°/s cần khoảng 1066,7 Hz. Chia microstep mịn không tự tạo độ chính xác tương ứng [S8].

Có thể bắt đầu nhận dạng mô hình từ lệnh vận tốc đến góc/vận tốc trục ra: trễ, hằng số thời gian, tốc độ tối đa chạy được, ma sát, rơ khi đảo chiều. Đây là mô hình hệ motor + driver + cơ cấu, đủ để tinh chỉnh vòng góc; không cần biết toàn bộ thông số điện bên trong nếu đo đáp ứng tốt.

Nếu cần mô hình động lực chi tiết hơn, giữ cấu trúc hai quán tính trong `simulate_prototype.m`, thay các tham số bằng số đo. Với q_m trục motor, q_a trục anten, q_e góc nâng:

```text
z = q_m/n - q_a
J_m*q_m'' = T_motor - b_m*q_m' - T_belt/n - T_loss,m
J_a(q_e)*q_a'' + (dJ_a/dq_e)*q_e'*q_a' = T_belt - T_friction,a - T_load,a
J_e*q_e'' = T_servo - T_gravity(q_e) - T_friction,e
           + 0.5*(dJ_a/dq_e)*(q_a')^2
```

Đây là cấu trúc rút gọn giả định đối xứng quán tính theo phương vị, không phải phương trình tổng quát của mọi gimbal. T_belt dùng phần tử rơ + đàn hồi/cản; T_motor cần phụ thuộc dòng và tốc độ khi nghiên cứu mất đồng bộ. Mô hình hiện tại dùng sin góc lệch với mô-men cực đại hằng, chưa mô tả đầy đủ đặc tuyến mô-men–tốc độ/chopper. Khi dùng hiệu suất, tổn hao phải tiêu tán năng lượng và xét đúng chiều truyền công suất.

J phương vị V3≈0,005903 kg.m² và J nâng≈0,0002167 kg.m² chỉ là giá trị ban đầu từ CAD cũ. Cân khối lượng in thật, lắp đúng động cơ và tải thật rồi cập nhật. Mô-men giữ/kẹt không phải mô-men chạy liên tục. Không lấy hệ số dự trữ 16,63 lần và 9,64 lần của báo cáo cũ làm kết luận cho hai motor mới.

### 5.2 Servo

LD-1501MG nhận lệnh vị trí và có vòng điều khiển bên trong. Nên nhận dạng **khối kín từ độ rộng xung đến góc trục ra**, gồm offset, gain, trễ, tốc độ giới hạn, deadband và rơ. Thử bước nhỏ ở nhiều góc, hai chiều và dưới tải chảo. Có thể chọn mô hình bậc nhất/bậc hai có trễ nếu khớp tập dữ liệu kiểm chứng riêng.

Không gọi PI nội bộ giả định trong mô phỏng là hàm truyền hãng. Không chỉ thay nhãn MG946R thành LD-1501MG hoặc tăng giới hạn mô-men. Ánh xạ xung 500–2500 µs chỉ là danh định; bắt đầu quanh trung tính, mở rộng theo các mốc đã đo, sau khi kiểm tra hành trình cơ khí.

## 6. Thiết kế điều khiển mờ đề xuất

### 6.1 Phương vị

```text
Góc đặt -> tạo quỹ đạo/giới hạn hành trình -> sai số so với góc đo
        -> Sugeno(e/E_az, -omega_do/V_az) -> vận tốc yêu cầu
        -> giới hạn vận tốc/gia tốc/đổi chiều -> STEP/DIR -> TB6600 -> motor -> đai -> anten
                                                         ^ góc đo trục anten phản hồi
```

Giữ Sugeno bậc 0, hai đầu vào, năm tập tam giác NB/NS/ZE/PS/PB với tâm [-1,-0,5,0,0,5,1], 25 luật, AND tích và giải mờ trung bình trọng số [S9]. Mã hiện có thực hiện đúng một FIS dạng này; công thức tạo luật là điểm bắt đầu tinh chỉnh, chưa phải tập luật tối ưu.

Các singleton hiện có (hàng là e, cột là đầu vào vận tốc lấy dấu âm):

| e / -omega | NB | NS | ZE | PS | PB |
|---|---:|---:|---:|---:|---:|
| NB | -1 | -1 | -1 | -1 | -1 |
| NS | -1 | -1 | -1 | -0,75 | -0,5 |
| ZE | -0,5 | -0,25 | 0 | 0,25 | 0,5 |
| PS | 0,5 | 0,75 | 1 | 1 | 1 |
| PB | 1 | 1 | 1 | 1 | 1 |

Sai số dương lớn làm quay dương; khi đang tiến nhanh về đích, đầu vào -omega âm làm giảm lệnh. Lấy đạo hàm từ góc đo đã lọc giúp tránh xung đạo hàm khi thay đổi góc đặt. Bộ giới hạn gia tốc, quãng dừng và dải chết nằm ngoài luật mờ; phải mô tả riêng trong báo cáo và giữ giống nhau khi so baseline.

E_az, V_az, hệ số lọc, deadband và gia tốc phải tinh chỉnh từ phần cứng. Bắt đầu kiểm tra ở vận tốc khoảng 5–10°/s và gia tốc thấp, rồi tăng sau khi đo. 30°/s là mục tiêu tham khảo cần kiểm chứng; không mặc nhiên là yêu cầu đã đạt cho cấu hình mới. Có thể giữ chu kỳ vòng ngoài 10 ms làm giá trị khởi đầu; cần đo thời gian thực thi trên F103.

### 6.2 Hướng mở rộng nếu sau này cần mờ hai trục

**Không thuộc cấu hình hiện chọn.** Hiện tại STM32 gửi PWM theo bảng hiệu chuẩn cho LD-1501MG, servo tự đóng vòng vị trí bên trong. Có thể thêm ramp lệnh để chuyển động êm, nhưng ramp không biến trục nâng thành vòng mờ. Các phương trình dưới đây chỉ áp dụng khi bổ sung phản hồi nâng và đổi phạm vi thực hiện.

Dùng cảm biến nâng tạo e_el và vận tốc đo. FIS thứ hai có cùng cấu trúc nhưng E_el, V_el, luật/hệ số có thể khác. Đầu ra vận tốc mờ đi qua giới hạn rồi tích phân thành **lệnh vị trí cho servo**:

```text
v_el = governor(V_el * F_el(e_el/E_el, -omega_el_do/V_el))
q_servo_cmd[k+1] = clamp(q_servo_cmd[k] + Ts*v_el, q_cmd_min, q_cmd_max)
pulse_us = calibration(q_servo_cmd)
```

Khởi tạo lệnh theo vị trí thực và quan hệ góc servo–góc nâng đã hiệu chuẩn. Giới hạn độ dẫn trước giữa lệnh và góc đo để lệnh không tích lũy xa khi kẹt; đóng băng/reset trạng thái khi lỗi/giới hạn. Vòng mờ ngoài chạy chậm hơn động học vòng servo bên trong; tốc độ cập nhật PWM 50 Hz không tự chứng minh băng thông servo. Chọn lọc, hệ số và tốc độ vòng ngoài qua thử nghiệm.

Không điều khiển trực tiếp điện áp/mô-men motor bên trong servo ba dây. Lợi ích cần chứng minh là cải thiện bám góc chảo khi có tải, rơ hoặc lệch góc; nếu so với servo mặc định không cải thiện thì báo cáo trung thực. Hai vòng SISO có kiểm tra chuyển động đồng thời là mức phù hợp bài tập lớn; chưa cần FIS bốn đầu vào với hàng trăm luật.

Nếu dùng quỹ đạo liên tục, chọn rõ `e_dot = r_dot - omega_do` hoặc giữ phản hồi -omega và thêm feedforward r_dot. Bộ hãm sqrt(2*a*abs(e)) phù hợp bài đến vị trí đứng yên; cần đánh giá lại khi mục tiêu chuyển động.

## 7. Nhận dạng và tiêu chí nghiệm thu

Thứ tự thực hiện: xác minh điện/đấu cuộn -> lắp và kiểm tra cảm biến -> hiệu chuẩn góc -> đo đáp ứng vòng hở nhỏ -> khớp mô hình -> tinh chỉnh mờ trong mô phỏng -> chạy góc nhỏ trên board -> nâng dần tốc độ -> kiểm tra hai trục đồng thời.

Đo ít nhất: số xung/vòng thực, tỉ số truyền, chiều quay, rơ hai chiều, dòng/nguồn khi chạy, đáp ứng servo theo xung, khối lượng/chênh tâm chảo. Lưu lại mỗi cấu hình driver và điện áp thử. Dùng tập dữ liệu khác để kiểm chứng mô hình đã khớp, tránh vừa khớp vừa chấm cùng một lần chạy.

Các mục tiêu sau là **đề xuất ban đầu để thống nhất với giảng viên**, không phải kết quả đo hoặc cam kết linh kiện:

| Đại lượng | Mục tiêu thử ban đầu |
|---|---|
| Sai số cuối phương vị | ≤0,5° ở từng điểm, trong cửa sổ 2 s cuối |
| Sai số cuối nâng | ≤1° ở từng điểm, trong cửa sổ 2 s cuối |
| Độ lặp lại | Báo khoảng max–min tại cùng đích khi tiếp cận hai chiều; lặp ≥5 lần |
| Vọt lố | Bước đủ lớn: thử mục tiêu ≤2%; luôn báo thêm độ vượt tuyệt đối theo độ |
| Xác lập | Báo cả T_s,2% và T_s,abs; chỉ ghi đạt khi ở trong dải đến hết đoạn thử |
| Tốc độ | Đo mỗi trục, nêu cách lọc/ước lượng; tăng dần đến giới hạn được xác minh |
| Lỗi | Dừng yêu cầu chuyển động khi quá hạn cảm biến, sai hành trình hoặc mất heartbeat; thời hạn đặt theo tốc độ và quãng dừng cho phép |

`T_s,abs` dùng ±0,5° phương vị, ±1° nâng. Với bước nhỏ có 2% thấp hơn khả năng đo, không âm thầm gọi dải tuyệt đối là “2%”. Có thể định nghĩa chỉ tiêu vận hành dải hỗn hợp max(2% biên độ bước, dải tuyệt đối), nhưng phải đặt tên riêng. Với bước 0°, POT không xác định. Sai số xác lập “bằng 0” cần diễn giải theo độ phân giải, độ chính xác hiệu chuẩn và dải đánh giá.

Với cấu hình hiện tại, lưu timestamp, mã test, chế độ controller, góc phương vị đặt/đo, vận tốc đo/lệnh, tần số STEP, lệnh góc/xung servo và trạng thái lỗi. Góc nâng thực chỉ có từ phép đo ngoài; không tạo cột góc nâng đo bằng cách sao chép lệnh PWM. Đề xuất log phương vị 50–100 Hz tùy dung lượng đường truyền; đo đỉnh xung bằng oscilloscope/logic analyzer và ghi rõ giới hạn của tốc độ log. Log MCU chưa thay thế chuẩn góc độc lập dùng để xác minh cảm biến. Nếu cần overshoot hoặc thời gian xác lập động của nâng, phải đo ngoài đủ nhanh, ví dụ video đã hiệu chuẩn; thước đọc ở cuối chỉ đủ đánh giá sai số cuối.

File `test_matrix.csv` liệt kê các ca cần chạy; ô kết quả để `NOT_RUN`. Không có kết quả phần cứng nào được tạo trong lần rà soát này. Giữ tốc độ/hành trình, tải, nguồn, vị trí ban đầu, lọc và giới hạn giống nhau khi so controller. Tinh chỉnh baseline công bằng và dành ca kiểm chứng chưa dùng để tune.

## 8. Demo với giảng viên, khoảng 8–10 phút

1. **1 phút:** chỉ mô hình hai trục, motor, driver, hai cảm biến trục ra; chỉ ra trên sơ đồ vị trí FIS và nguồn phản hồi.
2. **1 phút:** giải thích một luật tăng tốc và một luật hãm; mở mặt điều khiển/rule viewer để thấy FIS hoạt động.
3. **2 phút:** giữ nâng cố định; chạy phương vị 0 -> +30 -> -30 -> 0°. Hiển thị đặt/đo/lỗi và thời gian xác lập.
4. **1 phút:** giữ phương vị; chạy nâng quanh trung tính cơ khí, ví dụ lệnh servo 75 -> 90 -> 105° sau khi hiệu chuẩn; hiển thị góc nâng thật tương ứng. Nếu chỉ làm một vòng mờ, nói rõ đây là servo vị trí.
5. **1–2 phút:** chạy cặp góc liên tiếp trong hành trình đã xác nhận, cho thấy hai trục cùng bám. Đánh dấu mục tiêu bằng thước/vạch góc hoặc chuẩn quan sát cố định; không cần phát/thu RF.
6. **1 phút:** mở bảng so P/PD và mờ cùng điều kiện. Nếu demo trực tiếp chỉ một chế độ, dùng log/video lặp lại của chế độ kia; ghi rõ đâu là số đo và đâu là mô phỏng.
7. **1 phút:** minh họa phần mềm mất heartbeat hoặc lỗi dữ liệu cảm biến có kiểm soát; show fault và dừng lệnh. Không cần kẹt cơ cấu. Dừng STEP có thể vẫn giữ mô-men; không mô tả là cắt toàn bộ năng lượng.

Nên dùng các góc vừa phải như trên thay cho quét 0–360° vì cơ cấu có dây và chưa có slip ring. Chỉ mở rộng hành trình sau khi kiểm tra dây/va chạm thật. Demo có màn hình log, sơ đồ vòng kín, bảng tiêu chí và video dự phòng sẽ thuyết phục hơn chỉ cho chảo quay theo góc đã lập trình.

Khi được hỏi vì sao không dùng hàm truyền DC trong PDF: “Đối tượng thực đã thay thành stepper và servo vị trí; em giữ phương pháp thiết kế mờ và cách đánh giá, còn mô hình đối tượng được xây dựng/nhận dạng theo phần cứng thực.” Khi được hỏi vì sao cần cảm biến dù stepper đếm xung: “Cảm biến cho biết góc thực sau đai và cho vòng mờ sửa được sai lệch cơ khí/mất bước.”

## 9. Kết quả chạy lại trong lượt rà soát

Đã đọc hai trang PDF cả văn bản và hình, đối chiếu mã MATLAB/C, cấu hình CAD và các báo cáo có sẵn. Đã biên dịch lại lõi C với GCC `-Wall -Wextra -Werror`, chạy đạt 40.401 điểm kiểm tra; chạy lại trên MATLAB R2026a Update 2 với script `run_review_checks.m`.

- 1.681 điểm đối chiếu FIS–C: sai lệch lớn nhất khoảng 1e-7; MATLAB thủ công–FIS khoảng 3,33e-16.
- Chạy lại nominal V3 48 s khớp ba chỉ số vọt lố/sai số cuối/tốc độ với báo cáo cũ trong lần chạy này.
- Cấu hình cũ: vọt lố phương vị lớn nhất≈0,3942%; tốc độ đỉnh≈27,7193°/s; sai số góc trạng thái mô hình cuối lớn nhất≈0,0125°.
- Ở các đích này encoder mô phỏng có thể báo sai số≈0 trong khi trạng thái góc thật của mô hình còn lệch. Encoder cũ chia 0,15°/count; không thể dùng số 0,0125° làm bằng chứng độ chính xác thực đã đo.
- Sai số nâng ở cuối bài mô phỏng≈0,1933°; chỉ số này không nằm trong `pass_tracking` và dùng servo giả định.
- CSV cũ ghi tốc độ đỉnh≈48,28°/s khi nhả kẹt và≈45,88°/s ở tải xung 0,08 N.m. Các ca này không đạt bám góc theo giới hạn cũ.

Các giá trị trên thuộc **cấu hình mô phỏng V3 cũ có encoder**, chưa xác nhận hệ STP-43D2073-01 + TB6600 + LD-1501MG với MT6701 người dùng đang chuẩn bị tích hợp. Không có nạp chip, kết nối UART hay chuyển động phần cứng trong lần này.

Chạy lại từ thư mục Review: `run_review_checks`. Kết quả riêng ở `results/review_checks.json` và `results/legacy_true_vs_encoder.csv`, không ghi đè kết quả Simulation cũ.

## 10. Thứ tự chỉnh sửa dự án tiếp theo

1. Xác minh module TB6600 hỗ trợ 12 V, nhãn STP, thông số board F103 và đấu cuộn; chốt nhánh servo khoảng 7 V đủ dòng.
2. Gắn MT6701 có sẵn lên trục phương vị sau đai; sửa gá theo số đo. Ghi rõ một vòng mờ phương vị và servo nâng nội bộ trong phạm vi báo cáo.
3. Tạo cấu hình phần cứng thực riêng; không đổi tên cấu hình cũ rồi giữ nguyên số. Lớp driver góc phải thay encoder TIM2/2400 bằng giao tiếp của cảm biến đã chọn.
4. Tham số hóa góc đặt, thời gian và bộ chấm trong mô phỏng; bổ sung baseline trên cùng prototype, chỉ tiêu nâng, lỗi cảm biến và quỹ đạo đồng thời.
5. Đồng bộ bộ tạo lệnh phương vị/nâng giữa MATLAB và C; dùng bảng hiệu chuẩn servo, ramp lệnh và kiểm tra góc nâng bằng chuẩn ngoài.
6. Nhận dạng từ phần cứng rồi tinh chỉnh/kiểm chứng lại, xuất bảng số đo theo `test_matrix.csv` và tổ chức demo như mục 8.

Chưa thể chốt bộ hệ số mờ cuối, dòng DIP, độ chính xác hoặc firmware nạp ngay khi chưa có số đo/nhãn chính xác. Phần đã chọn là một vòng phản hồi mờ phương vị dùng MT6701, servo nâng có vòng nội bộ, nguồn 12 V cho TB6600 và nhánh hạ áp khoảng 7 V cho servo.

## Nguồn kỹ thuật

- [S1] [Leadshine DM542 V3.0 User Manual, bản do hãng phát hành được lưu trên website nhà phân phối](https://kitaez-cnc.com/f/leadshine_dm542_v30.pdf), phần 2 và 6.
- [S2] [Leadshine DM542E, trang hãng; mẫu khác DM542-05](https://en.leadshine.com/product-detail/stepper-drive/stepper/DM542E.html).
- [S3] [Hiwonder, tài liệu PWM LD-1501MG](https://wiki.hiwonder.com/projects/Ackermann-Chassis/en/latest/docs/3_Arduino_Version_formatted.html), mục 3.2.3.
- [S4] [Hiwonder, bảng thông số LD-1501MG trong sản phẩm Ackermann](https://www.hiwonder.com/products/ackermann-steering-chassis).
- [S5] [MagnTek MT6701 Rev.1.8](https://www.magntek.com.cn/upload/pdf/202407/MT6701_Rev.1.8.pdf), phần tính năng và giao tiếp số.
- [S6] [ams OSRAM AS5600 datasheet](https://look.ams-osram.com/m/7059eac7531a86fd/original/AS5600-DS000365.pdf).
- [S7] [Oriental Motor, các cách đấu unipolar/bipolar](https://www.orientalmotor.com/stepper-motors/technology/unipolar-bipolar-connections.html); nguyên lý chung, không phải pinout STP-43D2073-01.
- [S8] [Texas Instruments, How to Improve Motion Smoothness and Accuracy of Stepper Motors](https://www.ti.com/lit/an/sloa293a/sloa293a.pdf).
- [S9] [MathWorks, sugfis](https://www.mathworks.com/help/fuzzy/sugfis.html).
- [S10] [DFRobot, module TB6600 DRI0043, dải nguồn 9–42 VDC](https://wiki.dfrobot.com.cn/_SKU__DRI0043__TB6600_%E6%AD%A5%E8%BF%9B%E7%94%B5%E6%9C%BA%E9%A9%B1%E5%8A%A8%E5%99%A8).

Trạng thái tham số và linh kiện thực được lưu ở `actual_hardware.json`. Các nguồn không phải datasheet gốc đúng STP-43D2073-01 không được dùng để khẳng định dòng pha/mô-men của motor thực.
