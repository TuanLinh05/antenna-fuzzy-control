"""Measure the delivered STEP holes and check nominal M4x20 mounting hardware.

This reads exported STEP files independently of the model builder. Units: mm.
It does not establish printed tolerances or the fit of unmeasured real hardware.
"""
from pathlib import Path
import itertools
import json
import math
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2] / 'tmp' / 'cad_runtime'))
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

C = json.loads((ROOT / 'parameters.json').read_text(encoding='utf-8'))['motor_center_distance']
names = ['01_base', '02_azimuth_bearing_tower', '03_stepper_tension_bridge',
         '04_GT2_80T_integrated_rotor', '07_fork_crossbeam',
         '08_right_bearing_arm', '09_left_bearing_arm', '10_LD1501MG_reinforced_carrier']
shapes = {n: cq.importers.importStep(str(ROOT / 'STEP' / (n + '.step'))) for n in names}
cylinders = {}
for name, shape in shapes.items():
    cylinders[name] = []
    for face in shape.val().Faces():
        if face.geomType() != 'CYLINDER':
            continue
        cylinder = BRepAdaptor_Surface(face.wrapped).Cylinder()
        loc, axis = cylinder.Location(), cylinder.Axis().Direction()
        b = face.BoundingBox()
        cylinders[name].append(dict(diameter=cylinder.Radius()*2,
            origin=(loc.X(), loc.Y(), loc.Z()), axis=(axis.X(), axis.Y(), axis.Z()),
            bounds=((b.xmin, b.ymin, b.zmin), (b.xmax, b.ymax, b.zmax))))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def on_axis(cylinder, point, direction):
    delta = tuple(cylinder['origin'][i]-point[i] for i in range(3))
    projection = dot(delta, direction)
    distance = math.sqrt(sum((delta[i]-projection*direction[i])**2 for i in range(3)))
    return abs(abs(dot(cylinder['axis'], direction))-1) < 1e-6 and distance < 1e-5


def cylinder(diameter, length, point, direction):
    return cq.Workplane(cq.Plane(origin=point, normal=direction)).circle(diameter/2).extrude(length)


def intersection_volume(a, b):
    aa, bb = a.val().BoundingBox(), b.val().BoundingBox()
    if any(min(getattr(aa, k+'max'), getattr(bb, k+'max')) <=
           max(getattr(aa, k+'min'), getattr(bb, k+'min')) + 1e-6 for k in 'xyz'):
        return 0.0
    return max(0.0, a.intersect(b).val().Volume())


joints = []


def add(group, point, direction, mates, nut_start, nut_axis, nut_trap=None):
    joints.append(dict(group=group, point=point, direction=direction, mates=mates,
                       nut_start=nut_start, nut_axis=nut_axis, nut_trap=nut_trap))


for x, y in itertools.product((-26, 26), repeat=2):
    add('tower_to_base', (x, y, 3.2), (0, 0, 1), names[0:2], (x, y, 14), (0, 0, 1))
for dx, y in itertools.product((-27, 27), (-35, 35)):
    x = C+dx
    add('bridge_to_base', (x, y, 3.2), (0, 0, 1), [names[0], names[2]], (x, y, 14), (0, 0, 1))
for x, y in itertools.product((-30, 30), (-12, 12)):
    add('crossbeam_to_rotor', (x, y, 97), (0, 0, -1), [names[4], names[3]],
        (x, y, 81), (0, 0, 1), (names[3], (x, y, 81), (0, 0, 1)))
for x, y in itertools.product((-77, 77), (-20, 20)):
    add('arms_to_crossbeam', (x, y, 105), (0, 0, -1),
        [names[5] if x > 0 else names[6], names[4]], (x, y, 89), (0, 0, 1),
        (names[4], (x, y, 89), (0, 0, 1)))
for y, dz in itertools.product((-24, 24), (-40, 17)):
    z = 209+dz
    add('servo_carrier_to_left_arm', (-107, y, z), (1, 0, 0), [names[7], names[6]],
        (-90.2, y, z), (1, 0, 0), (names[6], (-90.5, y, z), (1, 0, 0)))

