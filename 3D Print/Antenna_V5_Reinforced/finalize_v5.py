"""Check deliverable completeness, summarize limits and create a self-contained ZIP."""
from pathlib import Path
import json,csv,collections,hashlib,zipfile,sys,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parents[2]/'tmp/cad_runtime'))
import trimesh,numpy as np
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def write(p,data):(R/p).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
required=['assembly_validation.json','fastener_validation.json','m4_audit.json','audit/interface_validation.json','audit/load_validation.json','audit/access_validation.json','audit/reinforcement_validation.json']
for p in required:assert read(p)['status'].startswith('PASS'),p
mesh=read('mesh_validation.json');expected={q['part']:q['quantity'] for q in mesh}
assert len(list((R/'STL').glob('*.stl')))==len(expected)
assert all(q['watertight'] and q['connected_components']==1 and q['winding_consistent'] for q in mesh)
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
counts=collections.Counter();plate_checks=[]
for plate in sorted((R/'3MF_plates').glob('*.3mf')):
    with zipfile.ZipFile(plate) as z:
        assert z.testzip() is None
        xml=ET.fromstring(z.read('3D/3dmodel.model'))
    assert xml.get('unit')=='millimeter'
    objects={o.get('id'):o for o in xml.findall('m:resources/m:object',ns)}
    for item in xml.findall('m:build/m:item',ns):
        o=objects[item.get('objectid')];name=o.get('name');counts[name]+=1
        v=np.array([[float(x.get(k)) for k in ('x','y','z')] for x in o.findall('m:mesh/m:vertices/m:vertex',ns)])
        faces=[[int(f.get(k)) for k in ('v1','v2','v3')] for f in o.findall('m:mesh/m:triangles/m:triangle',ns)]
        m=trimesh.Trimesh(vertices=v,faces=faces,process=True)
        assert np.all(v.min(axis=0)>=-.001) and np.all(v.max(axis=0)<=256.001),(plate.name,name)
        source=trimesh.load_mesh(R/'STL'/f'{name}.stl')
        assert abs(m.volume/source.volume-1)<1e-5,(plate.name,name)
        plate_checks.append(dict(plate=plate.name,part=name,bounds_mm=m.bounds.round(3).tolist()))
assert dict(counts)==expected,(dict(counts),expected)
parts=read('audit/interface_validation.json');loads=read('audit/load_validation.json');fast=read('fastener_validation.json')
reinforcement=read('audit/reinforcement_validation.json');access=read('audit/access_validation.json')
budget=dict(status='PASS_ASSUMED_POWER_BUDGET_NOT_MEASURED',input_V=12,input_A=5,input_capacity_W=60,
    servo_output_V=7,servo_peak_current_assumed_A=3,buck_efficiency_assumed=.85,
    servo_input_power_estimate_W=7*3/.85,stepper_driver_input_budget_assumed_W=15,
    MCU_logic_input_budget_assumed_W=2)
budget['total_input_power_estimate_W']=budget['servo_input_power_estimate_W']+17
budget['estimated_input_current_A']=budget['total_input_power_estimate_W']/12
budget['unused_input_budget_W']=60-budget['total_input_power_estimate_W']
budget['physical_supply_transients_and_thermal_verified']=False
write('audit/power_budget.json',budget)
bom=[('17HS1352-P4130 stepper',1,'Chosen model; shaft bore/current convention must be checked on received unit'),
     ('TB6600 driver',1,'Select exact module rated for 12V input; set current from motor and peak/RMS table'),
     ('LD-1501MG + supplied round horn',1,'User owns round horn; ear/axis dimensions require fit gauge'),
     ('MT6701 module 23x23mm',1,'User already owns; confirm actual pinout and IC center'),
     ('Diametric magnet 4x2mm',1,'User supplied; field strength and angle accuracy unmeasured'),
     ('GT2 metal pulley 20T for 6mm belt',1,'Nominal 5mm bore; measure actual shaft before purchase'),
     ('Closed-loop 2GT belt 280mm x6mm',1,'140 teeth at 2mm pitch'),
     ('608 bearing 8x22x7mm',4,'Two azimuth and two elevation'),
     ('8mm steel shaft stock 200mm',1,'Cut 120 +40 +30mm; preserve round bearing seats and file specified drive flats'),
     ('12V 5A regulated power supply',1,'Selected; whole-system transient/load validation required'),
     ('Buck to approximately 7V for servo',1,'At least the assumed 3A transient plus margin; actual thermal rating required'),
     ('STM32F103 board',1,'User owns; exact board variant and power arrangement unverified'),
     ('MCU logic regulator / STEP-DIR buffers',1,'Use 3.3V sensor interface and driver-compatible pulse levels'),
     ('Suitable magnet adhesive and insulated flexible cable',1,'Not price-quoted; mechanically retain and strain-relieve')]
