# Kiểm tra M4 — V3, 24/10/2026

Khung dùng **20 M4×20 DIN912, 20 đai ốc M4 thường**. Đầu danh định Ø7×4 mm, đai ốc AF7 dày 3,2 mm. M4 sẵn có phải đúng đầu/chiều dài trước khi thay.

Mỗi nhóm 4 vít: trụ–đế, gá motor–đế, dầm–rotor, hai càng–dầm, gá servo–càng. Tổng **40 đường dẫn**: 36 lỗ tròn Ø4,4 và 4 rãnh 4,4×9,4 của gá servo, chỉnh cao ±2,5 mm. audit_m4.py đọc trực tiếp STEP đã xuất; từng vị trí trong m4_audit.json. Ăn ren danh định tối thiểu đủ 3,2 mm của đai ốc.

8 hốc đầu dưới đế Ø8,2 sâu 3,2 mm; đầu nhô 0,8 mm. Chân cao 90 mm chừa khoảng trống cho cả encoder. Gá encoder đã tránh đầu M4. Không đặt đế sát bàn khi thiếu chân.

Gá servo có hốc mở; M4 từ đáy hốc vào đai ốc càng, không xuyên cả gá. Không thêm vòng đệm tại đây. Lắp M4 trước khi đặt servo để có đường đưa chìa vào, siết cố định khe trượt trước khi chạy.

M4 không thay M3/M2 ở motor, servo, chảo, encoder. Còn cần M3×8:4, M3×10:6, M3×12:12, M3×16:6, M3×20:7, M2×10:2; đai ốc M3:28, M2:2. Xem bảng vị trí trong hướng dẫn lắp.

fastener_validation.json: 142.990 phép kiểm tra đầu/thân vít/đai ốc danh định tại các góc lấy mẫu. Đây là kiểm tra CAD, chưa thử siết hoặc thử độ bền ren bản in.
