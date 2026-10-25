function antenna_model_init(model)
folder=fileparts(get_param(model,'FileName'));
if isempty(folder),folder=fileparts(mfilename('fullpath'));end
c=jsondecode(fileread(fullfile(folder,'selected_dc_config.json')));
ws=get_param(model,'ModelWorkspace');assignin(ws,'dc_cfg',c);
assignin(ws,'antenna_fis',readfis(fullfile(folder,'antenna_sugeno25.fis')));
assignin(ws,'theta_reference',[0 pi/3;12 5*pi/6;24 pi/6;36 pi/2;48 pi/2]);
end
