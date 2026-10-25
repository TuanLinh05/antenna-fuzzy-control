# Anten hai trục V3 — in và lắp

Bản ngày 24/10/2026: chảo Ø160 mm, MG946R 180°, NEMA17 SL42STH40-1684A, GT2-280 rộng 6 mm, truyền đai 80:20, encoder LPD3806-600BM ở **trục ra**. MG946R thay MG996R theo nguồn hàng Thế Giới IC. V1/V2 và mô hình gốc giữ riêng.

**Chưa in, lắp hoặc đo trên phần cứng thật.** Đây là mô hình thực nghiệm trong nhà; chảo nhựa chưa thu sóng thiên văn. Kích thước cửa hàng chưa công bố đủ cần đo khi nhận hàng: vị trí trục servo, tay tròn, chiều dài thân encoder và chiều dọc pulley.

## File sử dụng

| File | Công dụng |
|---|---|
| XEM_MO_HINH_3D.html | Xem offline, chỉnh hai góc |
| STL/; printed_parts.csv | 22 loại, tổng 36 vật kể cả 4 mẫu thử |
| 3MF_plates/ | 5 bàn 256 × 256 mm, chưa profile/support/G-code |
| STEP/ASSEMBLY_with_hardware_envelopes.step | Cụm lắp và bao hình danh định, không in nguyên cụm |
| DANH_SACH_MUA_THEGIOIIC.md | 35 mã, lượng cần/mua, giá và tồn kho theo thời điểm |
| KIEM_TRA_OC_M4.md | Đối chiếu 20 mối ghép M4 |
| ../../Firmware/DIEN_VA_DIEU_KHIEN.md | Nguồn, dây, STM32 và chạy thử |
| ../../Simulation/README.md | Cách chạy mô phỏng DC và stepper |
| BAO_CAO_KIEM_TRA_V3.md | Kết quả và giới hạn kiểm chứng |

## Cơ khí và đường truyền lực

Đế 208 × 146 × 8 mm, 4 chân Ø32 cao 90 mm. Tâm nâng Z=209 mm từ đáy đế, tức 299 mm từ mặt bàn. Chảo f=80 mm, sâu 20 mm, thành 2,4 mm. Motor trục 5 mm, bi 608ZZ Ø8×Ø22×7 mm (4 chiếc). Tâm hai pulley 87,9173 mm; motor chỉnh căng ±5 mm. Không tự đổi đai sang 300XL/đai hở hoặc motor trục 4,5 mm.

Hai 608 đỡ trục phương vị. Tải đứng từ vai rotor qua spacer vào vòng trong bi trên; vòng chặn dưới chống nhấc. **Encoder chỉ đo, không đỡ tải anten**. Khớp cứng D14 L25 cần đồng tâm, không dùng vít siết kéo trục lệch về nhau. Hai trục nâng được đỡ bởi 608 ở càng; mặt D và vít kẹp truyền mô-men. Dùng tay tròn/vít tâm đúng bộ servo, không in spline thay thế.

## In thử và A1

1. In mẫu **16, 17, 20, 23**, thêm adapter 11 và vòng chặn 18 để thử. Mẫu 16: 22,0/22,2/22,4 mm; mẫu 17: 8,0/8,2/8,4 mm. Mẫu D 23: Ø8,2, mặt cách tâm 3,7 mm. Bù dung sai theo mẫu, không scale cả cụm.
2. Mẫu 20 chỉ kiểm tra thân/tai. Gá 10 có tai chỉnh ±3 mm và toàn gá chỉnh cao ±2,5 mm để căn với tâm 608. Nếu vượt phạm vi, sửa CAD rồi xuất/kiểm tra lại. Không ép lệch tâm.
3. Tay servo danh định Ø24×3 mm. Adapter nhận hai lỗ đối xứng ở bán kính 6,5–10,5 mm. Mở lỗ tay nhựa lên 2,2 mm nếu cần cho M2 xuyên; giữ spline, tránh vít chạm vỏ. Nếu bộ hàng thiếu tay/vít tâm, yêu cầu cửa hàng bổ sung đúng bộ.
4. A1 nozzle 0,4 mm, scale 100%, lớp 0,20 mm. Khung 4–5 vòng thành, 5 lớp trên/dưới, gyroid 30–40%. Rotor/adapter/vòng chặn 6 vòng thành, infill 60–100%; rotor thử lớp 0,16 mm. Spacer/đệm 1 mm in đặc. Đây là thiết lập khởi đầu chưa in kiểm chứng.
5. Support cho **03, 04, 12, 22**. Đĩa nhô rotor và tấm trên gá encoder cần support; tránh khóa hốc đai ốc/lỗ D. Rà từng mặt nhô trong Slice preview. Chảo lòng hướng lên theo STL.
6. 3MF chỉ kiểm tra footprint vật trong bàn, không gồm brim/support/vùng tránh đầu in. Auto Arrange lại nếu cần và in từng bàn. Thử đai ăn răng rotor riêng, không đội/kẹt. Chưa có G-code.

