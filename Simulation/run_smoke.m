function run_smoke
folder=fileparts(mfilename('fullpath'));addpath(folder);mkdir(fullfile(folder,'results'));
disp(version);v=ver;for k=1:numel(v),disp(v(k).Name);end
fis=make_antenna_fis(folder);disp(verify_fuzzy(folder,fis));
c=dc_default_config;r=simulate_dc(c);disp(r.metrics);disp(struct2table(r.metrics.steps));
save(fullfile(folder,'results','smoke_dc.mat'),'r');
end
