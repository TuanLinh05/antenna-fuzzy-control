"""Neutral 3MF plates, units mm, no slicer profile or G-code."""
from pathlib import Path
import sys,math,json,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
runtime=ROOT.parents[2]/'tmp'/'cad_runtime'
if runtime.exists():sys.path.insert(0,str(runtime))
import numpy as np,trimesh
from scipy.spatial import ConvexHull
plates={
 'Plate_01_base_crossbeam':[(1,128,87,0),(7,128,200,0),(5,14,190,0),(5,14,216,0)],
 'Plate_02_dish_cradle_feed_arms':[(12,92,92,0),(13,98,207,0),(14,218,51,90),(14,218,132,90),(14,218,213,90)],
 'Plate_03_drive_and_servo_mounts':[(8,79,45,0),(9,79,111,0),(2,53,198,0),(3,199,42,0),(10,199,105,0),(4,196,204,0),(11,131,235,0)],
 'Plate_04_fit_test_and_feed_hub':[(16,67,48,0),(17,65,91,0),(15,138,55,0),(18,130,103,0),(18,171,103,0),(19,28,143,0),(19,64,143,0),(19,100,143,0),(19,136,143,0),(20,195,177,0),(5,14,108,0),(21,30,181,0),(21,46,181,0),(21,62,181,0),(21,78,181,0),(21,30,198,0),(21,46,198,0),(21,62,198,0)],
 'Plate_05_encoder_and_D_shaft_gauge':[(22,65,65,0),(23,137,46,90)]}
out=ROOT/'3MF_plates';out.mkdir(exist_ok=True)
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
checks=[]
def separation(a,b):
    # Separating-axis distance of convex XY footprints; touching is permitted.
    gaps=[]
    for hull in (a,b):
        for v,w in zip(hull,np.roll(hull,-1,axis=0)):
            edge=w-v;axis=np.array([-edge[1],edge[0]]);axis/=np.linalg.norm(axis)
            pa,pb=a@axis,b@axis
            gaps.append(max(pb.min()-pa.max(),pa.min()-pb.max()))
    return max(gaps)
for plate,entries in plates.items():
    model=ET.Element('{'+ns+'}model',unit='millimeter');res=ET.SubElement(model,'{'+ns+'}resources');build=ET.SubElement(model,'{'+ns+'}build');footprints=[]
    for idx,(num,x,y,angle) in enumerate(entries,1):
        p=next((ROOT/'STL').glob(f'{num:02d}_*.stl'));m=trimesh.load_mesh(p)
        a=math.radians(angle);rot=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
        m.vertices=m.vertices@rot.T+np.array([x,y,0])
        assert m.bounds[0,0]>=0 and m.bounds[0,1]>=0 and m.bounds[1,0]<=256 and m.bounds[1,1]<=256, (plate,p.name,m.bounds)
        obj=ET.SubElement(res,'{'+ns+'}object',id=str(idx),type='model',name=p.stem)
        me=ET.SubElement(obj,'{'+ns+'}mesh');vv=ET.SubElement(me,'{'+ns+'}vertices');ff=ET.SubElement(me,'{'+ns+'}triangles')
        for v in m.vertices:ET.SubElement(vv,'{'+ns+'}vertex',x=f'{v[0]:.6f}',y=f'{v[1]:.6f}',z=f'{v[2]:.6f}')
        for f in m.faces:ET.SubElement(ff,'{'+ns+'}triangle',v1=str(f[0]),v2=str(f[1]),v3=str(f[2]))
        ET.SubElement(build,'{'+ns+'}item',objectid=str(idx))
        xy=np.unique(m.vertices[:,:2],axis=0);h=xy[ConvexHull(xy).vertices];footprints.append((p.stem,h))
    for i in range(len(footprints)):
        for j in range(i):
            n,a=footprints[i];q,b=footprints[j];gap=separation(a,b)
            assert gap>=-.001,(plate,n,q,gap)
            checks.append(dict(plate=plate,part_a=n,part_b=q,XY_separation_mm=round(float(gap),3)))
    with zipfile.ZipFile(out/f'{plate}.3mf','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
(ROOT/'plate_validation.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
old=ROOT/'Printable_parts_IMPORT_AND_ARRANGE.3mf'
if old.exists():old.unlink()
print('Five non-overlapping A1 print plates exported for V3.',flush=True)
