# Điện và điều khiển V3

Chọn **STM32F103C8T6** làm cấu hình chính. Lõi Sugeno25 luật đã biên dịch cho Cortex-M3 và Cortex-M4; firmware hoàn chỉnh đi kèm dành riêng cho F103C8, không nạp fileHEX đó vào F4. Kết quả biên dịch không thay thế thử I/O thật.

## Cấu trúc vòng kín

Góc đặt -> sai số góc và vận tốc đo -> bộ mờ Sugeno -> vận tốc yêu cầu -> giới hạn gia tốc -> STEP/DIR -> NEMA17 -> đai4:1 -> trục anten -> encoder600P/R -> STM32.

Encoder đo **trục anten sau đai**, có2400count/vòng khi giải mã4 cạnh, tương ứng0,15°/count. Độ chia lệnh1/16 là0,028125°/microstep; đây không phải độ chính xác đã đo. Servo nâng dùng vòng điều khiển bên trong servo; V3 chưa có cảm biến nâng độc lập và không gọi trục nâng là vòng fuzzy đã được thực nghiệm.

## Sơ đồ chân F103

| Chân | Chức năng | Đấu dây |
|---|---|---|
| PA0/TIM2_CH1 | Encoder A | A xanh lục ->1k nối tiếp ->PA0; A kéo lên3,3V bằng4k7 |
| PA1/TIM2_CH2 | Encoder B | B trắng ->1k nối tiếp ->PA1; B kéo lên3,3V bằng4k7 |
| PA6/TIM3_CH1 | STEP | PA6 ->1k ->base Q1; collectorQ1 vàoPUL-;PUL+ vào5V |
| PA7 | DIR | PA7 ->1k ->base Q2; collectorQ2 vàoDIR-;DIR+ vào5V |
| PB6/TIM4_CH1 | Servo | PB6 ->1k ->baseQ3; collectorQ3 vào dây tín hiệu servo, kéo lên5V bằng4k7 |
| PA9/USART1_TX | Dữ liệu ra | NốiRX của CP2102 |
| PA10/USART1_RX | Lệnh vào | NốiTX của CP2102, mức logic3,3V |
| GND | Mass tham chiếu | GND MCU, emitter3 transistor, encoder, driver và5V nối chung theo hình sao |

Q1/Q2/Q3 dùng2N3904. Mỗi base có10k xuống emitter; emitter vềGND. Với linh kiện ON Semiconductor theo datasheet: chân1=E,2=B,3=C; đối chiếu đúng hướng nhìn vỏ và linh kiện nhận được. Tín hiệu servo được đảo quaQ3 nên firmware dùng **PWM2**, tạo xung dương ở collector. Không đổi sangPWM1 mà giữ nguyên mạch.

Không nối5V hay12V vào PA0/PA1/PB6. Encoder cấp5V ở đỏ, GND ở đen; ngõ ra NPN cực thu hở chỉ kéo lên3,3V. Kiểm tra mức điện áp A/B khi quay tay trước khi nối vào MCU. ENA của driver để hở theo cấu hình mặc định và kiểm tra driver có giữ trục khi dừng; lỗi phần mềm dừng phát STEP, không chủ động ngắt mô-men giữ.

## Đấu nguồn

1. Adapter kín12V5A -> jack5525 cái -> nhánh TB6600 và đầu vàoMP2482.
2. MP2482 tạo5V cho servo, encoder và mạch đệm. Đo ra5V đúng cực trước khi gắn servo. Tụ1000uF16V song song5V/GND sát nhánh servo, đúng cực tụ.
3. BoardF103 nhận5V ở chân5V trên board có ổn áp3,3V. Khi dùngUSB cấp board thì không đấu đồng thời5V ngoài vào board nếu chưa kiểm tra mạch cách ly nguồn. CP2102 khi board đã được cấp nguồn chỉ nốiTX/RX/GND; không nối chân5V/3,3V của CP2102.
4. Dây nguồn đỏ/đen18AWG; dòng servo không đi qua dây Dupont hoặc padPCB mảnh. Tín hiệu và nguồn tách đường, mass về điểm chung gần đầu ra nguồn. Bảng hàn đặt cố định ngoài cơ cấu quay và cách điện mặt dưới.
5. Dây servo300mm chưa đủ cho mọi cách đi dây. Nối dài bằng dây silicon mềm, hàn và bọc riêng từng mối bằng ống co nhiệt, chừa khoảng500–600mm vòng dây hoạt động tùy vị trí đặt mạch. Dây tín hiệu dùng dây mềm dòng nhỏ; không để mối nối chịu kéo. Quay tay hết phạm vi sử dụng với nguồn tắt trước khi chạy điện. Chưa có slipring.

Ngân sách thiết kế: servo3A đỉnh, encoder0,1A, MCU và logic0,15A ở5V; nhánh5V dự kiến dưới3,25A. Đây là giả thiết chọn nguồn, không phải dòng kẹt trục servo đã đo. Mức5A củaMP2482 là thông số cửa hàng; phải kiểm tra nhiệt và sụt áp khi chạy tải. Không giữ servo ở trạng thái kẹt.

## Driver và hành trình ban đầu

