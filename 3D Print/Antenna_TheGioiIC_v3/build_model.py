"""Parametric desktop antenna demonstrator. Units: mm. Requires CadQuery + trimesh.
Original 3MF remains untouched. Hardware envelopes are nominal, not manufacturing drawings.
GT2 groove coordinates: droftarts (2012), rbuckland/openscad.parametric-pulley.
"""
from pathlib import Path
import math, json, sys, csv, zipfile, itertools
ROOT = Path(__file__).resolve().parent
runtime = ROOT.parents[2] / 'tmp' / 'cad_runtime'
if runtime.exists(): sys.path.insert(0, str(runtime))
import cadquery as cq
import numpy as np
import trimesh

P = dict(dish_diameter=160., focal_length=80., dish_wall=2.4,
         bearing_seat=22.2, shaft_clearance=8.2, m3_clearance=3.3,
         m4_clearance=4.4, driven_teeth=80, driver_teeth=20,
         belt_pitch=2., belt_length=280., belt_width=6., elevation_axis_z=209.,
         motor_body_length=40., motor_shaft_length=20., servo_model='MG946R',
         servo_window_width=21.4, horn_hole_min_radius=6.5, horn_hole_max_radius=10.5,
         printed_foot_height=90., azimuth_shaft_length=120., azimuth_shaft_bottom=-14.,
         d_socket_flat_offset=3.7, steel_flat_offset=3.5,
         encoder_ppr=600, encoder_count_multiplier=4, encoder_body_clearance_length=45.)
R = P['driven_teeth']*P['belt_pitch']/(2*math.pi)
r = P['driver_teeth']*P['belt_pitch']/(2*math.pi)
def belt_length(c):
    a=math.asin((R-r)/c)
    return 2*math.sqrt(c*c-(R-r)**2)+R*(math.pi+2*a)+r*(math.pi-2*a)
lo,hi=R-r+1,200
for _ in range(60):
    mid=(lo+hi)/2
    if belt_length(mid)<P['belt_length']:lo=mid
    else:hi=mid
C=(lo+hi)/2
P['motor_center_distance']=C

def box(x,y,z,at):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate(at)
def cyl(d,h,at=(0,0,0)):return cq.Workplane('XY').circle(d/2).extrude(h).translate(at)
def axis_cyl(d,length,start,axis):
    return cq.Workplane(cq.Plane(origin=start,normal=axis)).circle(d/2).extrude(length)
def hexcut(af,h,start,axis=(0,0,1)):
    return cq.Workplane(cq.Plane(origin=start,normal=axis)).polygon(6,af/math.cos(math.pi/6)).extrude(h)
def hole(s,d,h,start,axis=(0,0,1)):return s.cut(axis_cyl(d,h,start,axis))

def d_hole(s,d,h,start,axis,flat_normal,offset=3.7):
    # Positive mechanical drive: the steel shaft must have a matching filed flat.
    p=tuple(start[i]+offset*flat_normal[i] for i in range(3))
    half=cq.Workplane(cq.Plane(origin=p,normal=flat_normal)).rect(150,150).extrude(150)
    return s.cut(axis_cyl(d,h,start,axis).cut(half))
def slot_xy(length,width,z,h,x,y,angle=0):
    return cq.Workplane('XY').slot2D(length,width,angle).extrude(h).translate((x,y,z))
def normalized(s):
    b=s.val().BoundingBox()
    return s.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))
def elev(s,a):
    return s.translate((0,0,-8)).rotate((0,0,0),(1,0,0),a-90).translate((0,0,P['elevation_axis_z']))
parts={}; instances=[]
def add(name,shape,color,group='azimuth',print_shape=None,qty=1):
    print('BUILD',name,flush=True)
    assert shape.val().isValid(),name+' invalid CAD'
    assert len(shape.solids().vals())==1,name+' disconnected CAD'
    parts[name]=dict(shape=shape,print_shape=normalized(print_shape if print_shape is not None else shape),color=color,group=group,qty=qty)
