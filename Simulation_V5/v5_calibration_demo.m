function out = v5_calibration_demo()
%V5_CALIBRATION_DEMO MT6701 harmonic calibration, checked on the model.
%   Runs the same procedure as v5_calibrate_mt6701 on the simulated plant
%   (MT6701 with +-0.8 deg INL): 19 points from -135 to +135 deg approached
%   in the positive direction, STEP count as reference, harmonic fit, then the
%   course sequence with and without the correction. Writes
%   results/v5_calibration_demo.json and .png.
here = fileparts(mfilename('fullpath'));
deg = pi/180;
cfg = v5_config();
pts = -135:15:135;
sc = v5_scenario('pdf', 'duration', 6 + 3*numel(pts) + 1);
c = struct('t', 0, 'type', 'goto', 'args', [1 -140*deg 0 1]);
for i = 1:numel(pts)
    c(end+1) = struct('t', 6 + 3*(i-1), 'type', 'goto', 'args', [1 pts(i)*deg 0 1]); %#ok<AGROW>
end
sc.commands = c;
sc.name = 'calibration';
r = v5_simulate(cfg, sc);
raw = zeros(numel(pts), 1); st = zeros(numel(pts), 1); truth = zeros(numel(pts), 1);
for i = 1:numel(pts)
    te = 6 + 3*i;
    k = r.log.t >= te - 0.4 & r.log.t < te - 0.05;
    raw(i) = median(r.log.raw(k));
    st(i) = median(r.log.steps(k));
    truth(i) = median(r.log.true(k));
end
cal = v5_fit_sensor_cal(raw, st, double(cfg.ctrl.steps_rev), cfg.plant.sensor_sign);

% course sequence without / with the correction (the zero mark is re-taken)
sc1 = v5_scenario('pdf');
r0 = v5_simulate(cfg, sc1);
sc1.ctrl = struct('cal_a1', cal.a1, 'cal_b1', cal.b1, 'cal_a2', cal.a2, 'cal_b2', cal.b2);
r1 = v5_simulate(cfg, sc1);
out = struct('fit', cal, 'points_deg', pts, ...
    'final_true_error_before_deg', r0.metrics.worst_final_true_deg, ...
    'final_true_error_after_deg', r1.metrics.worst_final_true_deg, ...
    'segments_before', r0.metrics.segments, 'segments_after', r1.metrics.segments);
fid = fopen(fullfile(here, 'results', 'v5_calibration_demo.json'), 'w');
fwrite(fid, jsonencode(out, PrettyPrint=true)); fclose(fid);

phi = linspace(0, 2*pi, 400);
P = cfg.plant;
inl = P.inl_a1*sin(phi + P.inl_p1) + P.inl_a2*sin(2*phi + P.inl_p2);
fitc = cal.a1*cos(phi) + cal.b1*sin(phi) + cal.a2*cos(2*phi) + cal.b2*sin(2*phi);
fig = figure('Visible', 'off', 'Position', [50 50 900 450], 'Color', 'w');
try, theme(fig, 'light'); catch, end
plot(phi/deg, inl/deg, 'b', phi/deg, (fitc - mean(fitc - inl))/deg, 'r--', 'LineWidth', 1.3);
hold on;
pr = double(raw)*360/16384;
plot(pr, (unwrap(double(raw)*2*pi/16384) - double(st)*2*pi/12800 - cal.c0 + mean(fitc - inl))/deg, 'ko');
grid on; xlabel('góc cảm biến (°)'); ylabel('sai số (°)');
legend('INL mô hình MT6701', 'hiệu chỉnh khớp (5 hệ số)', 'điểm đo: góc cảm biến − góc từ số STEP', ...
    'Location', 'best');
title(sprintf('Hiệu chuẩn MT6701: sai số cuối thật %.3f° → %.3f°', ...
    out.final_true_error_before_deg, out.final_true_error_after_deg));
exportgraphics(fig, fullfile(here, 'results', 'v5_calibration_demo.png'), 'Resolution', 130);
close(fig);
disp(out);
end
