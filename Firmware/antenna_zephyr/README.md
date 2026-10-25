# Firmware Zephyr — Anten V5 (STM32F103 Blue Pill)

Cấu hình: **STM32F103C8 Blue Pill + TB6600 (12 V, 1/16) + 17HS1352‑P4130 + đai GT2 20T:80T (4:1) + MT6701 trên trục anten + LD‑1501MG (~7 V)**. Zephyr 3.7.0, Zephyr SDK 0.16.8, board `stm32_min_dev@blue`.

> Trạng thái: **đã build, đã kiểm thử trên máy tính (host test, SIL bằng MEX, PIL qua board ảo) — chưa nạp và chưa chạy trên chip thật**. Lúc làm bài không có Blue Pill/ST‑LINK nào cắm vào máy. Làm theo mục "Chạy thử lần đầu" khi có phần cứng.

## 1. Cấu trúc

```
antenna_zephyr/
  core/            C99 thuần, không phụ thuộc Zephyr — dùng chung firmware / MATLAB MEX / test máy tính
    antenna_core.*   bộ mờ Sugeno 25 luật, giới hạn quãng dừng + gia tốc, làm trơn lệnh,
                     đọc góc MT6701 (offset, chiều, hiệu chuẩn), giám sát lỗi, ramp servo, chuỗi đề bài
    stepgen.*        máy trạng thái phát STEP/DIR (gọi từ ngắt timer)
    link_proto.*     giao thức dòng lệnh ASCII trên UART (cả chế độ PIL)
  src/             phần gắn với phần cứng Zephyr
    main.c           vòng 10 ms: đọc MT6701 → acore_step → cập nhật timer STEP + PWM servo → lệnh UART
    hw_stepper.c     TIM2 (counter 1 MHz) → ngắt mỗi cạnh STEP; GPIO STEP/DIR/ENA
    hw_mt6701.c      I2C2 400 kHz, địa chỉ 0x06, thanh ghi 0x03/0x04 (14 bit)
    hw_servo.c       TIM4_CH1 PWM 50 Hz, độ phân giải 1 µs
    uart_link.c      USART1 ngắt, hàng đợi dòng nhận, ring buffer phát 4 KB
    params_store.c   lưu tham số (NVS) ở 4 KB cuối flash: mốc 0, chiều, hiệu chuẩn, hệ số mờ
  app.overlay      sơ đồ chân / timer / vùng flash      prj.conf, Kconfig
  build.ps1        build (tự ánh xạ thư mục sang ổ ảo vì đường dẫn có dấu tiếng Việt)
  flash.ps1        nạp bằng STM32CubeProgrammer (ST‑LINK SWD hoặc bootloader UART)
  tests/host/      test máy tính + "board ảo" (cùng giao thức) dùng cho MATLAB
  dist/            antenna_v5_bluepill.hex/.bin/.elf/.map + build_info.json
```

Bộ nhớ (build hiện tại): Flash 42 872 B / 60 KB vùng code, RAM 10 048 B / 20 KB.

## 2. Sơ đồ chân Blue Pill

| Chân | Chức năng | Nối tới |
|---|---|---|
| PB13 | STEP (GPIO, ngắt TIM2) | tầng NPN → TB6600 **PUL−** |
| PB12 | DIR | tầng NPN → TB6600 **DIR−** |
| PB14 | ENA (tùy chọn) | tầng NPN → TB6600 **EN−**; mức cao = nhả động cơ |
| PB6 | TIM4_CH1, PWM servo 50 Hz | 1 kΩ nối tiếp → dây tín hiệu LD‑1501MG |
| PB10 / PB11 | I2C2 SCL / SDA | MT6701 SCL / SDA, kéo lên 4,7 kΩ về 3,3 V (nếu module chưa có) |
| PA9 / PA10 | USART1 TX / RX, 115200 8N1 | RX / TX của USB‑UART (CP2102…) |
| PA13 / PA14 | SWD | ST‑LINK (SWDIO/SWCLK) |
| PC13 | LED trên board | 1 Hz: hoạt động; nháy ngắn 1 lần/s: chưa có mốc 0; 5 Hz: lỗi; sáng liên tục: PIL |

**TB6600 (nối chung anode, như hướng dẫn DFRobot DRI0043):** PUL+, DIR+, EN+ → +5 V. PUL−/DIR−/EN− → collector 2N3904; emitter → GND; base ← chân MCU qua 1 kΩ, 10 kΩ base–emitter. MCU mức cao → opto dẫn (8–15 mA). EN để hở nếu không dùng PB14 (driver luôn bật). Không nối 12 V vào chân STM32.

**DIP TB6600** (đối chiếu bảng in trên module thật, các bản TB6600 khác nhau):
- Vi bước 1/16 = 3200 xung/vòng: S1 OFF, S2 OFF, S3 ON.
- Dòng 1,0 A (đỉnh 1,2 A) cho motor 1,3 A: S4 ON, S5 OFF, S6 ON. Tắt nguồn trước khi gạt DIP.
- Motor 4 dây: A+/A− một cuộn, B+/B− cuộn kia (đo điện trở ~2,1 Ω để xác định cặp).

**MT6701:** cấp 3,3 V; module phải ở chế độ I²C/SSI (chân MODE theo tài liệu module; nếu không đọc được địa chỉ 0x06 thì kiểm tra MODE). Khe nam châm–mặt IC 0,5–2 mm, lệch tâm ≤ 0,3 mm (datasheet). Sai số phi tuyến INL ±1° điển hình khi chưa hiệu chuẩn — xem mục 6.

**Nguồn:** 12 V → TB6600; buck ~7 V (≥ 3 A đỉnh) → servo; 5 V → chân 5V Blue Pill (hoặc cấp qua USB); GND chung hình sao.

