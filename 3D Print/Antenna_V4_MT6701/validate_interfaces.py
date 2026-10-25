"""Independent exported-solid checks for transmission and adjustable interfaces."""
from pathlib import Path
import sys,json,math,itertools
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[2]/'tmp/cad_runtime'))
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN
P=json.loads((ROOT/'parameters.json').read_text())
def solid(name):return cq.Workplane(obj=cq.Shape.importBrep(str(ROOT/'qa_cache'/f'{name}.brep')))
def cyl(d,h,point,axis=(0,0,1)):
    return cq.Workplane(cq.Plane(origin=point,normal=axis)).circle(d/2).extrude(h)
def nut(af,h,point,axis=(0,0,1)):
    return cq.Workplane(cq.Plane(origin=point,normal=axis)).polygon(6,af/math.cos(math.pi/6)).extrude(h).cut(cyl(2 if af==4 else 3,h,point,axis))
def overlap(a,b):
    x,y=a.val().BoundingBox(),b.val().BoundingBox()
    if any(min(getattr(x,k+'max'),getattr(y,k+'max'))-max(getattr(x,k+'min'),getattr(y,k+'min'))<1e-5 for k in 'xyz'):return 0.
    return max(0.,a.intersect(b).val().Volume())
checks={};failures=[];counts={}
def clear(label,a,b):
    v=overlap(a,b);counts[label]=counts.get(label,0)+1
    if v>.01:failures.append(dict(check=label,intersection_mm3=v))
    return v<=.01

ratio=P['driven_teeth']/P['driver_teeth'];C=P['motor_center_distance']
R=P['driven_teeth']*P['belt_pitch']/(2*math.pi);r=P['driver_teeth']*P['belt_pitch']/(2*math.pi)
def length(c):
    a=math.asin((R-r)/c)
    return 2*math.sqrt(c*c-(R-r)**2)+R*(math.pi+2*a)+r*(math.pi-2*a)
wrap=math.pi-2*math.asin((R-r)/C)
checks['ratio_is_exactly_4_to_1']=ratio==4
checks['belt_pitch_length_matches_280mm']=abs(length(C)-280)<1e-6
checks['small_pulley_engages_at_least_6_teeth']=P['driver_teeth']*wrap/(2*math.pi)>=6
rotor=solid('04_GT2_80T_integrated_rotor')
# Count actual solid/air transitions on a circle through the exported tooth grooves.
probe_radius=R-.254-.40
classifier=BRepClass3d_SolidClassifier(rotor.val().wrapped)
inside=[]
for i in range(720):
    a=i*math.pi/360
    classifier.Perform(gp_Pnt(probe_radius*math.cos(a),probe_radius*math.sin(a),73),1e-6)
    inside.append(classifier.State()==TopAbs_IN or classifier.IsOnAFace())
print('Exported rotor groove count checked',flush=True)
grooves=sum(inside[i] and not inside[(i+1)%len(inside)] for i in range(len(inside)))
checks['exported_rotor_has_80_tooth_grooves']=grooves==80

bridge=solid('03_stepper_tension_bridge');motor=solid('17HS1352_P4130_nominal_envelope')
for dx in (-5,0,5):
    clear('motor_body_and_pilot_in_tension_slots',motor.translate((dx,0,0)),bridge)
    for x,y in itertools.product((-15.5,15.5),repeat=2):
        clear('motor_M3_screws_in_slots',cyl(3,6,(C+x+dx,y,58)),bridge)
checks['motor_nominal_34mm_body_and_20mm_shaft_fit']=not any(q['check'].startswith('motor_') for q in failures)
checks['motor_shaft_engages_pulley_hub_6mm']=min(78,58+P['motor_shaft_length'])-64>=6
carrier=solid('10_LD1501MG_adjustable_carrier')
for pitch,width in itertools.product((45.,47.6,50.),(8.,10.,12.)):
    for sy,sz in itertools.product((-1,1),repeat=2):
        clear('servo_ear_screw_pattern_range',cyl(3,4,(-141,sy*width/2,198.5+sz*pitch/2),(1,0,0)),carrier)
checks['servo_ear_slots_cover_tested_patterns']=not any(q['check']=='servo_ear_screw_pattern_range' for q in failures)
coupler=solid('11_servo_horn_shaft_coupler')
for rad in (6.5,8.5,10.5):
    for sign in (-1,1):
        clear('round_horn_M2_bolt_radial_range',cyl(2,6,(-119,sign*rad,209),(1,0,0)),coupler)
        clear('round_horn_M2_nut_radial_range',nut(4,2,(-115,sign*rad,209),(1,0,0)),coupler)