## Vít và đai ốc

Dùng đầu trụ DIN912, chiều dài từ dưới đầu, đai ốc lục giác thường. Vít M4 đang có chỉ thay khi đúng đầu và dài 20 mm; đầu chìm/đầu tròn lớn không mặc nhiên khớp.

| Mối lắp | Vít | Đai ốc/ren |
|---|---|---|
| Trụ–đế; gá motor–đế; dầm–rotor; càng–dầm; gá servo–càng | Mỗi nhóm 4 M4×20 | Mỗi nhóm 4 M4 |
| Motor vào gá | 4 M3×10 + 4 đệm 21 | Ren motor, sâu danh định 3 mm |
| Tai servo | 4 M3×12 | 4 M3 |
| Chân đế | 4 M3×12 | 4 M3 gần đầu chân |
| Hai vòng chặn | 2 M3×16 | 2 M3 |
| Kẹp rotor | 1 M3×12 | 1 M3 |
| Kẹp hai trục vào giá | 2 M3×10 | 2 M3 |
| Kẹp adapter | 1 M3×8 | 1 M3 |
| Chảo vào giá | 4 M3×20 | 4 M3 |
| Chân thanh đầu thu | 3 M3×20 | 3 M3 |
| Thanh vào hub | 3 M3×12 | 3 M3 |
| Tay tròn vào adapter | 2 M2×10 | 2 M2 đồng |
| Gá encoder vào đế | 4 M3×16 | 4 M3 |
| Mặt encoder vào gá | 3 M3×8 + 3 đệm 21 | Ren encoder, sâu danh định 3 mm |

Tổng: **20 M4×20; 4 M3×8; 6 M3×10; 12 M3×12; 6 M3×16; 7 M3×20; 2 M2×10**. Đai ốc: 20 M4, 28 M3, 2 M2; đệm 21: 7. Vít tâm servo và vít kẹp sẵn pulley/khớp giữ đúng loại đi kèm. Không thêm vòng đệm vào 4 M4 của gá servo vì chiều dài ren đã tính sát.

## Cắt và giũa trục

**Trước khi cắt**, dùng thanh 200 mm còn thẳng căn hai bi nâng trên càng chưa lắp giá chảo rồi rút ra. Không đẩy trục tròn qua lỗ D. Cắt 120+40+30 mm, chừa tổng 10 mm cho đường cưa/sửa đầu; tẩy ba via, tránh làm cong trục.

Giũa sâu danh định 0,5 mm (mặt cách tâm 3,5 mm), đo thước cặp và giũa dần. Mẫu 23 kiểm tra lắp, không phải dưỡng chiều sâu. Vùng trong bi phải giữ tròn.

| Đoạn | Mặt phẳng cần giũa | Hướng ở CAD nâng 0° |
|---|---|---|
| 120 mm | 17 mm từ đầu trên, Z=89…106 | +Y |
| 40 mm trái | 13 mm từ đầu ngoài servo, X=-114…-101 | -Z |
| 40 mm trái | 3–11 mm từ đầu trong, X=-85…-77 | Cùng mặt -Z |
| 30 mm phải | 8 mm từ đầu trong, X=77…85 | -Z |

## Lắp theo thứ tự

