# Báo cáo kiểm tra V4 - 25/10/2026

**Kết luận: đạt kiểm tra hình học số sau các lần sửa; khả thi theo ước lượng tải/nguồn đã nêu; chưa nghiệm thu phần cứng hoặc chất lượng bám góc.**

## Hình học và bộ file

- 29 loại STL, 43 vật in kể cả dưỡng; năm bàn A1, đơn vị mm. Mesh kín, một khối, hướng mặt nhất quán, thể tích dương. Kiểm tra lại 3MF độc lập đúng số lượng, trong 256 mm và thể tích khớp STL. Chưa slice support/brim/G-code.
- 14,795 kiểm tra giao khối cụm và 191,008 kiểm tra vít/ê-cu không còn lỗi ở các góc lấy mẫu. Góc nâng 0–180° và phương vị 0–360° được lấy mẫu để kiểm tra hình học; không suy ra hành trình vận hành có dây hoặc an toàn servo đủ 180°.
- Kiểm tra riêng M4x20 đọc từ STEP và chiều dài vít; các giao diện motor/servo/bo được kiểm tra độc lập ở biên rãnh chỉnh. Không dùng kiểm tra hữu hạn làm chứng minh mọi va chạm liên tục.

## Bộ truyền

- Đã đếm trên solid xuất ra đủ 80 rãnh rotor, ghép pulley thương mại 20T: **4:1**.
- Đai đường bước 280.000000 mm, tâm 87.917296 mm; góc ôm bánh nhỏ 154.907°, tương ứng 8.606 răng.
- Motor trượt ±5 mm; kiểm tra thân, boss và bốn vít ở ba vị trí. Chất lượng răng in, độ căng và không trượt răng vẫn phải kiểm tra với đai thật.
- 1/16: độ chia lệnh 0.028125°; cần 1066.67 Hz để đặt 30°/s, motor 20 rpm. Không gọi đây là độ chính xác định hướng.

## MT6701 và động cơ

- PCB 23x23 mm, lỗ người dùng khoảng 2 mm; pitch suy ra 18 mm. Vít và ê-cu trượt đã kiểm tra ở pitch 17,5 /18 /19 mm. Carrier chỉnh XY ±1,5 mm và Z tổng 1,5 mm.
- Hốc nam châm Ø4,2 x2,2 mm cho nam châm Ø4 x2 mm; mặt nam châm cần lắp ngang miệng hốc. Khe mặt nam châm–mặt IC danh định 1 mm, chỉnh 0,5–2 mm theo chiều cao giả định.
- PCB dày 1,6 mm, IC cao 1,7 mm và vị trí header là giả định. Hàn dây mềm hoặc dùng header thấp/vuông góc hướng dây ra bên hông; không để pin đứng cao hơn bao 3 mm chĩa vào đầu giữ nam châm. Căn tâm IC thực và đo khe sau khi lắp. Không xác nhận từ trường/độ chính xác chỉ từ khe đúng; nam châm nhỏ hơn loại tham chiếu datasheet.
- Motor dựng thân 34 mm, trục nhô 20 mm, Ø5 mm. Thông tin bán hàng còn ghi 4,5 mm; chưa có motor nên chưa xác nhận lỗ pulley. Dưỡng 28/30 dành cho bước này.
- Servo LD-1501MG dùng đĩa tròn người dùng có. Cửa thân 21,6 mm; lỗ tai kiểm tra pitch dài 45–50 mm và ngang 8–12 mm. Rãnh adapter đĩa kiểm tra vít/ê-cu M2 ở bán kính 6,5–10,5 mm. Dưỡng 20 và căn đồng trục vẫn cần thực hiện.

## Tải và nguồn

Khối lượng tính theo chi tiết in đặc PLA và các khối lượng linh kiện ghi rõ nguồn/giả định: **1.832 kg**. J phương vị lớn nhất 0.0056565 kg.m², J nâng 0.0002167 kg.m².

- Với gia tốc phương vị 30°/s², tốc độ 30°/s, ma sát Coulomb giả định 0,02 N.m và cản nhớt 0,01 N.m.s/rad: cần khoảng 0.02820 N.m ở trục ra. Để có dự trữ 3 lần theo phép tính này, motor cần mô-men chạy ít nhất **0.02644 N.m** với bộ truyền hiệu suất giả định 0,8; chưa gồm hiệu ứng quá độ rotor/đai chưa nhận dạng.
- Nếu tạm giả định motor giữ được 0,05 N.m khi chạy, dự trữ tải tính ra 5.67 lần. **0,05 N.m là giả định thiết kế, không phải đặc tuyến đã đo hoặc lấy trực tiếp từ mô-men giữ 0,25 N.m.**
- Tải nâng ước lượng 0.01831 N.m; dùng 20% mô-men kẹt hãng công bố ở 6 V làm mức lập kế hoạch cho ra dự trữ 13.92 lần. Điều này không chứng nhận mô-men liên tục, nhiệt hay sai số servo ở 7 V.
- Biên trọng tâm bảo thủ khi thay lượng nhựa in 35–100% khoảng 20.76 mm trong đa giác chân. Chưa xét gió, kéo dây hoặc va đập. Không có FEA/chứng nhận bền lớp in.
- Ngân sách nguồn giả định: servo 7 V x3 A qua buck hiệu suất 85%, stepper/driver 15 W và logic 2 W, tổng khoảng 41.7 W / 3.48 A ở 12 V, dưới 60 W danh định. **Chưa đo dòng, sụt áp, nhiệt hoặc quá độ; nhãn 5 A của nguồn/buck chưa thay phép đo.**

## Phạm vi bài toán điều khiển

Phần cứng chọn phù hợp cấu trúc một vòng mờ phương vị với MT6701 đo trục anten. Nâng dùng vòng vị trí nội bộ của servo và hiệu chuẩn bằng chuẩn ngoài. Chưa có căn cứ gọi cả hai trục là điều khiển mờ.

Firmware cũ đọc encoder AB/2400 count, chưa tích hợp MT6701. Cần sửa lớp đọc góc, wrap/offset, kiểm tra mất dữ liệu và ramp servo trước khi thử V4. Báo cáo mô phỏng V3 cũ không được dùng làm kết quả bám góc V4. Các chỉ tiêu vọt lố ≤2%, sai số ≤0,5° và giới hạn tốc độ thực chỉ có thể nghiệm thu sau nhận dạng/tinh chỉnh và chạy test thật.

## Các bước vật lý còn lại

1. In dưỡng 20/26/27/28/30 trước; xác nhận trục motor, tai servo, đĩa tròn và lỗ bo.
2. Kiểm tra răng/đai, mặt D, vòng bi và pulley đồng phẳng; siết đai vừa, không ép bi.
3. Gắn nam châm, căn tâm IC và khe thực; quay tay kiểm tra góc đủ vòng, đo tại chuẩn góc và khi cấp điện motor.
4. Kiểm tra mức logic, dòng TB6600, nguồn 7 V servo và 12 V khi chạy đồng thời.
5. Port firmware MT6701; thử từ 5–10°/s, chấm sai số và vọt lố bằng test case, rồi tăng tốc nếu đạt.

Xem README_START_HERE.md để lắp và tái tạo. Các JSON kiểm tra nằm trong audit/ và các file *_validation.json.
