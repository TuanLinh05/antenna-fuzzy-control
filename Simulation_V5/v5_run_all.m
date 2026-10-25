function summary = v5_run_all(varargin)
%V5_RUN_ALL Full validation of the V5 antenna model and of the firmware core.
%   summary = v5_run_all()                     everything, incl. video
%   summary = v5_run_all('video', false)       skip the CAD animation
%   summary = v5_run_all('pil', false)         skip PIL through the virtual board
%
%   1. SIL/PIL equivalence (v5_sil_check): C core == MATLAB mirror == FIS
%   2. course sequence 60,150,30,90 deg with the fuzzy controller (nominal)
%   3. same sequence: linear P baseline, measured-velocity input, no
%      smoothing, calibrated MT6701
%   4. robustness: inertia, friction, clearance, belt, driver current, noise
%   5. disturbances and faults: load torque, lost STEP pulses, sensor glitch /
%      failure / freeze, jammed output, lost host heartbeat
%   6. bench demo and moving-target scenarios, CAD animation
%   Results in results/: v5_validation.json, v5_scenarios.csv, figures, video.
o = struct('video', true, 'pil', true);
for k = 1:2:numel(varargin), o.(varargin{k}) = varargin{k+1}; end
here = fileparts(mfilename('fullpath'));
cd(here);
out = fullfile(here, 'results');
if ~exist(out, 'dir'), mkdir(out); end
v5_ensure_mex();
cfg = v5_config();
deg = pi/180;
P = cfg.plant;

summary = struct();
summary.date = char(datetime('now', 'Format', 'yyyy-MM-dd HH:mm'));
summary.matlab = version;
summary.equivalence = v5_sil_check(o.pil);

%% cases ------------------------------------------------------------------
pdf = v5_scenario('pdf');
C = {};
C(end+1, :) = {'pdf_fuzzy', 'Đề bài: 60/150/30/90°, bộ mờ (danh định)', pdf, 'spec'};
C(end+1, :) = {'pdf_linear', 'Cùng giới hạn, bộ P tuyến tính', with(pdf, 'ctrl', struct('ctrl', 1)), 'spec'};
C(end+1, :) = {'pdf_vel_measured', 'Bộ mờ, đầu vào vận tốc đo từ MT6701', with(pdf, 'ctrl', struct('vel_src', 1)), 'spec'};
C(end+1, :) = {'pdf_no_smoothing', 'Bộ mờ, tắt làm trơn lệnh STEP', with(pdf, 'ctrl', struct('smooth_n', 1)), 'info'};
C(end+1, :) = {'pdf_sensor_calibrated', 'MT6701 đã hiệu chuẩn sai số phi tuyến', with(pdf, 'sensor_cal', true), 'spec'};
C(end+1, :) = {'robust_J_x0.5', 'Quán tính ×0,5', with(pdf, 'plant', struct('J_coef', P.J_coef*0.5)), 'robust'};
C(end+1, :) = {'robust_J_x1.5', 'Quán tính ×1,5', with(pdf, 'plant', struct('J_coef', P.J_coef*1.5)), 'robust'};
C(end+1, :) = {'robust_friction_x2', 'Ma sát ×2', with(pdf, 'plant', struct('Tc_az', P.Tc_az*2, 'b_az', P.b_az*2)), 'robust'};
C(end+1, :) = {'robust_hard_clearance', 'Khe hở răng cứng 0,5°', with(pdf, 'plant', struct('backlash', 0.5*deg, 'gap_soft', 0)), 'robust'};
C(end+1, :) = {'robust_belt_soft', 'Đai mềm ×0,6, giảm chấn ×0,5', with(pdf, 'plant', struct('k_belt', P.k_belt*0.6, 'c_belt', P.c_belt*0.5)), 'robust'};
C(end+1, :) = {'robust_current_0.8', 'Dòng TB6600 ×0,8', with(pdf, 'plant', struct('I_set', P.I_set*0.8)), 'robust'};
C(end+1, :) = {'robust_noise_x3', 'Nhiễu MT6701 ×3', with(pdf, 'plant', struct('noise', P.noise*3)), 'robust'};
C(end+1, :) = {'robust_combined', 'J×1,5 + ma sát×2 + khe hở cứng 0,5° + đai ×0,6', ...
    with(pdf, 'plant', struct('J_coef', P.J_coef*1.5, 'Tc_az', P.Tc_az*2, 'backlash', 0.5*deg, ...
    'gap_soft', 0, 'k_belt', P.k_belt*0.6, 'c_belt', P.c_belt*0.5)), 'robust'};