def inst(name,shape=None,group=None,label=None):
    p=parts[name]
    instances.append(dict(name=label or name,shape=shape if shape is not None else p['shape'],color=p['color'],group=group or p['group'],printed=True))
def hardware(name,s,color='#8a99a7',group='azimuth'):
    instances.append(dict(name=name,shape=s,color=color,group=group,printed=False))

# Fixed base. Holes have recessed screw heads on underside.
s=box(208,146,8,(36,0,0)).edges('|Z').fillet(10)
for x,y in itertools.product((-26,26),repeat=2):
    s=hole(s,4.4,10,(x,y,-1));s=hole(s,8.2,3.2,(x,y,0))
for dx,y in itertools.product((-27,27),(-35,35)):
    s=hole(s,4.4,10,(C+dx,y,-1));s=hole(s,8.2,3.2,(C+dx,y,0))
for x,y in itertools.product((-54,126),(-60,60)):
    s=hole(s,3.3,10,(x,y,-1));s=hole(s,6.3,4,(x,y,4))
for x,y in itertools.product((-36,36),(-18,18)):
    s=hole(s,3.3,10,(x,y,-1));s=hole(s,6.3,3.3,(x,y,4.8))
s=hole(s,13,10,(0,0,-1));s=hole(s,32,6,(0,0,0))
add('01_base',s,'#263c50','fixed');inst('01_base')

# Two 608 bearing seats inserted from opposite ends; outer races bear against 19 mm shoulders.
s=cyl(84,6,(0,0,8)).union(cyl(40,58,(0,0,8)))
s=hole(s,19,60,(0,0,7))
s=hole(s,P['bearing_seat'],7.05,(0,0,8))
s=hole(s,P['bearing_seat'],7.05,(0,0,58.95))
for x,y in itertools.product((-26,26),repeat=2):s=hole(s,4.4,8,(x,y,7))
add('02_azimuth_bearing_tower',s,'#3f6579','fixed');inst('02_azimuth_bearing_tower')

# NEMA17 bridge: front face z58; fits bodies up to 48 mm, slots allow +/-5 mm tension adjustment.
s=box(70,64,6,(C,0,58))
for y in (-27,27):
    s=s.union(box(70,8,50,(C,y,8)))
for y in (-34,34):s=s.union(box(70,12,6,(C,y,8)))
s=s.cut(slot_xy(32.8,22.8,57,8,C,0))
for dx,y in itertools.product((-15.5,15.5),repeat=2):s=s.cut(slot_xy(13.3,3.3,57,8,C+dx,y))
for dx,y in itertools.product((-27,27),(-35,35)):s=hole(s,4.4,8,(C+dx,y,7))
add('03_stepper_tension_bridge',s,'#3f6579','fixed',s.rotate((C,0,8),(C+1,0,8),90));inst('03_stepper_tension_bridge')

# GT2 2 mm pitch, groove depth 0.76447, pitch-line differential 0.254 mm.
# Width expanded 0.10 mm for an initial FDM prototype; coupon validates belt engagement.
groove=[(.747183,-.5),(.747183,0),(.647876,.037218),(.598311,.130528),(.578556,.238423),(.547158,.343077),(.504649,.443762),(.451556,.53975),(.358229,.636924),(.2484,.707276),(.127259,.750044),(0,.76447),(-.127259,.750044),(-.2484,.707276),(-.358229,.636924),(-.451556,.53975),(-.504649,.443762),(-.547158,.343077),(-.578556,.238423),(-.598311,.130528),(-.647876,.037218),(-.747183,0),(-.747183,-.5)]
od=2*R-.508
s=cyl(od,7,(0,0,69.5))
cuts=[]
for i in range(P['driven_teeth']):
    pts=[(x*(1+.10/1.494),od/2-y) for x,y in groove]
    cuts.append(cq.Workplane('XY').polyline(pts).close().extrude(7.2).translate((0,0,69.4)).rotate((0,0,0),(0,0,1),i*360/P['driven_teeth']).val())
