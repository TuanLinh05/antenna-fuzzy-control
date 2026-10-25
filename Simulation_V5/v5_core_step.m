function [c, out] = v5_core_step(c, p, in, varargin)
%V5_CORE_STEP MATLAB mirror of acore_step (antenna_core.c), single precision.
%   [c, out] = v5_core_step(c, p, in)
%     in.raw (0..16383), in.sensor_ok, in.heartbeat, in.overrun, in.steps
%     out.half_period_us, out.dir, out.settled, out.servo_us
%   Helper access (used by other scripts):
%     v5_core_step('raw_to_az', p, raw), ('sensor_angle', p, raw), ('brake', accel, ts, e),
%     ('half_period', p, v), ('servo_us', p, el), ('wrap', x)
if ischar(c)
    switch c
        case 'raw_to_az', c = raw_to_az(p, in);
        case 'sensor_angle', c = sensor_angle(p, in);
        case 'brake', c = brake_speed(single(p), single(in), single(varargin{1}));
        case 'half_period', c = vel_to_hp(p, in);
        case 'servo_us', c = servo_us(p, in);
        case 'wrap', c = wrap_pi(single(p));
    end
    return
end
s = @single;
ts = p.ts;
step_angle = s(2*pi)/p.steps_rev;
c.tick = c.tick + 1;

%% 1. measurement
if c.first
    if in.sensor_ok
        c.theta = raw_to_az(p, in.raw);
        c.target = c.theta;
        c.first = uint8(0);
        c.settled = uint8(1);
        c.bad_count = uint8(0);
        c = resync(c, in);
    else
        c.bad_count = c.bad_count + 1;
        if c.bad_count >= p.glitch_n
            c = enter_fault(c, 32);
        end
    end
else
    predicted = c.theta + c.v_out*ts;
    if in.sensor_ok, th = raw_to_az(p, in.raw); else, th = predicted; end
    d = wrap_pi(th - c.theta);
    if ~in.sensor_ok || abs(d) > p.glitch
        c.bad_count = c.bad_count + 1;           % uint8 saturates at 255 like C
        th = wrap_pi(predicted);
        d = wrap_pi(th - c.theta);
        if c.bad_count >= p.glitch_n
            c = enter_fault(c, 32);
        end
    else
        c.bad_count = uint8(0);
    end
    c.theta = th;
    c.w_meas = c.w_meas + p.vf_alpha*(d/ts - c.w_meas);
end

%% 2. supervision
if in.overrun
    c.overrun_count = c.overrun_count + 1;
    if c.overrun_count >= 3, c = enter_fault(c, 8); end
else
    c.overrun_count = uint8(0);
end
if ~c.first && c.mode ~= 0 && abs(c.theta) > p.az_fault
    c = enter_fault(c, 2);
end
if c.hb_required
    if in.heartbeat, c.hb_age = s(0); else, c.hb_age = c.hb_age + ts; end
    if p.hb_timeout > 0 && c.hb_age > p.hb_timeout
        c = enter_fault(c, 1);
    end
end
if ~c.first
    if c.out.half_period_us == 0 && c.v_cmd == 0 && c.v_out == 0
        c.idle_time = c.idle_time + ts;
        if c.idle_time >= p.resync_time
            c = resync(c, in);
        end
    else
        c.idle_time = s(0);
    end
    c.trk_dev = s(int32(in.steps) - c.step_ref)*step_angle - (c.theta - c.theta_ref);
    if c.mode == 1 && abs(c.trk_dev) > p.trk_err
        c.trk_timer = c.trk_timer + ts;
        if c.trk_timer >= p.trk_time, c = enter_fault(c, 4); end
    else
        c.trk_timer = s(0);
    end
end

%% 3. built-in sequence
if c.seq_active && c.mode == 1
    if c.seq_timer >= p.seq_dwell - s(0.5)*ts
        c.seq_idx = c.seq_idx + 1;
        if c.seq_idx >= p.seq_n
            if c.seq_loop, c.seq_idx = uint8(0); else, c.seq_active = uint8(0); end
        end
        if c.seq_active, c = sequence_point(c, p); end
    end
    c.seq_timer = c.seq_timer + ts;
end