C(end+1, :) = {'dist_torque', 'Mômen tải 0,1 N.m trong 0,3 s khi đang giữ', ...
    with(pdf, 'duration', 24, 'dist', dist('torque', 6, 6.3, 0.1)), 'recover'};
C(end+1, :) = {'dist_pulse_loss', 'Mất 3 % xung STEP khi đang chạy (MT6701 bù)', ...
    with(pdf, 'duration', 24, 'dist', dist('pulse_loss', 12.3, 14, 0.03)), 'recover'};
C(end+1, :) = {'fault_pulse_loss', 'Mất 15 % xung STEP (lệch > 4°)', ...
    with(pdf, 'duration', 24, 'dist', dist('pulse_loss', 12.3, 14, 0.15)), 'fault:4'};
C(end+1, :) = {'dist_sensor_glitch', 'Một mẫu MT6701 sai 45°', ...
    with(pdf, 'duration', 24, 'dist', dist('sensor_glitch', 12.5, 12.505, 2048)), 'recover'};
C(end+1, :) = {'fault_sensor_fail', 'Mất I2C MT6701 khi đang chạy', ...
    with(pdf, 'duration', 24, 'dist', dist('sensor_fail', 12.5, 13.5, 0)), 'fault:32'};
C(end+1, :) = {'fault_sensor_freeze', 'MT6701 đứng giá trị khi đang chạy', ...
    with(pdf, 'duration', 24, 'dist', dist('sensor_freeze', 12.5, 20, 0)), 'fault:4'};
C(end+1, :) = {'fault_jam', 'Kẹt trục anten khi đang chạy', ...
    with(pdf, 'duration', 24, 'dist', dist('jam', 12.6, 14, 0)), 'fault:4'};
C(end+1, :) = {'fault_heartbeat', 'Máy tính ngừng gửi heartbeat', ...
    with(v5_scenario('demo'), 'heartbeat_until', 4), 'fault:1'};
C(end+1, :) = {'demo_pm30', 'Demo 0 → +30 → −30 → 0°', v5_scenario('demo'), 'spec'};
C(end+1, :) = {'track_sine', 'Bám mục tiêu 40 sin(2πt/20)°', v5_scenario('track'), 'track'};

%% run --------------------------------------------------------------------
rows = {};
R = struct();
for k = 1:size(C, 1)
    [id, desc, sc, kind] = C{k, :};
    sc.name = id;
    t0 = tic;
    r = v5_simulate(cfg, sc);
    m = r.metrics;
    if strcmp(kind, 'track')
        m.worst_pot_pct = NaN;               % no steps: POT is not defined
    end
    switch strtok(kind, ':')
        case 'spec'
            ok = m.pass_spec;
        case 'info'
            ok = m.worst_pot_pct <= 2 && m.final_fault == 0;
        case 'robust'
            ok = m.worst_pot_pct <= 2 && m.final_fault == 0 && m.worst_final_meas_deg <= 0.1;
        case 'recover'
            ok = m.final_fault == 0 && m.worst_final_meas_deg <= 0.1;
        case 'fault'
            bit = str2double(extractAfter(kind, ':'));
            ok = bitand(m.final_fault, bit) ~= 0 && all(r.log.hp(find(r.log.fault, 1):end) == 0);
        case 'track'
            ok = m.final_fault == 0;
    end
    if strcmp(id, 'track_sine')
        k2 = r.log.t > 5;
        m.track_rms_deg = sqrt(mean((r.log.target(k2) - r.log.true(k2)).^2))/deg;
        m.track_max_deg = max(abs(r.log.target(k2) - r.log.true(k2)))/deg;
    end
    seg = m.segments;
    rows(end+1, :) = {id, desc, kind, ok, m.sum_ts2_s, m.worst_ts2_s, m.worst_pot_pct, ...
        m.peak_speed_dps, m.worst_final_meas_deg, m.worst_final_true_deg, m.el_tail_error_deg, ...
        m.final_fault, m.first_fault_s, abs(m.rotor_offset_microsteps), toc(t0)}; %#ok<AGROW>
    R.(matlab.lang.makeValidName(id)) = r;
    s = rmfield(m, 'segments');
    s.segments = seg;
    s.kind = kind; s.ok = ok; s.description = desc;
    summary.cases.(matlab.lang.makeValidName(id)) = s;
    fprintf('%-24s %-8s ok=%d  sum ts2 %6.2f s  POT %.3f %%  peak %5.2f °/s  final %.4f° (true %.3f°)  fault %d\n', ...
        id, kind, ok, m.sum_ts2_s, m.worst_pot_pct, m.peak_speed_dps, m.worst_final_meas_deg, ...
        m.worst_final_true_deg, m.final_fault);
    if isfield(m, 'track_rms_deg')
        fprintf('%-24s tracking error rms %.3f°, max %.3f°\n', '', m.track_rms_deg, m.track_max_deg);
    end
