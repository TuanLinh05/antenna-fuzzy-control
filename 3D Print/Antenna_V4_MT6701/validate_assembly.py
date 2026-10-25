"""CAD solid intersection checks; intentional mating surfaces have zero volume.
Hardware envelopes and the visual belt do not model tolerances / threads / electronics.
"""
from pathlib import Path
import json,sys,itertools,math
ROOT=Path(__file__).resolve().parent
runtime=ROOT.parents[2]/'tmp'/'cad_runtime'
if runtime.exists():sys.path.insert(0,str(runtime))
import cadquery as cq
data=json.loads((ROOT/'preview'/'mesh_data.json').read_text(encoding='utf-8'))
objects=[]
for row in data:
    if row['name'].endswith('_belt_PITCH_ENVELOPE'):continue
    row['shape']=cq.Workplane(obj=cq.Shape.importBrep(str(ROOT/'qa_cache'/f"{row['name']}.brep")))
    objects.append(row)
def position(row,a):
    s=row['shape']
    if row['group']=='elevation_local':return s.translate((0,0,-8)).rotate((0,0,0),(1,0,0),a-90).translate((0,0,209))
    if row['group']=='elevation_world':return s.rotate((0,0,209),(1,0,209),a)
    return s
def overlap(s,t):
    a,b=s.val().BoundingBox(),t.val().BoundingBox()
    for dim in ('x','y','z'):
        if min(getattr(a,dim+'max'),getattr(b,dim+'max'))-max(getattr(a,dim+'min'),getattr(b,dim+'min'))<.0001:return 0.
    v=s.intersect(t).val().Volume()
    return max(0.,float(v))
bad=[];count=0;maximum=0.
for i,j in itertools.combinations(objects,2):
    v=overlap(position(i,35),position(j,35));count+=1;maximum=max(maximum,v)
    if v>.02:bad.append(dict(angle=35,part_a=i['name'],part_b=j['name'],intersection_mm3=round(v,4)))
moving=[i for i in objects if i['group'] in ('elevation_local','elevation_world')]
frame=[i for i in objects if i['group'] not in ('elevation_local','elevation_world')]
for angle in range(0,181,15):
    for i,j in itertools.product(moving,frame):
        v=overlap(position(i,angle),position(j,angle));count+=1
        if v>.02:bad.append(dict(angle=angle,part_a=i['name'],part_b=j['name'],intersection_mm3=round(v,4)))
    print('SWEEP',angle,flush=True)
rotor=[i for i in objects if i['group']!='fixed'];fixed=[i for i in objects if i['group']=='fixed']
for angle in range(0,361,30):
    for i,j in itertools.product(rotor,fixed):
        rotated=position(i,35).rotate((0,0,0),(0,0,1),angle)
        v=overlap(rotated,position(j,35));count+=1
        if v>.02:bad.append(dict(azimuth=angle,part_a=i['name'],part_b=j['name'],intersection_mm3=round(v,4)))
    print('AZIMUTH',angle,flush=True)
report=dict(status='PASS' if not bad else 'FAIL',intersection_checks=count,elevation_samples_deg=list(range(0,181,15)),azimuth_samples_deg=list(range(0,361,30)),maximum_at_35_deg_mm3=round(maximum,5),failures=bad,limitations=['Discrete samples, not a continuous swept-volume proof.','No physical fit, backlash, loaded servo travel, or print verification.','Belt mesh is a visual pitch-line envelope and excluded from solid intersection checks.','Screw bodies and nuts are not in the assembly CAD; fastener lengths were separately checked.'])
(ROOT/'assembly_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
if bad:sys.exit(1)
