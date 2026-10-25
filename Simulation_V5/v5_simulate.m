function res = v5_simulate(cfg, sc)
%V5_SIMULATE Closed-loop simulation of the V5 antenna (azimuth + elevation).
%   res = v5_simulate(cfg, scenario)
%
%   Plant (continuous, RK4 with exact event times):
%     x = [theta_m; omega_m; i_a; i_b; theta_a; omega_a; q_e; omega_e; z]
%     - hybrid stepper, 50 rotor teeth, two phases R-L with back-EMF; the
%       TB6600 chopper is an average current loop limited by the 12 V bus;
%       microstep currents I*cos/sin(Nr*theta_cmd); detent torque
%     - GT2 belt 20T:80T as spring-damper with backlash (contact only)
%     - antenna inertia J(q_e) from CAD V5, LuGre (stick-slip) + viscous friction, cable
%     - LD-1501MG: internal position loop surrogate with torque-speed limit,
%       dead band and the CAD gravity torque
%   controller: 'mex' (C core via MEX, default), 'm' (MATLAB mirror) or
%   'pil' (processor in the loop: the core runs on the board or on the
%   virtual board given by cfg.sim.link; the MEX runs alongside as a shadow
%   and every step is compared bit for bit).
%   Firmware (discrete):
%     - MT6701 read at t_k + 60 us: 14-bit quantisation, INL, noise
%     - control core (C via MEX, or the MATLAB mirror) every 10 ms
%     - STEP command at t_k + 350 us, edges from the stepgen state machine
%     - servo pulse applied at the next 20 ms PWM frame
%
%   scenario fields (see v5_scenario): name, duration, az0, el0, commands,
%   heartbeat_until, dist, plant (overrides), ctrl (overrides), sensor_cal

P = cfg.plant;
if isfield(sc, 'plant'), P = override(P, sc.plant); end
p = cfg.ctrl;
if isfield(sc, 'ctrl'), p = override(p, sc.ctrl); end
controller = cfg.sim.controller;
if isfield(sc, 'controller'), controller = sc.controller; end
useMex = strcmpi(controller, 'mex');
usePil = strcmpi(controller, 'pil');
h = cfg.sim.h;
rng(cfg.sim.seed);

deg = pi/180;
Ts = double(p.ts);
N = round(sc.duration/Ts);
ratio = P.ratio;
dth_m = 2*pi/(200*P.microstep);                  % motor angle per STEP
Jm = P.J_rotor + P.J_pulley;
Vlim = P.V_bus - P.V_drop;

%% sensor model -----------------------------------------------------------
inl = @(phi) P.inl_a1*sin(phi + P.inl_p1) + P.inl_a2*sin(2*phi + P.inl_p2);
if isfield(sc, 'sensor_cal') && sc.sensor_cal
    % after harmonic calibration only a residual remains
    inl = @(phi) 0.03*deg*sin(3*phi + 0.4);
end
cnt = P.sensor_counts;
sensor_raw = @(th, noise) mod(round((P.sensor_sign*th + P.sensor_offset + ...
    inl(P.sensor_sign*th + P.sensor_offset) + noise)*cnt/(2*pi)), cnt);

%% controller initialisation (zero set at azimuth 0 by the 'Z' procedure) -
raw0 = sensor_raw(0, 0);
p.zero_valid = uint8(1);
p.zero_rad = v5_core_step('sensor_angle', p, raw0);   % calibrated sensor angle at the mark
p.sensor_sign = int8(P.sensor_sign);
if useMex || usePil
    rc = antenna_core_mex('init', p);
    if rc ~= 0, error('v5_simulate: parameter check failed (%d)', rc); end
else
    c = v5_core_init(p);
end
pil = struct('steps', 0, 'mismatch', 0, 'first_mismatch', NaN, 'cycles', zeros(N,1), ...
    'link', '');
if usePil
    lk = cfg.sim.link;
    pil.link = lk.kind;
    lk.query("M 1", ["OK M" "ERR M"]);        % STEP output off, core re-initialised
    v5_params_sync(lk, p);
    lk.query("M 1", ["OK M" "ERR M"]);        % re-initialise with these parameters
end

