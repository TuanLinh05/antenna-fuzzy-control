"""Write the V3 delivery guides from reviewed design and machine-readable results."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent
PROJECT=R.parents[1]
SIMULATION=PROJECT/'Simulation'
FIRMWARE=PROJECT/'Firmware'
guide='''# Anten hai trục V3 — in và lắp

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
'''
(R/'HUONG_DAN_LAP_RAP.md').write_text(guide,encoding='utf-8')
m4='''# Kiểm tra M4 — V3, 24/10/2026

Khung dùng **20 M4×20 DIN912, 20 đai ốc M4 thường**. Đầu danh định Ø7×4 mm, đai ốc AF7 dày 3,2 mm. M4 sẵn có phải đúng đầu/chiều dài trước khi thay.

Mỗi nhóm 4 vít: trụ–đế, gá motor–đế, dầm–rotor, hai càng–dầm, gá servo–càng. Tổng **40 đường dẫn**: 36 lỗ tròn Ø4,4 và 4 rãnh 4,4×9,4 của gá servo, chỉnh cao ±2,5 mm. audit_m4.py đọc trực tiếp STEP đã xuất; từng vị trí trong m4_audit.json. Ăn ren danh định tối thiểu đủ 3,2 mm của đai ốc.

8 hốc đầu dưới đế Ø8,2 sâu 3,2 mm; đầu nhô 0,8 mm. Chân cao 90 mm chừa khoảng trống cho cả encoder. Gá encoder đã tránh đầu M4. Không đặt đế sát bàn khi thiếu chân.

Gá servo có hốc mở; M4 từ đáy hốc vào đai ốc càng, không xuyên cả gá. Không thêm vòng đệm tại đây. Lắp M4 trước khi đặt servo để có đường đưa chìa vào, siết cố định khe trượt trước khi chạy.

M4 không thay M3/M2 ở motor, servo, chảo, encoder. Còn cần M3×8:4, M3×10:6, M3×12:12, M3×16:6, M3×20:7, M2×10:2; đai ốc M3:28, M2:2. Xem bảng vị trí trong hướng dẫn lắp.

fastener_validation.json: 142.990 phép kiểm tra đầu/thân vít/đai ốc danh định tại các góc lấy mẫu. Đây là kiểm tra CAD, chưa thử siết hoặc thử độ bền ren bản in.
'''
(R/'KIEM_TRA_OC_M4.md').write_text(m4,encoding='utf-8')
matlab='''# MATLAB/Simulink — Anten V3

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
'''
(SIMULATION/'README.md').write_text(matlab,encoding='utf-8')
(SIMULATION/'README.md').write_text(matlab+'\n## Điều khiển board thật (chưa kiểm thử I/O)\n\nSau khi đấu dây/hiệu chỉnh theo tài liệu điện, chạy `serialportlist` để xem cổng, thêm `../Firmware/tools` vào MATLAB path rồi chạy `hardware_console("COM5")` với cổng đúng. Cửa sổ gửi heartbeat 0,4 s, chỉ đặt mốc Z/gửi góc khi bạn bấm nút. Đóng cửa sổ gửi S. Chưa thử kết nối thật; không chạy khi chưa xác nhận chiều encoder và nguồn. Firmware prototype dùng vmax=0,47 rad/s; nhánh DC giữ vmax=0,48 rad/s.\n\nAPI: [MathWorks serialport](https://www.mathworks.com/help/matlab/ref/serialport.html).\n',encoding='utf-8')
print('V3 assembly, M4 and MATLAB guides written.')
(R/'package_delivery.py').write_text('"""Validate and package the final V3 delivery."""\nfrom finalize_delivery import main\nif __name__ == "__main__":\n    main()\n',encoding='utf-8')
if (SIMULATION/'results/comprehensive_validation.json').exists():
    sim=json.loads((SIMULATION/'results/comprehensive_validation.json').read_text(encoding='utf-8'))
    load=json.loads((R/'audit/load_validation.json').read_text(encoding='utf-8'))
    bom=json.loads((R/'procurement.json').read_text(encoding='utf-8'))
    fw=json.loads((R/'audit/firmware_build_validation.json').read_text(encoding='utf-8'))
    dc=sim['dc_nominal'];pr=sim['prototype_nominal']
    steps='\n'.join(f"| {q['time_s']:.0f} | {q['target_deg']:.0f}° | {q['overshoot_percent']:.3f}% | {q['settling_2percent_s']:.4f} | {q['tail_max_error_rad']:.3g} |" for q in dc['steps'])
    report=f'''# Báo cáo kiểm tra anten V3 — 24/10/2026

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

Tính tải theo CAD: khối lượng giả thiết in đặc tổng {load['total_full_solid_mass_kg']:.3f} kg; J phương vị lớn nhất {load['yaw_inertia_max_kgm2']:.6f} kg.m². Mô-men yêu cầu {load['yaw_required_Nm']:.4f} N.m phương vị, {load['elevation_required_Nm']:.4f} N.m nâng. Hệ số dự trữ tương ứng {load['yaw_torque_margin']:.2f} và {load['elevation_torque_margin']:.2f}, dựa trên mô-men chạy stepper giả thiết 0,12 N.m và chỉ dùng 20% mô-men kẹt servo tại 4,8 V. Biên trọng tâm bảo thủ khi thay khối lượng chi tiết in 35–100% là {load['conservative_variable_infill_support_margin_mm']:.1f} mm trong đa giác chân. Đây là ước lượng, không phải chứng nhận vật liệu/FEA/thử tải.

## 3. BOM chỉ Thế Giới IC

Đã mở trang sản phẩm và đối chiếu mã, tồn kho, số mua tối thiểu/bội số cho **{len(bom['items'])} mã** ngày {bom['verified_date']}. Số tồn đều đủ lượng mua đề xuất tại thời điểm kiểm tra. Tổng **{bom['system_total_vnd']:,} VND**: cơ khí {bom['mechanical_total_vnd']:,}, điện {bom['electrical_total_vnd']:,}; chưa gồm in, vận chuyển và board STM32 đang có. Danh sách mua đã có dự phòng/đơn tối thiểu. Nếu đã có M4×20 đúng loại có thể bỏ dòng mua M4.

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
{steps}

Đỉnh tốc độ {dc['peak_speed_rad_s']*180/3.141592653589793:.3f}°/s <30; điện áp {dc['peak_voltage_V']:.3f} V <12; quá điều chỉnh ≤2%. Kiểm tra 12 tổ hợp sai lệch thông số ngẫu nhiên có seed, nhiễu tải 2 N.m và giảm bước từ 100 xuống 50 µs đều đạt các tiêu chí đã định. Bộ tích phân MATLAB độc lập khớp Simulink tới sai số số học trong trường hợp danh định. Chọn nhanh nhất trong 18 ứng viên thử, không chứng minh tối ưu toàn cục.

### Nhánh stepper theo CAD

Đã xét động cơ phi tuyến, đàn hồi/độ rơ đai, lượng tử xung/encoder, quán tính phụ thuộc góc nâng và servo giả định. Danh định: quá điều chỉnh {pr['worst_overshoot_percent']:.3f}%, sai số cuối lớn nhất {pr['worst_tail_error_rad']*180/3.141592653589793:.4f}°, tốc độ đỉnh {pr['peak_speed_rad_s']*180/3.141592653589793:.3f}°/s. Có kiểm tra mất xung, tải thêm 0,02 N.m, quán tính 0,5–1,5 lần, độ rơ 3°, nhiễu encoder, chu kỳ 12 ms và tinh chỉnh bước tích phân.

**Giới hạn được phát hiện:** va đập tải 0,08 N.m làm đỉnh tốc độ {sim['overload_peak_speed_deg_s']:.2f}°/s, vượt 30°/s; nhả kẹt cũng có bật đàn hồi. Phát hiện encoder đứng/mất liên lạc/kẹt đạt thời gian đặt trong bài kiểm tra, nhưng không đồng nghĩa phanh cơ khí hoặc giữ được góc khi lỗi. Những ca này vẫn được lưu với cột tracking_requirements_met=false. Không ghi tất cả stress test là đạt bám góc.

Động học servo, mô-men chạy, độ cứng/cản/độ rơ đai và quán tính rotor motor chưa được đo; cần nhận dạng lại trên phần cứng. Không có HIL, mô phỏng nhiệt/chopper cuộn dây, FEA hoặc RF.

## 6. Điều kiện nghiệm thu thực tế còn lại

1. Đo linh kiện nhận được, in 4 mẫu thử và kiểm tra tay servo/adapter/vòng chặn trước toàn bộ bộ in.
2. Cắt/giũa D theo bản hướng dẫn, căn bi và hai khớp đồng trục; quay tay không kẹt, encoder không đỡ tải.
3. Kiểm tra 5 V lúc tải servo, nhiệt driver/nguồn, xung và chiều encoder/motor; hiệu chỉnh mốc tay bằng Z.
4. Thử từ góc nhỏ, đo sai số và nhận dạng lại mô hình; chỉ mở rộng hành trình/tốc độ khi dữ liệu thực đạt. Cơ cấu hiện dành thử nghiệm tải nhẹ trong nhà, chưa được phê duyệt cho va đập/kẹt, kéo dây hoặc tải ngoài trời.

File chi tiết: audit/STAGE_GATES.json, assembly_validation.json, fastener_validation.json, m4_audit.json, audit/load_validation.json, audit/transmission_validation.json, audit/electrical_validation.json, audit/firmware_build_validation.json, ../../Simulation/results/comprehensive_validation.json và các CSV/MAT/ảnh/video đi kèm.
'''
    (R/'BAO_CAO_KIEM_TRA_V3.md').write_text(report,encoding='utf-8')
