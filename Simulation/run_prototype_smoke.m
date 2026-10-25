function run_prototype_smoke
folder=fileparts(mfilename('fullpath'));addpath(folder);
c=prototype_default_config;r=simulate_prototype(c);disp(r.metrics);disp(struct2table(r.metrics.steps));
save(fullfile(folder,'results','smoke_prototype.mat'),'r');
end
