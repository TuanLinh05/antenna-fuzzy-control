function cal = v5_fit_sensor_cal(raw, steps, steps_rev, sensor_sign)
%V5_FIT_SENSOR_CAL Harmonic correction of the MT6701 from STEP-counted angles.
%   cal = v5_fit_sensor_cal(raw, steps)            12800 STEP/rev, sign +1
%   cal = v5_fit_sensor_cal(raw, steps, steps_rev, sensor_sign)
%   raw   : MT6701 readings (0..16383) at rest, one per calibration point
%   steps : STEP counter at the same instants (the stepper + 4:1 belt is the
%           reference: 0.028 deg per microstep at the antenna, no drift)
%   Points must all be approached from the same side so the belt preload is
%   the same. Fits  phi - s*theta_steps = c0 + a1 cos(phi) + b1 sin(phi)
%   + a2 cos(2 phi) + b2 sin(2 phi), phi = raw*2*pi/16384, and returns the
%   coefficients in rad (firmware parameters cal_a1..cal_b2) and the RMS
%   residual. The constant c0 is the zero offset and is not part of cal.
if nargin < 3, steps_rev = 12800; end
if nargin < 4, sensor_sign = 1; end
phi = double(raw(:))*2*pi/16384;
th = double(steps(:))*2*pi/steps_rev;
d = unwrap(phi) - sensor_sign*th;
A = [ones(size(phi)) cos(phi) sin(phi) cos(2*phi) sin(2*phi)];
x = A\d;
res = d - A*x;
cal = struct('a1', x(2), 'b1', x(3), 'a2', x(4), 'b2', x(5), 'c0', x(1), ...
    'rms_before_deg', std(d)*180/pi, 'rms_after_deg', sqrt(mean(res.^2))*180/pi, ...
    'points', numel(phi), 'span_deg', (max(phi) - min(phi))*180/pi);
end
