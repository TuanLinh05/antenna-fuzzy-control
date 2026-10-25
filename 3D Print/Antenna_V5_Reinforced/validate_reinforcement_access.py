"""Assembly access and a transparent V4/V5 beam-section comparison, not FEA."""
from pathlib import Path
import sys,json,math,itertools
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parents[2]/'tmp/cad_runtime'))
import cadquery as cq
import numpy as np
P=json.loads((R/'parameters.json').read_text())
def shape(name):return cq.Workplane(obj=cq.Shape.importBrep(str(R/'qa_cache'/f'{name}.brep')))
def box(dx,dy,dz,p):return cq.Workplane('XY').box(dx,dy,dz,centered=(True,True,False)).translate(p)
def cyl(d,h,p,axis=(0,0,1)):
    return cq.Workplane(cq.Plane(origin=p,normal=axis)).circle(d/2).extrude(h)
def overlap(a,b):
    aa,bb=a.val().BoundingBox(),b.val().BoundingBox()
    if any(min(getattr(aa,k+'max'),getattr(bb,k+'max'))-max(getattr(aa,k+'min'),getattr(bb,k+'min'))<1e-5 for k in 'xyz'):return 0.
    return max(0.,a.intersect(b).val().Volume())
bad=[];counts={}
def clear(label,a,b):
    v=overlap(a,b);counts[label]=counts.get(label,0)+1
    if v>.01:bad.append(dict(check=label,intersection_mm3=v))
carrier=shape('10_LD1501MG_reinforced_carrier')
for y,z in itertools.product((-24,24),(169,226)):
    for dz in (-2.5,0,2.5):
        clear('M4_head_insertion_from_outer_face',cyl(7.5,39,(-146,y,z+dz),(1,0,0)),carrier)
        clear('M4_3mm_hex_key_path',cyl(3.6,68,(-175,y,z+dz),(1,0,0)),carrier)
fixed=shape('22_MT6701_open_U_bridge');tray=shape('24_MT6701_3point_carrier');cap=shape('25_rotating_4x2_magnet_cap')
sensor=[shape(n) for n in ['MT6701_23mm_PCB_envelope','MT6701_IC_height_assumption','MT6701_header_body_clearance','MT6701_header_solder_tail_clearance']]
for x,y in P['sensor_adjustment_stud_points']:
    for z in (-32.2,-27.4):
        # Envelope of a thin 5.5 mm spanner, approaching from the open front.
        tool=cyl(10,1.6,(x,y,z-.8)).cut(cyl(6.5,2,(x,y,z-1)))
        tool=tool.union(box(6,45,1.6,(x,y-24,z-.8)))
        for q in [fixed,tray,cap]+sensor:clear('sensor_nut_tool_access_from_front',tool,q)
moving=[tray]+sensor
for x,y in P['sensor_adjustment_stud_points']:
    stud=cyl(3,25,(x,y,-42)).union(cyl(5.5,3,(x,y,-45)))
    for drop in (-5,-10,-20,-26):
        for obstacle in [fixed,tray,cap]+sensor:
            clear('sensor_stud_withdrawal_nuts_removed',stud.translate((0,0,drop)),obstacle)
for x,y in itertools.product((-9,9),repeat=2):
    bolt=cyl(2,8,(x,y,-22.7),(0,0,-1)).union(cyl(4,2,(x,y,-22.7)))
    moving.append(bolt)
    moving.append(cq.Workplane('XY').polygon(6,4/math.cos(math.pi/6)).extrude(1.6).translate((x,y,-30.8)))
for drop in (-1,-2,-3):
    for q in moving:
        clear('tray_lowering_after_three_studs_removed',q.translate((0,0,drop)),fixed)
        clear('tray_lowering_after_three_studs_removed',q.translate((0,0,drop)),cap)
for dy in (-5,-10,-20,-35,-55):
    for q in moving:
        clear('tray_front_removal_path',q.translate((0,dy,-3)),fixed)
        clear('tray_front_removal_path',q.translate((0,dy,-3)),cap)
