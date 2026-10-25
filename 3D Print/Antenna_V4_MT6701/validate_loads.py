"""Conservative rigid-body load estimates from exported CAD tessellations.

Printed parts use fully solid PLA mass. Strength, friction and running motor
torque are explicitly design assumptions, not measured material certificates.
"""
from pathlib import Path
import json, math, sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[2]/'tmp'/'cad_runtime'))
import numpy as np
import trimesh

data=json.loads((ROOT/'preview'/'mesh_data.json').read_text(encoding='utf-8'))
densities={'PLA':1.24e-6,'steel':7.93e-6,'aluminium':2.7e-6}
parts=[]
for q in data:
    m=trimesh.Trimesh(vertices=q['v'],faces=q['f'],process=True)
    if q['printed']:
        mass=m.volume*densities['PLA']; provenance='fully solid PLA, density assumption 1240 kg/m3'
    elif q['name'].startswith('608_'):
        mass=.012;provenance='assumed 12 g bearing, measure actual'
    elif 'shaft_' in q['name']:
        mass=m.volume*densities['steel'];provenance='CAD steel volume, density assumption 7930 kg/m3'
    elif q['name']=='LD1501MG_nominal_envelope':
        mass=.061;provenance='61 g LD-1501MG published by Hiwonder'
    elif q['name']=='17HS1352_P4130_nominal_envelope':
        mass=.22;provenance='assumed 220 g motor, stationary; weigh actual unit'
    elif 'MT6701' in q['name']:
        mass=.004 if 'PCB' in q['name'] else .001;provenance='assumed module/component mass, stationary'
    elif 'diametric_magnet' in q['name']:
        mass=m.volume*7.5e-6;provenance='assumed NdFeB density 7500 kg/m3'
    elif 'horn' in q['name']:
        mass=.004;provenance='assumed 4 g horn'
    elif 'belt' in q['name']:
        mass=.006;provenance='assumed 6 g belt, visual envelope only'
    else:
        mass=m.volume*densities['aluminium'];provenance='CAD envelope at assumed aluminium density'
    parts.append(dict(name=q['name'],group=q['group'],printed=q['printed'],mass=mass,
                      center=np.array(m.center_mass),inertia=np.array(m.moment_inertia)*(mass/m.volume),
                      mass_provenance=provenance))


def placed(q,el):
    p=q['center'].copy();inertia=q['inertia'].copy();r=np.eye(3)
    if q['group'] in ('elevation_local','elevation_world'):
        angle=math.radians(el-(90 if q['group']=='elevation_local' else 0))
        c,s=math.cos(angle),math.sin(angle)
        r=np.array([[1,0,0],[0,c,-s],[0,s,c]])
        p[2]-=8 if q['group']=='elevation_local' else 209
        p=r@p+np.array([0,0,209])
        inertia=r@inertia@r.T
    return p,inertia


samples=[]
for el in range(0,181,5):
    yaw_j=0.;elev_j=0.;gravity_x=0.;moving_mass=0.;total_mass=0.;weighted=np.zeros(3)
    for q in parts:
        p,im=placed(q,el);mass=q['mass'];total_mass+=mass;weighted+=mass*p
        if q['group']!='fixed':
            yaw_j+=(im[2,2]+mass*(p[0]**2+p[1]**2))*1e-6
        if q['group'] in ('elevation_local','elevation_world'):
            elev_j+=(im[0,0]+mass*(p[1]**2+(p[2]-209)**2))*1e-6
            gravity_x+=mass*9.80665*p[1]*.001;moving_mass+=mass
    samples.append(dict(elevation_deg=el,yaw_inertia_kgm2=yaw_j,elevation_inertia_kgm2=elev_j,
                        gravity_elevation_Nm=gravity_x,total_mass_kg=total_mass,
                        elevation_moving_mass_kg=moving_mass,center_of_mass_mm=(weighted/total_mass).tolist()))

max_yaw_j=max(q['yaw_inertia_kgm2'] for q in samples)
max_el_j=max(q['elevation_inertia_kgm2'] for q in samples)
gravity=max(abs(q['gravity_elevation_Nm']) for q in samples)
# Running torque is assumed at 20% of the seller's 0.25 Nm holding-torque claim.
az_torque=max_yaw_j*math.radians(30)+.020+.010*math.radians(30)
az_available=.25*.20*4*.80  # running torque is a planning assumption, not measured
el_torque=gravity+max_el_j*math.radians(60)+.015
el_available=13*.0980665*.20  # published 6 V stall torque, 20% design derating
flat_width=2*math.sqrt(4**2-3.5**2)
# Flat-bearing pressure at a deliberately conservative 1 Nm jam torque.
flat_pressure_MPa=1000/(3.5*flat_width*16)
allowable_MPa=8.  # unverified FDM engineering assumption, needs proof load
shaft_bending_MPa=32*(20*11)/(math.pi*8**3)
beam_I=math.pi*(40**4-22.2**4)/64
tower_stress_MPa=20*58*20/beam_I
tower_deflection_mm=20*58**3/(3*1000*beam_I)
arm_I=60*10**3/12
arm_side_load_stress_MPa=2*104*5/arm_I
arm_side_load_deflection_mm=2*104**3/(3*1000*arm_I)
minimum_edge=1e9
conservative_infill_edge=1e9
for q in samples:
    cx,cy,cz=q['center_of_mass_mm']
    # Check all azimuth angles. Fixed parts remain fixed while the upper mechanism rotates.
    for az in range(0,361,5):
        a=math.radians(az);weighted=np.zeros(3);total=0
        for p in parts:
            center,_=placed(p,q['elevation_deg'])
            if p['group']!='fixed':
                x,y=center[:2];center[:2]=[x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)]
            weighted+=p['mass']*center;total+=p['mass']
        cg=weighted/total
        minimum_edge=min(minimum_edge,cg[0]+54,126-cg[0],cg[1]+60,60-cg[1])
        # Independent printed-mass fractions in [0.35,1]. Lower bound for each
        # support-edge moment, divided by maximum total mass, is conservative.
        for edge in range(4):
            low_moment=0.
            for p in parts:
                center,_=placed(p,q['elevation_deg'])
                if p['group']!='fixed':
                    x,y=center[:2];center[:2]=[x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)]
                distance=(center[0]+54,126-center[0],center[1]+60,60-center[1])[edge]
                fraction=.35 if p['printed'] and distance>=0 else 1.
                low_moment+=p['mass']*fraction*distance
            conservative_infill_edge=min(conservative_infill_edge,low_moment/total)

