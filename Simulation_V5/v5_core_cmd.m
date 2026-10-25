function [c, p, rc] = v5_core_cmd(c, p, cmd, varargin)
%V5_CORE_CMD Commands of the MATLAB core mirror (acore_cmd_* in C).
%   [c,p,rc] = v5_core_cmd(c,p,'goto',mask,az,el,host)  mask: 1 az, 2 el, 3 both
%   [c,p,rc] = v5_core_cmd(c,p,'stop')
%   [c,p,rc] = v5_core_cmd(c,p,'estop')
%   [c,p,rc] = v5_core_cmd(c,p,'clear')
%   [c,p,rc] = v5_core_cmd(c,p,'sequence',loop)
%   [c,p,rc] = v5_core_cmd(c,p,'zero',raw,az_now)
s = @single;
rc = 0;
switch cmd
    case 'goto'
        mask = varargin{1}; az = s(varargin{2}); el = s(varargin{3}); host = varargin{4};
        if c.mode == 2, rc = -1; return; end
        if bitand(mask, 1) && (c.mode == 0 || c.first), rc = -2; return; end
        if isnan(az) || isnan(el), rc = -3; return; end
        if bitand(mask, 1)
            c.target = min(p.az_max, max(p.az_min, az));
            c.settled = uint8(0);
        end
        if bitand(mask, 2)
            c.el_target = min(p.el_max, max(p.el_min, el));
        end
        c.seq_active = uint8(0);
        c.hb_required = uint8(host && p.hb_timeout > 0);
        c.hb_age = s(0);
    case 'stop'
        c.seq_active = uint8(0);
        c.hb_required = uint8(0);
        if c.mode == 1 && ~c.first
            v = c.v_cmd;
            dist = v*abs(v)/(s(2)*p.accel) + s(0.5)*v*p.ts;
            c.target = min(p.az_max, max(p.az_min, c.theta + c.pending + dist));
            c.settled = uint8(0);
        end
        c.el_target = c.el_cmd;
    case 'estop'
        c.fault = bitor(c.fault, uint16(16));
        c.mode = uint8(2);
        c.v_cmd = s(0); c.v_des = s(0); c.v_out = s(0); c.pending = s(0); c.vhist(:) = 0;
        c.seq_active = uint8(0); c.hb_required = uint8(0);
        c.el_target = c.el_cmd;
    case 'clear'
        c.fault = uint16(0); c.bad_count = uint8(0); c.overrun_count = uint8(0);
        c.hb_required = uint8(0); c.trk_timer = s(0);
        c.v_cmd = s(0); c.v_des = s(0); c.v_out = s(0); c.pending = s(0); c.vhist(:) = 0;
        c.target = c.theta; c.settled = uint8(1);
        c.idle_time = p.resync_time;
        c.mode = uint8(p.zero_valid ~= 0);
    case 'sequence'
        if c.mode ~= 1 || c.first || p.seq_n == 0, rc = -1; return; end
        c.seq_active = uint8(1);
        c.seq_loop = uint8(varargin{1} ~= 0);
        c.seq_idx = uint8(0);
        c.hb_required = uint8(0);
        c.target = min(p.az_max, max(p.az_min, p.seq_az(1)));
        c.el_target = min(p.el_max, max(p.el_min, p.seq_el(1)));
        c.settled = uint8(0);
        c.seq_timer = s(0);
    case 'zero'
        raw = varargin{1}; az_now = s(varargin{2});
        if c.mode == 1 && (c.v_cmd ~= 0 || c.v_out ~= 0 || c.out.half_period_us ~= 0), rc = -1; return; end
        if abs(az_now) > p.az_max, rc = -2; return; end
        z0 = p.zero_rad; p.zero_rad = s(0); sgn = p.sensor_sign; p.sensor_sign = int8(1);
        phi = v5_core_step('raw_to_az', p, raw);          % calibrated sensor angle, wrapped
        p.zero_rad = z0; p.sensor_sign = sgn;
        if p.sensor_sign > 0, ref = az_now; else, ref = -az_now; end
        p.zero_rad = v5_core_step('wrap', phi - ref);
        p.zero_valid = uint8(1);
        c.theta = v5_core_step('raw_to_az', p, raw);
        c.target = c.theta; c.settled = uint8(1); c.w_meas = s(0);
        c.idle_time = p.resync_time;
        if c.mode == 0, c.mode = uint8(1); end
    otherwise
        error('v5_core_cmd: unknown command %s', cmd);
end
end
