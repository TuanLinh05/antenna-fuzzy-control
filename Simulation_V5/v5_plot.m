function fig = v5_plot(res, file, ttl)
%V5_PLOT Response figure of one v5_simulate result.
%   fig = v5_plot(res)              visible figure
%   v5_plot(res, 'x.png', 'title')  saved, invisible
deg = 180/pi;
L = res.log; H = res.hi;
vis = 'on'; if nargin > 1 && ~isempty(file), vis = 'off'; end
if nargin < 3, ttl = res.name; end
fig = figure('Visible', vis, 'Position', [50 50 1200 900], 'Color', 'w');
try, theme(fig, 'light'); catch, end
tl = tiledlayout(fig, 4, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
title(tl, ttl, 'Interpreter', 'none');

ax = nexttile(tl);
plot(ax, L.t, L.target*deg, 'k--', H.t, H.az*deg, 'b', L.t, L.meas*deg, 'r:', 'LineWidth', 1.1);
grid(ax, 'on'); ylabel(ax, 'Phương vị (°)');
legend(ax, 'đặt', 'thật (trục anten)', 'đo MT6701', 'Location', 'best');

ax = nexttile(tl);
err = (L.target - L.meas)*deg;
plot(ax, L.t, err, 'r', 'LineWidth', 1);
hold(ax, 'on');
tt = interp1(H.t, H.az, L.t, 'linear', 'extrap');
plot(ax, L.t, (L.target - tt)*deg, 'b', 'LineWidth', 0.8);
yline(ax, [-0.05 0.05], 'k:');
ylim(ax, [-1 1]); grid(ax, 'on'); ylabel(ax, 'Sai số (°)');
legend(ax, 'đặt − đo (MT6701)', 'đặt − thật (gồm INL MT6701 nếu chưa hiệu chuẩn)', '±0,05°', 'Location', 'best');

ax = nexttile(tl);
plot(ax, H.t, H.w*deg, 'b', L.t, L.vout*deg, 'r', 'LineWidth', 1);
yline(ax, [-30 30], 'k--', 'π/6');
grid(ax, 'on'); ylabel(ax, 'Tốc độ (°/s)');
legend(ax, 'thật', 'lệnh STEP (sau làm trơn)', 'Location', 'best');

ax = nexttile(tl);
plot(ax, L.t, L.el_cmd*deg, 'k--', H.t, H.el*deg, 'm', 'LineWidth', 1.1);
grid(ax, 'on'); ylabel(ax, 'Góc nâng (°)'); xlabel(ax, 't (s)');
legend(ax, 'lệnh servo (dốc 30°/s)', 'thật', 'Location', 'best');
if nargin > 1 && ~isempty(file)
    exportgraphics(fig, file, 'Resolution', 130);
    close(fig);
end
end
