function cal = v5_calibrate_mt6701(port, apply)
%V5_CALIBRATE_MT6701 Measure and correct the MT6701 non-linearity on the board.
%   cal = v5_calibrate_mt6701("COM5")          measure and fit only
%   cal = v5_calibrate_mt6701("COM5", true)    also write cal_* and the
%                                               re-based zero, then save (W)
%   Requirements: zero set (Z), 12 V on, free travel -140..+135 deg, cables
%   slack. The antenna visits 19 points from -135 to +135 deg, always moving
%   in the positive direction; at each point the STEP counter (reference,
%   0.028 deg/microstep at the antenna) and the raw MT6701 value are logged.
%   The same procedure is verified on the model by v5_calibration_demo.
if nargin < 2, apply = false; end
here = fileparts(mfilename('fullpath'));
deg = pi/180;
lk = v5_link('serial', port);
cleanup = onCleanup(@() lk.close());
lk.send("T 50");
lk.drain(0.3);
pts = -135:15:135;
raw = zeros(numel(pts), 1); st = zeros(numel(pts), 1);
move(-140);
for i = 1:numel(pts)
    move(pts(i));
    [raw(i), st(i)] = sample(10);
    fprintf('%7.1f deg: raw %5d  steps %7d\n', pts(i), raw(i), st(i));
end
move(0);
p = read_params();
cal = v5_fit_sensor_cal(raw, st, p.steps_rev, p.sensor_sign);
cal.raw = raw; cal.steps = st; cal.points_deg = pts;
fprintf('RMS (sensor - STEP) %.3f deg -> after fit %.3f deg\n', cal.rms_before_deg, cal.rms_after_deg);
d = fullfile(here, 'results', 'hw_logs');
if ~exist(d, 'dir'), mkdir(d); end
fid = fopen(fullfile(d, ['mt6701_cal_' char(datetime('now', 'Format', 'yyyyMMdd_HHmmss')) '.json']), 'w');
fwrite(fid, jsonencode(cal, PrettyPrint=true)); fclose(fid);
if apply
    % keep the mechanical zero mark at 0 deg after the correction
    z = p.zero_rad;
    zn = z - (cal.a1*cos(z) + cal.b1*sin(z) + cal.a2*cos(2*z) + cal.b2*sin(2*z));
    vals = {'cal_a1_deg', cal.a1; 'cal_b1_deg', cal.b1; 'cal_a2_deg', cal.a2; ...
        'cal_b2_deg', cal.b2; 'zero_deg', zn};
    for k = 1:size(vals, 1)
        lk.query(sprintf('PX %s %08X', vals{k, 1}, typecast(single(vals{k, 2}), 'uint32')), ...
            ["OK P" "ERR P"]);
    end
    r = lk.query("W", ["OK W" "ERR W"]);
    fprintf('saved: %s\n', r);
end

    function move(az)
        lk.query(sprintf('A %.3f', az), ["OK A" "ERR A"]);
        t0 = tic; still = 0;
        while toc(t0) < 30
            lk.send("H");
            l = lk.readline(0.2);
            if startsWith(l, "T,")
                v = sscanf(extractAfter(l, 2), '%f,');
                if v(3) ~= 0, error('fault %d during calibration', v(3)); end
                if v(14) == 1 && v(6) == 0 && abs(v(4) - v(5)) < 100
                    still = still + 1;
                    if still >= 10, return; end      % 0.5 s settled
                else
                    still = 0;
                end
            end
        end
        error('point %.1f deg not reached', az);
    end

    function [r, s] = sample(n)
        R = []; S = [];
        while numel(R) < n
            lk.send("H");
            l = lk.readline(0.5);
            if startsWith(l, "T,")
                v = sscanf(extractAfter(l, 2), '%f,');
                R(end+1) = v(9); S(end+1) = v(8); %#ok<AGROW>
            end
        end
        r = median(R); s = median(S);
    end

    function p = read_params()
        lk.send("P");
        p = struct('steps_rev', 12800, 'sensor_sign', 1, 'zero_rad', 0);
        t0 = tic;
        while toc(t0) < 5
            l = lk.readline(0.5);
            if startsWith(l, "OK P"), break; end
            q = split(l, ',');
            if numel(q) == 4 && q(1) == "P"
                switch q(2)
                    case "steps_rev", p.steps_rev = str2double(q(3));
                    case "sensor_sign", p.sensor_sign = str2double(q(3));
                    case "zero_deg"
                        p.zero_rad = double(typecast(uint32(hex2dec(q(4))), 'single'));
                end
            end
        end
    end
end
