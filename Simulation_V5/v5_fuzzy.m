function [u, m1, m2] = v5_fuzzy(p, x1, x2)
%V5_FUZZY Zero-order Sugeno controller of the azimuth loop (MATLAB mirror of
%   acore_fuzzy in antenna_core.c, single precision, same operation order).
%     inputs : x1 = e/E, x2 = -omega/V, each clamped to [-1, 1]
%     sets   : 5 triangles per input, centres -1, -a, 0, a, 1 (NB NS ZE PS PB)
%     rules  : 25, IF x1 is E_i AND x2 is D_j THEN u = rules(i,j)
%     AND = product, defuzzification = weighted average
x1 = single(x1); x2 = single(x2);
m1 = memberships(x1, single(p.mf_e_in));
m2 = memberships(x2, single(p.mf_de_in));
num = single(0); den = single(0);
for i = 1:5
    for j = 1:5
        w = m1(i)*m2(j);
        num = num + w*p.rules(i,j);
        den = den + w;
    end
end
if den > 0
    u = num/den;
else
    u = single(0);
end
end

function mu = memberships(x, inner)
c = [single(-1) -inner single(0) inner single(1)];
x = min(single(1), max(single(-1), x));
mu = zeros(1, 5, 'single');
for k = 1:5
    if k == 1, a = c(1) - (c(2) - c(1)); else, a = c(k-1); end
    b = c(k);
    if k == 5, d = c(5) + (c(5) - c(4)); else, d = c(k+1); end
    up = (x - a)/(b - a);
    down = (d - x)/(d - b);
    if up < down, m = up; else, m = down; end
    if m > 0, mu(k) = m; end
end
end
