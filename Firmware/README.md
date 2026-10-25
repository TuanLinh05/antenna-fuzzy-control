# Firmware STM32F103

## Bản hiện hành: Zephyr cho cấu hình V5 → [antenna_zephyr/](antenna_zephyr/README.md)

STM32F103C8 Blue Pill + TB6600 (12 V, 1/16) + 17HS1352‑P4130 + đai 4:1 + **MT6701 trên trục anten (I2C2)** + LD‑1501MG. Zephyr 3.7, file nạp `antenna_zephyr/dist/antenna_v5_bluepill.hex`. Lõi điều khiển (`antenna_zephyr/core/`) là C thuần, dùng chung với MATLAB (MEX/SIL, PIL) trong [../Simulation_V5](../Simulation_V5/README.md). Đã build và kiểm thử trên máy tính; chưa chạy trên chip thật.

Phần dưới đây là **firmware cũ V3 (bare‑metal, encoder AB)**, giữ lại để đối chiếu; không dùng cho V5.

---

## Firmware cũ — Anten V3

**CAD hiện hành là [V5 gia cố với MT6701](../3D%20Print/Antenna_V5_Reinforced/README_START_HERE.md). Firmware trong thư mục này vẫn đọc encoder AB/2400 count, chưa có giao tiếp MT6701 và chưa nghiệm thu với motor/servo V5.** Bản cho V5 là `antenna_zephyr/` ở trên.

Đọc `DIEN_VA_DIEU_KHIEN.md` trước khi đấu hoặc nạp. Đây là bản thử nghiệm **đã biên dịch và kiểm tra trên máy tính, chưa thử trên chip**.

- `build/antenna_f103.hex` hoặc `.bin`: F103C8, Flash 64 KB, SRAM 20 KB, HSI 8 MHz. BIN nạp tại 0x08000000. Không nạp file này lên F4.
- `stm32f103_main.c`: GPIO/timer/UART/watchdog, vòng 100 Hz. `startup_f103.S`, `stm32f103c8.ld`: vector khởi động và bố trí bộ nhớ.
- `fuzzy_controller.c/.h`: Sugeno 25 luật, vận tốc yêu cầu tối đa 0,47 rad/s; dùng được làm lõi tính toán Cortex-M3/M4. F4 cần viết lại lớp ngoại vi/khởi động.
- `test_fuzzy.c`: 40.401 điểm kiểm tra, tràn encoder và dải chết; xuất CSV 1.681 điểm để MATLAB đối chiếu FIS.
- `build_firmware.py`: GCC máy tính + GNU Arm Embedded trong STM32CubeIDE đã cài. Đường dẫn công cụ hiện khai báo trong script; chỉnh nếu cài chỗ khác. Biên dịch có `-Wall -Wextra -Werror`.

Bản đã build dùng 5.152 byte Flash, 2.432 byte RAM gồm stack dự phòng 2.048 byte. Đây là kiểm tra tĩnh và dự trữ, chưa phải đo đỉnh stack/thời gian chạy trên chip. Báo cáo ở `build/firmware_build_validation.json`.

Nạp qua CP2102/ROM bootloader hoặc bộ SWD đang có; phần điện ghi rõ mức 3,3/5 V, dòng TB6600 và nguồn servo. Dùng `tools/hardware_console.m` để gửi heartbeat/góc bằng UART sau khi đã căn mốc và xác nhận chiều. Cửa sổ này chưa được kiểm thử với phần cứng.

Không có auto-home hoặc công tắc hành trình cứng. Mỗi lần bật nguồn phải căn tay và gửi Z; đặt góc phương vị trong ±150°, nâng ban đầu 45–135°. Dừng S giữ nguồn holding; muốn cách ly năng lượng phải ngắt adapter. Phát hiện lệch bám không thay phanh cơ khí khi kẹt/va đập.
