# Kiểm tra ốc M4 — anten V2

Đã kiểm tra trực tiếp các file STEP xuất của V2 ngày **11/10/2026**. Phần khung dùng **20 ốc M4×20 đầu trụ lục giác DIN912** và **20 đai ốc M4 lục giác thường**. Các lỗ M4 hiện đúng kích thước; không cần sửa hình học để dùng loại ốc này.

Ốc đã chọn tại Thế Giới IC: [M4×20 DIN912 304 — IC10179](https://www.thegioiic.com/oc-luc-giac-m4-x-20mm-din912-304). Chiều dài 20 mm tính từ **dưới đầu ốc đến đầu ren**. Có thể dùng ốc M4 sẵn có nếu cùng chiều dài và dạng đầu. Chỉ tên “M4” chưa xác định chiều dài hoặc kích thước đầu ốc.

## Các mối ghép M4

| Mối ghép | Chi tiết in | Số ốc | Lỗ xuyên | Loại ốc |
|---|---|---:|---|---|
| Trụ vòng bi vào đế | 02 + 01 | 4 | Ø4,4 mm | M4×20 DIN912 |
| Gá stepper vào đế | 03 + 01 | 4 | Ø4,4 mm | M4×20 DIN912 |
| Dầm vào rotor | 07 + 04 | 4 | Ø4,4 mm | M4×20 DIN912 |
| Hai càng vào dầm | 08/09 + 07 | 4 | Ø4,4 mm | M4×20 DIN912 |
| Gá servo vào càng trái | 10 + 09 | 4 | Ø4,4 mm | M4×20 DIN912 |

20 mối ghép tương ứng **40 lỗ trên các chi tiết ghép đôi**. Lỗ Ø4,4 mm là lỗ cho ốc xuyên qua, có độ hở đường kính 0,4 mm so với thân M4 danh định. Cần đai ốc riêng; lỗ nhựa không được tạo ren M4.

## Đầu ốc, đai ốc và chiều dài

- Bao hình đầu trụ được kiểm tra: Ø7 mm, cao 4 mm. Không có giao khối với các chi tiết khung được kiểm tra.
- 8 hốc đầu ốc dưới đế: Ø8,2 mm, sâu 3,2 mm. Đầu ốc nhô **0,8 mm** dưới đế; phải lắp 4 chân in 19 cao 10 mm như thiết kế.
- Hốc đai ốc trong rotor, dầm và càng trái: khoảng cách hai mặt phẳng đối diện **7,3 mm**, sâu **3,5 mm**. Đai ốc kiểm tra danh định: rộng hai mặt 7 mm, dày 3,2 mm. Các đai ốc trên chân trụ/gá stepper nằm ngoài, không cần hốc giữ.
- Với M4×20, chiều dài ren nằm trong mỗi đai ốc đạt đủ **3,2 mm danh định**. Ở gá servo, đầu ren vừa tới mặt ngoài đai ốc; tránh thêm vòng đệm tại mối ghép này vì sẽ giảm độ ăn ren.
- Dùng đầu trụ theo BOM. Nếu thay bằng đầu chìm, đầu lục giác ngoài, đai ốc mặt bích hoặc đai ốc tán keo, cần kiểm tra lại kích thước và mặt tì.

## Các vị trí vẫn dùng cỡ khác

V2 **không dùng M4 cho toàn bộ mô hình**. Cỡ vít hiện tại:

| Vị trí | Vít cần |
|---|---|
| Bắt trực tiếp motor NEMA17 vào gá | 4×M3×10 + 4 đệm in 21; vào ren motor |
| Tai servo vào gá | 4×M3×12 + đai ốc M3 |
| Tay tròn servo vào adapter | 2×M2×10 + đai ốc M2 |
| Vít tâm tay servo | Vít đi kèm đúng bộ servo |
| Chân đế, vòng chặn/kẹp trục, chảo, các thanh và hub đầu thu | M3 theo bảng trong hướng dẫn lắp |

Tổng vít khác: **28 vít M3** (1×8, 6×10, 12×12, 2×16, 7×20 mm) và **2 vít M2×10**, ngoài vít tâm đi kèm servo. Các chi tiết in ở nhóm M3 hiện có lỗ Ø3,3 mm; rãnh M2 trên adapter rộng 2,2 mm. Không thể đưa M4 vào những vị trí này theo bản V2 hiện tại. Riêng motor và phụ kiện servo phải dùng vít phù hợp với lỗ/ren của linh kiện.

## Kết quả và giới hạn

`audit_m4.py` đọc độc lập 8 file STEP của khung, đo 40 lỗ M4, kiểm tra đồng tâm, hốc đầu ốc, bao hình đầu/thân ốc và đai ốc, hốc đai ốc và chiều dài ăn ren. Kết quả **PASS**, lưu trong `m4_audit.json`. Kiểm tra giao khối vít toàn cụm trước đó trong `fastener_validation.json` cũng đạt PASS.

Đây là kiểm tra hình học CAD, chưa in thử. Dung sai máy in và đầu ren vát chưa được đo. In đúng **100%**; sau khi in, thử một ốc M4 và đai ốc thật trước khi lắp cả khung. Nếu lỗ bị co hoặc có ba via, làm sạch và rà nhẹ bằng mũi Ø4,4 mm. Không siết ép ốc lớn vào lỗ M3/M2.
