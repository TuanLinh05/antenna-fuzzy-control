function map = v5_param_names()
%V5_PARAM_NAMES Struct field <-> protocol parameter name (core/link_proto.c).
%   Rows: {field, [row col] or [], protocol name}. 'ts' is read-only on the
%   board and omitted. Protocol values shown by "P" are in degrees where the
%   name says so; PX always carries the internal (SI) value.
scalar = {
    'steps_rev', 'steps_rev'; 'sensor_sign', 'sensor_sign'; 'motor_sign', 'motor_sign';
    'ctrl', 'ctrl'; 'zero_rad', 'zero_deg';
    'cal_a1', 'cal_a1_deg'; 'cal_b1', 'cal_b1_deg'; 'cal_a2', 'cal_a2_deg'; 'cal_b2', 'cal_b2_deg';
    'az_fault', 'az_fault_deg'; 'az_min', 'az_min_deg'; 'az_max', 'az_max_deg';
    'vel_src', 'vel_src'; 'glitch_n', 'glitch_n'; 'smooth_n', 'smooth_n';
    'e_scale', 'e_scale_deg'; 'de_scale', 'de_scale_dps'; 'v_max', 'v_max_dps';
    'mf_e_in', 'mf_e_in'; 'mf_de_in', 'mf_de_in'; 'kp_lin', 'kp_lin';
    'accel', 'accel_dps2'; 'db_out', 'db_out_deg'; 'db_in', 'db_in_deg';
    'vf_alpha', 'vf_alpha'; 'hp_min_us', 'hp_min_us';
    'trk_err', 'trk_err_deg'; 'trk_time', 'trk_time'; 'resync_time', 'resync_time';
    'glitch', 'glitch_deg'; 'hb_timeout', 'hb_timeout';
    'el_min', 'el_min_deg'; 'el_max', 'el_max_deg'; 'el_rate', 'el_rate_dps';
    'el_init', 'el_init_deg'; 'el_ref', 'el_ref_deg'; 'us_ref', 'us_ref';
    'us_per_rad', 'us_per_deg'; 'us_min', 'us_min'; 'us_max', 'us_max';
    'seq_dwell', 'seq_dwell'; 'seq_n', 'seq_n'; 'zero_valid', 'zero_valid'};
map = cell(0, 3);
for k = 1:size(scalar, 1)
    map(end+1, :) = {scalar{k, 1}, [], scalar{k, 2}}; %#ok<AGROW>
end
for i = 1:5
    for j = 1:5
        map(end+1, :) = {'rules', [i j], sprintf('r%d%d', i-1, j-1)}; %#ok<AGROW>
    end
end
for k = 1:8
    map(end+1, :) = {'seq_az', [1 k], sprintf('seq_az%d', k-1)}; %#ok<AGROW>
    map(end+1, :) = {'seq_el', [1 k], sprintf('seq_el%d', k-1)}; %#ok<AGROW>
end
end