s=s.cut(cq.Compound.makeCompound(cuts))
s=s.union(cyl(od+4,1.5,(0,0,68))).union(cyl(od+4,1.5,(0,0,76.5))).union(cyl(30,3,(0,0,78)))
s=hole(s,P['shaft_clearance'],15,(0,0,67))
# Keep this solid until the table is added: the rotor is ONE printed part in V2.
pulley=s

# Narrow inner-race-only bearing spacers, one per azimuth bearing.
sp=cyl(11.5,2).cut(cyl(P['shaft_clearance'],2))
add('05_bearing_spacer',sp,'#e0a04c',qty=3)
inst('05_bearing_spacer',sp.translate((0,0,66)),label='upper_bearing_spacer')
inst('05_bearing_spacer',sp.translate((0,0,6)),label='lower_bearing_spacer')
inst('05_bearing_spacer',sp.rotate((0,0,0),(0,1,0),90).translate((97,0,209)),label='right_elevation_inner_race_spacer')

s=cyl(96,8,(0,0,81)).union(cyl(30,16,(0,0,89))).union(pulley)
s=hole(s,P['shaft_clearance'],9,(0,0,80))
s=d_hole(s,P['shaft_clearance'],18,(0,0,89),(0,0,1),(0,1,0))
for x,y in itertools.product((-30,30),(-12,12)):
    s=hole(s,4.4,10,(x,y,80));s=s.cut(hexcut(7.3,3.5,(x,y,81)))
# Radial M3 nut trap and screw against flat on shaft; shaft rotates with turntable.
s=hole(s,3.3,18,(0,-16,100),(0,1,0));s=s.cut(hexcut(5.8,3.2,(0,-15,100),(0,1,0)))
add('04_GT2_80T_integrated_rotor',s,'#e0a04c');inst('04_GT2_80T_integrated_rotor')

s=box(208,60,8,(0,0,89)).edges('|Z').fillet(5)
s=hole(s,32,10,(0,0,88))
for x,y in itertools.product((-30,30),(-12,12)):s=hole(s,4.4,10,(x,y,88))
for x,y in itertools.product((-77,77),(-20,20)):
    s=hole(s,4.4,10,(x,y,88));s=s.cut(hexcut(7.3,3.5,(x,y,89)))
add('07_fork_crossbeam',s,'#3f6579');inst('07_fork_crossbeam')

def arm(left=False):
    s=box(32,60,8,(81,0,97)).union(box(10,60,136,(92,0,97)))
    # Empty upper part above elevation centre is retained for servo carrier screws.
    s=hole(s,19,12,(86,0,209),(1,0,0))
    s=hole(s,P['bearing_seat'],7.05,(89.95,0,209),(1,0,0))
    for y in (-20,20):s=hole(s,4.4,10,(77,y,96))
    if left:
        for y,dz in itertools.product((-24,24),(-40,17)):
            s=hole(s,4.4,12,(86,y,209+dz),(1,0,0))
            s=s.cut(hexcut(7.3,3.5,(87,y,209+dz),(1,0,0)))
        s=s.mirror('YZ',union=False)
    return s
s=arm();add('08_right_bearing_arm',s,'#3f6579',print_shape=s.rotate((0,0,0),(0,1,0),90));inst('08_right_bearing_arm')
s=arm(True);add('09_left_bearing_arm',s,'#3f6579',print_shape=s.rotate((0,0,0),(0,1,0),-90));inst('09_left_bearing_arm')

# MG946R carrier. Nominal ear-hole pattern 47.6 x10; shop body 40 x19 x43.
# Front servo face x=-126, output axis z209. The mounting plate supports the ears only.
s=box(4,58,78,(-139,0,159))
s=s.cut(box(6,P['servo_window_width'],41.5,(-139,0,178.25)))
for z in (175.2,222.8):
    for y in (-5,5):
        cut=cq.Workplane('YZ').slot2D(9.3,3.3,90).extrude(6).translate((-142,y,z))
        s=s.cut(cut)