checks={
    'yaw_running_torque_margin_at_least_3':az_available/az_torque>=3,
    'elevation_derated_torque_margin_at_least_3':el_available/el_torque>=3,
    'D_flat_jam_pressure_below_assumed_8_MPa':flat_pressure_MPa<allowable_MPa,
    'steel_shaft_bending_below_assumed_100_MPa':shaft_bending_MPa<100,
    'tower_stress_below_assumed_8_MPa':tower_stress_MPa<allowable_MPa,
    'arm_2N_side_load_stress_below_assumed_8_MPa':arm_side_load_stress_MPa<allowable_MPa,
    'gravity_COM_inside_support_centres_at_all_sampled_angles':minimum_edge>10,
    'gravity_support_margin_with_independent_35_to_100_percent_printed_masses':conservative_infill_edge>10,
    'shaft_cut_lengths_plus_kerfs_fit_200mm':120+40+30+3*1.5+2<=200,
    'magnet_cap_shaft_insertion_8mm':min(-6,106)-max(-14,-14)>=8,
}
checks={k:bool(v) for k,v in checks.items()}
report=dict(status='PASS_LOAD_ESTIMATES_UNMEASURED_TORQUE' if all(checks.values()) else 'FAIL',checks=checks,
            total_full_solid_mass_kg=samples[0]['total_mass_kg'],
            yaw_inertia_max_kgm2=max_yaw_j,elevation_inertia_max_kgm2=max_el_j,
            gravity_torque_max_Nm=gravity,yaw_required_Nm=az_torque,yaw_available_running_Nm=az_available,
            yaw_torque_margin=az_available/az_torque,elevation_required_Nm=el_torque,
            elevation_available_derated_Nm=el_available,elevation_torque_margin=el_available/el_torque,
            D_flat_pressure_at_1Nm_MPa=flat_pressure_MPa,shaft_bending_at_20N_MPa=shaft_bending_MPa,
            tower_stress_at_20N_MPa=tower_stress_MPa,tower_deflection_at_20N_mm=tower_deflection_mm,
            arm_stress_at_2N_MPa=arm_side_load_stress_MPa,arm_deflection_at_2N_mm=arm_side_load_deflection_mm,
            support_polygon_minimum_COM_margin_mm=minimum_edge,
            conservative_variable_infill_support_margin_mm=conservative_infill_edge,
            required_motor_running_torque_for_3x_margin_Nm=3*az_torque/(4*.8),
            actual_motor_torque_speed_verified=False,physical_hardware_validated=False,
            assumptions=dict(PLA_density_kgm3=1240,steel_density_kgm3=7930,printed_E_MPa=1000,
                             printed_allowable_stress_MPa=8,stepper_running_torque_Nm=.05,
                             transmission_efficiency=.80,yaw_friction_Nm=.020,elevation_friction_Nm=.015,
                             belt_pretension_per_span_N=10),
            mass_properties=[dict(name=q['name'],mass_kg=q['mass'],provenance=q['mass_provenance']) for q in parts],
            angle_samples=samples,
            limitations=['Engineering estimates, not a 3D FEA, material certification or physical proof load.',
                         'Mass distribution inside infill parts, servo internals and stepper rotor inertia are not measured.',
                         'Running stepper torque and continuous servo torque must be checked at selected current, supply and temperature.',
                         'D flats must be filed to the gauge; smooth round shafts are not an accepted substitute for these drive joints.',
                         'Support margin checks gravity only; anchor the base for cable pulls, outdoor use or lateral impacts.',
                         'Assembly fit, layer adhesion, belt tooth engagement and coaxial alignment remain commissioning checks.'])
(ROOT/'audit'/'load_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
angle_radians=np.radians([q['elevation_deg'] for q in samples])
fit=np.column_stack([np.ones(len(samples)),np.cos(2*angle_radians),np.sin(2*angle_radians)])
coeff=np.linalg.lstsq(fit,np.array([q['yaw_inertia_kgm2'] for q in samples]),rcond=None)[0]
(ROOT/'audit'/'simulation_parameters_v4.json').write_text(json.dumps(dict(yaw_inertia=max_yaw_j,elevation_inertia=max_el_j,
    yaw_inertia_coefficients=coeff.tolist(),
    gravity_torque_max=gravity,ratio=4,absolute_encoder_counts=16384,microstep_angle_output_rad=2*math.pi/12800,
    yaw_motor_running_torque_assumed=.05,prototype_velocity_limit_rad_s=math.pi/6),indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('mass_properties','angle_samples','limitations')},indent=2))
if not all(checks.values()):sys.exit(1)