pts=np.array(P['sensor_adjustment_stud_points']);u=pts[1]-pts[0];v=pts[2]-pts[0]
area=abs(float(u[0]*v[1]-u[1]*v[0]))/2
assert len(pts)==3 and area>100
access=dict(status='PASS_ACCESS_ENVELOPES' if not bad else 'FAIL',counts=counts,failures=bad,
    sensor_support_points_mm=pts.tolist(),support_triangle_area_mm2=area,
    removal_sequence=['Switch off motion power; support the tray.',
      'Securely raise/support the assembly to leave at least 30mm below the M3 stud heads for withdrawal; the feet alone leave only 10mm.',
      'Remove all three M3x25 studs and their nuts while holding the tray.',
      'Lower tray by 3mm and slide toward negative Y through the open front.',
      'Install/service PCB and M2 screws with tray outside; reinstall, align IC and reset the gap.'],
    limitations=['Tool paths use stated envelopes, not every available screwdriver or spanner.',
      'Stud withdrawal assumes at least 30mm clearance below the screw heads; the 55mm feet alone do not provide it.',
      'PCB dimensions/connector envelopes and print tolerances still require physical fit checks.'])
(R/'audit'/'access_validation.json').write_text(json.dumps(access,indent=2),encoding='utf-8')
print('Access envelopes:',access['status'],counts,flush=True)

# Compare area moments of inertia of real CAD cross-sections along the cantilever.
# Both versions are referenced to the unchanged x=-137 face and x=-97 arm side.
v4=R/'reference'/'V4_servo_carrier.step'
old=cq.importers.importStep(str(v4))
rows=[];t=.2
for x in np.linspace(-136.5,-97.5,27):
    data={}
    for name,q in [('V4',old),('V5',carrier)]:
        sl=q.intersect(box(t,90,100,(x,0,150)))
        m=np.array(cq.Shape.matrixOfInertia(sl.val()));center=sl.val().Center();b=sl.val().BoundingBox()
        data[name]=dict(area_mm2=sl.val().Volume()/t,Iy_mm4=m[1,1]/t,Iz_mm4=m[2,2]/t,
            cZ_mm=max(b.zmax-center.z,center.z-b.zmin),cY_mm=max(b.ymax-center.y,center.y-b.ymin))
    rows.append(dict(x_mm=float(x),**data))
    print('SECTION',round(float(x),1),flush=True)
F=20.;E=1000.;est={}
for name in ('V4','V5'):
    distances=np.array([q['x_mm']+137 for q in rows]);result={}
    for axis,Ikey,ckey in [('force_Z','Iy_mm4','cZ_mm'),('force_Y','Iz_mm4','cY_mm')]:
        ii=np.array([q[name][Ikey] for q in rows]);cc=np.array([q[name][ckey] for q in rows])
        values=distances**2/ii
        integral=float(np.sum((values[1:]+values[:-1])*.5*np.diff(distances)))
        result[axis]=dict(approx_tip_deflection_mm=float(F/E*integral),
                          max_nominal_bending_stress_MPa=float(np.max(F*distances*cc/ii)))
    est[name]=result
ratios={a:est['V4'][a]['approx_tip_deflection_mm']/est['V5'][a]['approx_tip_deflection_mm'] for a in ('force_Z','force_Y')}
strength=dict(status='PASS_SECTION_STIFFNESS_COMPARISON' if min(ratios.values())>1 else 'FAIL',
    servo_face_thickness_mm={'V4':4,'V5':8},side_beam_width_mm={'V4':10,'V5':16},
    added_top_and_bottom_cross_ties_mm=8,estimated_stiffness_ratio_V5_over_V4=ratios,
    comparison_force_N=F,assumed_effective_E_MPa=E,beam_length_mm=40,
    estimates=est,cross_section_samples=rows,physical_strength_tested=False,FEA_performed=False,
    limitations=['Euler-Bernoulli cantilever approximation using sampled CAD section inertias, not a full frame or joint FEA.',
      'Anisotropic print strength, layer separation, stress concentration, bolt preload and plate flexure are not included.',
      'The selected 20N static comparison is an illustrative design load, not an impact rating or a proof-load certificate.'])
(R/'audit'/'reinforcement_validation.json').write_text(json.dumps(strength,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in strength.items() if k!='cross_section_samples'},indent=2),flush=True)
assert not bad and strength['status'].startswith('PASS')
