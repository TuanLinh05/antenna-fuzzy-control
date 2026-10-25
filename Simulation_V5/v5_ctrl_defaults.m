function p = v5_ctrl_defaults()
%V5_CTRL_DEFAULTS Controller parameters = acore_params_default() in C.
%   Single precision, same field names and same arithmetic as the firmware
%   core (antenna_core.c). v5_sil_check verifies equality bit for bit with
%   the values returned by the MEX build of the C core.
s = @single;
D = @(x) s(x)*(s(pi)/s(180));
centre = s([-1 -0.5 0 0.5 1]);

p.ts = s(0.01);
p.steps_rev = s(200)*s(16)*s(4);
p.sensor_sign = int8(1);
p.motor_sign = int8(1);
p.zero_valid = uint8(0);
p.ctrl = uint8(0);                 % 0 fuzzy, 1 linear baseline
p.zero_rad = s(0);
p.cal_a1 = s(0); p.cal_b1 = s(0); p.cal_a2 = s(0); p.cal_b2 = s(0);
p.az_min = D(-150);
p.az_max = D(150);
p.az_fault = D(155);
p.vel_src = uint8(0);              % 0 commanded velocity, 1 measured
p.glitch_n = uint8(3);
p.smooth_n = uint8(13);           % STEP velocity moving average (130 ms)
p.e_scale = D(6);
p.de_scale = D(26);
p.v_max = D(26);
p.mf_e_in = s(0.5);
p.mf_de_in = s(0.5);
r = zeros(5, 'single');
for i = 1:5
    for j = 1:5
        r(i,j) = min(s(1), max(s(-1), s(2)*centre(i) + s(0.5)*centre(j)));
    end
end
p.rules = r;                       % rows: e NB..PB, columns: de/dt NB..PB
p.kp_lin = s(5.8);
p.accel = D(60);
p.db_in = D(0.03);
p.db_out = D(0.10);
p.vf_alpha = s(0.3);
p.hp_min_us = s(100);
p.trk_err = D(4);
p.trk_time = s(0.3);
p.resync_time = s(0.5);
p.glitch = D(3);
p.hb_timeout = s(2);
p.el_min = D(45);
p.el_max = D(135);
p.el_rate = D(30);
p.el_init = D(90);
p.el_ref = D(90);
p.us_ref = s(1500);
p.us_per_rad = s(2000)/s(pi);
p.us_min = s(1000);
p.us_max = s(2000);
p.seq_dwell = s(12);
p.seq_n = uint8(4);
p.seq_az = [D(60) D(150) D(30) D(90) zeros(1,4,'single')];
p.seq_el = [D(60) D(90) D(120) D(80) zeros(1,4,'single')];
end
