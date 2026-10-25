function result=simulate_dc(c,actual,disturbance)
% Exact assignment equations, fixed-step classical RK4; no state clipping.
if nargin<2,actual=c.plant;end
if nargin<3,disturbance=0;end
h=c.h;n=round(c.duration/h)+1;ratio=round(c.Ts/h);
assert(abs(ratio*h-c.Ts)<1e-10 && h<=1e-4);
t=(0:n-1)'*h;x=zeros(n,3);voltage=zeros(n,1);vref=zeros(n,1);ref=zeros(n,1);
state=[0;0];u=0;v=0;targets=[pi/3 5*pi/6 pi/6 pi/2];
for k=1:n
    segment=min(4,floor((k-1)/round(12/h))+1);ref(k)=targets(segment);
    if mod(k-1,ratio)==0
        error=ref(k)-x(k,1);
        if strcmp(c.mode,'fuzzy')
            f=sugeno25(error/c.error_width,-x(k,2)/c.vmax);
        else
            f=max(-1,min(1,2*error/c.error_width-.5*x(k,2)/c.vmax));
        end
        [u,state,v]=dc_control_transition(state,f,error,x(k,2),c);
    end
    voltage(k)=u;vref(k)=v;
    if k==n,break;end
    load=disturbance*(t(k)>=18 && t(k)<20);
    a=rhs(x(k,:)',u,actual,load);b=rhs(x(k,:)'+h*a/2,u,actual,load);
    d=rhs(x(k,:)'+h*b/2,u,actual,load);e=rhs(x(k,:)'+h*d,u,actual,load);
    x(k+1,:)=x(k,:)+(h/6*(a+2*b+2*d+e))';
end
metrics=score_steps(t,x(:,1),ref);
metrics.peak_speed_rad_s=max(abs(x(:,2)));metrics.peak_voltage_V=max(abs(voltage));
metrics.peak_current_A=max(abs(x(:,3)));
metrics.pass=metrics.worst_overshoot_percent<=2 && metrics.worst_tail_error_rad<=1e-5 && ...
    metrics.peak_speed_rad_s<=pi/6+1e-6 && metrics.peak_voltage_V<=12+1e-10 && all(isfinite(x(:)));
result=struct('t',t,'x',x,'u',voltage,'velocity_reference',vref,'reference',ref,'metrics',metrics,'config',c,'actual_plant',actual);
end
function d=rhs(x,u,p,load)
d=[x(2);(p.N*p.Kt*x(3)-p.B*x(2)-p.Tc*tanh(x(2)/p.epsilon)-load)/p.J; ...
    (u-p.Ra*x(3)-p.Kb*p.N*x(2))/p.La];
end