%% plant initial state ----------------------------------------------------
x = zeros(9,1);
x(5) = sc.az0;
x(1) = ratio*sc.az0;
x(7) = sc.el0;
th_cmd0 = x(1);                                   % electrical reference of step 0
I = P.I_set;
x(3) = I; x(4) = 0;                               % holding current at theta_cmd0
sg = v5_stepgen('init', [], 50);
steps_applied = 0;                                % pulses that reached the motor
servo_q = double(p.el_init);                      % servo target angle [rad]
servo_pending = NaN;
t = 0;
next_sg = inf;
last_tick = 0;                                    % time of the last STEP timer interrupt
next_frame = 0;
last_step_t = -inf;
hb_next = 0;
hb_flag = 0;

%% disturbances -----------------------------------------------------------
dist = struct('type', {}, 't0', {}, 't1', {}, 'value', {});
if isfield(sc, 'dist'), dist = sc.dist; end
breaks = [];
for k = 1:numel(dist), breaks = [breaks dist(k).t0 dist(k).t1]; end %#ok<AGROW>
breaks = sort(breaks(breaks > 0));
miss_acc = 0;
held_raw = NaN;
jam_angle = NaN;

%% logs -------------------------------------------------------------------
L.t = (0:N-1)'*Ts;
L.target = zeros(N,1); L.meas = zeros(N,1); L.true = zeros(N,1);
L.vcmd = zeros(N,1); L.vout = zeros(N,1); L.omega = zeros(N,1); L.steps = zeros(N,1); L.hp = zeros(N,1);
L.mode = zeros(N,1); L.fault = zeros(N,1); L.ufz = zeros(N,1); L.wmeas = zeros(N,1);
L.el_cmd = zeros(N,1); L.el = zeros(N,1); L.servo_us = zeros(N,1); L.raw = zeros(N,1);
L.ok = zeros(N,1); L.trk = zeros(N,1);
nh = ceil(sc.duration/cfg.sim.log_dt) + 1;
H.t = nan(nh,1); H.az = nan(nh,1); H.w = nan(nh,1); H.el = nan(nh,1); H.we = nan(nh,1);
H.Te = nan(nh,1); H.Tb = nan(nh,1); H.load_angle = nan(nh,1); H.i = nan(nh,1);
hi = 0; next_log = 0;
peak = struct('w', 0, 'load_angle', 0, 'Tb', 0, 'Te', 0, 'we', 0, 'i', 0);

% constants for the right-hand side (v5_plant_rhs, shared with Simulink)
K = v5_plant_K(P);

cmds = sc.commands;
next_cmd = 1;

for k = 1:N
    tk = (k-1)*Ts;
    % ---- sensor read at tk + t_sample
    advance(tk + P.t_sample);
    [raw, ok] = read_sensor();

    % ---- control step
    if usePil
        flags = ok + 2*hb_flag;
        yl = lk.query(sprintf('X %d %d %d %d', k, raw, sg.steps, flags), ["Y," "ERR X"]);
        q = split(yl, ',');
        ys = antenna_core_mex('step', raw, ok, hb_flag, 0, sg.steps);   % shadow (SIL)
        hp = str2double(q(10)); dirc = str2double(q(11)); servo_us = str2double(q(12));
        f32 = @(h) double(typecast(uint32(hex2dec(h)), 'single'));
        th = f32(q(5)); vc = f32(q(6)); uf = f32(q(7)); wm = f32(q(8)); vo = f32(q(9));
        same = isequal([str2double(q(3)) str2double(q(4)) th vc uf wm vo hp dirc servo_us], ...
            [ys(5) ys(6) ys(7) ys(9) ys(11) ys(8) ys(16) ys(1) ys(2) ys(4)]);
        pil.steps = pil.steps + 1;
        if ~same
            pil.mismatch = pil.mismatch + 1;
            if isnan(pil.first_mismatch), pil.first_mismatch = tk; end
        end
        pil.cycles(k) = str2double(q(14));
        L.mode(k) = str2double(q(3)); L.fault(k) = str2double(q(4)); L.meas(k) = th;
        L.wmeas(k) = wm; L.vcmd(k) = vc; L.ufz(k) = uf; L.vout(k) = vo;
        L.target(k) = ys(12); L.el_cmd(k) = ys(13); L.trk(k) = ys(14);
    elseif useMex
        y = antenna_core_mex('step', raw, ok, hb_flag, 0, sg.steps);
        hp = y(1); dirc = y(2); servo_us = y(4);
        L.mode(k) = y(5); L.fault(k) = y(6); L.meas(k) = y(7); L.wmeas(k) = y(8);
        L.vcmd(k) = y(9); L.ufz(k) = y(11); L.target(k) = y(12); L.el_cmd(k) = y(13);
        L.trk(k) = y(14); L.vout(k) = y(16);
    else
        in = struct('raw', raw, 'sensor_ok', ok, 'heartbeat', hb_flag, 'overrun', 0, ...
            'steps', sg.steps);
        [c, out] = v5_core_step(c, p, in);
        hp = double(out.half_period_us); dirc = double(out.dir); servo_us = double(out.servo_us);
        L.mode(k) = c.mode; L.fault(k) = c.fault; L.meas(k) = c.theta; L.wmeas(k) = c.w_meas;
        L.vcmd(k) = c.v_cmd; L.ufz(k) = c.u_fz; L.target(k) = c.target; L.el_cmd(k) = c.el_cmd;
        L.trk(k) = c.trk_dev; L.vout(k) = c.v_out;
    end
    hb_flag = 0;
    L.raw(k) = raw; L.ok(k) = ok; L.servo_us(k) = servo_us; L.hp(k) = hp;

    % ---- UART lines received up to now are executed after the step (as in
    %      main.c) and therefore act from the next step on
    if tk >= hb_next && tk <= sc.heartbeat_until
        hb_flag = 1; hb_next = hb_next + cfg.sim.host_heartbeat;
    end
    while next_cmd <= numel(cmds) && cmds(next_cmd).t <= tk + 1e-9
        apply_command(cmds(next_cmd));
        next_cmd = next_cmd + 1;
    end

    % ---- actuation: STEP timer and servo compare register
    advance(tk + P.t_act);
    [sg, start] = v5_stepgen('command', sg, hp, dirc);
    if start > 0
        next_sg = t + start*1e-6; last_tick = t;
    elseif sg.running
        [sg, iv] = v5_stepgen('retime', sg, floor((t - last_tick)*1e6 + 1e-6));
        if iv > 0, next_sg = last_tick + iv*1e-6; end
    end
    if servo_us ~= servo_pending, servo_pending = servo_us; end

    advance(tk + Ts);
    L.true(k) = x(5); L.omega(k) = x(6); L.steps(k) = sg.steps; L.el(k) = x(7);