end
T = cell2table(rows, 'VariableNames', {'id', 'description', 'kind', 'ok', 'sum_ts2_s', ...
    'worst_ts2_s', 'worst_pot_pct', 'peak_speed_dps', 'final_meas_deg', 'final_true_deg', ...
    'el_tail_deg', 'final_fault', 'first_fault_s', 'rotor_offset_microsteps', 'cpu_s'});
writetable(T, fullfile(out, 'v5_scenarios.csv'));
summary.all_ok = all(T.ok);
summary.controller = cfg.ctrl;
summary.plant = cfg.plant;
summary.sources = cfg.source;

%% figures ----------------------------------------------------------------
v5_plot(R.pdf_fuzzy, fullfile(out, 'v5_pdf_fuzzy.png'), ...
    'V5: bộ mờ phương vị + servo nâng, chuỗi 60/150/30/90° (mô hình đầy đủ)');
v5_plot(R.pdf_linear, fullfile(out, 'v5_pdf_linear.png'), 'V5: bộ P tuyến tính, cùng giới hạn');
v5_plot(R.track_sine, fullfile(out, 'v5_track.png'), 'V5: bám mục tiêu chuyển động');
v5_plot(R.robust_combined, fullfile(out, 'v5_robust_combined.png'), 'V5: trường hợp xấu kết hợp');
compare_figure(R, fullfile(out, 'v5_compare_controllers.png'));
fault_figure(R, fullfile(out, 'v5_faults.png'));
fuzzy_figure(cfg.ctrl, fullfile(out, 'v5_fuzzy_surface.png'));
log = R.pdf_fuzzy.log; hi = R.pdf_fuzzy.hi; %#ok<NASGU>
save(fullfile(out, 'v5_pdf_fuzzy.mat'), 'log', 'hi');
h = v5_view_cad(60, 60, false, 'off');
exportgraphics(h.figure, fullfile(out, 'v5_cad_in_matlab.png'), 'Resolution', 120);
close(h.figure);
if o.video
    v5_animate(R.pdf_fuzzy, fullfile(out, 'v5_pdf_animation.mp4'), 4, 25);
end
fid = fopen(fullfile(out, 'v5_validation.json'), 'w');
fwrite(fid, jsonencode(summary, PrettyPrint=true));
fclose(fid);
disp(T(:, {'id', 'ok', 'sum_ts2_s', 'worst_pot_pct', 'peak_speed_dps', 'final_meas_deg', ...
    'final_true_deg', 'final_fault'}));
end

%% ------------------------------------------------------------------------
function sc = with(sc, varargin)
for k = 1:2:numel(varargin), sc.(varargin{k}) = varargin{k+1}; end
end

function d = dist(type, t0, t1, value)
d = struct('type', type, 't0', t0, 't1', t1, 'value', value);
end

