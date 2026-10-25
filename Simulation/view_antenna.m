function h=view_antenna(azimuth,elevation,interactive)
% Import V3 CAD tessellations at assembly coordinates (millimetres).
% All mesh triangles originate in the delivered STEP CAD, not a conceptual sketch.
if nargin<1,azimuth=0;end
if nargin<2,elevation=35;end
if nargin<3,interactive=true;end
folder=fileparts(mfilename('fullpath'));data=jsondecode(fileread(fullfile(folder,'..','3D Print','Antenna_TheGioiIC_v3','preview','mesh_data.json')));
visibility='off';if interactive,visibility='on';end
fig=figure('Color',[.96 .97 .98],'Position',[80 80 1000 850],'Visible',visibility,'Name','Antenna V3 CAD in MATLAB');
ax=axes(fig,'Position',[.05 .17 .9 .76],'Color',[.96 .97 .98], ...
    'XColor',[.18 .22 .25],'YColor',[.18 .22 .25],'ZColor',[.18 .22 .25]);
hold(ax,'on');objects=gobjects(numel(data),1);
for k=1:numel(data)
    color=sscanf(data(k).color(2:end),'%2x%2x%2x',[1 3])/255;
    objects(k)=patch(ax,'Vertices',data(k).v,'Faces',data(k).f+1, ...
        'FaceColor',color,'EdgeColor','none','FaceLighting','gouraud','AmbientStrength',.4);
end
axis(ax,'equal');axis(ax,[-190 180 -160 160 -100 320]);view(ax,[-38 22]);grid(ax,'on');
xlabel(ax,'X (mm)');ylabel(ax,'Y (mm)');zlabel(ax,'Z (mm)');camlight(ax,'headlight');
h=struct('figure',fig,'axes',ax,'data',data,'patches',objects);
update_antenna(h,azimuth,elevation);
if interactive
    uicontrol(fig,'Style','text','String','Azimuth (deg)','Units','normalized','Position',[.06 .08 .15 .03]);
    az=uicontrol(fig,'Style','slider','Min',-150,'Max',150,'Value',azimuth,'Units','normalized','Position',[.23 .08 .68 .025]);
    uicontrol(fig,'Style','text','String','Elevation (deg)','Units','normalized','Position',[.06 .03 .15 .03]);
    el=uicontrol(fig,'Style','slider','Min',0,'Max',180,'Value',elevation,'Units','normalized','Position',[.23 .03 .68 .025]);
    az.Callback=@(~,~)update_antenna(h,az.Value,el.Value);
    el.Callback=@(~,~)update_antenna(h,az.Value,el.Value);
end
end
