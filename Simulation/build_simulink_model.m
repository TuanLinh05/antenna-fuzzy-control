function report=build_simulink_model
folder=fileparts(mfilename('fullpath'));addpath(folder);model='antenna_dc_fuzzy';
if bdIsLoaded(model),close_system(model,0);end
c=jsondecode(fileread(fullfile(folder,'selected_dc_config.json')));p=c.plant;
new_system(model);cleanup=onCleanup(@()close_system(model,0)); %#ok<NASGU>
set_param(model,'SolverType','Fixed-step','Solver','ode4','FixedStep','1e-4','StopTime','48');
ws=get_param(model,'ModelWorkspace');assignin(ws,'dc_cfg',c);
assignin(ws,'antenna_fis',readfis(fullfile(folder,'antenna_sugeno25.fis')));
assignin(ws,'theta_reference',[0 pi/3;12 5*pi/6;24 pi/6;36 pi/2;48 pi/2]);
add_block('simulink/Sources/From Workspace',[model '/Reference'],'VariableName','theta_reference','Interpolate','off', ...
    'OutputAfterFinalValue','Holding final value','Position',[30 60 130 90]);
add_block('simulink/Math Operations/Sum',[model '/Angle_error'],'Inputs','+-','Position',[180 60 205 90]);
add_block('simulink/Math Operations/Gain',[model '/Normalize_error'],'Gain',num2str(1/c.error_width,17),'Position',[245 50 325 90]);
add_block('simulink/Discrete/Zero-Order Hold',[model '/Sample_error_100Hz'],'SampleTime','.01','Position',[355 50 415 90]);
add_block('simulink/Discontinuities/Saturation',[model '/Bound_error'],'UpperLimit','1','LowerLimit','-1','Position',[445 50 500 90]);
add_block('simulink/Math Operations/Gain',[model '/Normalize_velocity'],'Gain',num2str(-1/c.vmax,17),'Position',[245 170 325 210]);
add_block('simulink/Discrete/Zero-Order Hold',[model '/Sample_velocity_100Hz'],'SampleTime','.01','Position',[355 170 415 210]);
add_block('simulink/Discontinuities/Saturation',[model '/Bound_velocity'],'UpperLimit','1','LowerLimit','-1','Position',[445 170 500 210]);
add_block('simulink/Signal Routing/Mux',[model '/FIS_inputs'],'Inputs','2','Position',[535 65 540 190]);
load_system('fuzblock');sources=find_system('fuzblock','SearchDepth',1,'Type','Block');
source=sources(contains(sources,'Fuzzy Logic')&~contains(sources,'Ruleviewer'));
assert(numel(source)==1);add_block(source{1},[model '/Sugeno_25_rules'],'Position',[580 95 715 160]);
parameters=fieldnames(get_param([model '/Sugeno_25_rules'],'DialogParameters'));
index=find(strcmpi(parameters,'fis'),1);assert(~isempty(index),'FIS mask parameter not found.');
set_param([model '/Sugeno_25_rules'],parameters{index},'antenna_fis');
add_block('simulink/Signal Routing/Mux',[model '/Control_inputs'],'Inputs','3','Position',[755 90 760 240]);
add_block('simulink/User-Defined Functions/Level-2 MATLAB S-Function',[model '/Rate_governor_and_velocity_PI'], ...
    'FunctionName','sfun_dc_inner','Parameters','dc_cfg','Position',[800 125 970 205]);
add_block('simulink/Signal Routing/Demux',[model '/Control_signals'],'Outputs','2','Position',[1010 130 1015 200]);
A=[0 1 0;0 -p.B/p.J p.N*p.Kt/p.J;0 -p.Kb*p.N/p.La -p.Ra/p.La];
B=[0 0;0 -1/p.J;1/p.La 0];
add_block('simulink/Signal Routing/Mux',[model '/Motor_voltage_and_friction'],'Inputs','2','Position',[1090 100 1095 240]);
add_block('simulink/Continuous/State-Space',[model '/DC_plant_theta_omega_current'], ...
    'A',mat2str(A,17),'B',mat2str(B,17),'C','eye(3)','D','zeros(3,2)','X0','[0;0;0]', ...
    'Position',[1140 115 1295 195]);