measured = []
failures = []
for idx, joint in enumerate(joints, 1):
    p, v = joint['point'], joint['direction']
    hole_rows = []
    for mate in joint['mates']:
        if mate=='10_LD1501MG_reinforced_carrier':
            hits=[c for c in cylinders[mate] if abs(c['diameter']-4.4)<1e-5 and
                  abs(abs(dot(c['axis'],v))-1)<1e-6 and abs(c['origin'][1]-p[1])<1e-5 and
                  abs(abs(c['origin'][2]-p[2])-2.5)<1e-5]
            if len(hits)!=2:
                failures.append(dict(joint=idx,part=mate,expected='two slot-end surfaces, width4.4 length9.4',found=len(hits)))
            else:
                hole_rows.append(dict(part=mate,feature_type='vertical_adjustment_slot',width_mm=4.4,length_mm=9.4,
                                      adjustment_each_direction_mm=2.5))
            continue
        hits = [c for c in cylinders[mate] if on_axis(c, p, v) and abs(c['diameter']-4.4) < 1e-5]
        if len(hits) != 1:
            failures.append(dict(joint=idx, part=mate, expected='one coaxial diameter 4.4 mm face', found=len(hits)))
        else:
            hole_rows.append(dict(part=mate, diameter_mm=round(hits[0]['diameter'], 6), bounds_mm=hits[0]['bounds']))
    head_start = tuple(p[i]-4*v[i] for i in range(3))
    bolt = cylinder(4, 20, p, v).union(cylinder(7, 4, head_start, v))
    np, nv = joint['nut_start'], joint['nut_axis']
    nut = cq.Workplane(cq.Plane(origin=np, normal=nv)).polygon(6, 7/math.cos(math.pi/6)).extrude(3.2)
    nut = nut.cut(cylinder(4, 3.2, np, nv))
    collisions = []
    for name, shape in shapes.items():
        for kind, hardware in [('bolt_and_head', bolt), ('nut', nut)]:
            volume = intersection_volume(shape, hardware)
            if volume > .02:
                collisions.append(dict(part=name, hardware=kind, volume_mm3=round(volume, 6)))
    failures.extend(dict(joint=idx, **r) for r in collisions)
    nut_interval = sorted([dot(tuple(np[i]-p[i] for i in range(3)), v),
                           dot(tuple(np[i]+3.2*nv[i]-p[i] for i in range(3)), v)])
    engagement = max(0, min(20, nut_interval[1])-max(0, nut_interval[0]))
    if engagement < 3.2-1e-5:
        failures.append(dict(joint=idx, engagement_mm=engagement))
    trap_check = None
    if joint['nut_trap']:
        name, origin, normal = joint['nut_trap']
        # A slightly undersized 7.3 AF x3.5 gauge verifies the full trap envelope.
        origin = tuple(origin[i]+.001*normal[i] for i in range(3))
        gauge = cq.Workplane(cq.Plane(origin=origin, normal=normal)).polygon(6, 7.298/math.cos(math.pi/6)).extrude(3.498)
        volume = intersection_volume(shapes[name], gauge)
        trap_check = dict(part=name, minimum_clear_AF_mm=7.298, minimum_clear_depth_mm=3.498,
                          interference_mm3=round(volume, 6))
        if volume > .02:
            failures.append(dict(joint=idx, nut_trap=trap_check))
    measured.append(dict(joint=idx, group=joint['group'], holes=hole_rows,
                         nominal_nut_engagement_mm=round(engagement, 6),
                         tip_beyond_nut_mm=round(20-nut_interval[1], 6),
                         nut_trap=trap_check, collisions=collisions))

carrier_bounds=shapes['10_LD1501MG_reinforced_carrier'].val().BoundingBox()
slot_margins=dict(lower_mm=169-6.6-carrier_bounds.zmin,
                  upper_mm=carrier_bounds.zmax-226-6.6,
                  side_mm=carrier_bounds.ymax-24-4.1)
if min(slot_margins['lower_mm'],slot_margins['upper_mm'])<5 or slot_margins['side_mm']<2.5:
    failures.append(dict(carrier_slot_edge_margins_mm=slot_margins))
head_recesses = [c for c in cylinders[names[0]] if abs(c['diameter']-8.2) < 1e-5]
if len(head_recesses) != 8 or any(abs(c['bounds'][1][2]-c['bounds'][0][2]-3.2) > 1e-5 for c in head_recesses):
    failures.append(dict(head_recesses='expected eight diameter 8.2 x3.2 mm recesses'))
previous = json.loads((ROOT/'fastener_validation.json').read_text(encoding='utf-8'))
report = dict(status='PASS' if not failures else 'FAIL', inspected_source='Delivered part STEP files',
              screw='M4x20 DIN912, nominal head diameter 7 mm and height 4 mm',
              joint_count=len(joints), measured_coaxial_hole_count=sum(len(r['holes']) for r in measured),
              base_head_recess_count=len(head_recesses), base_head_protrusion_mm=.8,
              printed_foot_height_mm=55, carrier_slot_edge_margins_mm=slot_margins,
              nut='Standard M4 hex nut, nominal AF7 x3.2 mm',
              existing_assembly_fastener_validation=previous['status'],
              remaining_screws=previous['bolt_counts'], joints=measured, failures=failures,
              limitations=['CAD dimensions only; no physical print or thread inspection.',
                           'Nut engagement uses nominal 3.2 mm thickness; tip chamfer and tolerances are not modeled.',
                           'The base heads project 0.8 mm below the plate and require the supplied 55 mm printed feet.',
                           'M4 clearance holes require separate nuts; they are not tapped plastic holes.'])
(ROOT/'m4_audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ('joints', 'remaining_screws', 'limitations')}, indent=2))
if failures:
    sys.exit(1)
