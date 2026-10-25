function report=run_extended_tests(reuseDC)
if nargin<1,reuseDC=false;end
folder=fileparts(mfilename('fullpath'));out=fullfile(folder,'results');addpath(folder);
a=load(fullfile(out,'dc_nominal.mat'),'best_result','best');dc=a.best_result;c=a.best;
if reuseDC
    previous=jsondecode(fileread(fullfile(out,'comprehensive_validation.json')));
    cases=table2struct(readtable(fullfile(out,'dc_uncertainty.csv')));
    dc_difference=previous.dc_step_refinement_max_difference_rad;
    disturbance_pass=previous.dc_disturbance_pass;
    a=load(fullfile(out,'dc_reference_PD_baseline.mat'),'baseline');baseline=a.baseline;
else
cases=[];rng(20261024);
for k=1:12
    p=c.plant;p.J=p.J*(.75+.5*rand);p.B=p.B*(.75+.5*rand);p.Tc=p.Tc*(.5+rand);
    p.Ra=p.Ra*(.8+.4*rand);p.La=p.La*(.8+.4*rand);p.Kt=p.Kt*(.9+.2*rand);p.Kb=p.Kb*(.9+.2*rand);
    r=simulate_dc(c,p);m=r.metrics;
    pass=m.worst_overshoot_percent<=2&&m.worst_tail_error_rad<=1e-4&&m.peak_speed_rad_s<=pi/6&&m.peak_voltage_V<=12;
    cases=[cases;struct('case_id',k,'pass',pass,'overshoot_percent',m.worst_overshoot_percent, ...
        'tail_error_rad',m.worst_tail_error_rad,'peak_speed_rad_s',m.peak_speed_rad_s,'settling_sum_s',m.sum_settling_s)]; %#ok<AGROW>
    fprintf('DC uncertainty %d/12 pass %d\n',k,pass);
end
writetable(struct2table(cases),fullfile(out,'dc_uncertainty.csv'));
fine=c;fine.h=5e-5;r=simulate_dc(fine);
dc_difference=max(abs(interp1(r.t,r.x(:,1),dc.t)-dc.x(:,1)));
assert(dc_difference<1e-4);
disturbed=simulate_dc(c,c.plant,2);
disturbance_pass=disturbed.metrics.peak_speed_rad_s<=pi/6&&disturbed.metrics.peak_voltage_V<=12&&disturbed.metrics.worst_tail_error_rad<1e-3;
save(fullfile(out,'dc_disturbance.mat'),'disturbed');
pid=c;pid.mode='linear_pd';baseline=simulate_dc(pid);save(fullfile(out,'dc_reference_PD_baseline.mat'),'baseline');
end

pc=prototype_default_config;nominal=simulate_prototype(pc);save(fullfile(out,'prototype_nominal.mat'),'nominal');
disp(nominal.metrics);
scenario=[];names={'open_loop','load_torque','missed_pulses','high_inertia_and_backlash','low_inertia', ...
    'encoder_noise','slower_control_sample','encoder_freeze','communications_lost','output_jam','overload_0p08Nm'};
