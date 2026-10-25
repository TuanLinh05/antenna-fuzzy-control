# Anten V5 - gia cố giá servo và gá MT6701 dễ thao tác

Ngày 25/10/2026. Đơn vị mm, in tỷ lệ 100%. V5 thay V4 theo hai ảnh người dùng gửi; giữ nguyên motor, servo, bộ truyền 4:1, nam châm và vị trí trục.

**Đã kiểm tra số về hình học, lắp ghép và đường thao tác theo các bao dụng cụ ghi trong báo cáo. Chưa in/lắp thử, chưa thử phá hủy hoặc chịu va đập.** Không suy diễn tăng độ cứng hình học thành bảo đảm chịu mọi lực mạnh.

**Cấu hình in theo xác nhận của người dùng: Bambu A1, đầu 0,4 mm, PETG.** Mở dự án trong `3MF_A1_PETG_0p4/`, bắt đầu từ bàn 00 để thử dung sai. Xem [hướng dẫn thông số, support và hiệu chuẩn](print_profiles/README_A1_PETG.md). Các file ở `3MF_plates/` vẫn là bản hình học trung tính; bộ cấu hình mới gồm sáu bàn với tổng số lượng giữ nguyên.

## Hai chi tiết đã sửa

### 1. Giá servo ở hình 1

Chi tiết mới: `STL/10_LD1501MG_reinforced_carrier.stl`.

- Tấm mặt tăng **4 lên 8 mm**, giữ nguyên mặt tì servo và vị trí trục.
- Hai dầm bên tăng **10 lên 16 mm**; thêm giằng nối trên và dưới dày **8 mm**, tạo khung hộp thay cho hai nhánh đứng riêng.
- Mép ngoài/cửa servo được bo góc. Đường tránh adapter đĩa tròn nằm trong dầm, không cắt mất tai bắt servo.
- Bỏ các khoét hở lớn quanh đầu vít M4. Thay bằng **đường đưa đầu vít rộng 8,2 mm**, có khoảng chỉnh cao và đưa vít từ mặt ngoài tới chỗ tì đầu vít ở x=-107 mm.
- Vẫn dùng bốn M4x20 bắt giá vào càng. Dùng chìa lục giác M4 loại đủ dài, thanh khóa khoảng 3 mm; đường cho đầu vít Ø7,5 mm và thanh khóa Ø3,6 mm đã được kiểm tra ở ba vị trí chỉnh cao.
- **Bốn vít tai servo đổi từ M3x12 sang M3x16** do mặt gá dày thêm 4 mm. Đệm tai 0,5 mm và vị trí servo được giữ.

STL 10 đã đặt mặt lưng lớn xuống bàn in. Xem `preview/servo_before_inside_V4.png` và `preview/servo_reinforced_inside_V5.png` để so sánh phía dầm; hai ảnh `servo_before_V4.png` / `servo_reinforced_V5.png` cho phía tấm mặt. Không dùng vị trí và chiều dài vít M3 tai servo của V4 cho V5.

### 2. Gá cảm biến ở hình 2

Hình 2 ở V4 là cầu cố định bắt vào đáy, PCB nằm trên khay ở giữa và nam châm nằm trên trục quay. Cơ cấu đó **không đỡ tải chảo**: hai bi 608 đỡ trục anten; gá chỉ giữ cảm biến đứng yên. Tuy nhiên, hai tấm lớn và bốn trụ ở V4 che khuất bo, khó đưa tay vào và khó in.

V5 đổi thành:

