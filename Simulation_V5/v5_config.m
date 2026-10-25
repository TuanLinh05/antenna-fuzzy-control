function cfg = v5_config()
%V5_CONFIG Parameters of the V5 antenna model (SI units, angles in rad).
%   cfg.plant  : 17HS1352-P4130 + TB6600 (12 V) + GT2 20T:80T + CAD V5 load
%                + MT6701 on the azimuth shaft + LD-1501MG elevation servo
%   cfg.ctrl   : controller parameters, identical to acore_params_default()
%                in ../Firmware/antenna_zephyr/core/antenna_core.c
%   cfg.sim    : numerical settings
%   cfg.source : provenance of every non-CAD plant number
%
% Numbers marked "assumed" have no measurement yet; the robustness runs in
% v5_run_all vary them. CAD values are read from the V5 delivery.

here = fileparts(mfilename('fullpath'));
cadDir = fullfile(here, '..', '3D Print', 'Antenna_V5_Reinforced');
cad = jsondecode(fileread(fullfile(cadDir, 'audit', 'simulation_parameters_v5.json')));
geo = jsondecode(fileread(fullfile(cadDir, 'parameters.json')));
deg = pi/180;

%% Stepper motor 17HS1352-P4130 (seller listing + 17HS catalogue)
P.Nr        = 50;            % rotor teeth (1.8 deg full step)
P.R         = 2.1;           % ohm/phase
P.L         = 2.5e-3;        % H/phase
P.I_rated   = 1.3;           % A
P.T_hold    = 0.25;          % N.m, both phases at rated current
P.Km        = P.T_hold/(sqrt(2)*P.I_rated);   % N.m/A per phase
P.J_rotor   = 35e-7;         % kg.m^2 (35 g.cm^2)
P.T_detent  = 0.012;         % N.m (assumed, typical 34 mm NEMA17)
P.b_motor   = 1e-4;          % N.m.s/rad internal damping (assumed, NEMA17 order)
P.Tc_motor  = 0.002;         % N.m bearing friction (assumed)
P.eps_motor = 0.05;          % rad/s friction smoothing

%% TB6600 driver at 12 V
P.V_bus     = 12;
P.V_drop    = 0.8;           % bridge drop at ~1 A (assumed)
P.I_set     = 1.2;           % A peak: DIP 1.0 A (1.2 A peak) for a 1.3 A motor
P.microstep = 16;
P.Kc        = 60;            % ohm, average model of the chopper current loop
P.idle_ratio = 0.5;          % "automatic semi-flow" standstill current
P.idle_delay = 0.3;          % s without STEP before current reduction (assumed)

%% GT2 belt 20T:80T (CAD: 80 grooves counted, belt 280 mm, centre 87.917 mm)
P.ratio     = geo.driven_teeth/geo.driver_teeth;          % 4
r1 = geo.driver_teeth*geo.belt_pitch/(2*pi)*1e-3;          % m
r2 = geo.driven_teeth*geo.belt_pitch/(2*pi)*1e-3;
C  = geo.motor_center_distance*1e-3;
P.span      = sqrt(C^2 - (r2-r1)^2);                       % m
P.belt_EA   = 5e3;           % N, 6 mm glass-fibre GT2 (assumed, 3..8 kN)
k_belt = 2*P.belt_EA/P.span*r2^2;                          % both spans preloaded
P.k_teeth   = 200;           % N.m/rad printed 80T teeth/D-flat (assumed)
P.k_belt    = 1/(1/k_belt + 1/P.k_teeth);                  % N.m/rad at the antenna
P.backlash  = 0.2*deg;       % total tooth clearance at the antenna (assumed)
P.gap_soft  = 0.10;          % stiffness inside the clearance / k_belt: belt pretension keeps
                             % the teeth loaded (0 = hard gap, contact forces only)
P.J_pulley  = 3e-7;          % kg.m^2 GT2 20T aluminium pulley (estimated)
P.belt_eta  = 0.10;          % material loss factor of the neoprene belt (assumed, 0.05..0.15)
J_m_ref = P.ratio^2*(P.J_rotor + P.J_pulley);
% lowest torsional mode: antenna on (belt in series with the stepper's magnetic
% stiffness N_r*K_m*I referred to the antenna); belt damping c = eta*k/omega there
k_mag = P.ratio^2*P.Nr*P.Km*P.I_set;
P.f_mode    = sqrt(1/(1/P.k_belt + 1/k_mag)/cad.yaw_inertia)/(2*pi);   % Hz (~11 Hz)
P.c_belt    = P.belt_eta*P.k_belt/(2*pi*P.f_mode);