for y in (-24,24):
    s=s.union(box(40,10,78,(-117,y,159)))
    for dz in (-40,17):
        cut=cq.Workplane('YZ').slot2D(9.4,4.4,90).extrude(46).translate((-142,y,209+dz))
        s=s.cut(cut)
        # Open screw access pocket: head bears at x=-107; M4x20 reaches the arm nut.
        s=s.cut(box(34,10,20,(-124,y,209+dz-10)))
# Cable notch at bottom of carrier; preserves mounting ribs.
s=s.cut(box(6,9,7,(-139,0,162)))
add('10_MG946R_short_screw_carrier',s,'#e0a04c',print_shape=s.rotate((0,0,0),(0,1,0),-90));inst('10_MG946R_short_screw_carrier')

# Coupler is printable round-disc adapter, NOT an imitation of the servo spline.
s=axis_cyl(36,4,(-119,0,209),(1,0,0)).union(axis_cyl(20,14,(-115,0,209),(1,0,0)))
s=d_hole(s,P['shaft_clearance'],14.05,(-115.05,0,209),(1,0,0),(0,0,-1));s=hole(s,6.5,5,(-119.5,0,209),(1,0,0))
for a in (0,90,180,270):
    # M2 through-bolts into the supplied round horn; no uncertain extra spline part.
    c0=8.5;yy=c0*math.cos(math.radians(a));zz=209+c0*math.sin(math.radians(a))
    s=s.cut(cq.Workplane('YZ').slot2D(6.2,2.2,a).extrude(8).translate((-119.5,yy,zz)))
    # A radial open nut pocket allows nuts to follow the adjustable hole radius.
    s=s.cut(cq.Workplane('YZ').slot2D(8.5,4.8,a).extrude(2.8).translate((-115,yy,zz)))
s=hole(s,3.3,12,(-108,0,220),(0,0,-1));s=s.cut(hexcut(5.8,3.2,(-108,0,219),(0,0,-1)))
add('11_servo_horn_shaft_coupler',s,'#e0a04c','elevation_world',s.rotate((0,0,0),(0,1,0),-90));inst('11_servo_horn_shaft_coupler')

# Parabolic reflector: exact quadratic Bezier z=r^2/(4f), with reinforced fastening bosses.
rad=P['dish_diameter']/2; f=P['focal_length']; t=P['dish_wall']
s=cq.Workplane('XZ').moveTo(0,-t).bezier([(rad/2,-t),(rad,rad*rad/(4*f)-t)],includeCurrent=True).lineTo(rad,rad*rad/(4*f)).bezier([(rad/2,0),(0,0)],includeCurrent=True).close().revolve(360,(0,0),(0,1))
for x,y in itertools.product((-18,18),repeat=2):s=s.union(cyl(10,11.2,(x,y,-8)))
feed_angles=(90,210,330)
for a in feed_angles:
    x,y=74*math.cos(math.radians(a)),74*math.sin(math.radians(a))
    s=s.union(cyl(11,9,(x,y,13)));s=hole(s,3.3,12,(x,y,12))
for x,y in itertools.product((-18,18),repeat=2):s=hole(s,3.3,15,(x,y,-9))
add('12_parabolic_dish_160mm',s,'#e0e9ed','elevation_local');inst('12_parabolic_dish_160mm')

# Cradle bridges behind reflector. Socket axes coincide with the two 608 inner races.
s=box(60,48,6,(0,0,-14)).union(box(170,20,8,(0,0,-14)))
for x in (-81,81):
    s=s.union(box(8,24,29,(x,0,-14)))
    s=d_hole(s,P['shaft_clearance'],12,(x-6,0,8),(1,0,0),(0,1,0))
    s=hole(s,3.3,15,(x,-13,8),(0,1,0));s=s.cut(hexcut(5.8,3.2,(x,-12,8),(0,1,0)))