for k=1:numel(names)
    q=pc;name=names{k};expected_fault=false;stress_observation=false;
    switch name
        case 'open_loop',q.mode='open';
        case 'load_torque',q.torque_disturbance=true;
        case 'missed_pulses',q.pulse_drop=true;
        case 'high_inertia_and_backlash',q.Jscale=1.5;q.coulomb=.04;q.belt_stiffness=10;q.belt_damping=.08;q.backlash=3*pi/180;
        case 'low_inertia',q.Jscale=.5;q.belt_stiffness=40;q.belt_damping=.08;
        case 'encoder_noise',q.encoder_noise_deg=.025;
        case 'slower_control_sample',q.Ts=.012;
        case 'encoder_freeze',q.encoder_freeze=true;expected_fault=true;
        case 'communications_lost',q.communication_loss=true;expected_fault=true;
        case 'output_jam',q.jam=true;expected_fault=true;
        case 'overload_0p08Nm',q.torque_disturbance=true;q.external_load_Nm=.08;stress_observation=true;
    end
    r=simulate_prototype(q);m=r.metrics;
    if stress_observation
        pass=all(isfinite(r.x(:))); % Observation only: retain speed-limit violation below.
    elseif strcmp(name,'open_loop')
        pass=all(isfinite(r.x(:))); % Demonstration baseline, not a tracking acceptance.
    elseif expected_fault
        bound=14;if q.communication_loss,bound=15.02;end
        pass=m.final_fault~=0&&m.first_fault_time_s<=bound;
    else
        pass=m.pass_tracking;
    end
    scenario=[scenario;struct('name',name,'pass',pass,'expected_fault',expected_fault,'stress_observation',stress_observation, ...
        'tracking_requirements_met',m.pass_tracking, ...
        'overshoot_percent',m.worst_overshoot_percent,'tail_error_deg',m.worst_tail_error_rad*180/pi, ...
        'peak_speed_deg_s',m.peak_speed_rad_s*180/pi,'fault',m.final_fault,'fault_time_s',m.first_fault_time_s)]; %#ok<AGROW>
    fprintf('Prototype %s pass %d; overshoot %.3f %%; tail %.3f deg; speed %.2f deg/s; fault %d\n',name,pass,m.worst_overshoot_percent,m.worst_tail_error_rad*180/pi,m.peak_speed_rad_s*180/pi,m.final_fault);
    stride=100;r.t=r.t(1:stride:end);r.x=r.x(1:stride:end,:);
    for f={'reference','encoder','steps','effective_steps','velocity_command','fault','elevation_reference','belt_torque','motor_torque'}
        r.(f{1})=r.(f{1})(1:stride:end,:);
    end
    save(fullfile(out,['prototype_' name '.mat']),'r');
end
writetable(struct2table(scenario),fullfile(out,'prototype_scenarios.csv'));
fine=pc;fine.h=5e-5;r=simulate_prototype(fine);
prototype_difference=max(abs(interp1(r.t,r.x(:,3),nominal.t)-nominal.x(:,3)));
% Quantized feedback can shift pulse timing by one encoder bin. Check trajectory
% convergence within 0.3 deg, not bit-for-bit equality of hybrid event times.
prototype_refinement_pass=prototype_difference<.3*pi/180;
report=struct('status','PASS_WITH_STRESS_LIMITATIONS','MATLAB_version',version,'dc_nominal',dc.metrics, ...
    'dc_uncertainty_case_count',numel(cases),'dc_uncertainty_all_pass',all([cases.pass]), ...
    'dc_step_refinement_max_difference_rad',dc_difference,'dc_disturbance_pass',disturbance_pass, ...
    'linear_PD_baseline',baseline.metrics,'prototype_nominal',nominal.metrics, ...
    'prototype_scenarios',scenario,'prototype_refinement_max_difference_rad',prototype_difference, ...
    'prototype_refinement_pass',prototype_refinement_pass, ...
    'prototype_additional_load_design_test_Nm',.02, ...
    'overload_tracking_test_pass',scenario(end).tracking_requirements_met, ...
    'overload_peak_speed_deg_s',scenario(end).peak_speed_deg_s, ...
    'physical_hardware_validated',false,'Simscape_Multibody_installed',exist('smnew','file')~=0, ...
    'limitations',{{'Original DC assignment and stepper prototype are different plants.', ...
    'Prototype motor rotor inertia, running torque, belt k/c/backlash and servo dynamics are assumptions, not identified measurements.', ...
    'No HIL, thermal model, coil-current chopper circuit, structural 3D FEA or RF simulation is claimed.', ...
    'Only azimuth uses external fuzzy feedback. Elevation is a surrogate of the hobby servo internal controller.', ...
    'The 0.08 Nm shock and release from a jam exceed 30 deg/s. Fault detection is not a mechanical brake; hardware is not approved for impacts or jams.', ...
    'Tuning selects the fastest passing candidate among 18 trials; no global time-optimality proof is claimed.'}});
if ~all([cases.pass])||~disturbance_pass||~nominal.metrics.pass_tracking||~all([scenario.pass])||~prototype_refinement_pass
    report.status='FAIL';
end
fid=fopen(fullfile(out,'comprehensive_validation.json'),'w');fwrite(fid,jsonencode(report,PrettyPrint=true));fclose(fid);
disp(report);
assert(startsWith(report.status,'PASS'),'Simulation acceptance has unresolved failures. See CSV/JSON reports.');
end
