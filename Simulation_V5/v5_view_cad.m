function h = v5_view_cad(azimuth, elevation, interactive, visible)
%V5_VIEW_CAD Show the V5 CAD (STEP tessellation) in MATLAB with movable axes.
%   v5_view_cad(30, 60)          azimuth/elevation in degrees, with sliders
%   h = v5_view_cad(0, 90, false, 'off')   handle for animation (v5_animate)
%   Meshes come from 3D Print/Antenna_V5_Reinforced/preview/mesh_data.json
%   (exported from the delivered STEP files, millimetres). Groups: fixed,
%   azimuth (turns with the antenna), elevation_local / elevation_world (also
%   tilt about the elevation axis at z = 209 mm). The 20T motor pulley turns
%   with the motor (4x the azimuth angle).
if nargin < 1, azimuth = 0; end
if nargin < 2, elevation = 90; end
if nargin < 3, interactive = true; end
if nargin < 4, visible = 'on'; end
cfg = v5_config();
data = jsondecode(fileread(fullfile(cfg.cad.dir, 'preview', 'mesh_data.json')));
fig = figure('Color', [.96 .97 .98], 'Position', [80 80 1000 850], 'Visible', visible, ...
    'Name', 'Anten V5 - CAD trong MATLAB');
try, theme(fig, 'light'); catch, end
ax = axes(fig, 'Position', [.05 .17 .9 .76], 'Color', [.96 .97 .98]);
hold(ax, 'on');
objects = gobjects(numel(data), 1);
pulley = [];
for k = 1:numel(data)
    color = sscanf(data(k).color(2:end), '%2x%2x%2x', [1 3])/255;
    objects(k) = patch(ax, 'Vertices', data(k).v, 'Faces', data(k).f + 1, 'FaceColor', color, ...
        'EdgeColor', 'none', 'FaceLighting', 'gouraud', 'AmbientStrength', .4);
    if contains(data(k).name, 'GT2_20T'), pulley = k; end
end
centre = [0 0];
if ~isempty(pulley), centre = mean(data(pulley).v(:, 1:2), 1); end
axis(ax, 'equal'); axis(ax, [-190 180 -160 160 -100 320]); view(ax, [-38 22]); grid(ax, 'on');
xlabel(ax, 'X (mm)'); ylabel(ax, 'Y (mm)'); zlabel(ax, 'Z (mm)'); camlight(ax, 'headlight');
h = struct('figure', fig, 'axes', ax, 'data', data, 'patches', objects, 'pulley', pulley, ...
    'pulley_centre', centre, 'ratio', cfg.plant.ratio);
v5_pose_cad(h, azimuth, elevation);
if interactive
    uicontrol(fig, 'Style', 'text', 'String', 'Phương vị (°)', 'Units', 'normalized', ...
        'Position', [.06 .08 .15 .03]);
    az = uicontrol(fig, 'Style', 'slider', 'Min', -150, 'Max', 150, 'Value', azimuth, ...
        'Units', 'normalized', 'Position', [.23 .08 .68 .025]);
    uicontrol(fig, 'Style', 'text', 'String', 'Nâng (°)', 'Units', 'normalized', ...
        'Position', [.06 .03 .15 .03]);
    el = uicontrol(fig, 'Style', 'slider', 'Min', 0, 'Max', 180, 'Value', elevation, ...
        'Units', 'normalized', 'Position', [.23 .03 .68 .025]);
    az.Callback = @(~, ~) v5_pose_cad(h, az.Value, el.Value);
    el.Callback = @(~, ~) v5_pose_cad(h, az.Value, el.Value);
end
end
