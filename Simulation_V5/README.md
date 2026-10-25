# MATLAB/Simulink — Anten V5 (17HS1352‑P4130 + TB6600 + GT2 4:1 + MT6701 + LD‑1501MG)

Mô phỏng sát cấu hình phần cứng V5 và **kiểm thử chéo với firmware Zephyr**: bộ điều khiển trong mô phỏng chính là mã C của firmware (`../Firmware/antenna_zephyr/core`), biên dịch thành MEX. MATLAB R2026a + Fuzzy Logic Toolbox + Simulink, trình biên dịch MEX MinGW64.

> Mọi số liệu dưới đây là **mô phỏng** (chưa có số đo phần cứng). Lần chạy 25/10/2026, MATLAB R2026a Update 2.

## 1. Chạy nhanh

Trong MATLAB, chuyển Current Folder vào thư mục này:

| Lệnh | Việc |
|---|---|
| `v5_run_all` | toàn bộ: kiểm thử tương đương, 23 kịch bản, hình, JSON/CSV, video CAD (≈ 3–4 phút) |
| `v5_sil_check(true)` | MEX(C) ≡ MATLAB ≡ FIS toolbox ≡ test C trên máy tính; PIL qua board ảo |
| `r = v5_simulate(v5_config, v5_scenario('pdf')); v5_plot(r)` | một lần chạy, chuỗi đề bài 60/150/30/90° |
| `v5_build_simulink` | dựng `antenna_v5_sim.slx` (khối Fuzzy Logic Controller) và so với mô hình script |
| `v5_view_cad(30, 60)` | CAD V5 trong MATLAB, thanh trượt phương vị/nâng |
| `v5_tune(1)`, `v5_tune(2)` | lưới chỉnh giới hạn chuyển động / hình dạng luật mờ |
| `v5_calibration_demo` | thủ tục hiệu chuẩn MT6701 kiểm chứng trên mô hình |
| `v5_console("COM5")` | cửa sổ điều khiển board thật (hoặc `"virtual"`) |
| `v5_pil_board("COM5")` | PIL: lõi chạy trên STM32, đối tượng trong MATLAB, so từng bit với SIL |
| `v5_calibrate_mt6701("COM5", true)` | hiệu chuẩn MT6701 trên phần cứng, lưu vào flash |

## 2. Mô hình đối tượng (`v5_simulate`, `v5_plant_rhs`)

Trạng thái `x = [θm, ωm, iA, iB, θa, ωa, qe, ωe]`, tích phân RK4 bước ≤ 50 µs, **cạnh STEP đặt đúng thời điểm** do máy trạng thái `stepgen` (cùng logic với ngắt TIM2) sinh ra.

| Khối | Mô hình | Nguồn số liệu |
|---|---|---|
| 17HS1352‑P4130 | stepper lai 50 răng, 2 pha R‑L có sức phản điện động, mô-men `Km·(−iA sin Nrθ + iB cos Nrθ)` + detent `Td sin 4Nrθ` | 1,8°, 1,3 A, 2,1 Ω, 2,5 mH, 0,25 N·m, 35 g·cm² (listing + catalogue 17HS); Td = 0,012 N·m giả định |
| TB6600 12 V | vòng dòng trung bình (chopper) bão hòa điện áp bus, dòng vi bước `I cos/sin`, 1/16, tự giảm 50 % dòng khi đứng | hướng dẫn DFRobot DRI0043: 1,0 A (đỉnh 1,2 A), 3200 xung/vòng |
| Đai GT2 20T:80T | lò xo–giảm chấn hai nhánh có lực căng, độ mềm răng in, khe hở răng 0,2° (mềm khi đai căng) | CAD V5: 80 rãnh, tâm 87,917 mm; EA = 5 kN, η = 0,1 giả định |
| Tải phương vị | `J(qe) = c1 + c2 cos 2qe + c3 sin 2qe` từ CAD V5, ma sát Coulomb + nhớt, dây cáp | `audit/simulation_parameters_v5.json` |
| MT6701 | 14 bit (0,022°), INL hài bậc 1–2 (±0,8°, datasheet ±1° điển hình), nhiễu 0,012° rms, đọc ở t_k + 60 µs | MagnTek MT6701 Rev.1.8 |
| LD‑1501MG | PD nội bộ điều khiển duty động cơ DC, giới hạn mô-men–tốc độ, vùng chết, trọng lực CAD | 15–17 kg·cm, 0,16 s/60°; động học giả định |
| Firmware | lõi C (MEX) mỗi 10 ms, lệnh STEP ở t_k + 350 µs, xung servo áp ở khung PWM 20 ms kế tiếp | `../Firmware/antenna_zephyr` |

