function c = v5_core_init(p)
%V5_CORE_INIT MATLAB mirror of acore_init (antenna_core.c).
s = @single;
c.tick = uint32(0);
c.mode = uint8(0);                  % 0 NOZERO, 1 ACTIVE, 2 FAULT
c.first = uint8(1);
c.settled = uint8(0);
c.hb_required = uint8(0);
c.fault = uint16(0);
c.bad_count = uint8(0);
c.overrun_count = uint8(0);
c.theta = s(0); c.w_meas = s(0); c.v_cmd = s(0); c.v_des = s(0); c.u_fz = s(0);
c.v_out = s(0); c.pending = s(0); c.vhist = zeros(1, 16, 'single'); c.vh_n = uint8(0);
c.target = s(0); c.hb_age = s(0); c.trk_timer = s(0); c.idle_time = s(0);
c.trk_dev = s(0); c.step_ref = int32(0); c.theta_ref = s(0);
c.el_cmd = s(0); c.el_target = s(0);
c.seq_active = uint8(0); c.seq_loop = uint8(0); c.seq_idx = uint8(0);
c.seq_timer = s(0);
c.out = struct('half_period_us', uint32(0), 'dir', int8(1), 'settled', uint8(0), ...
    'servo_us', uint16(0));
if p.zero_valid
    c.mode = uint8(1);
end
c.el_cmd = min(p.el_max, max(p.el_min, p.el_init));
c.el_target = c.el_cmd;
c.out.servo_us = v5_core_step('servo_us', p, c.el_cmd);
end