end

H = structfun(@(v) v(1:hi), H, 'UniformOutput', false);
res.name = sc.name;
res.scenario = sc;
res.log = L;
res.hi = H;
res.peak = peak;
res.missed_steps = (x(1) - th_cmd0)/dth_m - steps_applied;   % rotor vs pulses received [microsteps]
res.pulses_lost = sg.steps - steps_applied;
res.plant = P;
res.ctrl = p;
res.controller = controller;
if usePil
    lk.query("M 0", ["OK M" "ERR M"]);        % back to the saved parameters
    pil.cycles = pil.cycles(1:pil.steps);
end
res.pil = pil;
res.metrics = v5_metrics(res);

%% ======================================================================
    function apply_command(cm)
        a = cm.args;
        if usePil
            switch cm.type
                case 'goto'
                    hx = @(v) sprintf('%08X', typecast(single(v), 'uint32'));
                    line = sprintf('GX %d %s %s', a(1), hx(a(2)), hx(a(3)));
                case 'sequence', line = sprintf('Q %d', a(1));
                case 'stop',     line = 'S';
                case 'estop',    line = 'F';
                case 'clear',    line = 'C';
            end
            lk.query(line, ["OK" "ERR"]);
        end
        if useMex || usePil
            switch cm.type
                case 'goto',     antenna_core_mex('goto', a(1), a(2), a(3), a(4));
                case 'sequence', antenna_core_mex('sequence', a(1));
                case 'stop',     antenna_core_mex('stop');
                case 'estop',    antenna_core_mex('estop');
                case 'clear',    antenna_core_mex('clear');
            end
        else
            switch cm.type
                case 'goto',     [c, p] = v5_core_cmd(c, p, 'goto', a(1), a(2), a(3), a(4));
                case 'sequence', [c, p] = v5_core_cmd(c, p, 'sequence', a(1));
                otherwise,       [c, p] = v5_core_cmd(c, p, cm.type);
            end
        end
    end

    function [raw, ok] = read_sensor()
        ok = 1;
        raw = sensor_raw(x(5), P.noise*randn);
        frozen = false;
        for d = 1:numel(dist)
            if t >= dist(d).t0 && t < dist(d).t1
                switch dist(d).type
                    case 'sensor_fail', ok = 0; raw = 0;
                    case 'sensor_freeze'
                        if isnan(held_raw), held_raw = raw; end
                        raw = held_raw; frozen = true;
                    case 'sensor_glitch', raw = mod(raw + dist(d).value, cnt);
                end
            end
        end
        if ~frozen, held_raw = NaN; end
    end

    function advance(t_end)
        % integrate to t_end, processing STEP edges, PWM frames and disturbance breaks
        while t < t_end - 1e-12
            te = min([t_end, next_sg, next_frame, next_log]);
            nb = breaks(breaks > t + 1e-12);
            if ~isempty(nb), te = min(te, nb(1)); end
            if te > t
                integrate(te);
            end
            if abs(t - next_log) < 1e-12 || t > next_log
                log_hi();
                next_log = next_log + cfg.sim.log_dt;
            end
            if t >= next_frame - 1e-12
                if ~isnan(servo_pending)
                    servo_q = (servo_pending - P.servo_us0)/(P.servo_us180 - P.servo_us0)*pi;
                end
                next_frame = next_frame + P.pwm_frame;
            end
            if t >= next_sg - 1e-12
                [sg, nxt, pins] = v5_stepgen('tick', sg);
                last_tick = next_sg;
                if pins.stepped
                    lose = false;
                    for d = 1:numel(dist)
                        if strcmp(dist(d).type, 'pulse_loss') && t >= dist(d).t0 && t < dist(d).t1
                            miss_acc = miss_acc + dist(d).value;
                            if miss_acc >= 1, miss_acc = miss_acc - 1; lose = true; end
                        end
                    end
                    if ~lose
                        steps_applied = steps_applied + pins.dir;
                        last_step_t = t;
                    end
                end
                if nxt > 0, next_sg = next_sg + nxt*1e-6; else, next_sg = inf; end
            end
        end
    end

    function integrate(te)
        % inputs held constant over [t, te]
        th_cmd = th_cmd0 + steps_applied*dth_m;
        Iset = I;
        if t - last_step_t > P.idle_delay, Iset = I*P.idle_ratio; end
        U = [Iset*cos(P.Nr*th_cmd), Iset*sin(P.Nr*th_cmd), servo_q, 0, 0, NaN];
        for d = 1:numel(dist)
            if t >= dist(d).t0 && t < dist(d).t1
                switch dist(d).type
                    case 'torque', U(4) = U(4) + dist(d).value;
                    case 'jam'
                        if isnan(jam_angle), jam_angle = x(5); end
                        U(5) = 1; U(6) = jam_angle;
                end
            end
        end
        if U(5) == 0, jam_angle = NaN; end
        n = max(1, ceil((te - t)/h - 1e-9));
        dt = (te - t)/n;
        for s = 1:n
            k1 = v5_plant_rhs(x, K, U);
            k2 = v5_plant_rhs(x + 0.5*dt*k1, K, U);
            k3 = v5_plant_rhs(x + 0.5*dt*k2, K, U);
            k4 = v5_plant_rhs(x + dt*k3, K, U);
            x = x + dt/6*(k1 + 2*k2 + 2*k3 + k4);
            aw = abs(x(6));
            if aw > peak.w, peak.w = aw; end
            la = abs(P.Nr*(th_cmd - x(1)));
            if la > peak.load_angle, peak.load_angle = la; end
            if abs(x(8)) > peak.we, peak.we = abs(x(8)); end
        end
        t = te;
    end

    function log_hi()
        hi = hi + 1;
        if hi > nh, return; end
        th_cmd = th_cmd0 + steps_applied*dth_m;
        [~, Te, Tb] = v5_plant_rhs(x, K, [0 0 servo_q 0 0 NaN]);
        H.t(hi) = t; H.az(hi) = x(5); H.w(hi) = x(6); H.el(hi) = x(7); H.we(hi) = x(8);
        H.Te(hi) = Te; H.Tb(hi) = Tb; H.load_angle(hi) = P.Nr*(th_cmd - x(1));
        H.i(hi) = hypot(x(3), x(4));
        peak.Tb = max(peak.Tb, abs(Tb)); peak.Te = max(peak.Te, abs(Te));
        peak.i = max(peak.i, H.i(hi));
    end
end

%% ========================================================================
function s = override(s, o)
f = fieldnames(o);
for k = 1:numel(f)
    if isa(s.(f{k}), 'single'), s.(f{k}) = single(o.(f{k}));
    elseif isinteger(s.(f{k})), s.(f{k}) = cast(o.(f{k}), class(s.(f{k})));
    else, s.(f{k}) = o.(f{k});
    end
end
end
