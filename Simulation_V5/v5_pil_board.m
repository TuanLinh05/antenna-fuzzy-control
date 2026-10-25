function report = v5_pil_board(port, duration)
%V5_PIL_BOARD Processor-in-the-loop test on the real STM32 Blue Pill.
%   report = v5_pil_board("COM5")        course sequence, 48 s of model time
%   report = v5_pil_board("COM5", 20)
%
%   The board runs the control core compiled for Cortex-M3 by Zephyr; MATLAB
%   simulates the motor, belt, antenna, MT6701 and servo and exchanges one
%   line per 10 ms step over the UART ("X k raw steps flags" -> "Y,..."). In
%   PIL mode the firmware keeps the TB6600 released and emits no STEP pulse,
%   so the motor may stay connected, but keep the 12 V supply OFF anyway.
%   Every step is compared bit for bit with the same core run as a MEX
%   (SIL), and the execution time measured on the chip is reported.
%   Results: results/pil_board.json, results/pil_board.png
if nargin < 2, duration = 48; end
here = fileparts(mfilename('fullpath'));
v5_ensure_mex();
lk = v5_link('serial', port);
cleanup = onCleanup(@() lk.close());
lk.drain(0.5);
v = lk.query("V", "V,");
cfg = v5_config();
cfg.sim.link = lk;
sc = v5_scenario('pdf', 'duration', duration);
sc.controller = 'pil';
t0 = tic;
r = v5_simulate(cfg, sc);
cyc = r.pil.cycles;
f_cpu = 72e6;
report = struct('firmware', char(v), 'port', char(port), 'steps', r.pil.steps, ...
    'mismatch', r.pil.mismatch, 'first_mismatch_s', r.pil.first_mismatch, ...
    'core_exec_us_mean', mean(cyc)/f_cpu*1e6, 'core_exec_us_max', max(cyc)/f_cpu*1e6, ...
    'wall_time_s', toc(t0), 'metrics', rmfield(r.metrics, 'segments'));
fid = fopen(fullfile(here, 'results', 'pil_board.json'), 'w');
fwrite(fid, jsonencode(report, PrettyPrint=true));
fclose(fid);
v5_plot(r, fullfile(here, 'results', 'pil_board.png'), ...
    sprintf('PIL: lõi điều khiển chạy trên STM32F103 (%s), mô hình V5 trong MATLAB', port));
disp(report);
end
