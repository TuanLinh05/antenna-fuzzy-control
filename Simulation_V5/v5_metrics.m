function m = v5_metrics(res)
%V5_METRICS Step-response indicators of a v5_simulate result.
%   For every azimuth target change (>= 0.5 deg):
%     pot_pct           percent overshoot as in the course text: (y_max - y_final)/(y_final - y_0)
%                       on the true antenna angle (y_final = mean of the last second)
%     overshoot_pct     max excursion beyond the target, % of the step (true angle)
%     overshoot_deg     same in degrees; overshoot_meas_pct from the MT6701 value
%     ts2_s             2 % settling time of the true angle (inf if never inside)
%     ts_abs_s          settling into +-0.1 deg (true angle)
%     final_true_deg    |true - target| averaged over the last second
%     final_meas_deg    |mean measured - target| over the last second
%     peak_speed_dps    max |omega| of the antenna during the segment
%   Global: peak antenna speed, motor load angle, faults, elevation errors.
deg = pi/180;
L = res.log; H = res.hi;
tgt = L.target;
chg = find(abs(diff(tgt)) > 0.5*deg) + 1;
if ~isempty(tgt) && L.mode(1) == 1 && abs(tgt(1) - L.true(1)) > 0.5*deg
    chg = [1; chg];
end
seg = repmat(struct('t0', 0, 'from_deg', 0, 'to_deg', 0, 'pot_pct', 0, 'overshoot_pct', 0, ...
    'overshoot_deg', 0, 'overshoot_meas_pct', 0, 'ts2_s', inf, 'ts_abs_s', inf, ...
    'final_true_deg', 0, 'final_meas_deg', 0, 'peak_speed_dps', 0), numel(chg), 1);
for j = 1:numel(chg)
    k0 = chg(j);
    if j < numel(chg), k1 = chg(j+1) - 1; else, k1 = numel(tgt); end
    t0 = L.t(k0); t1 = L.t(k1) + (L.t(2) - L.t(1));
    target = tgt(k0);
    if k0 > 1, from = tgt(k0-1); else, from = L.true(1); end
    step = target - from;
    hk = H.t >= t0 & H.t < t1;
    az = H.az(hk); th = H.t(hk);
    sgn = sign(step);
    over = max(0, max(sgn*(az - target)));
    overm = max(0, max(sgn*(L.meas(k0:k1) - target)));
    out2 = find(abs(az - target) > 0.02*abs(step), 1, 'last');
    outa = find(abs(az - target) > 0.1*deg, 1, 'last');
    seg(j).t0 = t0;
    seg(j).from_deg = from/deg;
    seg(j).to_deg = target/deg;
    seg(j).overshoot_pct = 100*over/abs(step);
    seg(j).overshoot_deg = over/deg;
    seg(j).overshoot_meas_pct = 100*overm/abs(step);
    seg(j).ts2_s = settle(out2, th, t0, t1);
    seg(j).ts_abs_s = settle(outa, th, t0, t1);
    last = th >= t1 - 1;
    yf = mean(az(last)); y0 = az(1);
    if abs(yf - y0) > 0
        seg(j).pot_pct = 100*max(0, max(sign(yf - y0)*(az - yf)))/abs(yf - y0);
    end
    seg(j).final_true_deg = mean(abs(az(last) - target))/deg;
    % steady-state error seen by the sensor: mean over the last second (the
    % 14-bit sample noise of +-1 LSB is not a control error)
    lastk = L.t(k0:k1) >= t1 - 1;
    mk = L.meas(k0:k1);
    seg(j).final_meas_deg = abs(mean(mk(lastk)) - target)/deg;
    seg(j).peak_speed_dps = max(abs(H.w(hk)))/deg;
end
m.segments = seg;
if isempty(seg)
    m.worst_overshoot_pct = 0; m.worst_pot_pct = 0; m.worst_ts2_s = 0; m.sum_ts2_s = 0;
    m.worst_final_true_deg = 0; m.worst_final_meas_deg = 0;
else
    m.worst_overshoot_pct = max([seg.overshoot_pct]);
    m.worst_pot_pct = max([seg.pot_pct]);
    m.worst_ts2_s = max([seg.ts2_s]);
    m.sum_ts2_s = sum([seg.ts2_s]);
    m.worst_final_true_deg = max([seg.final_true_deg]);
    m.worst_final_meas_deg = max([seg.final_meas_deg]);
end
m.peak_speed_dps = res.peak.w/deg;
m.peak_load_angle_edeg = res.peak.load_angle/deg;      % electrical degrees (slip > 180)
m.peak_belt_torque_Nm = res.peak.Tb;
m.peak_motor_torque_Nm = res.peak.Te;
m.rotor_offset_microsteps = res.missed_steps;   % rotor vs received pulses (slip if >= 32)
m.pulses_lost = res.pulses_lost;
m.final_fault = L.fault(end);
f = find(L.fault ~= 0, 1);
if isempty(f), m.first_fault_s = NaN; else, m.first_fault_s = L.t(f); end
m.rms_error_deg = sqrt(mean((L.true - L.target).^2))/deg;
% elevation: |true - command| over the last second of each segment while the
% (ramped) command is constant
elc = L.el_cmd;
ends = [chg(2:end) - 1; numel(tgt)];
m.el_tail_error_deg = 0;
for k1 = ends'
    kk = max(1, k1 - 99):k1;
    if max(elc(kk)) - min(elc(kk)) < 1e-6
        m.el_tail_error_deg = max(m.el_tail_error_deg, max(abs(L.el(kk) - elc(kk)))/deg);
    end
end
m.peak_el_speed_dps = res.peak.we/deg;
% "steady-state error = 0" is judged at the resolution of the loop: inside the
% controller dead band (db_out = 0.1 deg = 4.5 MT6701 LSB = 3.6 microsteps)
m.pass_spec = m.worst_pot_pct <= 2 && m.peak_speed_dps <= 30 && ...
    m.worst_final_meas_deg <= 0.1 && m.final_fault == 0 && all(isfinite([seg.ts2_s]));
end

function ts = settle(idx, th, t0, t1)
if isempty(idx)
    ts = 0;
elseif idx < numel(th)
    ts = th(idx+1) - t0;
else
    ts = inf;
end
if ts > t1 - t0, ts = inf; end
end
