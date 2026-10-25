function best=tune_dc
folder=fileparts(mfilename('fullpath'));out=fullfile(folder,'results');mkdir(out);
base=dc_default_config;records=[];best_score=Inf;best=base;best_result=[];index=0;
for width=[.08 .12 .18]
    for acceleration=[.8 1.2 1.8]
        for kp=[6 12]
            c=base;c.error_width=width;c.accel=acceleration;c.kp_velocity=kp;
            r=simulate_dc(c);m=r.metrics;index=index+1;
            records=[records;struct('candidate',index,'error_width_rad',width,'accel_rad_s2',acceleration, ...
                'kp_velocity',kp,'settling_sum_s',m.sum_settling_s,'overshoot_percent',m.worst_overshoot_percent, ...
                'tail_error_rad',m.worst_tail_error_rad,'peak_speed_rad_s',m.peak_speed_rad_s,'pass',m.pass)]; %#ok<AGROW>
            fprintf('DC tuning %d/18: width %.2f accel %.1f kp %.0f -> pass %d, sumTs %.4f s\n',index,width,acceleration,kp,m.pass,m.sum_settling_s);
            if m.pass&&m.sum_settling_s<best_score,best_score=m.sum_settling_s;best=c;best_result=r;end
        end
    end
end
assert(isfinite(best_score),'No candidate meets all assignment constraints.');
writetable(struct2table(records),fullfile(out,'dc_tuning.csv'));
save(fullfile(out,'dc_nominal.mat'),'best_result','best');
fid=fopen(fullfile(folder,'selected_dc_config.json'),'w');fwrite(fid,jsonencode(best,PrettyPrint=true));fclose(fid);
disp(struct2table(best_result.metrics.steps));disp(best_result.metrics);
end
