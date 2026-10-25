function update_antenna(h,azimuth,elevation)
a=azimuth*pi/180;e=elevation*pi/180;
rz=[cos(a) -sin(a) 0;sin(a) cos(a) 0;0 0 1];
for k=1:numel(h.data)
    q=h.data(k);v=q.v;
    if strcmp(q.group,'elevation_local')
        v(:,3)=v(:,3)-8;angle=e-pi/2;
        rx=[1 0 0;0 cos(angle) -sin(angle);0 sin(angle) cos(angle)];
        v=v*rx';v(:,3)=v(:,3)+209;
    elseif strcmp(q.group,'elevation_world')
        v(:,3)=v(:,3)-209;
        rx=[1 0 0;0 cos(e) -sin(e);0 sin(e) cos(e)];
        v=v*rx';v(:,3)=v(:,3)+209;
    end
    if ~strcmp(q.group,'fixed'),v=v*rz';end
    h.patches(k).Vertices=v;
end
title(h.axes,sprintf('V3 CAD | Azimuth %.1f deg | Elevation %.1f deg',azimuth,elevation),'Color',[.12 .16 .20]);
drawnow;
end
