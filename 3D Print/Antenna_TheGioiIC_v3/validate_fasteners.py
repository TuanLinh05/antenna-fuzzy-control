"""Check nominal fastener envelopes against CAD, including their heads and nuts.
Threads and the actual servo accessories are not manufacturing-verified.
"""
from pathlib import Path
import sys,json,math,itertools
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[2]/'tmp'/'cad_runtime'))
import cadquery as cq
P=json.loads((ROOT/'parameters.json').read_text())
C=P['motor_center_distance']
rows=json.loads((ROOT/'preview'/'mesh_data.json').read_text())
objects=[]
for q in rows:
    if q['name'].endswith('_belt_PITCH_ENVELOPE'):continue
    q['shape']=cq.Workplane(obj=cq.Shape.importBrep(str(ROOT/'qa_cache'/f"{q['name']}.brep")))
    objects.append(q)
def cylinder(d,l,p,v):return cq.Workplane(cq.Plane(origin=p,normal=v)).circle(d/2).extrude(l)
def hexnut(af,h,p,v,rotation=0):
    s=cq.Workplane(cq.Plane(origin=p,normal=v)).polygon(6,af/math.cos(math.pi/6)).extrude(h)
    if rotation:s=s.rotate(p,tuple(p[i]+v[i] for i in range(3)),rotation)
    return s.cut(cylinder({4:2,5.5:3,7:4}[af],h,p,v))
fast=[];bolt_counts={};mating=[]
def add(name,d,L,p,v,group,nut=None,allowed=(),transform=None):
    head_d={2:4.,3:5.68,4:7.}[d];head_h=float(d)
    head_start=tuple(p[i]-v[i]*head_h for i in range(3))
    s=cylinder(d,L,p,v).union(cylinder(head_d,head_h,head_start,v))
    if transform:s=transform(s)
    fast.append(dict(name=name,shape=s,group=group,allowed=set(allowed)))
    key=f'M{d}x{L}';bolt_counts[key]=bolt_counts.get(key,0)+1
    if nut:
        af,h,np,nv,ang=nut
        s=hexnut(af,h,np,nv,ang)
        if transform:s=transform(s)
        fast.append(dict(name=name+'_nut',shape=s,group=group,allowed=set()))
        mating.append(frozenset((name,name+'_nut')))
def transform_right(s):return s.rotate((0,0,0),(0,1,0),90).translate((99,0,209))
for x,y in itertools.product((-26,26),repeat=2):
    add(f'tower_{x}_{y}',4,20,(x,y,3.2),(0,0,1),'fixed',(7,3.2,(x,y,14),(0,0,1),0))
for dx,y in itertools.product((-27,27),(-35,35)):
    x=C+dx;add(f'bridge_{dx}_{y}',4,20,(x,y,3.2),(0,0,1),'fixed',(7,3.2,(x,y,14),(0,0,1),0))
for x,y in itertools.product((-30,30),(-12,12)):
    add(f'crossbeam_{x}_{y}',4,20,(x,y,97),(0,0,-1),'azimuth',(7,3.2,(x,y,81),(0,0,1),0))
for x,y in itertools.product((-77,77),(-20,20)):
    add(f'arm_{x}_{y}',4,20,(x,y,105),(0,0,-1),'azimuth',(7,3.2,(x,y,89),(0,0,1),0))
for y,dz in itertools.product((-24,24),(-40,17)):
    add(f'carrier_{y}_{dz}',4,20,(-107,y,209+dz),(1,0,0),'azimuth',(7,3.2,(-90.2,y,209+dz),(1,0,0),0))
for x,y in itertools.product((-54,126),(-60,60)):
    add(f'foot_{x}_{y}',3,12,(x,y,4),(0,0,-1),'fixed',(5.5,2.4,(x,y,-7.7),(0,0,1),0))
for label,tf,group in [('lower',lambda s:s.translate((0,0,-2)),'azimuth'),('right',transform_right,'elevation_world')]:
    add(f'collar_{label}',3,16,(8,-7.5,4),(0,1,0),group,(5.5,2.4,(8,4.5,4),(0,1,0),0),transform=tf)
add('rotor_shaft',3,12,(0,-16,100),(0,1,0),'azimuth',(5.5,2.4,(0,-15,100),(0,1,0),0))
for x in (-81,81):
    add(f'cradle_shaft_{x}',3,10,(x,-14,8),(0,1,0),'elevation_local',(5.5,2.4,(x,-12,8),(0,1,0),0))
