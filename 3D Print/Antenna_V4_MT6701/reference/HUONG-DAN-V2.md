# MT6701 v2 — chỉnh phần lỗ bo

Người dùng xác nhận: phần bắt motor v1 đã khớp; bốn lỗ bo hơi lệch.
v2 giữ nguyên tâm motor 31 × 31, rãnh motor 5,2 × 5,2, khung ngoài 42 × 42,
chân bắt motor dày 2,4 và mặt kê bo cao 3,2 mm. Chỉ phần giữ bo được chỉnh.

## Thay đổi
- Tâm lỗ bo danh nghĩa: 17,5 × 17,5, thay cho 18 × 18.
  Đây là giá trị lắp thử suy từ ảnh, chưa xác nhận bằng đo trực tiếp.
- Mỗi lỗ vít M2 thành rãnh rộng 2,3, dài 3,0 dọc đường chéo của góc tương ứng.
  Tâm vít chỉnh ±0,35 mm theo đường chéo (tổng hành trình 0,7 mm).
- Hốc ê-cu M2 dưới mỗi bệ cũng có độ trượt ±0,35 mm theo cùng hướng,
  giúp vít và ê-cu di chuyển cùng nhau. Nới mỗi lỗ vít đơn lẻ sẽ không đủ.
- Bệ bo tăng từ Ø7,2 lên Ø7,4 để giữ thịt quanh hốc ê-cu.
- Nóc hốc ê-cu dày 1,4; thành mỏng nhất danh nghĩa trên 0,8 mm, chưa tính sai số in.

## Các file
- duong-lo-bo-v2-1mm.stl: dưỡng nhỏ 25 × 25 × 1 mm, chỉ thử bốn lỗ bo.
- de-mt6701-v2-lo-bo-chinh.stl: đế chính v2.
- dem-v2-0p5-va-1mm.stl: 4 đệm 0,5 và 4 đệm 1 mm, dịch từng đệm theo vít khi căn.
- de-mt6701-v2-tham-so.scad: nguồn có thể chỉnh và xuất STL bằng OpenSCAD.
- ban-ve-v2-lo-bo-chinh.png: hình chiếu và chi tiết rãnh.

## Thứ tự thử
1. In dưỡng bo trước ở tỷ lệ 100%, thử luồn đủ bốn vít M2 khi bo nằm tự nhiên,
   không ép bo cong. Dưỡng chỉ kiểm tra vị trí lỗ, không dùng thay đế khi vận hành.
2. Nếu dưỡng khớp, in đế chính cùng hướng như v1: mặt đáy lớn trên bàn in,
   hốc ê-cu hướng xuống. Giữ tỷ lệ 100%; không scale toàn bộ để sửa riêng lỗ bo
   vì phần motor v1 đã khớp. Với FDM béc 0,4: có thể bắt đầu lớp 0,2, 6 vách,
   6 lớp trên/dưới, infill 100%. Chọn nhiệt độ và làm mát theo vật liệu thực tế.
3. Thử ê-cu M2 trong hốc dưới: phải nằm chìm và trượt được một chút theo rãnh.
   Nếu nhựa thừa làm kẹt thì làm sạch hốc; không ép ê-cu đội mặt tì.
4. Lắp sơ cả bốn vít giữ bo khi đế chưa gắn lên motor để dễ giữ và dịch ê-cu.
   Chưa siết một góc trước khi cả bốn vít đã vào ren. Căn bo rồi siết đều vừa tay.
5. Nếu dùng đệm, dịch từng đệm theo vị trí vít để không khóa mất độ chỉnh.
   Kiểm tra chân header/mối hàn không chạm bệ, nắp motor hoặc nam châm.
6. Gắn lại motor, thay từng ốc. Giữ đúng ren và đủ độ ăn ren của ốc motor.
   Đầu vít giữ bo không được lòi xuống chạm motor.
7. IC hướng vào nam châm; kiểm tra và căn lại tâm IC/khe hở trên bộ thực tế.
   Xác nhận vị trí lỗ vừa không đồng nghĩa tâm từ và khoảng hở đã được xác nhận.

## Nếu vẫn lệch
Không ép bo hay tăng tỷ lệ toàn bộ file. Cho biết hai lỗ nào luồn vít được trước,
hai lỗ còn lại lệch ra ngoài/vào trong hay ngang/dọc, kèm độ lệch xấp xỉ.
Trong SCAD có thể chỉnh pcb_pitch_x và pcb_pitch_y độc lập; giữ nguyên motor_pitch_x/y.
Tăng hành trình rãnh cần đồng thời kiểm tra lại thành hốc ê-cu và chỗ cho chân hàn.

## Phạm vi kiểm tra
Đã kiểm tra STL kín, hướng tam giác nhất quán, thể tích dương và số khối.
Đã kiểm tra hình học vít M2/ê-cu tại đầu và giữa hành trình rãnh, hành lang giữa
IC và nam châm để trống; vùng rãnh ốc, bệ bắt motor và vành ngoài giống v1.
Chưa in/lắp xác minh v2. Hình ảnh không được dùng làm số đo tuyệt đối.
