function varargout = v5_stepgen(op, sg, varargin)
%V5_STEPGEN MATLAB mirror of the STEP/DIR generator (core/stepgen.c).
%   sg = v5_stepgen('init', [], guard_us)
%   [sg, start_us] = v5_stepgen('command', sg, half_period_us, dir)
%   [sg, iv_us]    = v5_stepgen('retime', sg, elapsed_us)   (0 = keep interval)
%   [sg, next_us, pins] = v5_stepgen('tick', sg)
%       pins.step_level, pins.dir, pins.dir_changed, pins.stepped
%   The firmware calls 'tick' from the TIM2 interrupt and 'command'/'retime'
%   from the control loop; the simulation calls them at the same instants to
%   place every STEP rising edge in time.
switch op
    case 'init'
        varargout{1} = struct('pending_hp', 0, 'pending_dir', 1, 'steps', 0, 'hp', 0, ...
            'interval', 0, 'guard', varargin{1}, 'dir', 1, 'level', 0, 'running', false, ...
            'retimable', false);
    case 'command'
        hp = double(bitand(uint32(varargin{1}), uint32(65535)));
        dir = varargin{2};
        sg.pending_hp = hp;
        if hp ~= 0 && dir < 0, sg.pending_dir = -1; else, sg.pending_dir = 1; end
        start = 0;
        if ~sg.running && hp ~= 0
            sg.running = true;
            sg.level = 0;
            start = 20;                      % STEPGEN_START_US
            sg.interval = start;
            sg.retimable = false;
        end
        varargout = {sg, start};
    case 'retime'
        elapsed = varargin{1};
        hp = sg.pending_hp; iv = 0;
        if sg.running && sg.retimable && hp ~= 0 && hp < sg.interval
            iv = max(hp, elapsed + 20);      % STEPGEN_RETIME_MARGIN_US
            if iv >= sg.interval
                iv = 0;
            else
                sg.interval = iv;
            end
        end
        varargout = {sg, iv};
    case 'tick'
        pins = struct('step_level', 0, 'dir', sg.dir, 'dir_changed', 0, 'stepped', 0);
        hp = sg.pending_hp;
        if sg.level
            sg.level = 0;
            if hp ~= 0 && hp < sg.hp, sg.hp = hp; end
            sg.interval = sg.hp; sg.retimable = true;
            next = sg.hp;
        elseif hp == 0
            sg.running = false; sg.retimable = false;
            next = 0;
        elseif sg.pending_dir ~= sg.dir
            sg.dir = sg.pending_dir;
            pins.dir = sg.dir;
            pins.dir_changed = 1;
            next = max(hp, sg.guard);
            sg.interval = next; sg.retimable = false;
        else
            sg.level = 1;
            sg.hp = hp;
            sg.steps = sg.steps + sg.dir;
            pins.step_level = 1;
            pins.stepped = 1;
            next = hp;
            sg.interval = hp; sg.retimable = true;
        end
        varargout = {sg, next, pins};
    otherwise
        error('v5_stepgen: unknown op %s', op);
end
end
