function fis = v5_make_fis(p, file)
%V5_MAKE_FIS Fuzzy Logic Toolbox object equal to the firmware rule base.
%   fis = v5_make_fis(p)              p from v5_ctrl_defaults (or a tuned set)
%   fis = v5_make_fis(p, 'x.fis')     also writes the .fis file
%   Inputs  : e_norm = e/E, de_norm = -omega/V   (range [-1 1], clamped by the caller)
%   Sets    : trimf NB NS ZE PS PB, centres -1 -a 0 a 1 (a = mf_e_in / mf_de_in)
%   Output  : u (constant singletons = p.rules), product AND, weighted average
labels = ["NB" "NS" "ZE" "PS" "PB"];
fis = sugfis(Name="antenna_v5_azimuth", AndMethod="prod", DefuzzificationMethod="wtaver");
fis = addInput(fis, [-1 1], Name="e_norm");
fis = addInput(fis, [-1 1], Name="de_norm");
ce = [-1 -double(p.mf_e_in) 0 double(p.mf_e_in) 1];
cd = [-1 -double(p.mf_de_in) 0 double(p.mf_de_in) 1];
for k = 1:5
    fis = addMF(fis, "e_norm", "trimf", tri(ce, k), Name=labels(k));
    fis = addMF(fis, "de_norm", "trimf", tri(cd, k), Name=labels(k));
end
fis = addOutput(fis, [-1 1], Name="u");
rules = zeros(25, 5);
n = 0;
for i = 1:5
    for j = 1:5
        n = n + 1;
        fis = addMF(fis, "u", "constant", double(p.rules(i, j)), ...
            Name=sprintf('r%s_%s', labels(i), labels(j)));
        rules(n, :) = [i j n 1 1];
    end
end
fis = addRule(fis, rules);
if nargin > 1
    writeFIS(fis, file);
end
end

function abc = tri(c, k)
if k == 1, a = c(1) - (c(2) - c(1)); else, a = c(k-1); end
if k == 5, b = c(5) + (c(5) - c(4)); else, b = c(k+1); end
abc = [a c(k) b];
end
