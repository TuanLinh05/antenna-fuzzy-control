function [dx, Te, Tb] = v5_plant_rhs(x, K, U) %#codegen
%V5_PLANT_RHS Right-hand side of the V5 plant (used by v5_simulate and Simulink).
%   x = [theta_m; omega_m; i_a; i_b; theta_a; omega_a; q_e; omega_e; z]
%   z = LuGre bristle deflection of the azimuth bearing friction (sticks at rest)
%   K = v5_plant_K(plant)   constant parameter vector
%   U = [i_ref_a, i_ref_b, servo_target, load_torque, jammed, jam_angle]
%   Te = motor torque (electromagnetic + detent), Tb = belt torque at the antenna
Nr = K(1); Km = K(2); R = K(3); L = K(4); Kc = K(5); Vl = K(6); Td = K(7);
bm = K(8); Tcm = K(9); em = K(10); Jm = K(11); n = K(12); kb = K(13); cb = K(14);
gap = K(15); c1 = K(16); c2 = K(17); c3 = K(18); Tca = K(19); ba = K(21);
kc = K(22); Je = K(23); Tg = K(24); Tce = K(25); Kp = K(26); Kd = K(27); db = K(28);
Tst = K(29); wnl = K(30);

thm = x(1); wm = x(2); ia = x(3); ib = x(4); tha = x(5); wa = x(6); qe = x(7); we = x(8);
s = sin(Nr*thm); c = cos(Nr*thm);
% TB6600: average current loop limited by the bus voltage
eA = -Km*wm*s; eB = Km*wm*c;
vA = R*U(1) + Kc*(U(1) - ia); vA = min(Vl, max(-Vl, vA));
vB = R*U(2) + Kc*(U(2) - ib); vB = min(Vl, max(-Vl, vB));
dia = (vA - R*ia - eA)/L;
dib = (vB - R*ib - eB)/L;
Te = Km*(-ia*s + ib*c) - Td*sin(4*Nr*thm);
% belt with tooth clearance: soft inside the gap when pretensioned (K(31) > 0),
% contact forces only for a hard gap
z = thm/n - tha; zd = wm/n - wa;
ks = K(31)*kb;
if z > gap
    Tb = ks*z + (kb - ks)*(z - gap) + cb*zd;
    if ks == 0, Tb = max(0, Tb); end
elseif z < -gap
    Tb = ks*z + (kb - ks)*(z + gap) + cb*zd;
    if ks == 0, Tb = min(0, Tb); end
else
    Tb = ks*z + K(31)*cb*zd;
end
dwm = (Te - bm*wm - Tcm*tanh(wm/em) - Tb/n)/Jm;
% antenna: CAD inertia depends on elevation
s2 = sin(2*qe); c2q = cos(2*qe);
J = c1 + c2*c2q + c3*s2;
dJ = -2*c2*s2 + 2*c3*c2q;
% LuGre friction (no Stribeck): dz = w - sigma0*|w|*z/Tc, T = sigma0*z + sigma1*dz + b*w
s0 = K(32); s1 = K(33);
dz = wa - s0*abs(wa)*x(9)/Tca;
Tfa = s0*x(9) + s1*dz + ba*wa;
Taz = Tb - Tfa - kc*tha - U(4) - dJ*we*wa;
if U(5)
    Taz = Taz - 400*(tha - U(6)) - 4*wa;          % jammed output (stiff stop)
end
dwa = Taz/J;
% LD-1501MG surrogate: internal P-D sets the PWM duty of a DC motor,
% T = Tstall*(duty - omega/omega_nl) (back-EMF damping always present)
err = U(3) - qe;
if abs(err) < db, err = 0; else, err = err - sign(err)*db; end
duty = min(1, max(-1, (Kp*err - Kd*we)/Tst));
Tm = Tst*(duty - we/wnl);
dwe = (Tm - Tg*cos(qe) - Tce*tanh(we/1e-3) + 0.5*dJ*wa^2)/Je;
dx = [wm; dwm; dia; dib; wa; dwa; we; dwe; dz];
end
