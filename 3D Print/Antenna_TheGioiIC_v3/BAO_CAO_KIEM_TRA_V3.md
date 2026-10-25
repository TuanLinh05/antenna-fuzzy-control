# Báo cáo kiểm tra anten V3 — 24/10/2026

Đã hoàn thành rà soát thiết kế, nguồn hàng, phần điện/lõi điều khiển và mô phỏng MATLAB/Simulink. **Kết luận: đạt các kiểm tra số trong phạm vi giả thiết; còn giới hạn khi va đập/nhả kẹt và chưa nghiệm thu phần cứng.** Không gọi đây là bảo đảm lắp hoàn hảo hoặc độ chính xác đã đo.

## 1. Các vấn đề đã sửa so với V2

- Bổ sung encoder ở **trục ra**, gá encoder và khớp 6–8 mm. Phương vị có phản hồi góc thật thay cho chỉ đếm lệnh stepper.
- Tạo mối truyền mô-men bằng mặt D trên rotor, giá chảo và adapter; chỉ định vùng giũa trục, giữ vùng chạy trong bi tròn nguyên.
- Trục đứng tăng thành 120 mm, chân cao 90 mm để đủ khoảng trống cho encoder và đầu M4; tổng cắt vẫn vừa một thanh 200 mm.
- Gá servo chỉnh cao ±2,5 mm, tai ±3 mm. Tăng phần nhựa quanh khe: mép dưới 5,3 mm, trên 6,3 mm, bên 2,8 mm. Dùng tay tròn đi kèm thay vì in spline không rõ kích thước.
- Cập nhật vít, nguồn, driver, chuyển mức 3,3/5 V, firmware STM32F103 và các tài liệu; MG946R là mã servo đang có hàng đã chọn theo cửa hàng.

## 2. Kiểm tra cơ khí và bộ in

22 loại STL, 36 vật in, 5 bàn A1. Mesh kín, một thành phần, chiều mặt nhất quán, thể tích dương. Kiểm tra 3MF độc lập đủ số lượng, footprint không chồng và nằm trong 256 mm; **chưa slice support/brim**.

12.040 phép kiểm tra giao khối cụm và 142.990 phép kiểm tra vít/đai ốc tại góc lấy mẫu không phát hiện giao khối ngoài các mối lắp chủ ý. Phương vị lấy mẫu 0–360°, nâng 0–180°. Có kiểm tra thêm biên hình học liên tục cho các cặp chảo–dầm/càng và các khoảng cao rotor–motor. Không gọi lấy mẫu là chứng minh mọi va chạm liên tục.

20 M4×20 đi qua 36 lỗ tròn Ø4,4 và 4 khe 4,4×9,4; ăn ren danh định tối thiểu 3,2 mm. Vẫn cần M3/M2 ở động cơ, chảo, encoder. Đọc đúng bảng vít và thứ tự lắp trong hướng dẫn.

Đai đúng đường bước 280,000 mm; tâm 87,9173 mm, góc ôm pulley nhỏ 154,91° tương đương 8,61 răng. Độ chia lệnh 1/16 là 0,028125° tại anten; encoder 600 P/R ×4 chia 0,15°. **Độ chia không phải độ chính xác định hướng thực tế.**

Tính tải theo CAD: khối lượng giả thiết in đặc tổng 2.202 kg; J phương vị lớn nhất 0.005903 kg.m². Mô-men yêu cầu 0.0231 N.m phương vị, 0.0183 N.m nâng. Hệ số dự trữ tương ứng 16.63 và 9.64, dựa trên mô-men chạy stepper giả thiết 0,12 N.m và chỉ dùng 20% mô-men kẹt servo tại 4,8 V. Biên trọng tâm bảo thủ khi thay khối lượng chi tiết in 35–100% là 24.3 mm trong đa giác chân. Đây là ước lượng, không phải chứng nhận vật liệu/FEA/thử tải.

## 3. BOM chỉ Thế Giới IC

Đã mở trang sản phẩm và đối chiếu mã, tồn kho, số mua tối thiểu/bội số cho **35 mã** ngày 2026-10-24. Số tồn đều đủ lượng mua đề xuất tại thời điểm kiểm tra. Tổng **1,226,517 VND**: cơ khí 814,280, điện 412,237; chưa gồm in, vận chuyển và board STM32 đang có. Danh sách mua đã có dự phòng/đơn tối thiểu. Nếu đã có M4×20 đúng loại có thể bỏ dòng mua M4.

Motor IC5255 chỉ còn **1 chiếc** tại thời điểm kiểm tra; tồn kho có thể đổi và chưa được giữ hàng. BOM đầy đủ có URL từng sản phẩm, gồm nguồn 12 V/5 A, buck 5 V/5 A, TB6600, encoder, chuyển mức và dây; không yêu cầu mua ngoài cửa hàng. Dụng cụ cưa/giũa/thước cặp/mỏ hàn và vật tư in là điều kiện gia công, không nằm trong giá BOM.

## 4. STM32 và logic mờ

F103C8 đủ bộ nhớ cho bản firmware đã biên dịch (khoảng 5,2 KB Flash, 2,5 KB RAM kể cả 2 KB stack). Lõi C cũng biên dịch cho Cortex-M4; bản tích hợp ngoại vi hiện dành F103, không tự coi là firmware F4 dùng được nguyên trạng.

