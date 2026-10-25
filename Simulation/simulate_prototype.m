function result=simulate_prototype(c)
% Nonlinear two-inertia stepper/belt model plus elevation servo surrogate.
% Motor rotor J, torque-speed envelope, belt k/c/backlash and servo dynamics
% are unmeasured assumptions. Geometry/load inertia comes from the V3 CAD.
h=c.h;n=round(c.duration/h)+1;ratio=round(c.Ts/h);assert(h<=1e-4);
t=(0:n-1)'*h;x=zeros(n,7);x(1,5)=pi/2;
ref=zeros(n,1);encoder=zeros(n,1);steps=zeros(n,1);drive_steps=zeros(n,1);
velocity_command=zeros(n,1);faultlog=zeros(n,1);eltarget=zeros(n,1);belt=zeros(n,1);mt=zeros(n,1);
targets=[pi/3 5*pi/6 pi/6 pi/2];el_targets=[60 90 120 80]*pi/180;
rng(c.seed);noise=randn(ceil(n/ratio)+1,1)*c.encoder_noise_deg*pi/180;noise_idx=0;
wf=0;previous_count=0;count=0;vcommand=0;phase=0;direction=1;guard=0;step_count=0;effective_steps=0;
miss_phase=0;bad_duration=0;fault=0;elcommand=pi/2;el_pwm=elcommand;held_encoder=0;
theta_command=0;frequency=0;last_heartbeat=0;
for k=1:n
    segment=min(4,floor((k-1)/round(12/h))+1);ref(k)=targets(segment);eltarget(k)=el_targets(segment);
    if mod(k-1,ratio)==0
        noise_idx=noise_idx+1;
        raw=x(k,3)+noise(noise_idx);
        if c.encoder_freeze&&t(k)>=13,raw=held_encoder;else,held_encoder=raw;end
        count=round(raw/(2*pi/2400));measured=count*(2*pi/2400);
        wf=.85*wf+.15*((count-previous_count)*(2*pi/2400)/c.Ts);previous_count=count;
        if ~c.communication_loss||t(k)<13,last_heartbeat=t(k);end
        if t(k)-last_heartbeat>2,fault=bitor(fault,1);end
        if abs(measured)>155*pi/180,fault=bitor(fault,2);end
        if abs(step_count*(2*pi/12800)-measured)>5*pi/180
            bad_duration=bad_duration+c.Ts;if bad_duration>=.3,fault=bitor(fault,4);end
        else,bad_duration=0;end
        if strcmp(c.mode,'open')
            error=ref(k)-step_count*(2*pi/12800);velocity=vcommand;
            % Open loop has no output encoder correction or tracking-fault detector.
            fault=bitand(fault,3);
        else,error=ref(k)-measured;velocity=wf;end
        desired=c.vmax*sugeno25(error/c.error_width,-velocity/c.vmax);
        brake=sqrt(2*c.accel*abs(error));desired=max(-brake,min(brake,desired));
        if abs(error)<c.deadband,desired=0;end
        vcommand=vcommand+max(-c.accel*c.Ts,min(c.accel*c.Ts,desired-vcommand));
        if fault,vcommand=0;end
        freq=abs(vcommand)/(2*pi/12800);requested=sign(vcommand);
        if freq<1.6,frequency=0;
        elseif requested~=direction
            direction=requested;guard=t(k)+.001;frequency=0;phase=0;
        else
            period=max(94,min(65535,round(100000/freq)));frequency=100000/period;
        end
        elcommand=elcommand+max(-25*pi/180*c.Ts,min(25*pi/180*c.Ts,el_targets(segment)-elcommand));
    end
    if mod(k-1,round(.02/h))==0,el_pwm=elcommand;end
    if t(k)>=guard&&frequency>0
        phase=phase+frequency*h;
        while phase>=1
            phase=phase-1;step_count=step_count+direction;drop=false;
            if c.pulse_drop&&t(k)>=13&&t(k)<13.5
                miss_phase=miss_phase+.05;if miss_phase>=1,drop=true;miss_phase=miss_phase-1;end
            end
            if ~drop,effective_steps=effective_steps+direction;end
        end
    end
    theta_command=effective_steps*(2*pi/3200);
    encoder(k)=count*(2*pi/2400);steps(k)=step_count;drive_steps(k)=effective_steps;
    velocity_command(k)=vcommand;faultlog(k)=fault;
    [~,belt(k),mt(k)]=rhs(x(k,:)',theta_command,el_pwm,c,t(k));
    if k==n,break;end
    a=rhs(x(k,:)',theta_command,el_pwm,c,t(k));
    b=rhs(x(k,:)'+h*a/2,theta_command,el_pwm,c,t(k)+h/2);
    d=rhs(x(k,:)'+h*b/2,theta_command,el_pwm,c,t(k)+h/2);
    e=rhs(x(k,:)'+h*d,theta_command,el_pwm,c,t(k)+h);
    x(k+1,:)=x(k,:)+(h/6*(a+2*b+2*d+e))';
    if c.jam&&t(k)>=13&&t(k)<14,x(k+1,3)=x(k,3);x(k+1,4)=0;end
end
metrics=score_steps(t,x(:,3),ref);
metrics.peak_speed_rad_s=max(abs(x(:,4)));metrics.peak_motor_torque_Nm=max(abs(mt));
metrics.peak_belt_torque_Nm=max(abs(belt));metrics.elevation_tail_error_deg=max(abs(x(end-10000:end,5)-eltarget(end-10000:end)))*180/pi;
first=find(faultlog~=0,1);if isempty(first),first_time=NaN;else,first_time=t(first);end
metrics.first_fault_time_s=first_time;metrics.final_fault=faultlog(end);
metrics.pass_tracking=metrics.worst_tail_error_rad<=.3*pi/180 && metrics.worst_overshoot_percent<=2 && ...
    metrics.peak_speed_rad_s<=pi/6 && faultlog(end)==0 && all(isfinite(x(:)));
result=struct('t',t,'x',x,'reference',ref,'encoder',encoder,'steps',steps, ...
    'effective_steps',drive_steps,'velocity_command',velocity_command,'fault',faultlog, ...
    'elevation_reference',eltarget,'belt_torque',belt,'motor_torque',mt,'metrics',metrics,'config',c);
end
function [dx,tbelt,tm]=rhs(x,command,elref,c,t)
z=x(1)/4-x(3);zv=x(2)/4-x(4);
gap=c.backlash/2;
if abs(z)>gap,tbelt=c.belt_stiffness*(z-sign(z)*gap)+c.belt_damping*zv;else,tbelt=0;end
tm=c.motor_torque*sin(50*(command-x(1)));
coeff=c.cad.yaw_inertia_coefficients;
J=c.Jscale*(coeff(1)+coeff(2)*cos(2*x(5))+coeff(3)*sin(2*x(5)));
dJ=c.Jscale*(-2*coeff(2)*sin(2*x(5))+2*coeff(3)*cos(2*x(5)));
load=c.external_load_Nm*(c.torque_disturbance&&t>=18&&t<18.5);
ae=(tbelt-c.viscous*x(4)-c.coulomb*tanh(x(4)/.01)-dJ*x(6)*x(4)-load)/J;
Je=c.cad.elevation_inertia;error=elref-x(5);raw=.10*error+.30*x(7)-.006*x(6);
servo=max(-.1765,min(.1765,raw));integral_dot=error+2*(servo-raw)/.30;
el_accel=(servo-c.cad.gravity_torque_max*cos(x(5))-.005*tanh(x(6)/.01)+.5*dJ*x(4)^2)/Je;
dx=[x(2);(tm-c.motor_damping*x(2)-tbelt/(4*c.efficiency))/c.Jmotor; ...
    x(4);ae;x(6);el_accel;integral_dot];
end