for name,n in fast['bolt_counts'].items():bom.append((name+' screw',n,'Nominal lengths checked; tapped motor holes remain a physical check'))
for size in (2,3,4):bom.append((f'M{size} hex nut',fast[f'M{size}_nut_count'],'Includes floating M2 PCB nuts and both M3 nuts per sensor stud'))
with (R/'hardware_BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['item','assembly_quantity','note']);w.writerows(bom)
status=dict(revision='V5',date_local='2026-10-25',status='PASS_DIGITAL_GEOMETRY_WITH_PHYSICAL_CHECKS_OPEN',
    STL_types=len(expected),print_objects=sum(expected.values()),plate_count=len(list((R/'3MF_plates').glob('*.3mf'))),
    assembly_intersection_checks=read('assembly_validation.json')['intersection_checks'],
    fastener_intersection_checks=fast['intersection_checks'],exact_ratio=parts['ratio'],
    belt_pitch_length_mm=parts['belt_pitch_length_mm'],center_distance_mm=parts['motor_center_distance_mm'],
    nominal_magnet_to_IC_gap_mm=parts['nominal_magnet_to_IC_gap_mm'],
    physical_fit_tested=False,magnetic_accuracy_verified=False,motor_torque_speed_verified=False,
    firmware_MT6701_port_complete=False,closed_loop_hardware_tracking_validated=False,
    previous_V3_simulation_not_reused_as_V5_proof=True,plate_objects=plate_checks,
    access_checks=access['counts'],physical_strength_tested=False,
    estimated_relative_section_stiffness=reinforcement['estimated_stiffness_ratio_V5_over_V4'])
write('delivery_validation.json',status)
configured_path=R/'audit'/'A1_PETG_print_validation.json'
if configured_path.exists():
    configured=read('audit/A1_PETG_print_validation.json')
    assert configured['status']=='PASS_A1_PETG_PROJECTS_AND_TOOLPATHS'
    status['configured_print_projects']=configured['project_count']
    status['configured_print_validation']=configured['status']
    write('delivery_validation.json',status)
report=f'''# Báo cáo kiểm tra V5 - 25/10/2026

**Kết luận: đạt kiểm tra hình học số sau các lần sửa; khả thi theo ước lượng tải/nguồn đã nêu; chưa nghiệm thu phần cứng hoặc chất lượng bám góc.**

## Hình học và bộ file

- {len(expected)} loại STL, {sum(expected.values())} vật in kể cả dưỡng; năm bàn A1, đơn vị mm. Mesh kín, một khối, hướng mặt nhất quán, thể tích dương. Kiểm tra lại 3MF độc lập đúng số lượng, trong 256 mm và thể tích khớp STL. Chưa slice support/brim/G-code.
- {status['assembly_intersection_checks']:,} kiểm tra giao khối cụm và {fast['intersection_checks']:,} kiểm tra vít/ê-cu không còn lỗi ở các góc lấy mẫu. Góc nâng 0–180° và phương vị 0–360° được lấy mẫu để kiểm tra hình học; không suy ra hành trình vận hành có dây hoặc an toàn servo đủ 180°.
- Kiểm tra riêng M4x20 đọc từ STEP và chiều dài vít; các giao diện motor/servo/bo được kiểm tra độc lập ở biên rãnh chỉnh. Không dùng kiểm tra hữu hạn làm chứng minh mọi va chạm liên tục.

## Gia cố giá servo và sử dụng gá cảm biến

- Giá servo 10 tăng mặt từ 4 lên 8 mm, dầm bên 10 lên 16 mm; thêm giằng trên/dưới 8 mm. Đường đưa đầu vít M4 được kiểm tra ở ba vị trí rãnh, không còn khoét hở toàn bề rộng dầm.
- Bốn vít tai servo đổi M3x12 sang M3x16; bốn M4x20 vào càng giữ nguyên. Đã kiểm tra chỗ đưa đầu vít Ø7,5 mm và thanh lục giác Ø3,6 mm từ mặt ngoài.
- Gá MT6701 22 là khung U mở trước, có cửa bên/lưng. Khay 24 dùng ba trụ M3x25 để chỉnh mặt phẳng. Đã kiểm tra đường cờ lê mỏng tới ê-cu, rút trụ xuống và đường hạ khay 3 mm rồi trượt ra trước sau khi tháo ba trụ. Khi bảo trì cần kê cụm chắc chắn để có ít nhất 30 mm dưới đầu vít; chân đế chỉ chừa khoảng 10 mm.
- So sánh dầm với tiết diện CAD lấy mẫu cho hệ số độ cứng tính toán V5/V4 khoảng {reinforcement['estimated_stiffness_ratio_V5_over_V4']['force_Z']:.2f} theo phương Z và {reinforcement['estimated_stiffness_ratio_V5_over_V4']['force_Y']:.2f} theo phương Y. Mô hình dùng lực tĩnh minh họa 20 N, E giả định 1000 MPa và gốc gá giữ cứng; chưa xét đầy đủ tấm mặt, mối ghép, bền lớp, tập trung ứng suất, va đập hoặc lật cả cụm. **Không dùng các hệ số này làm hệ số tăng tải phá hủy.**
- Nguyên lý gá cảm biến là giữ PCB đứng yên trước nam châm trên trục quay; tải chảo do hai bi đỡ trục, không đi qua PCB. Cấu trúc V4 dùng được về hình học nhưng bố trí hai tấm/bốn trụ khó thao tác hơn; V5 được thay theo phản hồi thực tế của người dùng.

## Bộ truyền (giữ nguyên)

- Đã đếm trên solid xuất ra đủ {parts['exported_rotor_grooves_count']} rãnh rotor, ghép pulley thương mại 20T: **4:1**.
- Đai đường bước {parts['belt_pitch_length_mm']:.6f} mm, tâm {parts['motor_center_distance_mm']:.6f} mm; góc ôm bánh nhỏ {parts['small_pulley_wrap_deg']:.3f}°, tương ứng {parts['small_pulley_engaged_teeth']:.3f} răng.
- Motor trượt ±5 mm; kiểm tra thân, boss và bốn vít ở ba vị trí. Chất lượng răng in, độ căng và không trượt răng vẫn phải kiểm tra với đai thật.
- 1/16: độ chia lệnh {parts['microstep_output_deg']:.6f}°; cần {parts['STEP_frequency_at_30deg_s']:.2f} Hz để đặt 30°/s, motor 20 rpm. Không gọi đây là độ chính xác định hướng.

## MT6701 và động cơ

- PCB 23x23 mm, lỗ người dùng khoảng 2 mm; pitch suy ra 18 mm. Vít và ê-cu trượt đã kiểm tra ở pitch 17,5 /18 /19 mm. Carrier chỉnh XY ±1,5 mm và Z tổng 1,5 mm.
- Hốc nam châm Ø4,2 x2,2 mm cho nam châm Ø4 x2 mm; mặt nam châm cần lắp ngang miệng hốc. Khe mặt nam châm–mặt IC danh định 1 mm, chỉnh 0,5–2 mm theo chiều cao giả định.
- PCB dày 1,6 mm, IC cao 1,7 mm và vị trí header là giả định. Hàn dây mềm hoặc dùng header thấp/vuông góc hướng dây ra bên hông; không để pin đứng cao hơn bao 3 mm chĩa vào đầu giữ nam châm. Căn tâm IC thực và đo khe sau khi lắp. Không xác nhận từ trường/độ chính xác chỉ từ khe đúng; nam châm nhỏ hơn loại tham chiếu datasheet.
- Motor dựng thân 34 mm, trục nhô 20 mm, Ø5 mm. Thông tin bán hàng còn ghi 4,5 mm; chưa có motor nên chưa xác nhận lỗ pulley. Dưỡng 28/30 dành cho bước này.
- Servo LD-1501MG dùng đĩa tròn người dùng có. Cửa thân 21,6 mm; lỗ tai kiểm tra pitch dài 45–50 mm và ngang 8–12 mm. Rãnh adapter đĩa kiểm tra vít/ê-cu M2 ở bán kính 6,5–10,5 mm. Dưỡng 20 và căn đồng trục vẫn cần thực hiện.

## Tải và nguồn

Khối lượng tính theo chi tiết in đặc PLA và các khối lượng linh kiện ghi rõ nguồn/giả định: **{loads['total_full_solid_mass_kg']:.3f} kg**. J phương vị lớn nhất {loads['yaw_inertia_max_kgm2']:.7f} kg.m², J nâng {loads['elevation_inertia_max_kgm2']:.7f} kg.m².

- Với gia tốc phương vị 30°/s², tốc độ 30°/s, ma sát Coulomb giả định 0,02 N.m và cản nhớt 0,01 N.m.s/rad: cần khoảng {loads['yaw_required_Nm']:.5f} N.m ở trục ra. Để có dự trữ 3 lần theo phép tính này, motor cần mô-men chạy ít nhất **{loads['required_motor_running_torque_for_3x_margin_Nm']:.5f} N.m** với bộ truyền hiệu suất giả định 0,8; chưa gồm hiệu ứng quá độ rotor/đai chưa nhận dạng.
- Nếu tạm giả định motor giữ được 0,05 N.m khi chạy, dự trữ tải tính ra {loads['yaw_torque_margin']:.2f} lần. **0,05 N.m là giả định thiết kế, không phải đặc tuyến đã đo hoặc lấy trực tiếp từ mô-men giữ 0,25 N.m.**
- Tải nâng ước lượng {loads['elevation_required_Nm']:.5f} N.m; dùng 20% mô-men kẹt hãng công bố ở 6 V làm mức lập kế hoạch cho ra dự trữ {loads['elevation_torque_margin']:.2f} lần. Điều này không chứng nhận mô-men liên tục, nhiệt hay sai số servo ở 7 V.
- Biên trọng tâm bảo thủ khi thay lượng nhựa in 35–100% khoảng {loads['conservative_variable_infill_support_margin_mm']:.2f} mm trong đa giác chân. Chưa xét gió, kéo dây hoặc va đập. Không có FEA/chứng nhận bền lớp in.
- Ngân sách nguồn giả định: servo 7 V x3 A qua buck hiệu suất 85%, stepper/driver 15 W và logic 2 W, tổng khoảng {budget['total_input_power_estimate_W']:.1f} W / {budget['estimated_input_current_A']:.2f} A ở 12 V, dưới 60 W danh định. **Chưa đo dòng, sụt áp, nhiệt hoặc quá độ; nhãn 5 A của nguồn/buck chưa thay phép đo.**

## Phạm vi bài toán điều khiển

Phần cứng chọn phù hợp cấu trúc một vòng mờ phương vị với MT6701 đo trục anten. Nâng dùng vòng vị trí nội bộ của servo và hiệu chuẩn bằng chuẩn ngoài. Chưa có căn cứ gọi cả hai trục là điều khiển mờ.

Firmware cũ đọc encoder AB/2400 count, chưa tích hợp MT6701. Cần sửa lớp đọc góc, wrap/offset, kiểm tra mất dữ liệu và ramp servo trước khi thử V5. Báo cáo mô phỏng V3 cũ không được dùng làm kết quả bám góc V5. Các chỉ tiêu vọt lố ≤2%, sai số ≤0,5° và giới hạn tốc độ thực chỉ có thể nghiệm thu sau nhận dạng/tinh chỉnh và chạy test thật.

## Các bước vật lý còn lại

1. In dưỡng 20/26/27/28/30 trước; xác nhận trục motor, tai servo, đĩa tròn và lỗ bo.
2. Kiểm tra răng/đai, mặt D, vòng bi và pulley đồng phẳng; siết đai vừa, không ép bi.
3. Gắn nam châm, căn tâm IC và khe thực; quay tay kiểm tra góc đủ vòng, đo tại chuẩn góc và khi cấp điện motor.
4. Kiểm tra mức logic, dòng TB6600, nguồn 7 V servo và 12 V khi chạy đồng thời.
5. Port firmware MT6701; thử từ 5–10°/s, chấm sai số và vọt lố bằng test case, rồi tăng tốc nếu đạt.

Xem README_START_HERE.md để lắp và tái tạo. Các JSON kiểm tra nằm trong audit/ và các file *_validation.json.
'''
(R/'BAO_CAO_KIEM_TRA_V5.md').write_text(report,encoding='utf-8')
if configured_path.exists():
    report+='\n## Preset in đã bổ sung theo máy của người dùng\n\n'
    report+=f"Bambu A1 đầu 0,4 mm, PETG thường, Textured PEI; sáu dự án trong `3MF_A1_PETG_0p4/`, gồm bàn 00 thử dung sai. Tổng 29 loại /43 vật in, giữ nguyên thể tích và kích thước CAD. Tất cả đã tạo được G-code trong Bambu Studio 02.08.02.60 và qua kiểm tra preset đọc lại, chiều cao chi tiết và biên đường in. Dự báo tổng {configured['estimated_total_hours']} giờ /{configured['estimated_total_filament_g']} g; chưa in đo thật.\n\n"
    report+='Chi tiết support và thông số từng nhóm ở `print_profiles/README_A1_PETG.md`, kết quả ở `audit/A1_PETG_print_validation.json`. Bộ năm bàn trung tính cũ vẫn giữ để đối chiếu.\n'
    (R/'BAO_CAO_KIEM_TRA_V5.md').write_text(report,encoding='utf-8')
excludes={'qa_cache','__pycache__'}
files=sorted(p for p in R.rglob('*') if p.is_file() and not any(x in excludes for x in p.relative_to(R).parts) and p.name!='file_manifest.json')
manifest=[dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in files]
write('file_manifest.json',manifest)
dest=R.with_suffix('.zip')
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files+[R/'file_manifest.json']:z.write(p,R.name+'/'+p.relative_to(R).as_posix())
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    for row in manifest:assert hashlib.sha256(z.read(R.name+'/'+row['path'])).hexdigest()==row['sha256']
print(json.dumps(dict(status=status['status'],STL_types=len(expected),print_objects=sum(expected.values()),ZIP=str(dest),ZIP_bytes=dest.stat().st_size),indent=2))