for x,y in itertools.product((-18,18),repeat=2):
    s=hole(s,3.3,8,(x,y,-15));s=s.cut(hexcut(5.8,2.7,(x,y,-14)))
add('13_dish_cradle',s,'#3f6579','elevation_local');inst('13_dish_cradle')

# Three equal feed struts: radial-normal plane, tangential thickness 8; print on side.
poly=[(70,22),(80,22),(80,26),(75,28),(13,78),(13,84),(5,84),(5,76),(9,76),(70,25)]
s=cq.Workplane('XZ').polyline(poly).close().extrude(4,both=True)
s=s.union(cyl(8,3.2,(74,0,26)))
s=hole(s,3.3,14,(74,0,20))
s=hole(s,6.3,6,(74,0,29.2))
s=hole(s,3.3,12,(8,0,74))
s=s.cut(hexcut(5.8,2.7,(8,0,76)).rotate((8,0,0),(8,0,1),30))
add('14_feed_strut',s,'#e0e9ed','elevation_local',s.rotate((0,0,0),(1,0,0),90),qty=3)
for a in feed_angles:inst('14_feed_strut',s.rotate((0,0,0),(0,0,1),a),label=f'feed_strut_{a}')
s=cyl(28,13,(0,0,75)).cut(cyl(8,10,(0,0,75))).union(cyl(8,11,(0,0,88)))
for a in feed_angles:
    s=s.cut(box(10.6,8.4,9.2,(10.3,0,74.9)).rotate((0,0,0),(0,0,1),a))
    ar=math.radians(a)
    s=hole(s,3.3,16,(8*math.cos(ar),8*math.sin(ar),74))
add('15_feed_hub',s,'#e0a04c','elevation_local');inst('15_feed_hub')

# Fit coupons are intended to be printed BEFORE the full model.
s=box(84,30,9,(0,0,0))
for x,d in zip((-27,0,27),(22.,22.2,22.4)):
    s=hole(s,d,7,(x,0,2));s=hole(s,8.2,10,(x,0,-.5))
add('16_608_fit_coupon',s,'#e0a04c','coupon')
s=box(42,16,8,(0,0,0))
for x,d in zip((-13,0,13),(8.,8.2,8.4)):s=hole(s,d,10,(x,0,-1))
add('17_shaft_fit_coupon',s,'#e0a04c','coupon')

# Printed split collars replace unavailable commercial 8mm collars.
# M3x16 across the slit, standard M3 nut, no set-screw thread cut into plastic.
s=cyl(24,8).union(box(10,5,8,(8,-5,0))).union(box(10,5,8,(8,5,0)))
s=hole(s,P['shaft_clearance'],10,(0,0,-1));s=s.cut(box(15,1.2,10,(7.5,0,-1)))
s=hole(s,3.3,20,(8,-10,4),(0,1,0));s=s.cut(hexcut(5.8,3.2,(8,4.5,4),(0,1,0)))
s=hole(s,6.3,4.5,(8,-12,4),(0,1,0))
add('18_printed_split_shaft_collar',s,'#e0a04c',qty=2)
inst('18_printed_split_shaft_collar',s.translate((0,0,-2)),label='printed_azimuth_lower_collar')
inst('18_printed_split_shaft_collar',s.rotate((0,0,0),(0,1,0),90).translate((99,0,209)),group='elevation_world',label='printed_right_elevation_collar')

# Raised feet provide room for the independently supported output encoder.
# The nut enters through a narrow side slot near the top; no long screw is needed.
s=cyl(32,P['printed_foot_height']-10,(0,0,-P['printed_foot_height'])).union(cyl(20,10,(0,0,-10)))
s=hole(s,3.3,12,(0,0,-11));s=s.cut(hexcut(5.8,2.7,(0,0,-7.7)))
s=s.cut(box(18,6.,2.7,(9,0,-7.7)))
add('19_bolted_printed_foot',s,'#263c50','fixed',qty=4)
for x,y in itertools.product((-54,126),(-60,60)):
    inst('19_bolted_printed_foot',s.translate((x,y,0)),label=f'printed_foot_{x}_{y}')