add('servo_coupler_shaft',3,8,(-108,0,221),(0,0,-1),'elevation_world',(5.5,2.4,(-108,0,219),(0,0,-1),0))
for dx,y in itertools.product((-15.5,15.5),repeat=2):
    add(f'motor_{dx}_{y}',3,10,(C+dx,y,65),(0,0,-1),'fixed',allowed=('SL42STH40_1684A_envelope',))
for x,y in itertools.product((-36,36),(-18,18)):
    add(f'encoder_bracket_{x}_{y}',3,16,(x,y,4.8),(0,0,-1),'fixed',
        (5.5,2.4,(x,y,-6.4),(0,0,1),0))
for a in (90,210,330):
    ar=math.radians(a);x,y=15*math.cos(ar),15*math.sin(ar)
    add(f'encoder_face_{a}',3,8,(x,y,-30),(0,0,-1),'fixed',
        allowed=('LPD3806_600BM_clearance_envelope',))
for y,z in itertools.product((-5,5),(175.2,222.8)):
    add(f'servo_ear_{y}_{z}',3,12,(-141,y,z),(1,0,0),'azimuth',(5.5,2.4,(-134.5,y,z),(1,0,0),0))
for x,y in itertools.product((-18,18),repeat=2):
    add(f'dish_{x}_{y}',3,20,(x,y,3.2),(0,0,-1),'elevation_local',(5.5,2.4,(x,y,-14),(0,0,1),0))
for a in (90,210,330):
    ar=math.radians(a);x,y=74*math.cos(ar),74*math.sin(ar)
    add(f'feed_foot_{a}',3,20,(x,y,29.2),(0,0,-1),'elevation_local',(5.5,2.4,(x,y,10.6),(0,0,1),0))
    x,y=8*math.cos(ar),8*math.sin(ar)
    add(f'feed_hub_{a}',3,12,(x,y,88),(0,0,-1),'elevation_local',(5.5,2.4,(x,y,76.3),(0,0,1),a+30))
for y in (-8.5,8.5):
    add(f'horn_{y}',2,10,(-122,y,209),(1,0,0),'elevation_world',(4,2.,(-115,y,209),(1,0,0),0),allowed=('MG946R_supplied_round_horn_envelope',))
def position(s,g,a,az=0):
    if g=='elevation_local':s=s.translate((0,0,-8)).rotate((0,0,0),(1,0,0),a-90).translate((0,0,209))
    elif g=='elevation_world':s=s.rotate((0,0,209),(1,0,209),a)
    if g!='fixed':s=s.rotate((0,0,0),(0,0,1),az)
    return s
def overlap(s,t):
    a,b=s.val().BoundingBox(),t.val().BoundingBox()
    if any(min(getattr(a,k+'max'),getattr(b,k+'max'))-max(getattr(a,k+'min'),getattr(b,k+'min'))<.0001 for k in 'xyz'):return 0.
    return max(0.,float(s.intersect(t).val().Volume()))
bad=[];count=0
samples=[(35,0)]+[(a,0) for a in range(0,181,30)]+[(35,a) for a in range(30,361,30)]
for sample_idx,(el,az) in enumerate(samples):
    placed=[dict(q,shape=position(q['shape'],q['group'],el,az)) for q in objects+fast]
    for ia,ja in itertools.combinations(range(len(placed)),2):
        if ja<len(objects):continue
        i,j=placed[ia],placed[ja]
        gi='elevation' if i['group'].startswith('elevation_') else i['group']
        gj='elevation' if j['group'].startswith('elevation_') else j['group']
        if sample_idx and gi==gj:continue
        if frozenset((i['name'],j['name'])) in mating:continue
        if i['name'] in j.get('allowed',set()) or j['name'] in i.get('allowed',set()):continue
        v=overlap(i['shape'],j['shape']);count+=1
        if v>.02:bad.append(dict(elevation=el,azimuth=az,part_a=i['name'],part_b=j['name'],intersection_mm3=round(v,4)))
    print('FASTENER SAMPLE',el,az,flush=True)
report=dict(status='PASS' if not bad else 'FAIL',intersection_checks=count,bolt_counts=bolt_counts,failures=bad,limitations=['Nominal DIN912 heads and nominal hex nuts, no thread form.','Motor tapped-hole volumes and prepared holes in the supplied servo horn are intentional mates and excluded.','Real servo horn diameter, thickness and hole locations must be checked before print; M2 through-holes may need opening to 2.2 mm.','Screw pairs and threaded nuts overlap intentionally and are excluded.'])
(ROOT/'fastener_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
if bad:sys.exit(1)
