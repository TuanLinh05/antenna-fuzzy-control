# MATLAB/Simulink — Anten V3

**CAD hiện hành là [V5 gia cố với MT6701](../3D%20Print/Antenna_V5_Reinforced/README_START_HERE.md).** Các kết quả và viewer MATLAB ở đây vẫn dùng CAD/tham số V3. Ước lượng CAD V5 được lưu riêng trong `../3D Print/Antenna_V5_Reinforced/audit/simulation_parameters_v5.json`; chưa nhận dạng hoặc kiểm chứng bám góc phần cứng V5.

Đã chạy trên MATLAB R2026a Update 2 với Fuzzy Logic Toolbox và Simulink. Không có Simscape Multibody được cài. CAD thật được nạp qua tam giác và chuyển động bằng phép quay trong MATLAB; động lực học dùng phương trình phi tuyến rút gọn, không phải mô hình solid-body Simscape hay FEA.

## Mở và chạy

Trong MATLAB, chuyển Current Folder vào thư mục này, chạy `run_final_validation`. Lệnh kiểm tra FIS với C, mô phỏng danh định, tạo/chạy SLX, chạy các kịch bản và xuất ảnh/video. Có thể mất vài phút. File đã xuất sẵn ở results/.

`open_system('antenna_dc_fuzzy.slx')` mở sơ đồ; `view_antenna(35,60,true)` mở CAD với hai thanh trượt. `render_results` chỉ xuất lại ảnh/video từ kết quả đã chạy. `tune_dc` chạy lại 18 ứng viên nếu muốn thay thông số điều khiển; sau đó phải chạy lại kiểm chứng. Thư mục Simulation nằm cạnh Firmware và 3D Print. CAD được đọc từ ../3D Print/Antenna_TheGioiIC_v3/preview/mesh_data.json, bộ kiểm tra C từ ../Firmware/build/fuzzy_C_vectors.csv.

## 1. Nhánh DC đúng đề môn học

Ra=1 Ω, La=0,005 H, Kt=Kb=0,1, N=150, J=7,25 kg.m², B=3,125 N.m.s/rad, Tc=5 N.m, epsilon=0,001. Trạng thái [theta,omega,i]; đầu vào điện áp ±12 V. Góc đặt 60°,150°,30°,90°, đổi mỗi 12 s trong 48 s, trạng thái ban đầu bằng 0. Giới hạn |omega|≤30°/s, quá điều chỉnh ≤2% biên độ bước.

25 luật Sugeno tạo vận tốc; lớp giới hạn quãng dừng/gia tốc, bù mô hình và PI vận tốc tạo điện áp. Đây là cấu trúc mờ kết hợp PI, không phải chỉ một khối mờ xuất trực tiếp điện áp. Hãm sớm khi |omega|>0,50 rad/s thay đổi điện áp thực, không cắt trạng thái vận tốc. Bộ điều khiển lấy mẫu 10 ms, tích phân ode4/RK4 cố định 100 µs; kiểm tra lại ở 50 µs. Tiêu chí sai số xác lập danh định là max 1 s cuối mỗi bước ≤1e-5 rad, không gọi phép đo số hữu hạn là chứng minh bằng 0 tuyệt đối.

Simulink có khối Fuzzy Logic Controller thật, ZOH, Level-2 S-function điều khiển, State-Space DC và ma sát tanh. Đã đối chiếu với bộ tích phân MATLAB độc lập. Chọn ứng viên nhanh nhất trong 18 cấu hình đã thử, không chứng minh tối ưu thời gian toàn cục. Có baseline PD tuyến tính cùng lớp PI/bù để tham khảo, không khẳng định mờ luôn tốt hơn PID.

## 2. Nhánh stepper theo CAD V3