- `STL/22_MT6701_open_U_bridge.stl`: **khung chữ U mở phía trước**, có cửa bên/lưng, mặt bắt đáy dày 7 mm và khung dưới dày 6 mm. Đã chừa phần đầu bốn vít M4 của đế nhô xuống 0,8 mm; không ép khung vào đầu vít.
- `STL/24_MT6701_3point_carrier.stl`: khay PCB chỉnh bằng **ba điểm**, không phải bốn điểm. Ba trụ M3x25 ở (-18,18), (18,18), (0,-18) mm, mỗi trụ hai ê-cu M3 để đỡ và khóa mặt phẳng bo.
- PCB vẫn bắt bằng bốn M2x8 vào ê-cu M2 trượt; lỗ phù hợp các pitch thử 17,5/18/19 mm. Khay chỉnh XY ±1,5 mm; mức Z làm việc giữ như V4.
- Giữ nam châm Ø4 x2 mm, đầu kẹp trục 25 và khe nam châm–mặt IC danh định 1 mm. Căn theo IC thực, đo khe 0,5–2 mm theo chiều cao linh kiện thật.

Xem `preview/MT6701_open_front.png`, `preview/MT6701_tray_removed.png` và `preview/MT6701_dimensions.png`.

## Thứ tự lắp và chỉnh MT6701

1. In dưỡng 26, thử bốn lỗ PCB và vít M2. Thử hốc nam châm bằng dưỡng 27. Dữ liệu PCB 23 x23 mm, lỗ khoảng 2 mm là số người dùng cung cấp, chưa phải bản vẽ dung sai của nhà sản xuất.
2. Lắp PCB lên **khay rời**, khi khay còn ở ngoài khung; lúc này dễ giữ ê-cu M2 và siết vít. Không cố siết M2 qua khoảng hẹp dưới nam châm khi bo đã nằm trong cụm.
3. Gắn khung U vào đáy bằng bốn M3x16 và ê-cu M3. Dẫn dây cố định ra bên hông, để một đoạn chùng khoảng 70 mm cho việc kéo khay ra bảo trì; không để dây chạm đầu kẹp trục quay.
4. Dùng ba M3x25 từ dưới khung lên làm trụ. Ê-cu dưới đỡ khay, ê-cu trên khóa khay. Đặt ba điểm cùng mức, rồi chỉnh từng điểm để bo phẳng và IC đồng tâm nam châm.
5. Hàn dây mềm hoặc dùng đầu cắm thấp/vuông góc hướng dây ra bên hông. Bao đầu cắm phía IC cao tối đa 3 mm; chân hàn dưới bo không quá 1,5 mm. Chưa kiểm tra đầu pin đứng dài của mọi loại module.
6. Đọc góc khi quay tay, xác nhận chiều, wrap 0/360° và tín hiệu ở các góc chuẩn. Sau khi khóa ê-cu, đo lại khe và độ lặp lại. Nam châm Ø4 x2 mm cần thử từ trường/độ chính xác thực; khe đúng chưa đủ kết luận.

### Tháo bo để sửa

1. Ngắt nguồn chuyển động, đỡ khay bằng tay và giữ dây chùng. Kê cụm chắc chắn để có **ít nhất 30 mm khoảng trống dưới đầu ba vít M3x25** khi rút vít xuống; chân đế hiện chỉ chừa khoảng 10 mm, không đủ rút hết vít khi đặt trực tiếp trên bàn.
2. Tháo ba vít M3x25 cùng các cặp ê-cu của chúng. Không tháo trục anten hoặc đầu giữ nam châm.
3. Hạ khay khoảng **3 mm** rồi trượt ra **phía trước, hướng Y âm**. Đường hạ và trượt đã được kiểm tra bằng hình học với PCB, đầu cắm và vít M2 còn trên khay.
4. Thay/sửa bo ngoài khung. Khi lắp lại phải căn tâm IC, chỉnh mặt phẳng/khe và kiểm tra mốc góc lại.

Các kiểm tra đường thao tác dùng bao chìa lục giác và cờ lê mỏng 5,5 mm dày khoảng 1,6 mm. Kiểm tra dụng cụ thật hoặc dùng kìm nhỏ phù hợp; không coi bao dụng cụ là chứng nhận mọi bộ dụng cụ đều vào được.

## In và file thay thế

