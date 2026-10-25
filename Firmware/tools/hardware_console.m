function hardware_console(port)
% Manual commissioning UI. No port is opened until the user calls this function.
% Example: hardware_console("COM5"). Has not been tested against physical I/O.
device=serialport(port,115200,'Timeout',.3);configureTerminator(device,"LF");flush(device);
fig=uifigure('Name','Anten V3 — STM32 UART','Position',[100 100 650 420]);
uilabel(fig,'Text','Chỉ bấm Z sau khi đã căn mốc 0 bằng tay và cơ cấu đứng yên.', ...
    'Position',[25 370 600 25]);
uilabel(fig,'Text','Phương vị (độ)','Position',[25 325 140 25]);
az=uieditfield(fig,'numeric','Limits',[-150 150],'Value',0,'RoundFractionalValues','on', ...
    'Position',[180 325 100 25]);
uilabel(fig,'Text','Nâng (độ)','Position',[315 325 100 25]);
el=uieditfield(fig,'numeric','Limits',[45 135],'Value',90,'RoundFractionalValues','on', ...
    'Position',[430 325 100 25]);
uibutton(fig,'Text','Z — mốc tay / xóa lỗi','Position',[25 270 190 35], ...
    'ButtonPushedFcn',@(~,~)send("Z"));
uibutton(fig,'Text','Gửi góc đặt','Position',[240 270 150 35], ...
    'ButtonPushedFcn',@(~,~)send(sprintf('G %d %d',round(az.Value),round(el.Value))));
uibutton(fig,'Text','S — dừng phát STEP','Position',[415 270 205 35], ...
    'ButtonPushedFcn',@(~,~)send("S"));
status=uilabel(fig,'Text','Heartbeat 0,4 s; đóng cửa sổ sẽ gửi S và ngắt UART.', ...
    'Position',[25 230 600 25]);
log=uitextarea(fig,'Editable','off','Position',[25 35 595 185], ...
    'Value',{'ms,measured_mdeg,target_mdeg,velocity_mdeg_s,fault,zeroed'});
lines=log.Value;
configureCallback(device,"terminator",@received);
heartbeat=timer('ExecutionMode','fixedSpacing','Period',.4,'BusyMode','drop','TimerFcn',@(~,~)send("H"));
fig.CloseRequestFcn=@close_console;
start(heartbeat);
    function send(command)
        try
            writeline(device,command);
        catch problem
            if isvalid(status),status.Text=['UART lỗi: ' problem.message];end
            if exist('heartbeat','var')&&isvalid(heartbeat),stop(heartbeat);end
        end
    end
    function received(src,~)
        try
            line=char(readline(src));lines=[lines;{line}];
            if numel(lines)>80,lines=lines(end-79:end);end
            if isvalid(log),log.Value=lines;end
        catch problem
            if isvalid(status),status.Text=['Đọc UART lỗi: ' problem.message];end
        end
    end
    function close_console(~,~)
        if isvalid(heartbeat),stop(heartbeat);delete(heartbeat);end
        send("S");configureCallback(device,"off");delete(device);delete(fig);
    end
end