Mode xoắn thấp nhất: quán tính anten trên đai nối tiếp "lò xo từ" của stepper ≈ **11 Hz** (`cfg.plant.f_mode`). Mô phỏng cho thấy mode này bị kích khi khởi động/đảo chiều và do mô-men detent; đây là lý do firmware có (a) **retime** bộ phát STEP khi tốc độ tăng và (b) bộ làm trơn lệnh trung bình trượt 90 ms ≈ một chu kỳ dao động.

## 3. Bộ điều khiển (giống hệt firmware)

```
θ_ref ─► e = θ_ref − (θ_MT6701 + quãng còn treo) ─► x1 = e/E ┐
                         −ω̂/V (ω̂ = vận tốc lệnh) ─► x2 ──────┴► Sugeno 25 luật ─► v_des = v_max·u
  ─► giới hạn quãng dừng √(2a|e|) (rời rạc) ─► giới hạn gia tốc ─► vùng chết trễ (0,03°/0,10°)
  ─► trung bình trượt N mẫu ─► tần số STEP/DIR ─► TB6600 ─► motor ─► đai 4:1 ─► anten ─► MT6701
Nâng: góc đặt ─► dốc 30°/s ─► xung 500–2500 µs (hiệu chuẩn) ─► LD‑1501MG (vòng vị trí nội)
```

Luật mờ: 5 tập tam giác NB NS ZE PS PB cho mỗi đầu vào (tâm −1, −a, 0, a, 1), AND = tích, giải mờ trung bình trọng số; bảng luật `u_ij = sat(2·c_e,i + k_d·c_de,j)`. `v5_make_fis` tạo đúng FIS này cho Fuzzy Logic Toolbox (sai khác với mã C ≈ 1e‑7).

## 4. Kết quả

### 4.1 Kiểm thử tương đương MATLAB ↔ firmware (`results/sil_check.json`)

| Phép so | Kết quả |
|---|---|
| Tham số mặc định C (`acore_params_default`) ↔ `v5_ctrl_defaults.m` | trùng từng bit |
| Mặt mờ: MEX(C) ↔ bản MATLAB, 40 401 điểm | sai khác 0 |
| Mặt mờ: MEX(C) ↔ Fuzzy Logic Toolbox (`evalfis`) | ≤ 1,4·10⁻⁷ (float/double) |
| Mặt mờ: MEX ↔ vector từ test C trên máy tính | ≤ 5·10⁻¹⁰ |
| Bộ phát STEP (có retime): C ↔ MATLAB, 3 000 ca ngẫu nhiên | 0 sai khác |
| Vòng kín 20 s trên mô hình đầy đủ: lõi C (MEX) ↔ bản MATLAB | quỹ đạo trùng tuyệt đối |
| **PIL qua board ảo** (cùng `link_proto` như STM32), 2 000 bước | 0 sai khác bit |
| Simulink (khối Fuzzy Logic Controller) ↔ mô hình script | lệch ≤ 0,07° khi đã xác lập, đỉnh tốc độ 28,69°/s như nhau |

### 4.2 Bộ tham số đã chỉnh (`v5_tune`, `results/tune_stage1.csv`, `tune_stage2.csv`)

v_max = 26°/s, gia tốc 60°/s², làm trơn 13 mẫu (130 ms), E = 6°, V = 26°/s, tâm NS/PS = 0,5, trọng số đạo hàm trong bảng luật 0,5, vùng chết 0,03°/0,10°. Chọn từ 100 + 45 tổ hợp: nhanh gần nhất (chậm hơn tổ hợp nhanh nhất ~3 %) nhưng giữ tốc độ thật ≤ 30°/s cả ở mô hình xấu.

### 4.3 Chuỗi đề bài 60 → 150 → 30 → 90° (bộ mờ, mô hình danh định)

| Đoạn | t_xl 2 % | POT | Đỉnh tốc độ thật | Sai số đo cuối | Sai số thật cuối (MT6701 chưa / đã hiệu chuẩn) |
|---|---|---|---|---|---|
| 0 → 60° | 2,61 s | 0,000 % | 27,7°/s | 0,032° | 0,17° / 0,050° |
| 60 → 150° | 3,69 s | 0,001 % | 26,8°/s | 0,014° | 0,86° / 0,003° |
| 150 → 30° | 4,87 s | 0,000 % | 28,7°/s | 0,015° | 0,011° / 0,017° |
| 30 → 90° | 2,60 s | 0,000 % | 28,0°/s | 0,033° | 0,60° / 0,009° |