add_block('simulink/Signal Routing/Demux',[model '/Plant_states'],'Outputs','3','Position',[1345 100 1350 225]);
add_block('simulink/User-Defined Functions/Fcn',[model '/Coulomb_tanh'], ...
    'Expr','5*tanh(u/0.001)','Position',[1120 305 1260 345]);
add_block('simulink/Signal Routing/Mux',[model '/Recorded_signals'],'Inputs','6','Position',[1440 90 1445 300]);
add_block('simulink/Sinks/To Workspace',[model '/Simulation_log'],'VariableName','simulation_log', ...
    'SaveFormat','StructureWithTime','Position',[1500 170 1620 210]);
wire(model,'Reference/1','Angle_error/1');wire(model,'Plant_states/1','Angle_error/2');
wire(model,'Angle_error/1','Normalize_error/1');wire(model,'Normalize_error/1','Sample_error_100Hz/1');
wire(model,'Sample_error_100Hz/1','Bound_error/1');wire(model,'Bound_error/1','FIS_inputs/1');
wire(model,'Plant_states/2','Normalize_velocity/1');wire(model,'Normalize_velocity/1','Sample_velocity_100Hz/1');
wire(model,'Sample_velocity_100Hz/1','Bound_velocity/1');wire(model,'Bound_velocity/1','FIS_inputs/2');
wire(model,'FIS_inputs/1','Sugeno_25_rules/1');wire(model,'Sugeno_25_rules/1','Control_inputs/1');
wire(model,'Angle_error/1','Control_inputs/2');wire(model,'Plant_states/2','Control_inputs/3');
wire(model,'Control_inputs/1','Rate_governor_and_velocity_PI/1');wire(model,'Rate_governor_and_velocity_PI/1','Control_signals/1');
wire(model,'Control_signals/1','Motor_voltage_and_friction/1');wire(model,'Coulomb_tanh/1','Motor_voltage_and_friction/2');
wire(model,'Motor_voltage_and_friction/1','DC_plant_theta_omega_current/1');
wire(model,'DC_plant_theta_omega_current/1','Plant_states/1');wire(model,'Plant_states/2','Coulomb_tanh/1');
names={'Reference/1','Plant_states/1','Plant_states/2','Plant_states/3','Control_signals/1','Control_signals/2'};
for k=1:6,wire(model,names{k},['Recorded_signals/' num2str(k)]);end
wire(model,'Recorded_signals/1','Simulation_log/1');
set_param(model,'InitFcn',"addpath(fileparts(get_param(bdroot,'FileName')));antenna_model_init(bdroot);");
note=Simulink.Annotation(model,'Assignment DC plant: N=150, J=7.25, B=3.125, La=5mH, u<=12V. Prototype stepper model is separate.');
note.Position=[30 380 1100 420];
save_system(model,fullfile(folder,[model '.slx']));
output=sim(model,'ReturnWorkspaceOutputs','on');log=output.simulation_log;
t=log.time;y=log.signals.values;metrics=score_steps(t,y(:,2),y(:,1));
metrics.peak_speed_rad_s=max(abs(y(:,3)));metrics.peak_voltage_V=max(abs(y(:,5)));
assert(metrics.worst_overshoot_percent<=2&&metrics.worst_tail_error_rad<=1e-5&& ...
    metrics.peak_speed_rad_s<=pi/6+1e-6&&metrics.peak_voltage_V<=12+1e-9);
independent=load(fullfile(folder,'results','dc_nominal.mat'),'best_result');r=independent.best_result;
difference=max(abs(interp1(r.t,r.x(:,1),t)-y(:,2)));
assert(difference<.002,'Simulink/MATLAB implementations differ too much.');
report=struct('status','PASS_SIMULATED','model_file',[model '.slx'],'solver','ode4', ...
    'fixed_step_s',1e-4,'controller_sample_s',.01,'steps',numel(t), ...
    'independent_MATLAB_angle_difference_rad',difference,'metrics',metrics);
save(fullfile(folder,'results','simulink_dc.mat'),'t','y','report');
fid=fopen(fullfile(folder,'results','simulink_validation.json'),'w');fwrite(fid,jsonencode(report,PrettyPrint=true));fclose(fid);
print(['-s' model],'-dpng',fullfile(folder,'results','simulink_model.png'));
save_system(model);disp(report);
end
function wire(model,a,b),add_line(model,a,b,'autorouting','on');end