# Small servo mounting gauge for a cheap physical check before the full carrier.
s=box(56,70,4,(0,0,0)).cut(box(P['servo_window_width'],41.5,6,(0,-.5,-1)))
for yy in (-5,5):
    for zz in (-24.3,23.3):s=s.cut(slot_xy(9.3,3.3,-1,6,yy,zz,90))
add('20_MG946R_mount_fit_gauge',s,'#e0a04c','coupon')

s=cyl(8,1).cut(cyl(3.3,1))
add('21_M3_motor_screw_washer_1mm',s,'#e0a04c','fixed',qty=7)
for dx,y in itertools.product((-15.5,15.5),repeat=2):
    inst('21_M3_motor_screw_washer_1mm',s.translate((C+dx,y,64)),label=f'motor_screw_washer_{dx}_{y}')

# Encoder bracket: flange at -35, 20.6 boss window, radial slots for 28/30 PCD.
s=box(80,64,4,(0,0,-4));s=hole(s,34,6,(0,0,-5))
for x,y in itertools.product((-26,26),repeat=2):s=hole(s,8.4,6,(x,y,-5))
for x,y in itertools.product((-36,36),(-18,18)):s=hole(s,3.3,6,(x,y,-5))
for x,y in itertools.product((-25,25),(-22,22)):s=s.union(box(8,8,35,(x,y,-35)))
s=s.union(box(60,60,4,(0,0,-35)));s=hole(s,20.6,6,(0,0,-36))
for x,y in itertools.product((-26,26),repeat=2):s=hole(s,8.4,1.1,(x,y,-1))
for a in (90,210,330):
    ar=math.radians(a);xx,yy=14.5*math.cos(ar),14.5*math.sin(ar)
    s=s.cut(slot_xy(4.3,3.3,-36,6,xx,yy,a))
add('22_output_encoder_bracket',s,'#3f6579','fixed');inst('22_output_encoder_bracket')
for a in (90,210,330):
    ar=math.radians(a);xx,yy=15*math.cos(ar),15*math.sin(ar)
    washer=parts['21_M3_motor_screw_washer_1mm']['shape'].translate((xx,yy,-31))
    inst('21_M3_motor_screw_washer_1mm',washer,label=f'encoder_screw_washer_{a}')

s=box(38,20,8,(0,0,0));s=hole(s,8.1,10,(-9,0,-1))
s=d_hole(s,8.2,10,(9,0,-1),(0,0,1),(0,1,0))
add('23_D_shaft_fit_gauge',s,'#e0a04c','coupon')

# Hardware envelopes. Bearings show actual 8x22x7 annular dimensions.
for z in (8,59):hardware(f'608_az_{z}',cyl(22,7,(0,0,z)).cut(cyl(8,7,(0,0,z))),group='fixed')
shaft=cyl(8,P['azimuth_shaft_length'],(0,0,P['azimuth_shaft_bottom']))
shaft=shaft.cut(box(12,8,18,(0,7.5,89)))
hardware('azimuth_8mm_shaft_120mm_D_flat',shaft)
for x in (-97,90):hardware(f'608_elevation_{x}',axis_cyl(22,7,(x,0,209),(1,0,0)).cut(axis_cyl(8,7,(x,0,209),(1,0,0))))
shaft=axis_cyl(8,40,(-114,0,209),(1,0,0))
for xx,ln in ((-114,13),(-85,8)):
    shaft=shaft.cut(box(ln,12,8,(xx+ln/2,0,197.5)))
hardware('left_8mm_shaft_40mm_D_flats',shaft,group='elevation_world')
shaft=axis_cyl(8,30,(77,0,209),(1,0,0)).cut(box(8,12,8,(81,0,197.5)))
hardware('right_8mm_shaft_30mm_D_flat',shaft,group='elevation_world')

