"""Publish only after all six editable projects have passed actual slicing."""
from pathlib import Path
import csv,hashlib,json,zipfile
R=Path(__file__).resolve().parent
d=json.loads((R/'audit/A1_PETG_print_validation.json').read_text(encoding='utf-8'))
assert d['status']=='PASS_A1_PETG_PROJECTS_AND_TOOLPATHS'
assert (d['project_count'],d['print_objects'],d['STL_types'])==(6,43,29)
with (R/'print_profiles/ESTIMATED_PRINTS.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['project','object_count','estimated_hours','estimated_PETG_g','slicer_warning'])
    for row in d['plates']:
        p=R/'3MF_A1_PETG_0p4'/row['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
        w.writerow([row['file'],row['object_count'],row['estimated_hours'],row['estimated_filament_g'],row['slicer_warning']])
files=sorted((R/'3MF_A1_PETG_0p4').glob('*.3mf'))
files+=[p for p in sorted((R/'print_profiles').glob('*')) if p.name!='print_delivery_manifest.json']
files+=[R/'audit/A1_PETG_print_validation.json']
files+=sorted((R/'preview').glob('Plate_*_support.png'))
start=R/'PRINT_START_HERE.md'
start.write_text('# In V5 bằng Bambu A1 0,4 mm / PETG\n\nMở các dự án trong **3MF_A1_PETG_0p4/** bằng Open Project. In **Plate_00_CALIBRATION_FIRST** trước để đo và thử lắp. Tổng cộng sáu dự án, 29 loại /43 vật in, không nhân đôi dưỡng.\n\nXem [thông số, support và cách chốt dung sai](print_profiles/README_A1_PETG.md). Bảng thời gian/nhựa ở [ESTIMATED_PRINTS.csv](print_profiles/ESTIMATED_PRINTS.csv).\n\nSlicer dự báo tổng khoảng **'+str(d['estimated_total_hours'])+' giờ / '+str(d['estimated_total_filament_g'])+' g PETG**; đây là dự báo, chưa có in/đo thật. Các preset ưu tiên bề mặt và vách chịu lực, dùng nhựa PETG thường, Textured PEI. Nhiệt độ và flow vẫn cần khớp cuộn thực tế.\n',encoding='utf-8')
files.append(start)
manifest=[dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,
               sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files if p.is_file()]
(R/'print_profiles/print_delivery_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
manifest_file=R/'print_profiles/print_delivery_manifest.json'
if manifest_file not in files:files.append(manifest_file)
dest=R.parent/'Antenna_V5_A1_PETG_0p4.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:
        if p.is_file():z.write(p,p.relative_to(R).as_posix())
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    for row in manifest:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
print(json.dumps(dict(status='PASS_PRINT_PACKAGE',ZIP=str(dest),ZIP_bytes=dest.stat().st_size,
    estimated_hours=d['estimated_total_hours'],estimated_PETG_g=d['estimated_total_filament_g']),ensure_ascii=False,indent=2))