function compare_figure(R, file)
deg = 180/pi;
fig = figure('Visible', 'off', 'Position', [50 50 1200 800], 'Color', 'w'); light(fig);
tl = tiledlayout(fig, 2, 2, 'TileSpacing', 'compact');
title(tl, 'So sánh: mờ / P tuyến tính / mờ với vận tốc đo / không làm trơn (đoạn 60→150°)');
names = {'pdf_fuzzy', 'pdf_linear', 'pdf_vel_measured', 'pdf_no_smoothing'};
lbl = {'mờ', 'P tuyến tính', 'mờ, vận tốc đo', 'mờ, không làm trơn'};
ax1 = nexttile(tl); ax2 = nexttile(tl); ax3 = nexttile(tl); ax4 = nexttile(tl);
hold([ax1 ax2 ax3 ax4], 'on');
for k = 1:numel(names)
    r = R.(names{k}); H = r.hi; L = r.log;
    plot(ax1, H.t - 12, H.az*deg, 'LineWidth', 1.1);
    plot(ax2, H.t - 12, (150*pi/180 - H.az)*deg, 'LineWidth', 1.1);
    plot(ax3, H.t - 12, H.w*deg, 'LineWidth', 0.8);
    plot(ax4, L.t - 12, L.vout*deg, 'LineWidth', 1.1);
end
xlim(ax1, [0 6]); ylabel(ax1, 'phương vị thật (°)'); grid(ax1, 'on'); legend(ax1, lbl, 'Location', 'southeast');
xlim(ax2, [2.5 6]); ylim(ax2, [-0.5 2]); ylabel(ax2, '150° − thật (°)'); grid(ax2, 'on');
xlim(ax3, [0 6]); ylabel(ax3, 'tốc độ thật (°/s)'); yline(ax3, 30, 'k--'); grid(ax3, 'on');
xlim(ax4, [0 6]); ylabel(ax4, 'tốc độ lệnh STEP (°/s)'); grid(ax4, 'on');
xlabel([ax3 ax4], 't - 12 s');
exportgraphics(fig, file, 'Resolution', 130);
close(fig);
end

function fault_figure(R, file)
deg = 180/pi;
names = {'dist_torque', 'dist_pulse_loss', 'dist_sensor_glitch', 'fault_sensor_fail', ...
    'fault_sensor_freeze', 'fault_jam', 'fault_heartbeat'};
fig = figure('Visible', 'off', 'Position', [50 50 1200 1100], 'Color', 'w'); light(fig);
tl = tiledlayout(fig, numel(names), 1, 'TileSpacing', 'compact');
title(tl, 'Nhiễu và lỗi: phương vị thật/đo, mã lỗi (trục phải)');
for k = 1:numel(names)
    r = R.(names{k}); L = r.log; H = r.hi;
    ax = nexttile(tl);
    yyaxis(ax, 'left');
    plot(ax, H.t, H.az*deg, 'b-', L.t, L.meas*deg, 'r:', L.t, L.target*deg, 'k--');
    ylabel(ax, '°');
    yyaxis(ax, 'right');
    stairs(ax, L.t, L.fault, 'm', 'LineWidth', 1.2);
    ylabel(ax, 'lỗi');
    title(ax, names{k}, 'Interpreter', 'none');
    grid(ax, 'on');
end
exportgraphics(fig, file, 'Resolution', 110);
close(fig);
end

function fuzzy_figure(p, file)
fis = v5_make_fis(p);
fig = figure('Visible', 'off', 'Position', [50 50 1300 450], 'Color', 'w'); light(fig);
tl = tiledlayout(fig, 1, 3, 'TileSpacing', 'compact');
title(tl, 'Bộ mờ Sugeno 25 luật của firmware (giống hệt mã C)');
ax = nexttile(tl);
[x, y] = plotmf(fis, 'input', 1);
plot(ax, x, y, 'LineWidth', 1.2); title(ax, 'e/E: NB NS ZE PS PB'); grid(ax, 'on');
ax = nexttile(tl);
[x, y] = plotmf(fis, 'input', 2);
plot(ax, x, y, 'LineWidth', 1.2); title(ax, '-ω/V: NB NS ZE PS PB'); grid(ax, 'on');
ax = nexttile(tl);
[x1, x2] = meshgrid(linspace(-1, 1, 61));
antenna_core_mex('init', p);
u = antenna_core_mex('fuzzy', x1, x2);
surf(ax, x1, x2, double(u), 'EdgeAlpha', 0.2);
xlabel(ax, 'e/E'); ylabel(ax, '-ω/V'); zlabel(ax, 'u = v/v_{max}');
title(ax, 'Mặt điều khiển'); view(ax, [-35 30]);
exportgraphics(fig, file, 'Resolution', 130);
close(fig);
end

function light(fig)
% exported figures use the light theme whatever the desktop theme is
if exist('theme', 'file') || exist('theme', 'builtin')
    try, theme(fig, 'light'); catch, end
end
end
