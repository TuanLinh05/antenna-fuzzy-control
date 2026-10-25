function fis=make_antenna_fis(folder)
fis=sugfis(Name="Antenna_Sugeno25",AndMethod="prod",DefuzzificationMethod="wtaver");
fis=addInput(fis,[-1 1],Name="error_normalized");
fis=addInput(fis,[-1 1],Name="negative_velocity_normalized");
c=-1:.5:1;labels=["NB","NS","ZE","PS","PB"];
for k=1:5
    fis=addMF(fis,"error_normalized","trimf",[c(k)-.5 c(k) c(k)+.5],Name=labels(k));
    fis=addMF(fis,"negative_velocity_normalized","trimf",[c(k)-.5 c(k) c(k)+.5],Name=labels(k));
end
fis=addOutput(fis,[-1 1],Name="velocity_normalized");
rules=zeros(25,5);n=0;
for i=1:5
    for j=1:5
        n=n+1;
        fis=addMF(fis,"velocity_normalized","constant",max(-1,min(1,2*c(i)+.5*c(j))),Name="rule_"+n);
        rules(n,:)=[i j n 1 1];
    end
end
fis=addRule(fis,rules);
if nargin
    writeFIS(fis,fullfile(folder,'antenna_sugeno25.fis'));
    save(fullfile(folder,'antenna_fis.mat'),'fis');
end
end