# Conservative encoder body clearance envelope, not a mass-accurate solid.
encoder=cyl(38,P['encoder_body_clearance_length'],(0,0,-35-P['encoder_body_clearance_length']))
encoder=encoder.union(cyl(20,5,(0,0,-35))).union(cyl(6,13,(0,0,-30)))
for a in (90,210,330):
    ar=math.radians(a);xx,yy=15*math.cos(ar),15*math.sin(ar)
    encoder=hole(encoder,3.3,4,(xx,yy,-38.5))
hardware('LPD3806_600BM_clearance_envelope',encoder,'#48505b','fixed')
coupling=cyl(14,25,(0,0,-28)).cut(cyl(6,12.5,(0,0,-28))).cut(cyl(8,12.5,(0,0,-15.5)))
hardware('D14L25_6_8_encoder_coupling_envelope',coupling,'#abb6bf')
motor=box(42.3,42.3,P['motor_body_length'],(C,0,58-P['motor_body_length'])).edges('|Z').fillet(2)
motor=motor.union(cyl(22,2,(C,0,58))).union(cyl(5,P['motor_shaft_length'],(C,0,58)))
hardware('SL42STH40_1684A_envelope',motor,'#48505b','fixed')
driver=cyl(16,6,(C,0,64)).union(cyl(2*r-.508,7,(C,0,69.5))).union(cyl(16,1.5,(C,0,76.5)))
driver=driver.cut(cyl(5,15,(C,0,63)))
hardware('GT2_20T_metal_pulley_ENVELOPE',driver,'#abb6bf','fixed')
servo=box(37,19,40,(-144.5,0,178.5))
servo=servo.union(box(2,19.7,54,(-135.5,0,172)))
servo=servo.union(axis_cyl(6,6,(-126,0,209),(1,0,0)))
# Four nominal mounting holes in ears, avoiding false carrier interference.
for z in (175.2,222.8):
    for y in (-5,5):servo=hole(servo,3.3,4,(-137.5,y,z),(1,0,0))
hardware('MG946R_nominal_envelope',servo,'#35363c')
horn=axis_cyl(24,3,(-122,0,209),(1,0,0)).cut(axis_cyl(6,3,(-122,0,209),(1,0,0)))
hardware('MG946R_supplied_round_horn_envelope',horn,'#35363c')
# Belt at pitch line (visual envelope only), not a printable component.
a=math.acos((R-r)/C)
outline=[]
for th in np.linspace(a,2*math.pi-a,100):outline.append((R*math.cos(th),R*math.sin(th)))
for th in np.linspace(-a,a,55):outline.append((C+r*math.cos(th),r*math.sin(th)))
outer=cq.Workplane('XY').polyline(outline).close().offset2D(1).extrude(6).translate((0,0,70))
inner=cq.Workplane('XY').polyline(outline).close().offset2D(-.3).extrude(8).translate((0,0,69))
hardware('GT2_280mm_belt_PITCH_ENVELOPE',outer.cut(inner),'#35363c','fixed')

def placed(i,angle=35):
    if i['group']=='elevation_local':return elev(i['shape'],angle)
    if i['group']=='elevation_world':return i['shape'].rotate((0,0,209),(1,0,209),angle)
    return i['shape']

def mesh(s,tol=.12):
    vs,fs=s.val().tessellate(tol,.15)
    return trimesh.Trimesh(vertices=[[v.x,v.y,v.z] for v in vs],faces=fs,process=True)

