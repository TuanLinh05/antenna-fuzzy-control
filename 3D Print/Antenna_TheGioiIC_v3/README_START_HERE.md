# Anten hai trục — V3

Đọc [Báo cáo kiểm tra](BAO_CAO_KIEM_TRA_V3.md) trước. Bộ file đã được kiểm tra số và mô phỏng, **chưa in/lắp thử phần cứng**, có giới hạn khi va đập và nhả kẹt.

1. [Danh sách mua Thế Giới IC](DANH_SACH_MUA_THEGIOIIC.md): 35 mã, tồn kho ngày 24/10/2026, tổng 1.226.517 VND chưa gồm STM32 đang có, in và giao hàng. Motor chỉ còn 1 khi kiểm tra; chưa giữ hàng.
2. [In và lắp](HUONG_DAN_LAP_RAP.md), [vít M4](KIEM_TRA_OC_M4.md): in mẫu 16/17/20/23 trước, dùng 5 file Plate_*.3mf trong 3MF_plates/. Không in cả cụm STEP. 3MF chưa có support/profile/G-code.
3. [Phần điện và vận hành](../../Firmware/DIEN_VA_DIEU_KHIEN.md), [firmware](../../Firmware/README.md): F103 là bản ngoại vi đã build, F4 cần port riêng.
4. [MATLAB/Simulink](../../Simulation/README.md): chạy run_final_validation từ thư mục Simulation. Kết quả, SLX, FIS, ảnh và video đã có sẵn.

Xem offline bằng [trình xem 3D](XEM_MO_HINH_3D.html). 22 loại STL, 36 vật in kể cả 4 mẫu, 5 bàn A1. Bản CAD tham số ở build_model.py; STEP xuất tại tọa độ lắp, STL đã đặt hướng in.

Nhánh DC N=150 đúng đối tượng đề bài được báo cáo riêng với prototype stepper 4:1. Chỉ phương vị dùng điều khiển mờ phản hồi encoder bên ngoài. Các phép đo linh kiện, dung sai in, nguồn/xung và nhận dạng thực tế vẫn cần hoàn thành trước nghiệm thu phần cứng.
