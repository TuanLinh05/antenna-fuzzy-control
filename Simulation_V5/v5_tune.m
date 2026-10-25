function T = v5_tune(stage, limits)
%V5_TUNE Grid search of the azimuth controller on the full V5 model.
%   T = v5_tune(1)  motion limits: v_max x accel x smooth_n (fuzzy rules fixed)
%   T = v5_tune(2, [v_max_dps accel_dps2 smooth_n])  fuzzy shape: e_scale x
%                   mf_e_in x derivative weight of the rule table at these limits
%                   (default: fastest robust candidate of stage 1)
%   Objective: smallest sum of 2 % settling times on the course sequence
%   (60,150,30,90 deg) subject to POT <= 2 %, true antenna speed <= 30 deg/s,
%   final measured error <= 0.05 deg and no fault. Candidates that pass are
%   re-run on a pessimistic plant (inertia x1.5, friction x2, hard 0.5 deg
%   tooth clearance, belt stiffness x0.6, belt damping x0.5); there they must
%   keep POT <= 2 %, the final error and no fault (the speed is reported:
%   the rattle in a hard clearance is a mechanical limit, not a control one).
%   Results: results/tune_stage<k>.csv
if nargin < 1, stage = 1; end
here = fileparts(mfilename('fullpath'));
if ~exist(fullfile(here, 'results'), 'dir'), mkdir(fullfile(here, 'results')); end
cfg = v5_config();
deg = pi/180;
worst = struct('J_coef', cfg.plant.J_coef*1.5, 'Tc_az', cfg.plant.Tc_az*2, ...
    'backlash', 0.5*deg, 'gap_soft', 0, 'k_belt', cfg.plant.k_belt*0.6, ...
    'c_belt', cfg.plant.c_belt*0.5);
switch stage
    case 1
        [a, b, c] = ndgrid([20 22 24 26 28], [60 90 120 180 240], [1 5 9 13]);
        grid = [a(:) b(:) c(:)];
        names = {'v_max_dps', 'accel_dps2', 'smooth_n'};
        make = @(g) struct('v_max', g(1)*deg, 'de_scale', g(1)*deg, 'accel', g(2)*deg, ...
            'smooth_n', g(3));
    case 2
        if nargin < 2
            best = readtable(fullfile(here, 'results', 'tune_stage1.csv'));
            best = best(best.feasible_robust == 1, :);
            best = sortrows(best, 'sum_ts2_s');
            limits = [best.v_max_dps(1) best.accel_dps2(1) best.smooth_n(1)];
        end
        b1 = struct('v_max_dps', limits(1), 'accel_dps2', limits(2), 'smooth_n', limits(3));
        [a, b, c] = ndgrid([4 6 8 10 14], [0.2 0.35 0.5], [0.25 0.5 1.0]);
        grid = [a(:) b(:) c(:)];
        names = {'e_scale_deg', 'mf_e_in', 'kd_rule'};
        centre = [-1 -0.5 0 0.5 1];
        make = @(g) struct('v_max', b1.v_max_dps*deg, 'de_scale', b1.v_max_dps*deg, ...
            'accel', b1.accel_dps2*deg, 'smooth_n', b1.smooth_n, 'e_scale', g(1)*deg, ...
            'mf_e_in', g(2), 'rules', min(1, max(-1, 2*centre' + g(3)*centre)));
end
n = size(grid, 1);
out = zeros(n, 9);
for k = 1:n
    sc = v5_scenario('pdf');
    sc.ctrl = make(grid(k, :));
    r = v5_simulate(cfg, sc);
    m = r.metrics;
    feas = m.worst_pot_pct <= 2 && m.peak_speed_dps <= 30 && ...
        m.worst_final_meas_deg <= 0.05 && m.final_fault == 0 && isfinite(m.sum_ts2_s);
    rob = 0; wpk = NaN; wpot = NaN;
    if feas
        sc.plant = worst;
        rw = v5_simulate(cfg, sc);
        wpk = rw.metrics.peak_speed_dps; wpot = rw.metrics.worst_pot_pct;
        rob = wpot <= 2 && rw.metrics.final_fault == 0 && rw.metrics.worst_final_meas_deg <= 0.1;
    end
    out(k, :) = [m.sum_ts2_s m.worst_ts2_s m.worst_pot_pct m.peak_speed_dps ...
        m.worst_final_meas_deg feas rob wpk wpot];
    fprintf('%3d/%d %s -> sum ts %.2f s, POT %.3f %%, peak %.2f dps, feas %d robust %d\n', ...
        k, n, mat2str(grid(k, :)), out(k, 1), out(k, 3), out(k, 4), feas, rob);
end
T = array2table([grid out], 'VariableNames', [names, {'sum_ts2_s', 'worst_ts2_s', ...
    'worst_pot_pct', 'peak_speed_dps', 'final_meas_deg', 'feasible', 'feasible_robust', ...
    'robust_peak_dps', 'robust_pot_pct'}]);
writetable(T, fullfile(here, 'results', sprintf('tune_stage%d.csv', stage)));
ok = T(T.feasible_robust == 1, :);
if ~isempty(ok)
    ok = sortrows(ok, 'sum_ts2_s');
    disp(ok(1:min(8, height(ok)), :));
end
end