def export_all():
    for d in ('STL','STEP','preview','qa_cache'): (ROOT/d).mkdir(exist_ok=True)
    report=[]
    for name,p in parts.items():
        path=ROOT/'STL'/f'{name}.stl'
        cq.exporters.export(p['print_shape'],str(path),tolerance=.035,angularTolerance=.1)
        cq.exporters.export(p['shape'],str(ROOT/'STEP'/f'{name}.step'))
        m=trimesh.load_mesh(path)
        # OCC can emit zero-area facets at a surface-of-revolution pole. Remove only those.
        degenerate_count=int((~m.nondegenerate_faces()).sum())
        m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
        m.export(path)
        extent=m.extents
        check=dict(part=name,quantity=p['qty'],dimensions_mm=[round(float(x),2) for x in extent],volume_cm3=round(float(m.volume/1000),3),zero_area_facets_removed=degenerate_count,watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),connected_components=len(m.split(only_watertight=False)),fits_A1=bool(all(extent<240)))
        assert check['watertight'] and check['winding_consistent'] and check['connected_components']==1 and m.volume>0,check
        assert check['fits_A1'],check
        report.append(check);print('EXPORT',name,check['dimensions_mm'],flush=True)
    ass=cq.Assembly(name='Antenna_TheGioiIC_v3')
    for i in instances:
        i['shape'].val().exportBrep(str(ROOT/'qa_cache'/f"{i['name']}.brep"))
        c=i['color'];color=cq.Color(int(c[1:3],16)/255,int(c[3:5],16)/255,int(c[5:7],16)/255)
        ass.add(placed(i),name=i['name'],color=color)
    ass.export(str(ROOT/'STEP'/'ASSEMBLY_with_hardware_envelopes.step'))
    # Neutral 3MF, separate objects and no machine settings / G-code.
    # Export oriented printable meshes individually and arrange later in Bambu Studio.
    import runpy
    runpy.run_path(str(ROOT/'pack_print_plates.py'),run_name='__main__')
    (ROOT/'parameters.json').write_text(json.dumps(P,indent=2),encoding='utf-8')
    (ROOT/'mesh_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (ROOT/'printed_parts.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['part','quantity','X_mm','Y_mm','Z_mm','solid_volume_cm3'])
        for row in report:w.writerow([row['part'],row['quantity'],*row['dimensions_mm'],row['volume_cm3']])
    data=[]
    for i in instances:
        m=mesh(i['shape'])
        data.append(dict(name=i['name'],group=i['group'],color=i['color'],printed=i['printed'],v=np.round(m.vertices,3).tolist(),f=m.faces.tolist()))
    (ROOT/'preview'/'mesh_data.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')

def write_3mf():
    # One object per part, spaced in a grid of separate virtual plates (not a slicer project).
    import xml.etree.ElementTree as ET
    ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('',ns)
    model=ET.Element('{'+ns+'}model',unit='millimeter');resources=ET.SubElement(model,'{'+ns+'}resources');build=ET.SubElement(model,'{'+ns+'}build')
    idx=0
    for name,p in parts.items():
        if p['group']=='coupon':continue
        for copy in range(p['qty']):
            idx+=1;m=mesh(p['print_shape'],.04)
            obj=ET.SubElement(resources,'{'+ns+'}object',id=str(idx),type='model',name=f'{name}_{copy+1}')
            me=ET.SubElement(obj,'{'+ns+'}mesh');vv=ET.SubElement(me,'{'+ns+'}vertices');ff=ET.SubElement(me,'{'+ns+'}triangles')
            for v in m.vertices:ET.SubElement(vv,'{'+ns+'}vertex',x=f'{v[0]:.5f}',y=f'{v[1]:.5f}',z=f'{v[2]:.5f}')
            for f in m.faces:ET.SubElement(ff,'{'+ns+'}triangle',v1=str(f[0]),v2=str(f[1]),v3=str(f[2]))
            ET.SubElement(build,'{'+ns+'}item',objectid=str(idx),transform=f'1 0 0 0 1 0 0 0 1 {128+(idx-1)%5*270} {128+(idx-1)//5*270} 0')
    with zipfile.ZipFile(ROOT/'Printable_parts_IMPORT_AND_ARRANGE.3mf','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')

if __name__=='__main__':export_all()