- `STL/`: chi tiết in riêng. `STEP/`: nguồn hình học và cả cụm. `3MF_A1_PETG_0p4/`: sáu dự án có preset A1/PETG và thiết lập từng chi tiết. `3MF_plates/`: năm bàn hình học trung tính để đối chiếu.
- Ba chi tiết cơ khí thay đổi là **10, 22, 24**. Nếu đã in V4, các phần còn lại giữ nguyên kích thước; dùng BOM V5 để đổi vít tai servo và giảm một trụ chỉnh khay.
- STL 22 được xoay **mặt lưng xuống bàn**, để in khung U theo hướng mở dần ra trước. Không tự dựng lại theo ảnh cụm lắp. Kiểm tra preview lớp, support và brim trong slicer.
- Preset PETG mới dùng lớp thường 0,16 mm, 8 vách cho 10/22 và 45% gyroid; chảo 0,12 mm, các đệm mỏng 0,10 mm. Các đề xuất in chung trước đó được thay bằng bộ thông số chi tiết trong `print_profiles/`. Tăng số vách và hướng lớp là phần cần quan tâm khi gia cố; không chỉ tăng infill. [Prusa: Layers and perimeters](https://help.prusa3d.com/article/layers-and-perimeters_1748).
- Có thể dùng vùng modifier đặc hơn quanh vít/giằng. Không siết vít đến ép nứt lớp hoặc làm cong PCB. Dưỡng 20/26/27/28/30 vẫn nên in trước khi in toàn bộ.

## Những phần giữ nguyên

- 17HS1352-P4130, TB6600 cấp 12 V, LD-1501MG cấp khoảng 7 V, STM32F103.
- GT2 20T/80T, đai kín 280 mm rộng 6 mm; tâm 87,9173 mm và motor trượt ±5 mm.
- Trục phương vị Ø8, nam châm quay cùng trục, MT6701 đứng yên. Chân đế 55 mm.
- Đường kính trục motor vẫn chưa được đo: CAD dùng Ø5 mm theo bảng kích thước, phần mô tả bán hàng ghi 4,5 mm. Xác nhận trước khi chọn pulley; không ép lắp sai lỗ.
- Trục nâng dùng vòng vị trí trong servo, chưa có cảm biến nâng ngoài. Firmware cũ đọc encoder AB vẫn cần port MT6701; báo cáo mô phỏng V3 không chứng minh chất lượng điều khiển V5.

## Kiểm tra và giới hạn

`BAO_CAO_KIEM_TRA_V5.md` và `audit/` chứa kết quả giao khối, vít, rãnh chỉnh, đường thao tác, tải và so sánh tiết diện V4/V5. Kiểm tra độ cứng là mô hình dầm rút gọn với lực tĩnh minh họa 20 N; chưa có FEA liên kết, vật liệu in thực, bền lớp, va đập hoặc thử tải phá hủy.

Không gọi một hệ số tăng độ cứng tính toán là hệ số tăng tải phá hủy. Phép so sánh giả định gốc gá được giữ cứng, chưa xét lật cả cụm. Khi thử lực, cố định đế hoặc thử riêng chi tiết trong gá giữ; kiểm tra mối bắt vít, nứt lớp và biến dạng theo tải tăng dần trước khi dùng lực lớn.

## Tái tạo

```text
python build_model.py
python validate_assembly.py
python validate_fasteners.py
python audit_m4.py
python validate_interfaces.py
python validate_loads.py
python validate_reinforcement_access.py
python make_preview.py
python make_dimension_views.py
python finalize_v5.py
```

Các validator đọc hình học có thể chạy đồng thời sau build; `audit_m4.py` chạy sau kiểm tra vít. Runtime CadQuery/trimesh ưu tiên `D:/HK261/NMDKTM/tmp/cad_runtime`; máy khác cần cài các thư viện tương ứng. `reference/` chỉ chứa hình học V4 để so sánh, không in các file tham chiếu đó.