%% 4. azimuth control law
if c.mode == 1 && ~c.first
    e = c.target - (c.theta + c.pending);
    ae = abs(e);
    if c.settled
        if ae > p.db_out, c.settled = uint8(0); end
    elseif ae < p.db_in
        c.settled = uint8(1);
    end
    if c.settled
        c.v_des = s(0); c.u_fz = s(0);
    else
        if p.ctrl == 0
            if p.vel_src == 0, w_hat = c.v_cmd; else, w_hat = c.w_meas; end
            x1 = min(s(1), max(s(-1), e/p.e_scale));
            x2 = min(s(1), max(s(-1), -w_hat/p.de_scale));
            c.u_fz = v5_fuzzy(p, x1, x2);
            c.v_des = p.v_max*c.u_fz;
        else
            c.u_fz = s(0);
            c.v_des = min(p.v_max, max(-p.v_max, p.kp_lin*e));
        end
        vb = brake_speed(p.accel, ts, ae);
        c.v_des = min(vb, max(-vb, c.v_des));
    end
    c.v_cmd = c.v_cmd + min(p.accel*ts, max(-p.accel*ts, c.v_des - c.v_cmd));
else
    c = clear_motion(c); c.u_fz = s(0);
end

%% 4b. command smoothing (moving average over smooth_n periods)
if p.smooth_n ~= c.vh_n
    c.vhist(:) = 0;
    c.vh_n = p.smooth_n;
end
if c.vh_n <= 1
    c.v_out = c.v_cmd;
    c.pending = s(0);
else
    c.vhist(mod(double(c.tick), double(c.vh_n)) + 1) = c.v_cmd;
    acc = s(0); idle = true;
    for i = 1:double(c.vh_n)
        acc = acc + c.vhist(i);
        if c.vhist(i) ~= 0, idle = false; end
    end
    c.v_out = acc/s(c.vh_n);
    if idle, c.pending = s(0); else, c.pending = c.pending + (c.v_cmd - c.v_out)*ts; end
end

%% 5. elevation ramp
if c.mode ~= 2
    c.el_cmd = c.el_cmd + min(p.el_rate*ts, max(-p.el_rate*ts, c.el_target - c.el_cmd));
end

%% 6. outputs
c.out.half_period_us = vel_to_hp(p, c.v_out);
if c.out.half_period_us ~= 0
    if c.v_out > 0, c.out.dir = int8(1); else, c.out.dir = int8(-1); end
end
c.out.settled = c.settled;
c.out.servo_us = servo_us(p, c.el_cmd);
out = c.out;
end

%% ------------------------------------------------------------------------
function c = clear_motion(c)
c.v_cmd = single(0); c.v_des = single(0); c.v_out = single(0); c.pending = single(0);
c.vhist(:) = 0;
end

function c = enter_fault(c, bits)
c.fault = bitor(c.fault, uint16(bits));
c.mode = uint8(2);
c = clear_motion(c);
c.seq_active = uint8(0); c.hb_required = uint8(0);
c.el_target = c.el_cmd;
end

function c = resync(c, in)
c.step_ref = int32(in.steps);
c.theta_ref = c.theta;
c.trk_timer = single(0);
c.trk_dev = single(0);
end

function c = sequence_point(c, p)
i = double(c.seq_idx) + 1;
c.target = min(p.az_max, max(p.az_min, p.seq_az(i)));
c.el_target = min(p.el_max, max(p.el_min, p.seq_el(i)));
c.settled = uint8(0);
c.seq_timer = single(0);
end

function x = wrap_pi(x)
PI = single(pi); TWO = single(2*pi);
while x > PI, x = x - TWO; end
while x <= -PI, x = x + TWO; end
end

function phi = sensor_angle(p, raw)
phi = single(bitand(uint32(raw), uint32(16383)))*(single(2*pi)/single(16384));
if p.cal_a1 ~= 0 || p.cal_b1 ~= 0 || p.cal_a2 ~= 0 || p.cal_b2 ~= 0
    phi = phi - (p.cal_a1*cos(phi) + p.cal_b1*sin(phi) + p.cal_a2*cos(single(2)*phi) + ...
        p.cal_b2*sin(single(2)*phi));
end
end

function az = raw_to_az(p, raw)
d = wrap_pi(sensor_angle(p, raw) - p.zero_rad);
if p.sensor_sign > 0, az = d; else, az = -d; end
end

function v = brake_speed(accel, ts, abs_err)
h = single(0.5)*accel*ts;
v = sqrt(h*h + single(2)*accel*abs_err) - h;
end

function hp = vel_to_hp(p, v)
f = abs(v)*p.steps_rev*(single(1)/single(2*pi));
if f < single(500000)/single(65535)
    hp = uint32(0);
    return
end
h = single(500000)/f + single(0.5);
if h < p.hp_min_us, h = p.hp_min_us; end
if h > single(65535), h = single(65535); end
hp = uint32(fix(double(h)));
end

function us = servo_us(p, el)
u = p.us_ref + (el - p.el_ref)*p.us_per_rad;
u = min(p.us_max, max(p.us_min, u));
us = uint16(fix(double(u + single(0.5))));
end