checks['round_horn_radial_slots_6p5_to_10p5mm']=not any(q['check'].startswith('round_horn_') for q in failures)

pcb_carrier=solid('24_MT6701_XYZ_carrier')
for pitch in (17.5,18.,19.):
    for sx,sy in itertools.product((-1,1),repeat=2):
        x,y=sx*pitch/2,sy*pitch/2
        clear('PCB_screw_pitch_range',cyl(2,6.7,(x,y,-31)),pcb_carrier)
        clear('PCB_floating_nut_pitch_range',nut(4,1.6,(x,y,-30.8)),pcb_carrier)
checks['PCB_slots_and_nuts_accept_17p5_18_19mm_pitch']=not any(q['check'].startswith('PCB_') for q in failures)
pcb_names=['MT6701_23mm_PCB_envelope','MT6701_IC_height_assumption','MT6701_header_body_clearance','MT6701_header_solder_tail_clearance']
sensor_parts=[solid(n) for n in pcb_names]
fixed_bridge=solid('22_MT6701_fixed_bridge');cap=solid('25_rotating_4x2_magnet_cap')
for dx,dy,z in itertools.product((-1.5,0,1.5),(-1.5,0,1.5),(-32.,-31.,-30.5)):
    shift=(dx,dy,z+31)
    for q in [pcb_carrier]+sensor_parts:
        clear('sensor_XYZ_adjustment_clearance',q.translate(shift),fixed_bridge)
        clear('sensor_XYZ_adjustment_clearance',q.translate(shift),cap)
    for x,y in itertools.product((-18,18),repeat=2):
        clear('sensor_M3_adjustment_slots',cyl(3,2.4,(x,y,z)),pcb_carrier.translate(shift))
checks['sensor_adjustment_XY_1p5mm_Z_1p5mm_collision_free']=not any(q['check'].startswith('sensor_') for q in failures)
chip_top=P['sensor_PCB_bottom_z']+P['sensor_PCB_thickness']+P['sensor_chip_height_assumed']
gap=P['sensor_magnet_face_z']-chip_top
checks['nominal_magnet_to_IC_surface_gap_1mm']=abs(gap-1)<1e-8
checks['nominal_PCB_underside_header_tail_clearance']=all(clear('nominal_header_clearance',pcb_carrier,q) for q in sensor_parts[2:])
checks['lowest_fixed_bridge_hardware_above_55mm_foot_ground']=(-43)-(-P['printed_foot_height'])>=10

report=dict(status='PASS_EXPORTED_GEOMETRY' if all(checks.values()) and not failures else 'FAIL',
    checks=checks,intersection_check_counts=counts,failures=failures,ratio=ratio,
    belt_pitch_length_mm=length(C),motor_center_distance_mm=C,
    tension_center_distance_range_mm=[C-5,C+5],belt_length_corresponding_to_tension_endpoints_mm=[length(C-5),length(C+5)],
    small_pulley_wrap_deg=math.degrees(wrap),small_pulley_engaged_teeth=20*wrap/(2*math.pi),
    exported_rotor_grooves_count=grooves,
    full_step_output_deg=1.8/ratio,microstep_output_deg=1.8/(16*ratio),
    STEP_frequency_at_30deg_s=30/(1.8/(16*ratio)),motor_rpm_at_30deg_s=30*ratio/6,
    absolute_sensor_code_resolution_deg=360/16384,nominal_magnet_to_IC_gap_mm=gap,
    sensor_PCB_hole_pitch_from_user_geometry_mm=23-2*(1.5+2/2),
    magnetic_field_strength_of_supplied_4x2mm_magnet_verified=False,
    motor_actual_shaft_diameter_verified=False,physical_fit_verified=False,
    limitations=['Exact 4:1 ratio assumes actual 20T commercial pulley and no tooth slip.',
       'Adjustability tests check listed solid envelopes; they do not measure the actual module or print tolerances.',
       'PCB thickness 1.6mm, IC height 1.7mm and centered IC are assumptions; center the actual IC using XY and set the gap using Z nuts.',
       'Header envelope is at most 3mm high on the IC side; use direct flexible wires or a side-exit right-angle connector. Underside solder tails at most 1.5mm.',
       'Supplied 4x2mm magnet is smaller than the datasheet reference; signal quality and absolute accuracy require physical checks.',
       'Motor shaft diameter 5mm is taken from the drawing, while seller prose says 4.5mm; measure before selecting the pulley bore.',
       'Servo ear pitch is validated over specified patterns, but the actual round horn holes and mounting-axis offset still require the fit gauge.'])
(ROOT/'audit'/'interface_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
assert report['status'].startswith('PASS'), 'See interface_validation.json'
