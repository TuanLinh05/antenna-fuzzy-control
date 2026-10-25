function s=score_steps(t,theta,reference)
event=[0 12 24 36];target=[pi/3 5*pi/6 pi/6 pi/2];previous=[0 target(1:3)];
rows=repmat(struct('time_s',0,'target_deg',0,'overshoot_percent',0, ...
    'settling_2percent_s',Inf,'tail_max_error_rad',0),4,1);
for j=1:4
    keep=t>=event(j)-1e-10 & t<event(j)+12-1e-10;
    tt=t(keep);yy=theta(keep);step=target(j)-previous(j);
    overshoot=max(0,max(sign(step)*(yy-target(j)))/abs(step)*100);
    outside=find(abs(yy-target(j))>.02*abs(step));
    if isempty(outside)
        settling=0;
    elseif outside(end)<numel(tt)
        settling=tt(outside(end)+1)-event(j);
    else
        settling=Inf;
    end
    tail=yy(tt>=event(j)+11);
    rows(j)=struct('time_s',event(j),'target_deg',target(j)*180/pi, ...
        'overshoot_percent',overshoot,'settling_2percent_s',settling, ...
        'tail_max_error_rad',max(abs(tail-target(j))));
end
s=struct('steps',rows,'worst_overshoot_percent',max([rows.overshoot_percent]), ...
    'worst_tail_error_rad',max([rows.tail_max_error_rad]), ...
    'sum_settling_s',sum([rows.settling_2percent_s]), ...
    'rms_tracking_error_deg',sqrt(mean((theta-reference).^2))*180/pi);
end
