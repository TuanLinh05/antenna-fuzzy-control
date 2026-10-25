function run_final_validation
folder=fileparts(mfilename('fullpath'));addpath(folder);
fis=make_antenna_fis(folder);verification=verify_fuzzy(folder,fis);
fid=fopen(fullfile(folder,'results','fuzzy_validation.json'),'w');
fwrite(fid,jsonencode(verification,PrettyPrint=true));fclose(fid);
a=load(fullfile(folder,'results','dc_nominal.mat'),'best');
best=a.best;best_result=simulate_dc(best);
assert(best_result.metrics.pass);
save(fullfile(folder,'results','dc_nominal.mat'),'best','best_result');
build_simulink_model;
run_extended_tests;
render_results;
end