%% Azimuth load from CAD V5 (full-solid printed parts, inertia vs elevation)
P.J_coef    = cad.yaw_inertia_coefficients(:)';            % J = c1 + c2 cos2q + c3 sin2q
P.Tc_az     = 0.020;         % N.m Coulomb (assumed, as in the CAD load audit)
P.sigma0    = 200;           % N.m/rad LuGre bristle (pre-sliding) stiffness: sticks within
                             % Tc/sigma0 = 1e-4 rad (assumed)
P.b_az      = 0.010;         % N.m.s/rad (assumed)
P.eps_az    = 1e-3;          % rad/s (only for the motor/servo tanh friction)
P.sigma1    = 2*0.2*sqrt(P.sigma0*cad.yaw_inertia);   % N.m.s/rad pre-sliding damping
P.k_cable   = 0.002;         % N.m/rad cable drag around the axis (assumed)

%% Elevation: LD-1501MG at ~7 V, internal position loop (surrogate)
P.J_el      = cad.elevation_inertia;
P.Tg_max    = cad.gravity_torque_max;                      % N.m, T = Tg cos(q_e)
P.Tc_el     = 0.015;         % N.m (assumed)
P.servo_Tstall = 1.6;        % N.m (15 kg.cm @6 V .. 17 kg.cm @7.4 V)
P.servo_wnl = (60*deg/0.16)*7/7.4;                         % rad/s no-load
P.servo_J   = 6e-3;          % kg.m^2 reflected motor+gear inertia (assumed)
P.servo_Kp  = 12;            % N.m/rad internal loop (assumed)
P.servo_Kd  = 0.15;          % N.m.s/rad (assumed)
P.servo_db  = 0.2*deg;       % dead band (assumed, ~2 us)
P.servo_us0 = 500;  P.servo_us180 = 2500;                  % nominal 0..180 deg

%% MT6701 on the azimuth shaft
P.sensor_counts = 16384;
P.sensor_offset = 123.4*deg; % raw angle at azimuth 0 (mounting, arbitrary)
P.sensor_sign   = 1;
P.inl_a1 = 0.5*deg;  P.inl_p1 = 30*deg;   % uncalibrated INL, datasheet +-1 deg typ
P.inl_a2 = 0.3*deg;  P.inl_p2 = 110*deg;
P.noise  = 0.012*deg;        % rms (0.01 deg rms transition noise in the datasheet)
P.t_sample = 60e-6;          % I2C read instant after the tick (400 kHz, 5 bytes)
P.t_act    = 350e-6;         % STEP command applied after the tick

%% Firmware timing
P.Ts = 0.01;  P.pwm_frame = 0.02;

cfg.plant = P;
cfg.ctrl = v5_ctrl_defaults();
cfg.sim = struct('h', 50e-6, 'log_dt', 1e-3, 'seed', 7, 'controller', 'mex', ...
    'host_heartbeat', 0.4);
cfg.cad = struct('dir', cadDir, 'yaw_inertia_max', cad.yaw_inertia, ...
    'elevation_inertia', cad.elevation_inertia);
cfg.source = struct( ...
    'motor', '17HS1352-P4130: 1.8 deg, 1.3 A, 2.1 ohm, 2.5 mH, 0.25 N.m, 35 g.cm2 (seller listing / Einstronic 17HS catalogue)', ...
    'driver', 'TB6600 (DFRobot DRI0043 manual): 9-42 V, 1/16 = 3200 pulse/rev, 1.0 A setting, automatic half current', ...
    'sensor', 'MT6701 Rev.1.8: 14 bit, INL +-1 deg typ, I2C 0x06 reg 0x03/0x04', ...
    'servo', 'LD-1501MG: 6-8.4 V, 500-2500 us; speed/torque from Hiwonder 15-17 kg.cm class, dynamics assumed', ...
    'cad', 'Antenna_V5_Reinforced/audit/simulation_parameters_v5.json and parameters.json');
end
