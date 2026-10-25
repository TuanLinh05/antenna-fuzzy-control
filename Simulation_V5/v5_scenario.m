function sc = v5_scenario(name, varargin)
%V5_SCENARIO Test scenarios for v5_simulate.
%   sc = v5_scenario('pdf')          course reference: 60,150,30,90 deg every 12 s,
%                                     elevation 60,90,120,80 deg (built-in 'Q' sequence)
%   sc = v5_scenario('demo')         0 -> +30 -> -30 -> 0 deg, 6 s each (bench demo)
%   sc = v5_scenario('small')        1, 0.2 and 0.05 deg steps (resolution / dead band)
%   sc = v5_scenario('track')        moving target 40 sin(2 pi t/20) deg sent every 100 ms
%   Name/value pairs override fields, e.g. v5_scenario('pdf','duration',24).
deg = pi/180;
sc = struct('name', name, 'duration', 48, 'az0', 0, 'el0', 90*deg, ...
    'commands', cmd([], 0, 'sequence', 0), 'heartbeat_until', inf, ...
    'dist', struct('type', {}, 't0', {}, 't1', {}, 'value', {}));
switch name
    case 'pdf'
        % defaults
    case 'demo'
        sc.duration = 24;
        az = [0 30 -30 0]; c = [];
        for k = 1:4, c = cmd(c, 6*(k-1), 'goto', [3 az(k)*deg 90*deg 1]); end
        sc.commands = c;
    case 'small'
        sc.duration = 12;
        az = [1 1.2 1.25 0]; c = [];
        for k = 1:4, c = cmd(c, 3*(k-1), 'goto', [1 az(k)*deg 0 1]); end
        sc.commands = c;
    case 'track'
        sc.duration = 40;
        c = [];
        for tk = 0:0.1:sc.duration
            c = cmd(c, tk, 'goto', [1 40*deg*sin(2*pi*tk/20) 0 1]);
        end
        sc.commands = c;
    otherwise
        error('v5_scenario: unknown scenario %s', name);
end
for k = 1:2:numel(varargin)
    sc.(varargin{k}) = varargin{k+1};
end
end

function c = cmd(c, t, type, args)
e = struct('t', t, 'type', type, 'args', args);
if isempty(c), c = e; else, c(end+1) = e; end
end