Trạng thái [theta_motor,omega_motor,theta_output,omega_output,elevation,omega_elevation,integral_servo]. Quán tính và mô-men trọng lực lấy từ CAD, đơn vị SI; phi tuyến mô-men stepper dạng sin, đai đàn hồi/cản/độ rơ, lượng tử STEP và encoder 600 P/R ×4, vòng điều khiển 100 Hz, PWM nâng 50 Hz. FIS và hệ số phương vị tương ứng lõi C của prototype. Mô hình xung là xấp xỉ theo bước tích phân, không phải HIL hay mô phỏng từng cạnh của vi điều khiển.

Thông số chưa đo: J rotor motor 5,4e-6 kg.m², mô-men chạy 0,12 N.m, đai k=20 N.m/rad,c=0,12 N.m.s/rad, độ rơ 2°, hiệu suất 0,8; ma sát phương vị 0,02 N.m. Servo là mô hình PI nội bộ giả định, không phải hàm truyền nhận dạng MG946R. Chỉ phương vị dùng phản hồi mờ bên ngoài; chưa có cảm biến góc nâng độc lập.

Các phép thử: vòng hở, thêm tải 0,02 N.m trong 0,5 s, mất 5% xung trong 0,5 s, quán tính 0,5–1,5 lần/độ rơ 3°, nhiễu encoder, chu kỳ 12 ms, encoder đứng, mất liên lạc, kẹt và nhả, va đập tải 0,08 N.m. Bài va đập được giữ như stress test với chỉ tiêu bám góc báo riêng; phát hiện lỗi không phải cơ cấu phanh. Không suy diễn đạt danh định thành giữ được 30°/s khi nhả kẹt/va đập.

## Kết quả và file

- results/comprehensive_validation.json: kết quả cuối và giới hạn stress test.
- results/dc_tuning.csv; dc_uncertainty.csv; prototype_scenarios.csv: từng cấu hình/kịch bản.
- results/simulink_validation.json: bước tích phân, so sánh MATLAB/Simulink.
- results/fuzzy_validation.json: so sánh FIS/lõi C (tên thực tế nếu khác xem các JSON trong results/).
- results/dc_assignment.png; prototype_tracking.png: đáp ứng.
- results/antenna_CAD_in_MATLAB.png; antenna_CAD.fig; antenna_simulation.mp4: CAD và hoạt cảnh 48 s mô phỏng, nén thành 12 s video.
- ../3D Print/Antenna_TheGioiIC_v3/audit/initial_simulation_findings.json: phát hiện ở lượt kiểm tra đầu, giữ để truy vết sửa ngưỡng hãm và tải stress.

Không có kiểm chứng trên chip, HIL, nhiệt, mạch chopper cuộn motor, FEA 3D hoặc RF. Đề DC N=150 và prototype stepper 4:1 là hai đối tượng khác nhau; phần thực nghiệm cần đúng phạm vi giảng viên cho phép. Nhận dạng bằng số đo thật rồi chạy lại trước khi kết luận định lượng về phần cứng.

Nguồn: [MathWorks sugfis](https://www.mathworks.com/help/fuzzy/sugfis.html), [Fuzzy Logic Controller](https://www.mathworks.com/help/fuzzy/fuzzylogiccontroller.html), [Level-2 MATLAB S-function](https://www.mathworks.com/help/simulink/sfg/writing-level-2-matlab-s-functions.html).

## Điều khiển board thật (chưa kiểm thử I/O)

Sau khi đấu dây/hiệu chỉnh theo tài liệu điện, chạy `serialportlist` để xem cổng, thêm `../Firmware/tools` vào MATLAB path rồi chạy `hardware_console("COM5")` với cổng đúng. Cửa sổ gửi heartbeat 0,4 s, chỉ đặt mốc Z/gửi góc khi bạn bấm nút. Đóng cửa sổ gửi S. Chưa thử kết nối thật; không chạy khi chưa xác nhận chiều encoder và nguồn. Firmware prototype dùng vmax=0,47 rad/s; nhánh DC giữ vmax=0,48 rad/s.

API: [MathWorks serialport](https://www.mathworks.com/help/matlab/ref/serialport.html).
