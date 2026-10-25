function z=sugeno25(e,de)
% Exact bilinear evaluation of the 25 product/Sugeno singleton rules.
persistent rules
if isempty(rules)
    c=-1:.5:1;rules=zeros(5);
    for i=1:5
        for j=1:5
            rules(i,j)=max(-1,min(1,2*c(i)+.5*c(j)));
        end
    end
end
x=2*(max(-1,min(1,e))+1);y=2*(max(-1,min(1,de))+1);
i=min(4,floor(x)+1);j=min(4,floor(y)+1);a=x-(i-1);b=y-(j-1);
z=(1-a)*(1-b)*rules(i,j)+a*(1-b)*rules(i+1,j)+ ...
  (1-a)*b*rules(i,j+1)+a*b*rules(i+1,j+1);
end
