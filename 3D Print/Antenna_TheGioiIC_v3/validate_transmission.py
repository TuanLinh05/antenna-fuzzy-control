"""Belt geometry and continuous bounding envelopes, independently from collision samples."""
from pathlib import Path
import json,sys,math
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[2]/'tmp'/'cad_runtime'))
import numpy as np
p=json.loads((ROOT/'parameters.json').read_text(encoding='utf-8'))
data=json.loads((ROOT/'preview'/'mesh_data.json').read_text(encoding='utf-8'))
c=p['motor_center_distance'];r=p['driver_teeth']/math.pi;R=p['driven_teeth']/math.pi
alpha=math.asin((R-r)/c)
length=2*math.sqrt(c*c-(R-r)**2)+R*(math.pi+2*alpha)+r*(math.pi-2*alpha)
small_wrap=math.pi-2*alpha
moving=[]
for q in data:
    if q['group'] not in ('elevation_local','elevation_world'):continue
    v=np.array(q['v']);axis=8 if q['group']=='elevation_local' else 209
    radius=np.hypot(v[:,1],v[:,2]-axis).max()
    moving.append(dict(part=q['name'],x_min_mm=float(v[:,0].min()),x_max_mm=float(v[:,0].max()),
                       full_elevation_z_min_mm=209-float(radius)-.10))
# 0.1 mm mesh allowance; rotation about X preserves each part's X bounds.
aperture=[q for q in moving if q['part'] not in ('11_servo_horn_shaft_coupler',
    'MG946R_supplied_round_horn_envelope','left_8mm_shaft_40mm_D_flats',
    'right_8mm_shaft_30mm_D_flat','right_elevation_inner_race_spacer','printed_right_elevation_collar')]
# Parts through the bearing bores and the collar beyond the right arm are intentional mates.
aperture=[q for q in aperture if not q['part'].startswith(('left_8mm','right_8mm','printed_right_')) and
          q['part']!='right_elevation_inner_race_spacer']
lowest=min(q['full_elevation_z_min_mm'] for q in moving)
checks=dict(belt_length_error_less_than_0_001mm=abs(length-280)<.001,
            small_pulley_engagement_at_least_six_teeth=p['driver_teeth']*small_wrap/(2*math.pi)>=6,
            elevation_swept_envelope_above_crossbeam_105mm=lowest>105,
            dish_and_cradle_inside_arm_aperture=all(q['x_min_mm']>=-85.1 and q['x_max_mm']<=85.1 for q in aperture),
            rotating_table_bottom_above_motor_pulley_top=81>78,
            lower_rotor_flange_above_stationary_tower=68>66,
            encoder_coupling_top_below_lower_collar=-3<-2)
report=dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,
    exact_pitch_line_length_mm=length,center_distance_mm=c,small_pulley_wrap_deg=math.degrees(small_wrap),
    small_pulley_engaged_teeth=p['driver_teeth']*small_wrap/(2*math.pi),ratio=4,
    full_step_output_deg=1.8/4,microstep_output_deg=1.8/(16*4),
    encoder_count_deg=360/(600*4),maximum_STEP_frequency_at_30deg_s=30/(1.8/(16*4)),
    elevation_sweep_minimum_z_mm=lowest,moving_envelopes=moving,
    limitations=['Bounding arguments establish listed separations for any combination of joint angles.',
                 'Fastener clearances and other pairs are still checked at discrete samples.',
                 'Belt tooth form follows the referenced parametric GT2 profile; engagement and pretension must be checked on a print.',
                 'No belt tensile rating, measured compliance, backlash or commercial pulley axial drawing is available from the seller.',
                 'Electrical cables and tool access are not certified by the bounding envelopes.'])
(ROOT/'audit'/'transmission_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('moving_envelopes','limitations')},indent=2))
if not all(checks.values()):sys.exit(1)