## 3. Build và nạp

```bash
powershell -ExecutionPolicy Bypass -File build.ps1
```

```bash
powershell -ExecutionPolicy Bypass -File build.ps1 -Pristine
```

Mặc định dùng `D:\zephyrproject` (Zephyr 3.7), `D:\zephyr-sdk\zephyr-sdk-0.16.8`, dtc trong `C:\msys64\mingw64\bin`; đổi bằng biến môi trường ghi ở đầu `build.ps1`. Thư mục được ánh xạ tạm sang ổ `W:` (subst) vì toolchain Windows không nhận đường dẫn có "Bài tập lớn".

Nạp (ngắt nguồn 12 V trước):

```bash
powershell -ExecutionPolicy Bypass -File flash.ps1
```

```bash
powershell -ExecutionPolicy Bypass -File flash.ps1 -Port COM7
```

Lệnh thứ nhất dùng ST‑LINK; lệnh thứ hai dùng bootloader ROM qua USB‑UART (BOOT0 = 1, reset, nạp, rồi BOOT0 = 0). Vùng tham số 0x0800F000–0x0800FFFF không bị xóa khi nạp lại.

## 4. Giao thức UART (115200 8N1, kết thúc dòng LF)

| Lệnh | Ý nghĩa |
|---|---|
| `H` | heartbeat (gửi ≤ 0,4 s một lần khi máy tính điều khiển; mất > 2 s → lỗi 1) |
| `G az el` / `A az` / `E el` | đặt phương vị/nâng (độ, số thực). Phương vị cắt trong ±150°, nâng trong el_min..el_max |
| `S` | dừng êm (giảm tốc rồi giữ vị trí) |
| `F` | dừng khẩn: chốt lỗi 16, ngừng STEP ngay |
| `C` | xóa lỗi, giữ vị trí hiện tại |
| `Z [az]` | vị trí hiện tại = az (mặc định 0), **lưu flash** — chỉ khi đứng yên, đã căn vạch bằng tay |
| `Q [1]` | chạy chuỗi đề bài 60/150/30/90°, nâng 60/90/120/80°, mỗi điểm 12 s (`Q 1` lặp) |
| `T ms` / `?` | chu kỳ telemetry (0 = tắt, ≥ 10 ms) / gửi một dòng |
| `P` / `P tên giá_trị` / `PX tên hex` | liệt kê / đặt tham số (đơn vị hiển thị) / đặt đúng bit IEEE‑754 |
| `W` / `D` / `L` | lưu flash / nạp mặc định / đọc lại bản đã lưu |
| `M 0\|1`, `X k raw steps flags`, `GX mask az el` | chế độ PIL (dùng bởi MATLAB) |
| `V` | phiên bản |

Telemetry: `T,ms,mode,fault,đặt_mdeg,đo_mdeg,vSTEP_mdeg/s,vđo_mdeg/s,steps,raw,nâng_cdeg,servo_us,nửa_chu_kỳ_us,vòng_us,settled,pil`. Mode: 0 chưa có mốc, 1 hoạt động, 2 lỗi.

Mã lỗi (bit): 1 heartbeat, 2 vượt ±155°, 4 lệch STEP–cảm biến > 4° trong 0,3 s (kẹt/trượt/mất bước/sai chiều), 8 vòng điều khiển trễ 3 lần liên tiếp, 16 dừng khẩn, 32 MT6701 lỗi/nhảy > 3° trong 3 mẫu, 64 tham số không hợp lệ. Khi lỗi: ngừng STEP ngay, servo giữ lệnh cuối; driver vẫn giữ mô-men (chỉ ngắt nguồn mới cách ly năng lượng).

## 5. Chạy thử lần đầu

1. **Chưa cấp 12 V.** Cấp Blue Pill qua USB‑UART, mở MATLAB → `Simulation_V5` → `v5_console("COMx")`. Dòng khởi động báo `params=default ... sensor=0`.
2. Quay tay anten: góc đo phải đổi đều, không nhảy. Nếu chiều ngược quy ước: `P sensor_sign -1`.
3. Căn vạch 0° bằng tay → bấm **Z** (lưu flash). LED chuyển sang nháy 1 Hz.
4. Servo: thử `E 80`, `E 100`; đo góc thật bằng thước đo góc, chỉnh `us_ref`, `us_per_deg`, `el_min_deg`, `el_max_deg` nếu cần.
5. **Cấp 12 V**, thử `A 2`. Nếu anten quay ngược → lỗi 4 xuất hiện sau ~0,3 s: `C`, rồi `P motor_sign -1`, thử lại.
6. `W` để lưu. Thử `A 30`, `A -30`, rồi `Q` (chuỗi đề bài). Ghi log CSV trong console.
7. Hiệu chuẩn MT6701 (tùy chọn, tăng độ chính xác tuyệt đối từ ~±1° xuống ~0,05°): `v5_calibrate_mt6701("COMx", true)`.
8. Kiểm tra PIL trên chip: `v5_pil_board("COMx")` (chế độ PIL tự nhả driver, không phát STEP; nên tắt 12 V).

## 6. Kiểm thử đã chạy

| Kiểm thử | Lệnh | Kết quả |
|---|---|---|
| Host test lõi C (gcc, -Wall -Wextra -Werror) | `python tests/host/run_host_tests.py` | 22 631 phép kiểm, 0 lỗi |
| Build Zephyr (warnings = errors) | `build.ps1` | đạt |
| SIL: MEX(C) = MATLAB = FIS toolbox; PIL qua board ảo | `v5_sil_check(true)` trong `Simulation_V5` | đạt, 0 sai khác bit |
| PIL trên STM32 thật | `v5_pil_board("COMx")` | **chưa chạy (không có board)** |
