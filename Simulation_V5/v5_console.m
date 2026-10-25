function app = v5_console(port)
%V5_CONSOLE Control window for the antenna board (Zephyr firmware V5).
%   v5_console("COM5")      real board (USB-UART on PA9/PA10, 115200 8N1)
%   v5_console("virtual")   host build of the firmware protocol, for practice
%
%   Sends a heartbeat every 0.4 s while open; closing the window sends S.
%   Telemetry is plotted and can be logged to results/hw_logs/*.csv.
%   Before the first motion: check the wiring and directions (see
%   Firmware/antenna_zephyr/README.md), set the mechanical zero with Z.
if nargin < 1, port = "virtual"; end
here = fileparts(mfilename('fullpath'));
if strcmpi(port, "virtual")
    lk = v5_link('virtual');
else
    lk = v5_link('serial', port);
end
lk.send("T 50");

app = struct();
fig = uifigure('Name', sprintf('Anten V5 - %s', port), 'Position', [80 80 1100 720]);
g = uigridlayout(fig, [3 2]);
g.RowHeight = {150, '1x', '1x'}; g.ColumnWidth = {360, '1x'};

ctl = uipanel(g, 'Title', 'Lệnh'); ctl.Layout.Row = [1 3]; ctl.Layout.Column = 1;
cg = uigridlayout(ctl, [14 2]); cg.RowHeight = repmat({28}, 1, 14);
uilabel(cg, 'Text', 'Phương vị (°)');
azf = uieditfield(cg, 'numeric', 'Limits', [-150 150], 'Value', 0);
uilabel(cg, 'Text', 'Nâng (°)');
elf = uieditfield(cg, 'numeric', 'Limits', [0 180], 'Value', 90);
b = uibutton(cg, 'Text', 'Đi tới (G)', 'ButtonPushedFcn', @(~, ~) send(sprintf('G %.3f %.3f', azf.Value, elf.Value)));
b.Layout.Column = [1 2];
uibutton(cg, 'Text', 'Dừng êm (S)', 'ButtonPushedFcn', @(~, ~) send("S"));
uibutton(cg, 'Text', 'DỪNG KHẨN (F)', 'FontColor', [0.8 0 0], 'ButtonPushedFcn', @(~, ~) send("F"));
uibutton(cg, 'Text', 'Xóa lỗi (C)', 'ButtonPushedFcn', @(~, ~) send("C"));
uibutton(cg, 'Text', 'Chuỗi đề bài (Q)', 'ButtonPushedFcn', @(~, ~) send("Q"));
b = uibutton(cg, 'Text', 'Đặt vị trí hiện tại = 0° (Z)', 'ButtonPushedFcn', @(~, ~) confirm_zero());
b.Layout.Column = [1 2];
uilabel(cg, 'Text', 'Telemetry (ms)');
tdd = uidropdown(cg, 'Items', {'20', '50', '100', '200'}, 'Value', '50', ...
    'ValueChangedFcn', @(s, ~) send("T " + s.Value));
logcb = uicheckbox(cg, 'Text', 'Ghi CSV', 'Value', false, 'ValueChangedFcn', @(s, ~) toggle_log(s.Value));
logcb.Layout.Column = [1 2];
uibutton(cg, 'Text', 'Lưu tham số (W)', 'ButtonPushedFcn', @(~, ~) send("W"));
uibutton(cg, 'Text', 'Phiên bản (V)', 'ButtonPushedFcn', @(~, ~) send("V"));
status = uitextarea(cg, 'Editable', 'off', 'Value', {'chưa có dữ liệu'});
status.Layout.Row = [11 14]; status.Layout.Column = [1 2];

info = uitextarea(g, 'Editable', 'off', 'FontName', 'Consolas');
info.Layout.Row = 1; info.Layout.Column = 2;
ax1 = uiaxes(g); ax1.Layout.Row = 2; ax1.Layout.Column = 2;
ylabel(ax1, 'phương vị (°)'); grid(ax1, 'on'); hold(ax1, 'on');
pr = plot(ax1, NaN, NaN, 'k--'); pm = plot(ax1, NaN, NaN, 'b');
legend(ax1, 'đặt', 'đo MT6701');
ax2 = uiaxes(g); ax2.Layout.Row = 3; ax2.Layout.Column = 2;
ylabel(ax2, '°/s, °'); xlabel(ax2, 't (s)'); grid(ax2, 'on'); hold(ax2, 'on');
pv = plot(ax2, NaN, NaN, 'r'); pw = plot(ax2, NaN, NaN, 'b'); pe = plot(ax2, NaN, NaN, 'm');
legend(ax2, 'v lệnh', 'v đo', 'nâng lệnh');

buf = nan(0, 16);
logfile = -1;
msgs = {};
faults = {'heartbeat', 'giới hạn', 'lệch bước', 'quá chu kỳ', 'dừng khẩn', 'cảm biến', 'tham số'};
poll = timer('ExecutionMode', 'fixedSpacing', 'Period', 0.05, 'BusyMode', 'drop', ...
    'TimerFcn', @(~, ~) on_poll());
hb = timer('ExecutionMode', 'fixedSpacing', 'Period', 0.4, 'BusyMode', 'drop', ...
    'TimerFcn', @(~, ~) send("H"));
fig.CloseRequestFcn = @(~, ~) on_close();
start(poll); start(hb);
app = struct('figure', fig, 'link', lk);

    function send(line)
        try
            lk.send(line);
        catch err
            msgs{end+1} = ['UART: ' err.message];
        end
    end

    function confirm_zero()
        s = uiconfirm(fig, ['Chỉ đặt mốc khi anten đứng yên, đã căn đúng vạch 0° bằng tay. ' ...
            'Mốc được lưu vào flash. Tiếp tục?'], 'Đặt mốc 0', 'Options', {'Đặt mốc', 'Hủy'});
        if strcmp(s, 'Đặt mốc'), send("Z 0"); end
    end

    function toggle_log(on)
        if on
            d = fullfile(here, 'results', 'hw_logs');
            if ~exist(d, 'dir'), mkdir(d); end
            f = fullfile(d, ['hw_' char(datetime('now', 'Format', 'yyyyMMdd_HHmmss')) '.csv']);
            logfile = fopen(f, 'w');
            fprintf(logfile, ['ms,mode,fault,ref_mdeg,az_mdeg,vout_mdeg_s,wmeas_mdeg_s,steps,raw,' ...
                'el_cdeg,servo_us,half_period_us,loop_us,settled,pil\n']);
            msgs{end+1} = ['ghi: ' f];
        elseif logfile > 0
            fclose(logfile); logfile = -1;
        end
    end

    function on_poll()
        if ~isvalid(fig), return; end
        n = 0;
        while n < 200
            l = lk.readline(0);
            if l == "", break; end
            n = n + 1;
            if startsWith(l, "T,")
                v = sscanf(extractAfter(l, 2), '%f,')';
                if numel(v) == 15
                    buf(end+1, :) = [v NaN]; %#ok<AGROW>
                    if logfile > 0, fprintf(logfile, '%s\n', extractAfter(l, 2)); end
                end
            else
                msgs{end+1} = char(l); %#ok<AGROW>
            end
        end
        if size(buf, 1) > 3000, buf = buf(end-2999:end, :); end
        if numel(msgs) > 30, msgs = msgs(end-29:end); end
        status.Value = msgs;
        if isempty(buf), return; end
        t = (buf(:, 1) - buf(end, 1))/1000;
        set(pr, 'XData', t, 'YData', buf(:, 4)/1000); set(pm, 'XData', t, 'YData', buf(:, 5)/1000);
        set(pv, 'XData', t, 'YData', buf(:, 6)/1000); set(pw, 'XData', t, 'YData', buf(:, 7)/1000);
        set(pe, 'XData', t, 'YData', buf(:, 10)/100);
        xlim(ax1, [-30 0]); xlim(ax2, [-30 0]);
        s = buf(end, :);
        fl = faults(bitand(s(3), 2.^(0:6)) ~= 0);
        modes = {'CHƯA CÓ MỐC 0', 'HOẠT ĐỘNG', 'LỖI'};
        info.Value = {sprintf('chế độ: %s   lỗi: %d %s', modes{min(3, s(2)+1)}, s(3), strjoin(fl, ', ')), ...
            sprintf('phương vị đo %9.3f°   đặt %9.3f°   sai số %7.3f°', s(5)/1000, s(4)/1000, (s(4)-s(5))/1000), ...
            sprintf('tốc độ lệnh %7.2f °/s   đo %7.2f °/s   STEP %d   raw %d', s(6)/1000, s(7)/1000, s(8), s(9)), ...
            sprintf('nâng lệnh %6.2f°   servo %d us   chu kỳ vòng %d us', s(10)/100, s(11), s(13))};
        drawnow limitrate;
    end

    function on_close()
        try, send("S"); catch, end
        for tm = [poll hb]
            if isvalid(tm), stop(tm); delete(tm); end
        end
        if logfile > 0, fclose(logfile); end
        lk.close();
        delete(fig);
    end
end
