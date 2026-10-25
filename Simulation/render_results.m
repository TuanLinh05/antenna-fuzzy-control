function render_results
folder=fileparts(mfilename('fullpath'));out=fullfile(folder,'results');
a=load(fullfile(out,'dc_nominal.mat'),'best_result');r=a.best_result;
f=figure('Visible','off','Color','w','Position',[20 20 1250 900]);
tiledlayout(3,1,'TileSpacing','compact');
nexttile;plot(r.t,r.reference*180/pi,'--','LineWidth',1.4);hold on;plot(r.t,r.x(:,1)*180/pi,'LineWidth',1.1);
ylabel('Azimuth (deg)');grid on;legend('Assignment reference','Fuzzy closed loop','Location','best');
title('Original DC assignment: N=150, fixed-step RK4 h=100 us');
nexttile;plot(r.t,r.x(:,2)*180/pi);hold on;yline(30,'--r');yline(-30,'--r');
ylabel('Velocity (deg/s)');grid on;
nexttile;plot(r.t,r.u);hold on;yline(12,'--r');yline(-12,'--r');ylabel('Voltage (V)');xlabel('Time (s)');grid on;
light_style(f);exportgraphics(f,fullfile(out,'dc_assignment.png'),'Resolution',150);close(f);

a=load(fullfile(out,'prototype_nominal.mat'),'nominal');r=a.nominal;
f=figure('Visible','off','Color','w','Position',[20 20 1250 1100]);tiledlayout(4,1,'TileSpacing','compact');
nexttile;plot(r.t,r.reference*180/pi,'--');hold on;plot(r.t,r.x(:,3)*180/pi);plot(r.t,r.encoder*180/pi,':');
ylabel('Azimuth (deg)');legend('Reference','Physical model','Encoder','Location','best');grid on;
title('Stepper prototype: nonlinear motor, belt compliance/backlash, 600 P/R output encoder');
nexttile;plot(r.t,(r.x(:,3)-r.reference)*180/pi);ylabel('Tracking error (deg)');grid on;
nexttile;plot(r.t,r.x(:,4)*180/pi);hold on;yline(30,'--r');yline(-30,'--r');ylabel('Velocity (deg/s)');grid on;
nexttile;plot(r.t,r.elevation_reference*180/pi,'--');hold on;plot(r.t,r.x(:,5)*180/pi);
ylabel('Elevation (deg)');xlabel('Time (s)');legend('Servo setpoint','Unidentified servo surrogate','Location','best');grid on;
light_style(f);exportgraphics(f,fullfile(out,'prototype_tracking.png'),'Resolution',150);close(f);

h=view_antenna(35,60,false);exportgraphics(h.figure,fullfile(out,'antenna_CAD_in_MATLAB.png'),'Resolution',160);
savefig(h.figure,fullfile(out,'antenna_CAD.fig'));
indices=round(linspace(1,numel(r.t),96));
video=VideoWriter(fullfile(out,'antenna_simulation.mp4'),'MPEG-4');video.FrameRate=8;video.Quality=85;open(video);
temp=fullfile(out,'animation_frame.png');
for k=1:numel(indices)
    i=indices(k);update_antenna(h,r.x(i,3)*180/pi,r.x(i,5)*180/pi);
    title(h.axes,sprintf('V3 simulated motion | t = %.1f s',r.t(i)),'Color',[.12 .16 .20]);
    exportgraphics(h.figure,temp,'Resolution',90);writeVideo(video,imread(temp));
end
close(video);close(h.figure);delete(temp);
reader=VideoReader(fullfile(out,'antenna_simulation.mp4'));
assert(reader.Duration>=11.9&&reader.Width>500&&reader.Height>500);
imwrite(readFrame(reader),fullfile(out,'animation_first_frame.png'));
reader.CurrentTime=reader.Duration-.2;
imwrite(readFrame(reader),fullfile(out,'animation_last_frame.png'));
report=struct('status','PASS_ENCODED_AND_DECODED','duration_s',reader.Duration, ...
    'width',reader.Width,'height',reader.Height,'frame_rate',reader.FrameRate, ...
    'simulation_duration_s',r.t(end),'CAD_parameters',r.config.cad);
fid=fopen(fullfile(out,'video_validation.json'),'w');fwrite(fid,jsonencode(report,PrettyPrint=true));fclose(fid);
end
function light_style(f)
set(findall(f,'Type','axes'),'Color','w','XColor',[.15 .15 .15], ...
    'YColor',[.15 .15 .15],'ZColor',[.15 .15 .15],'GridColor',[.65 .65 .65]);
set(findall(f,'Type','text'),'Color',[.12 .12 .12]);
set(findall(f,'Type','legend'),'Color','w','TextColor',[.12 .12 .12],'EdgeColor',[.7 .7 .7]);
end