25 luật Sugeno, 5 tập tam giác cho mỗi đầu vào. Kiểm tra C trên 40.401 điểm; đối chiếu FIS MATLAB trên 1.681 điểm, sai lệch float tối đa khoảng 1e-7. TIM2 encoder, TIM3 STEP phần cứng, TIM4 PWM servo, vòng 100 Hz, UART và watchdog. Chỉ phương vị có điều khiển mờ bên ngoài; nâng dùng điều khiển vị trí nội bộ của servo. Prototype dùng vận tốc yêu cầu tối đa 0,47 rad/s để chừa dự trữ cho sai lệch quán tính/độ rơ; thông số này đồng bộ giữa C và MATLAB. Có hardware_console gửi heartbeat 0,4 s nhưng chưa thử UART thật.

Đã biên dịch và kiểm thử trên máy tính; **chưa nạp/đo thời gian trên chip, chưa đo nguồn hay xung thật**. Phải xác nhận chiều phản hồi, dòng driver, mức điện áp và servo trung tính trước khi đóng vòng. Xem ../../Firmware/DIEN_VA_DIEU_KHIEN.md.

## 5. Kết quả MATLAB/Simulink

Đã chạy MATLAB R2026a Update 2, Fuzzy Logic Toolbox và Simulink. Máy không có Simscape Multibody; CAD thật nạp vào MATLAB bằng tam giác và biến đổi tọa độ, động lực là mô hình phi tuyến rút gọn.

### Nhánh DC của đề môn học

Giữ đúng N=150, J=7,25 kg.m², B=3,125 N.m.s/rad và giới hạn ±12 V. Mô hình này **khác** prototype stepper 4:1. Sugeno tạo vận tốc, PI/bù tạo điện áp; không đổi tên mô hình stepper thành DC.

| Thời điểm (s) | Góc đặt | Quá điều chỉnh | Xác lập 2% (s) | Max sai số 1 s cuối (rad) |
|---:|---:|---:|---:|---:|
| 0 | 60° | 0.000% | 2.3119 | 2.17e-06 |
| 12 | 150° | 0.000% | 3.3579 | 2.47e-06 |
| 24 | 30° | 0.000% | 4.4134 | 2.76e-06 |
| 36 | 90° | 0.000% | 2.3119 | 2.16e-06 |

Đỉnh tốc độ 28.542°/s <30; điện áp 8.411 V <12; quá điều chỉnh ≤2%. Kiểm tra 12 tổ hợp sai lệch thông số ngẫu nhiên có seed, nhiễu tải 2 N.m và giảm bước từ 100 xuống 50 µs đều đạt các tiêu chí đã định. Bộ tích phân MATLAB độc lập khớp Simulink tới sai số số học trong trường hợp danh định. Chọn nhanh nhất trong 18 ứng viên thử, không chứng minh tối ưu toàn cục.

### Nhánh stepper theo CAD

Đã xét động cơ phi tuyến, đàn hồi/độ rơ đai, lượng tử xung/encoder, quán tính phụ thuộc góc nâng và servo giả định. Danh định: quá điều chỉnh 0.394%, sai số cuối lớn nhất 0.0125°, tốc độ đỉnh 27.719°/s. Có kiểm tra mất xung, tải thêm 0,02 N.m, quán tính 0,5–1,5 lần, độ rơ 3°, nhiễu encoder, chu kỳ 12 ms và tinh chỉnh bước tích phân.

**Giới hạn được phát hiện:** va đập tải 0,08 N.m làm đỉnh tốc độ 45.88°/s, vượt 30°/s; nhả kẹt cũng có bật đàn hồi. Phát hiện encoder đứng/mất liên lạc/kẹt đạt thời gian đặt trong bài kiểm tra, nhưng không đồng nghĩa phanh cơ khí hoặc giữ được góc khi lỗi. Những ca này vẫn được lưu với cột tracking_requirements_met=false. Không ghi tất cả stress test là đạt bám góc.

Động học servo, mô-men chạy, độ cứng/cản/độ rơ đai và quán tính rotor motor chưa được đo; cần nhận dạng lại trên phần cứng. Không có HIL, mô phỏng nhiệt/chopper cuộn dây, FEA hoặc RF.

## 6. Điều kiện nghiệm thu thực tế còn lại

1. Đo linh kiện nhận được, in 4 mẫu thử và kiểm tra tay servo/adapter/vòng chặn trước toàn bộ bộ in.
2. Cắt/giũa D theo bản hướng dẫn, căn bi và hai khớp đồng trục; quay tay không kẹt, encoder không đỡ tải.
3. Kiểm tra 5 V lúc tải servo, nhiệt driver/nguồn, xung và chiều encoder/motor; hiệu chỉnh mốc tay bằng Z.
4. Thử từ góc nhỏ, đo sai số và nhận dạng lại mô hình; chỉ mở rộng hành trình/tốc độ khi dữ liệu thực đạt. Cơ cấu hiện dành thử nghiệm tải nhẹ trong nhà, chưa được phê duyệt cho va đập/kẹt, kéo dây hoặc tải ngoài trời.

File chi tiết: audit/STAGE_GATES.json, assembly_validation.json, fastener_validation.json, m4_audit.json, audit/load_validation.json, audit/transmission_validation.json, audit/electrical_validation.json, audit/firmware_build_validation.json, ../../Simulation/results/comprehensive_validation.json và các CSV/MAT/ảnh/video đi kèm.
