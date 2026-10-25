function v5_animate(res, file, speedup, fps)
%V5_ANIMATE Animate the V5 CAD with a simulation result and write an MP4.
%   v5_animate(res, 'results/v5_pdf.mp4')        4x speed, 25 fps
%   v5_animate(res, file, speedup, fps)
if nargin < 3, speedup = 4; end
if nargin < 4, fps = 25; end
deg = 180/pi;
H = res.hi; L = res.log;
h = v5_view_cad(0, 90, false, 'off');
set(h.figure, 'Position', [50 50 960 820]);
vw = VideoWriter(file, 'MPEG-4');
vw.FrameRate = fps; vw.Quality = 90;
open(vw);
cleanup = onCleanup(@() close(vw));
t_end = H.t(end);
for t = 0:speedup/fps:t_end
    az = interp1(H.t, H.az, t)*deg;
    el = interp1(H.t, H.el, t)*deg;
    k = min(numel(L.t), max(1, floor(t/(L.t(2) - L.t(1))) + 1));
    label = sprintf('t = %5.2f s | phương vị %6.2f° (đặt %6.1f°) | nâng %5.1f° (lệnh %5.1f°)', ...
        t, az, L.target(k)*deg, el, L.el_cmd(k)*deg);
    v5_pose_cad(h, az, el, label);
    writeVideo(vw, getframe(h.figure));
end
close(h.figure);
end
