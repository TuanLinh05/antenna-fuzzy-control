classdef v5_link < handle
    %V5_LINK Line transport to the antenna firmware.
    %   lk = v5_link('serial', "COM5")      STM32 Blue Pill over a USB-UART (115200 8N1)
    %   lk = v5_link('virtual')             host build of the same protocol + core
    %                                       (Firmware/antenna_zephyr/tests/host/out/virtual_board.exe)
    %   lk.send("G 60 90")                  write one line
    %   line = lk.readline(timeout_s)       "" on timeout
    %   [reply, other] = lk.query("P accel_dps2 90", ["OK" "ERR"])
    %   lk.close()
    properties
        kind
        port
        timeout = 2.0
        log = strings(0, 1)      % non-reply lines seen while waiting (telemetry, comments)
    end
    properties (Access = private)
        dev
        proc
        jin
        jout
    end
    methods
        function obj = v5_link(kind, port, baud)
            obj.kind = kind;
            switch kind
                case 'serial'
                    if nargin < 3, baud = 115200; end
                    obj.port = port;
                    obj.dev = serialport(port, baud, 'Timeout', 0.5);
                    configureTerminator(obj.dev, "LF");
                    flush(obj.dev);
                case 'virtual'
                    here = fileparts(mfilename('fullpath'));
                    exe = fullfile(here, '..', 'Firmware', 'antenna_zephyr', 'tests', 'host', ...
                        'out', 'virtual_board.exe');
                    if ~isfile(exe)
                        error('v5_link: build the virtual board first (python run_host_tests.py)');
                    end
                    pb = java.lang.ProcessBuilder({char(exe)});
                    pb.redirectErrorStream(true);
                    obj.proc = pb.start();
                    obj.jout = obj.proc.getOutputStream();
                    obj.jin = java.io.BufferedReader(java.io.InputStreamReader( ...
                        obj.proc.getInputStream(), 'US-ASCII'));
                    first = obj.readline(5);
                    if ~startsWith(first, "#")
                        error('v5_link: virtual board did not start (%s)', first);
                    end
                otherwise
                    error('v5_link: kind must be serial or virtual');
            end
        end

        function send(obj, line)
            line = char(line);
            if strcmp(obj.kind, 'serial')
                writeline(obj.dev, line);
            else
                obj.jout.write(uint8([line 10]));
                obj.jout.flush();
            end
        end

        function line = readline(obj, timeout)
            if nargin < 2, timeout = obj.timeout; end
            line = "";
            t0 = tic;
            if strcmp(obj.kind, 'serial')
                while toc(t0) < timeout
                    if obj.dev.NumBytesAvailable > 0
                        l = readline(obj.dev);
                        if ~isempty(l), line = strip(string(l)); return; end
                    else
                        pause(0.001);
                    end
                end
            else
                while toc(t0) < timeout
                    if obj.jin.ready()
                        line = strip(string(char(obj.jin.readLine())));
                        return
                    end
                    java.lang.Thread.sleep(0);
                end
            end
        end

        function [reply, other] = query(obj, line, prefixes, timeout)
            %QUERY Send a line and wait for a reply starting with one of prefixes.
            if nargin < 4, timeout = obj.timeout; end
            obj.send(line);
            other = strings(0, 1);
            t0 = tic;
            reply = "";
            while toc(t0) < timeout
                l = obj.readline(timeout - toc(t0));
                if l == "", break; end
                if any(startsWith(l, prefixes))
                    reply = l;
                    return
                end
                other(end+1, 1) = l; %#ok<AGROW>
            end
            obj.log = [obj.log; other];
            if reply == ""
                error('v5_link: no reply to "%s"', line);
            end
        end

        function drain(obj, t)
            if nargin < 2, t = 0.2; end
            while true
                l = obj.readline(t);
                if l == "", return; end
                obj.log(end+1, 1) = l;
            end
        end

        function close(obj)
            if strcmp(obj.kind, 'serial')
                if ~isempty(obj.dev), delete(obj.dev); obj.dev = []; end
            elseif ~isempty(obj.proc)
                try
                    obj.send("EXIT");
                catch
                end
                obj.proc.destroy();
                obj.proc = [];
            end
        end

        function delete(obj)
            obj.close();
        end
    end
end