1. Lắp 4 chân bằng M3×12 từ trên đế, đai ốc ở hốc bên gần đỉnh chân. Bắt gá encoder 22 dưới đế bằng M3×16 **trước trụ** vì đầu vít sau đó bị che.
2. Ép 608 vào trụ, chỉ ép vòng ngoài; bắt trụ/gá motor bằng M4. Nhét các đai ốc rotor/dầm/càng trước khi mặt ghép bị che.
3. Trục 120 đặt Z=-14…106. Từ dưới lên: vòng chặn -2…6; spacer 6…8; bi dưới 8…15; bi trên 59…66; spacer 66…68; rotor 68…105. Căn mặt D rồi kẹp hub. Hết rơ dọc vừa đủ, quay nhẹ.
4. Encoder vào gá bằng 3 M3×8 + đệm 1 mm; mặt lắp Z=-35. Đo chiều sâu ren thật. Khớp đặt Z=-28…-3, đầu 8 phía trên, mỗi trục vào khoảng 11 mm, hai đầu cách khoảng 3 mm. Tránh vòng chặn; căn quay nhẹ rồi siết. CAD chừa thân encoder dài 45 mm, cần đo hàng thật.
5. Motor dùng M3×10+đệm, kiểm tra được vào ren 3 mm. Tâm răng pulley tại Z=73 mm. Đo hub thật, tránh cọ boss/mặt gá; lắp đai và căng nhẹ bằng rãnh.
6. Bắt dầm, hai càng, bi nâng. Căn bi bằng thanh thẳng trước khi cắt như trên. Bắt 4 M4 gá servo **trước khi đặt servo** để đưa chìa lục giác vào; chỉnh cao đúng tâm rồi siết. Có thể phải tháo servo khi chỉnh lại.
7. Bắt giá vào chảo, thanh đầu thu bằng M3×20. Nhét đai ốc đầu thanh trước khi lắp hub rồi bắt M3×12 từ trên. Các thanh ở 90°,210°,330°.
8. Trục trái 40 tại X=-114…-74, phải 30 tại 77…107. Căn mặt D, kẹp vít. Bên phải spacer 97…99, vòng chặn 99…107; spacer chỉ tì vòng trong bi. Giá cách càng khoảng 2 mm.
9. Cho servo về 90° bằng nguồn riêng rồi tắt để lắp tay. Tay/vít tâm đúng bộ, adapter bằng 2 M2 xuyên. Căn đồng trục rồi kẹp; không dùng servo kéo cơ cấu kẹt.
10. Tắt nguồn, quay tay hết phạm vi dùng. Chừa vòng dây mềm khoảng 500–600 mm tùy vị trí mạch, tránh đai/khớp/cạnh nhựa. Đặt đế chắc chắn, tránh dây kéo nghiêng chân cao. Chưa có slip ring, tự home hay công tắc hành trình cứng.

## Chạy thử thực tế

Bi phải quay nhẹ, encoder không gánh tải. Đánh dấu trục/rotor/adapter để phát hiện trượt. Đo 5 V lúc servo chạy và đo STEP/DIR/PWM, mức encoder trước khi nối MCU theo tài liệu điện. Xác nhận chiều motor/encoder bằng góc nhỏ trước khi đóng vòng; căn 0 bằng tay và lệnh Z sau mỗi lần bật nguồn. Bắt đầu ±150° phương vị, 45–135° nâng; thử 1–2° rồi tăng dần.

Ghi dòng, nhiệt, độ rơ và góc thật để nhận dạng lại mô-men chạy, ma sát, độ cứng đai và servo. CAD chưa xét ren thật, dây mềm, từng răng đai, spline trong servo hoặc độ bền bám lớp. Tính tải là ước lượng theo giả thiết, không phải FEA/thử tải. Kẹt/va đập có thể gây bật đàn hồi; xem kết quả stress test trước khi nâng tải.

## Tạo lại CAD

CadQuery 2.8, trimesh, numpy, VTK; runtime hiện tại D:/HK261/NMDKTM/tmp/cad_runtime, không đóng gói. Chạy build_model.py → validate_assembly.py → validate_fasteners.py → audit_m4.py → validate_loads.py → validate_transmission.py → validate_electrical.py → make_preview.py → kiểm tra MATLAB → package_delivery.py. Sửa parameters.json đơn lẻ không đổi hình học.
