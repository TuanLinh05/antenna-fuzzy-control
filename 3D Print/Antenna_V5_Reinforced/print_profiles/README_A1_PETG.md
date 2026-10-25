# Cấu hình in V5 — Bambu A1, đầu 0,4 mm, PETG

Mở các file trong **3MF_A1_PETG_0p4/** bằng **Open Project / Mở dự án** trong Bambu Studio. Không chỉ nhập hình học, vì cách đó bỏ thiết lập nhúng. Năm file ở `3MF_plates/` là bản hình học trung tính để đối chiếu.

Cấu hình ưu tiên bề mặt và các vách chịu lực, chấp nhận thời gian in dài. Chưa có bản in đo kiểm, nên không cam kết đây là một bộ thông số tối ưu tuyệt đối cho mọi hãng PETG hoặc bảo đảm dung sai cụ thể.

## Thiết lập đã nhúng

| Hạng mục | Giá trị |
|---|---|
| Máy / đầu phun | Bambu Lab A1 / 0,4 mm, flow Standard |
| Vật liệu | PETG thường; preset riêng dựa trên Generic PETG A1 của Bambu |
| Mặt bàn | Textured PEI Plate |
| Nozzle / bàn | 255°C / 80°C ở lớp đầu và các lớp sau |
| Lưu lượng thể tích tối đa | 8 mm³/s |
| Flow ratio khởi đầu | 0,95; chưa hiệu chuẩn theo cuộn thật |
| Lớp thường / đầu | 0,16 / 0,20 mm |
| Chảo 12 | 0,12 mm; 4 vách; 20% gyroid |
| Vách chi tiết chịu lực | 8 vách, gồm gá 10, khung 22, càng, tháp bi, đế và chân |
| Vách các chi tiết khác | 6 vách, trừ chảo |
| Infill chịu lực | 45% gyroid |
| Adapter 11, vòng kẹp 18, khay 24, đầu nam châm 25 | 100% infill; kích thước nhỏ |
| Top / bottom toàn cục | 8 lớp và chiều dày tối thiểu 1,28 mm |
| Vách ngoài / trong | 35 / 60 mm/s |
| Mặt trên / bridge | 30 / 20 mm/s |
| Infill / lớp đầu | 80 / 20 mm/s |
| Gia tốc thường / ngoài | 1500 / 800 mm/s² |
| Bề mặt | Monotonic; precise outer wall; ironing tắt |
| Chiều cao chính xác | Precise Z height bật; các vòng đệm mỏng dùng lớp 0,10 mm |
| Bù lỗ / biên XY | 0 / 0 mm; scale 100%, shrink 100% |
| Elephant foot compensation | 0,15 mm |
| Brim | Outer only 4 mm; chảo 5 mm; vòng đệm nhỏ 2 mm; khe brim 0,15 mm |
| Quạt thường | 30–50%; ba lớp đầu tắt; overhang tối đa 80% |

Nhiệt độ và flow là điểm bắt đầu cho PETG thường, không dành cho PETG-CF hoặc mặc định coi PETG-HF giống PETG thường. Nếu nhãn cuộn yêu cầu nhiệt độ khác, chọn theo cuộn và slice lại. Nhựa cần được làm khô theo hướng dẫn của hãng để hạn chế rỗ, sợi và giảm bám lớp. Hiệu chuẩn flow ratio/flow dynamics theo cuộn trước khi đánh giá dung sai.

## Support theo từng chi tiết

- Support tự động được bật cho **01, 03, 04, 12, 15, 22 và 25**. Các chi tiết còn lại giữ hướng STL đã chọn và tắt support để tránh nhựa đỡ kẹt trong các lỗ/rãnh nhỏ. Bridge ngắn được giữ cho máy tự bắc cầu.
- Các chi tiết cơ khí dùng **Normal Auto / Snug**, cho phép bắt đầu trên bề mặt chi tiết để đỡ được các bậc phía trong. Chảo dùng **Tree Auto / Hybrid**, chỉ từ bàn, giữ lòng chảo hướng lên để support nằm phía lưng.
- Cùng một loại PETG làm model và support: **Top/Bottom Z distance 0,24 mm**, XY distance 0,35 mm; ba lớp interface trên, hai lớp dưới; spacing mặt tiếp xúc trên 0,25 mm; interface 25 mm/s.
- Không đặt Z distance về 0 khi vẫn dùng cùng PETG. Không giả định có AMS hoặc cuộn vật liệu support riêng. Khoảng hở đang chọn cần thử thực tế để cân bằng tháo support và độ nhẵn mặt dưới.
- Giá servo 10 giữ tấm mặt lớn xuống bàn; khung U 22 giữ mặt lưng xuống bàn; giữ hướng này khi mở dự án. Support trong cửa khung 22 có đường lấy ra qua các cửa. Kiểm tra và làm sạch phần support dưới bàn rotor 04, trong hốc đế 01 và quanh đầu giữ nam châm 25 trước khi lắp.

## In dưỡng trước để chốt dung sai

**Plate_00_CALIBRATION_FIRST** gồm toàn bộ các dưỡng 16/17/20/23/26/27/28/30 và bốn đệm tai servo 29. Các chi tiết này đã được chuyển khỏi bàn 04/05, không nhân đôi tổng số lượng của bộ V5.

1. In bàn 00 bằng đúng cuộn PETG sẽ dùng cho phần còn lại. Chờ nguội rồi bóc brim và làm sạch sợi trước khi đo; không đo khi chi tiết còn nóng.
2. Dưỡng 16 có ổ bi Ø22,0 /22,2 /22,4 mm; dưỡng 17 có Ø8,0 /8,2 /8,4 mm. Kiểm tra bằng vòng bi 608 và trục thật, vừa đủ lắp và không rơ vượt yêu cầu. CAD hiện dùng ổ Ø22,2 và lỗ trục Ø8,2 mm.
3. Thử trục motor bằng dưỡng 28, tai/đĩa servo bằng dưỡng 20, mặt D bằng dưỡng 23, bo MT6701 bằng dưỡng 26 và nam châm bằng dưỡng 27. Motor chưa mua nên dưỡng chưa xác nhận được trục Ø4,5 hay Ø5 mm.
4. Đo kích thước ngoài và lỗ độc lập. Nếu kích thước ngoài đúng nhưng lỗ bị nhỏ, thử bù lỗ trên **dưỡng** theo bước 0,02–0,05 mm, slice và in lại; chưa áp một lượng bù lớn lên toàn bộ cụm. Mục tiêu thực dụng ban đầu cho mặt/lỗ quan trọng là sai lệch khoảng 0,1–0,2 mm, cần chứng minh bằng số đo, không phải độ chính xác được bảo đảm của preset.
5. Chỉ áp lượng bù đã thử lên nhóm chi tiết có lỗ tương ứng. Bù XY có thể tác động cả rãnh và hốc ê-cu. Bánh GT2, mặt D, hốc nam châm và lỗ PCB cần kiểm tra riêng; không scale cả cụm để sửa một lỗ.
6. Các đệm 29 dày 0,5 mm được in lớp 0,10 mm với lớp đầu 0,20 mm. Không thay tất cả về lớp 0,20 mm rồi bỏ qua chiều dày đệm.

Mặt tiếp xúc support có thể thô hơn các mặt không support. Bù kích thước trong slicer không thay được việc làm sạch support, kiểm tra lỗ hoặc căn đồng trục. Gia cố và vách dày cũng chưa thay phép thử tải của bản in thực.

## Thứ tự các bàn

| Bàn | Nội dung |
|---|---|
| 00 | Dưỡng và bốn đệm tai servo 0,5 mm — in trước |
| 01 | Đế, thanh ngang càng, hai đệm bi |
| 02 | Chảo, giá chảo và ba thanh feed |
| 03 | Càng trái/phải, tháp bi, gá motor, gá servo, rotor GT2, adapter servo |
| 04 | Đầu feed, hai vòng kẹp, bốn chân, một đệm bi và bốn vòng đệm vít motor |
| 05 | Khung U, khay ba điểm MT6701 và đầu nam châm |

Tổng vẫn **29 loại /43 vật in**, bố trí thành sáu dự án 3MF. Một số vị trí trên bàn 03 đã dịch nhẹ để chừa brim; kích thước chi tiết và lắp ghép CAD không đổi. Xem `ESTIMATED_PRINTS.csv` cho thời gian và khối lượng do slicer dự báo.

## Mở và sử dụng

Mở từng dự án, kiểm tra máy A1 0,4 mm, mặt bàn Textured PEI và vật liệu PETG. Giữ **Project/Modified settings** khi Bambu hỏi về preset từ dự án. Sau khi hiệu chuẩn đúng cuộn, kiểm tra lại các override tại **Process → Objects**, rồi Slice plate để tạo đường in theo thiết lập cuối cùng. Các file cung cấp là dự án chỉnh sửa được, chưa gửi lệnh tới máy in.

`audit/A1_PETG_print_validation.json` ghi kiểm tra mesh/volume, số lượng, preset đọc lại từ G-code, chiều cao in và biên đường in. `preview/Plate_*_support.png` minh họa đường support thật do slicer tạo. Các G-code dùng để kiểm tra được lưu trong thư mục làm việc, không phải file nạp được chứng nhận cho mọi cuộn PETG.

Nguồn preset là các file hệ thống Bambu Studio 02.08.02.60 đã cài trên máy. Tham khảo [preset Generic PETG A1 chính thức](https://github.com/bambulab/BambuStudio/blob/master/resources/profiles/BBL/filament/Generic%20PETG%20%40BBL%20A1.json), [tham số bù hình học trong mã nguồn Bambu Studio](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/PrintConfig.cpp) và [tài liệu CLI của Bambu](https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage).
