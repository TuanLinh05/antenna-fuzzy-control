function report=verify_fuzzy(folder,fis)
c=readmatrix(fullfile(folder,'..','Firmware','build','fuzzy_C_vectors.csv'));
reference=evalfis(fis,c(:,1:2));manual=zeros(size(reference));
for k=1:numel(reference),manual(k)=sugeno25(c(k,1),c(k,2));end
report=struct('status','PASS','points',numel(reference), ...
    'C_single_vs_FIS_max_error',max(abs(c(:,3)-reference)), ...
    'MATLAB_manual_vs_FIS_max_error',max(abs(manual-reference)));
assert(report.C_single_vs_FIS_max_error<2e-6 && report.MATLAB_manual_vs_FIS_max_error<1e-12);
writematrix([c reference manual],fullfile(folder,'results','fuzzy_equivalence.csv'));
fid=fopen(fullfile(folder,'results','fuzzy_validation.json'),'w');
fwrite(fid,jsonencode(report,PrettyPrint=true));fclose(fid);
end
