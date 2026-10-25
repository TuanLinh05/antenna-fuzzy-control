function report = v5_sil_check(withPil)
%V5_SIL_CHECK Equivalence tests between MATLAB and the firmware C code.
%   report = v5_sil_check()        SIL: MEX(C core) vs MATLAB mirror vs FIS vs host C
%   report = v5_sil_check(true)    also PIL through the virtual board (same C,
%                                  same line protocol as the STM32)
%   For the real board use v5_pil_board("COM5").
%   Writes results/sil_check.json.
if nargin < 1, withPil = false; end
here = fileparts(mfilename('fullpath'));
cd(here);
if ~exist(fullfile(here, 'results'), 'dir'), mkdir(fullfile(here, 'results')); end
v5_ensure_mex();
report = struct();

%% 1. parameter defaults: C == MATLAB, bit for bit
d = antenna_core_mex('defaults'); m = v5_ctrl_defaults();
f = fieldnames(m); bad = {};
for k = 1:numel(f)
    a = d.(f{k}); b = m.(f{k});
    if ~strcmp(class(a), class(b)) || ~isequal(size(a), size(b)) || ...
            any(typecast(a(:)', 'uint8') ~= typecast(b(:)', 'uint8'))
        bad{end+1} = f{k}; %#ok<AGROW>
    end
end
if ~isempty(setxor(fieldnames(d), f)), bad{end+1} = 'field list'; end
report.defaults_equal = isempty(bad);
report.defaults_mismatch = bad;

%% 2. fuzzy surface: C (MEX) vs MATLAB mirror vs Fuzzy Logic Toolbox vs host C
antenna_core_mex('init', m);
[x1, x2] = meshgrid(linspace(-1, 1, 201));
uc = antenna_core_mex('fuzzy', x1, x2);
um = zeros(size(x1), 'single');
for k = 1:numel(x1), um(k) = v5_fuzzy(m, x1(k), x2(k)); end
fis = v5_make_fis(m, fullfile(here, 'results', 'antenna_v5_azimuth.fis'));
uf = evalfis(fis, [x1(:) x2(:)]);
report.fuzzy_points = numel(x1);
report.fuzzy_mex_vs_m_max = double(max(abs(uc(:) - um(:))));
report.fuzzy_mex_vs_fis_max = max(abs(double(uc(:)) - uf));
hostcsv = fullfile(here, '..', 'Firmware', 'antenna_zephyr', 'tests', 'host', 'out', ...
    'fuzzy_C_vectors.csv');
if isfile(hostcsv)
    hv = readmatrix(hostcsv);
    uh = antenna_core_mex('fuzzy', hv(:, 1), hv(:, 2));
    report.fuzzy_host_vectors = size(hv, 1);
    report.fuzzy_mex_vs_host_max = max(abs(double(uh) - hv(:, 3)));
else
    report.fuzzy_host_vectors = 0;
    report.fuzzy_mex_vs_host_max = NaN;
end

%% 3. step generator: C vs MATLAB mirror on a random command sequence
rng(3);
antenna_core_mex('sg_init', 50);
sg = v5_stepgen('init', [], 50);
mism = 0;
for k = 1:3000
    hp = randi([0 3000]) * (rand > 0.1); dr = sign(rand - 0.3); if dr == 0, dr = 1; end
    if rand < 0.3
        a = antenna_core_mex('sg_command', hp, dr);
        [sg, b] = v5_stepgen('command', sg, hp, dr);
        mism = mism + (a ~= b);
    end
    if rand < 0.2
        el = randi([0 4000]);
        a = antenna_core_mex('sg_retime', el);
        [sg, b] = v5_stepgen('retime', sg, el);
        mism = mism + (a ~= b);
    end
    y = antenna_core_mex('sg_tick');
    [sg, nx, pins] = v5_stepgen('tick', sg);
    mism = mism + ~isequal(y, [nx pins.step_level pins.dir pins.dir_changed pins.stepped sg.steps]);
end
report.stepgen_cases = 3000;
report.stepgen_mismatch = mism;

%% 4. closed loop on the full plant: C core (MEX) vs MATLAB mirror
cfg = v5_config();
sc = v5_scenario('pdf', 'duration', 20);
sc.controller = 'mex'; r1 = v5_simulate(cfg, sc);
sc.controller = 'm';   r2 = v5_simulate(cfg, sc);
report.closed_loop_steps = numel(r1.log.t);
report.closed_loop_max_dtheta_deg = max(abs(r1.log.meas - r2.log.meas))*180/pi;
report.closed_loop_hp_equal = isequal(r1.log.hp, r2.log.hp);
report.closed_loop_servo_equal = isequal(r1.log.servo_us, r2.log.servo_us);

%% 5. PIL through the virtual board
if withPil
    lk = v5_link('virtual');
    cleanup = onCleanup(@() lk.close());
    cfg.sim.link = lk;
    sc.controller = 'pil';
    t0 = tic; r3 = v5_simulate(cfg, sc);
    report.pil_link = 'virtual board (host build of core + link_proto)';
    report.pil_steps = r3.pil.steps;
    report.pil_mismatch = r3.pil.mismatch;
    report.pil_vs_mex_max_dtheta_deg = max(abs(r3.log.meas - r1.log.meas))*180/pi;
    report.pil_wall_time_s = toc(t0);
end

report.pass = report.defaults_equal && report.fuzzy_mex_vs_m_max == 0 && ...
    report.fuzzy_mex_vs_fis_max < 1e-6 && report.stepgen_mismatch == 0 && ...
    report.closed_loop_max_dtheta_deg == 0 && report.closed_loop_hp_equal && ...
    (~withPil || report.pil_mismatch == 0);
fid = fopen(fullfile(here, 'results', 'sil_check.json'), 'w');
fwrite(fid, jsonencode(report, PrettyPrint=true));
fclose(fid);
disp(report);
end
