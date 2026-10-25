function sfun_dc_inner(block)
block.NumDialogPrms=1;block.NumInputPorts=1;block.NumOutputPorts=1;
block.SetPreCompInpPortInfoToDynamic;block.SetPreCompOutPortInfoToDynamic;
block.InputPort(1).Dimensions=3;block.InputPort(1).DatatypeID=0;block.InputPort(1).DirectFeedthrough=true;
block.OutputPort(1).Dimensions=2;block.OutputPort(1).DatatypeID=0;
block.SampleTimes=[block.DialogPrm(1).Data.Ts 0];block.SimStateCompliance='DefaultSimState';
block.RegBlockMethod('PostPropagationSetup',@post);block.RegBlockMethod('InitializeConditions',@init);
block.RegBlockMethod('Outputs',@outputs);block.RegBlockMethod('Update',@update);
end
function post(b)
b.NumDworks=1;b.Dwork(1).Name='PI_and_rate_state';b.Dwork(1).Dimensions=2;
b.Dwork(1).DatatypeID=0;b.Dwork(1).Complexity='Real';b.Dwork(1).UsedAsDiscState=true;
end
function init(b),b.Dwork(1).Data=[0;0];end
function outputs(b)
a=b.InputPort(1).Data;[u,~,v]=dc_control_transition(b.Dwork(1).Data,a(1),a(2),a(3),b.DialogPrm(1).Data);
b.OutputPort(1).Data=[u;v];
end
function update(b)
a=b.InputPort(1).Data;[~,next]=dc_control_transition(b.Dwork(1).Data,a(1),a(2),a(3),b.DialogPrm(1).Data);
b.Dwork(1).Data=next;
end