- TB6600 chọn1/16, tương ứng3200xung/vòng motor và12800xung/vòng anten. Đối chiếu bảngDIP in trên đúng driver nhận được; các bản TB6600 có bảng khác nhau.
- Bắt đầu mức dòng1,0A rồi kiểm tra tải; không tăng quá mức1,5A đã chọn khi chưa đo dòng và nhiệt. Đừng suy diễn nhãn dòng peak thànhRMS. Thông số motor1,68A/pha không có nghĩa cấp trực tiếp12V vào cuộn dây.
- STEP có độ rộng50us; tần số yêu cầu ở30°/s là1066,7Hz. Firmware giới hạn vận tốc yêu cầu0,47rad/s và gia tốc0,5236rad/s².
- Góc phương vị đặt trong[-150°,150°], dừng lỗi nếu đo vượt155°. Đây là giới hạn phần mềm; không có công tắc hành trình cứng tự động trong BOM.
- Trục nâng khởi động ở90°. Ban đầu chỉ cho45–135° với xung1000–2000us. Cửa hàng nêu500–2500us mới đủ180°; chỉ mở rộng sau khi đo và thử từng đầu hành trình, tránh ép chặn.

## Bộ mờ và firmware

Hai đầu vào chuẩn hóa: e/0,15rad và -omega/0,47rad/s, cắt trong[-1,1]. Mỗi đầu vào có5 tam giác tại[-1,-0,5,0,0,5,1].25 luật dùng AND tích; kết luận singleton=sat(2*c_e+0,5*c_de), giải mờ trung bình có trọng số. Đầu ra đổi thành vận tốc bằng hệ số0,47rad/s. Giới hạn quãng dừng sqrt(2*a*abs(e)), giới hạn gia tốc và dải chết0,12° được ghi riêng, không gọi chúng là luật mờ.

`Firmware/build_firmware.py` tạo fileELF/BIN/HEX trong`Firmware/build/`. Bản này dùngHSI8MHz,100Hz vòng điều khiển, TIM2 đọc encoder4 cạnh, TIM3 phát STEP bằng phần cứng, TIM4 tạoPWMservo50Hz. Tần số và độ rộng xung phải đo lại trên board thật; HSI có sai số nên cần hiệu chỉnh servo hoặc đổi sang cấu hình HSE đã xác nhận.

Đã kiểm tra40401điểm đầu vào trên máy tính: đầu ra hữu hạn, có giới hạn, đối xứng và đơn điệu theo sai số; đã kiểm tra tràn bộ đếm encoder. Firmware biên dịch không cảnh báo với`-Wall -Wextra -Werror`, chiếm khoảng5,2KBFlash và2,5KBRAM kể cả2KBstack dự phòng. Chưa đo thời gian chạy trên chip; phép so sánh lõiC với FIS được thực hiện trong bộ mô phỏng MATLAB.

## Nạp và chạy thử

Có thể nạp qua ROM bootloader UART với CP2102: ngắt nguồn động lực, BOOT0=1,BOOT1=0, resetboard; dùng STM32CubeProgrammer chọnUART đúngCOM để nạp HEX vào0x08000000. Sau đó BOOT0=0 và reset. Nếu cóST-LINK/J-LINK thì dùngSWD theo hướng dẫn của thiết bị. Không nạp khi cơ cấu đang mang tải hoặc chưa kiểm tra dây.

UART115200,8N1, kết thúc dòng bằngLF:

| Lệnh | Ý nghĩa |
|---|---|
| `Z` | Đặt vị trí **đã căn bằng tay** thành0; xóa lỗi và đồng bộ bộ đếm. Không phải tự tìmhome. Chỉ dùng khi cơ cấu đã đứng yên và đúng mốc. |
| `G 90 90` | Đặt phương vị90°, nâng90°, chỉ nhận sauZ và khi không có lỗi |
| `H` | Heartbeat, gửi ít nhất mỗi500ms trong khi làm việc |
| `S` | Dừng phát STEP và giữ lỗi, servo giữ lệnh cuối |
| `?` | Yêu cầu telemetry |

TelemetryCSV:ms,gócđo_millidegree,gócđặt_millidegree,vậntốc_millidegree_per_second,fault,zeroed. Chu kỳ định kỳ200ms. Lỗi bit:1=mất heartbeat hơn2s;2=vượt155°;4=lệch giữa xung lệnh và encoder hơn5° trong300ms;8=chu kỳ điều khiển hơn20ms;16=dừng theo lệnh;32=tràn dòngUART. Watchdog độc lập dự kiến khoảng1s theoLSI, chưa đo trên chip.

Trước khi đóng vòng: quay tay để xác nhận chiều dương encoder; kiểm tra motor chạy chiều dương tương ứng. Sửa`ENCODER_SIGN`/`MOTOR_SIGN` trong nguồn nếu cần. Sau đó mới thử mục tiêu1–2°, rồi tăng dần. Thiết kế có cơ chế phát hiện lệch bám, nhưng không thay thế kiểm tra đúng chiều phản hồi.

## Quan hệ với đề môn học

Đề PDF yêu cầu DC vớiN=150,u giới hạn±12V,J=7,25kg.m²,B=3,125Nm.s/rad. Prototype này là stepper đai4:1 với quán tính từCAD. Hai mô phỏng được báo cáo riêng. NhánhDC dùng bộ mờ tạo vận tốc và PI vận tốc tạo điện áp; nhánhprototype dùng bộ mờ tạo tần số STEP. Không dùng phương trình DC để mô tả trực tiếp stepper. Việc chấp nhận thay động cơ trong phần thực nghiệm cần theo phạm vi giảng viên cho phép.

Nguồn: [STM32F103x8 datasheet](https://www.st.com/resource/en/datasheet/stm32f103c8.pdf), [định nghĩa ngoại vi chính thức ST](https://github.com/STMicroelectronics/cmsis-device-f1/blob/master/Include/stm32f103xb.h), [2N3904 ON Semiconductor](https://www.onsemi.com/pdf/datasheet/2n3903-d.pdf), các trang sản phẩm trong BOM.