Thời gian xác lập gần giới hạn động học `Δθ/v_max + v_max/a`. Sai số đo cuối ≤ 0,035° (≈ 1,5 LSB MT6701, ~1 vi bước); sai số **thật** bị chặn bởi INL cảm biến nếu không hiệu chuẩn (0,86°), còn ≤ 0,05° sau hiệu chuẩn (`v5_calibration_demo`: 0,86° → 0,066° khi khớp từ dữ liệu mô phỏng). Nâng: sai số cuối ≤ 0,2° (vùng chết servo giả định).

### 4.4 So sánh, bền vững, lỗi (`results/v5_scenarios.csv`, 23 kịch bản, tất cả đạt)

| Kịch bản | Tổng t_xl | POT max | Đỉnh tốc độ | Ghi chú |
|---|---|---|---|---|
| Bộ mờ (danh định) | 13,76 s | 0,001 % | 28,7°/s | |
| P tuyến tính cùng giới hạn, cùng độ lợi nhỏ | 13,71 s | 0,17 % | 27,7°/s | sai số cuối 0,061° (mờ 0,033°) |
| Mờ, vận tốc đo từ MT6701 | 13,76 s | 0,001 % | 28,7°/s | |
| Không làm trơn lệnh | 13,51 s | 0,001 % | 29,2°/s | nhanh hơn, sát giới hạn tốc độ |
| J ×0,5 / ×1,5, ma sát ×2, dòng ×0,8, nhiễu ×3 | 13,76–13,77 s | ≤ 0,002 % | ≤ 29,0°/s | |
| Khe hở cứng 0,5°; đai mềm ×0,6 | 13,79 s | ≤ 0,006 % | ≤ 28,8°/s | |
| Kết hợp xấu nhất | 13,80 s | 0,000 % | 30,2°/s | vượt 0,6 % — cần đo giảm chấn thật |
| Mômen tải 0,1 N·m 0,3 s; mất 3 % xung; 1 mẫu cảm biến sai 45° | — | — | — | tự hồi phục, không lỗi |
| Mất 15 % xung / cảm biến đứng / kẹt trục | — | — | — | lỗi 4 (lệch bước) sau 0,45–1,3 s, ngừng STEP |
| Mất I2C | — | — | — | lỗi 32 sau 20–30 ms (3 mẫu) |
| Mất heartbeat | — | — | — | lỗi 1 sau 2 s |
| Bám mục tiêu 40 sin(2πt/20)° | — | — | 16°/s | sai số RMS 2,1° (bộ điều khiển điểm–điểm, chưa có feed‑forward) |

Hình: `v5_pdf_fuzzy.png`, `v5_pdf_linear.png`, `v5_compare_controllers.png`, `v5_faults.png`, `v5_robust_combined.png`, `v5_track.png`, `v5_fuzzy_surface.png`, `v5_calibration_demo.png`, `v5_simulink_model.png`, `v5_simulink_vs_script.png`, `v5_cad_in_matlab.png`; video CAD 48 s nén ×4: `v5_pdf_animation.mp4`.

### 4.5 Phát hiện thiết kế nhờ mô phỏng

1. **Khởi động STEP ở tần số rất thấp** giữ nửa chu kỳ dài (tới 65 ms) → anten đứng rồi giật, kích mode 11 Hz. Đã sửa bằng `stepgen_retime` (firmware nạp lại timer khi tốc độ tăng).
2. **Mode xoắn ~11 Hz** (quán tính anten 0,0077 kg·m² trên đai nối tiếp độ cứng từ của stepper) làm tốc độ thật vượt lệnh 4–7°/s nếu tăng tốc mạnh. Đã thêm làm trơn trung bình trượt 130 ms (≥ một chu kỳ) có bù quãng còn treo và giảm v_max xuống 26°/s.
3. **Ma sát và khe hở** quyết định sai số cuối và đỉnh tốc độ nhiều hơn hình dạng luật mờ: thu hẹp vùng chết dưới 0,03°/0,10° không giảm sai số mà gây "săn" quanh đích.

## 5. Giới hạn

- Chưa có số đo phần cứng: các tham số ghi "giả định" (detent, độ cứng/giảm chấn đai, khe hở răng, ma sát, động học servo) phải nhận dạng lại. Đỉnh tốc độ thực phụ thuộc mạnh vào giảm chấn mode 11 Hz và khe hở răng — đo bằng log MT6701 100 Hz khi dừng đột ngột.
- Sai số tuyệt đối của góc phương vị bị chặn bởi INL MT6701 (±1° điển hình) nếu không hiệu chuẩn.
- Mô hình Simulink dùng lưới 50 µs cho cạnh STEP và không có giám sát lỗi; mô hình chuẩn là `v5_simulate`.
