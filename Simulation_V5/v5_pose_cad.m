function v5_pose_cad(h, azimuth, elevation, label)
%V5_POSE_CAD Move the V5 CAD to the given azimuth/elevation (degrees).
%   Same kinematics as the CAD preview (make_preview.py): elevation axis along
%   X at z = 209 mm, elevation 90 deg = dish up; azimuth about Z.
a = azimuth*pi/180; e = elevation*pi/180;
rz = [cos(a) -sin(a) 0; sin(a) cos(a) 0; 0 0 1];
for k = 1:numel(h.data)
    q = h.data(k); v = q.v;
    switch q.group
        case 'elevation_local'
            v(:, 3) = v(:, 3) - 8; th = e - pi/2;
            rx = [1 0 0; 0 cos(th) -sin(th); 0 sin(th) cos(th)];
            v = v*rx'; v(:, 3) = v(:, 3) + 209;
        case 'elevation_world'
            v(:, 3) = v(:, 3) - 209;
            rx = [1 0 0; 0 cos(e) -sin(e); 0 sin(e) cos(e)];
            v = v*rx'; v(:, 3) = v(:, 3) + 209;
    end
    if ~strcmp(q.group, 'fixed')
        v = v*rz';
    elseif k == h.pulley
        b = a*h.ratio;                               % open belt: same sense, 4x
        c = h.pulley_centre;
        rp = [cos(b) -sin(b); sin(b) cos(b)];
        v(:, 1:2) = (v(:, 1:2) - c)*rp' + c;
    end
    h.patches(k).Vertices = v;
end
if nargin < 4
    label = sprintf('CAD V5 | phương vị %.1f° | nâng %.1f°', azimuth, elevation);
end
title(h.axes, label, 'Color', [.12 .16 .20]);
drawnow limitrate;
end
