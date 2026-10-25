function [u,next,vref]=dc_control_transition(state,fuzzy_normalized,e,w,c)
% Fuzzy speed demand, rate/braking governor, model feedforward and inner PI.
p=c.plant;iv=state(1);vp=state(2);Ts=c.Ts;
vg=c.vmax*fuzzy_normalized;
braking=sqrt(2*c.accel*abs(e));vg=max(-braking,min(braking,vg));
vref=vp+max(-c.accel*Ts,min(c.accel*Ts,vg-vp));
a=(vref-vp)/Ts;
iref=(p.B*vref+p.Tc*tanh(vref/p.epsilon)+p.J*a)/(p.N*p.Kt);
ff=p.Kb*p.N*vref+p.Ra*iref;
ev=vref-w;inew=max(-4,min(4,iv+c.ki_velocity*Ts*ev));
raw=ff+c.kp_velocity*ev+inew;
if abs(raw)>12 && sign(raw)==sign(ev)
    inew=iv;raw=ff+c.kp_velocity*ev+inew;
end
u=max(-12,min(12,raw));
% This changes voltage, never clips the physical plant speed.
if w>.50
    u=min(u,p.Kb*p.N*w+p.Ra*(p.B*w+p.Tc*tanh(w/p.epsilon)-2*p.J)/(p.N*p.Kt));
elseif w<-.50
    u=max(u,p.Kb*p.N*w+p.Ra*(p.B*w+p.Tc*tanh(w/p.epsilon)+2*p.J)/(p.N*p.Kt));
end
u=max(-12,min(12,u));next=[inew;vref];
end
