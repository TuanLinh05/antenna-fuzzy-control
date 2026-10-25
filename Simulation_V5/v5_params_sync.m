function v5_params_sync(lk, p)
%V5_PARAMS_SYNC Load a controller parameter struct into the board, bit exact.
%   v5_params_sync(link, p)   p as returned by v5_ctrl_defaults (internal SI units)
%   Uses "PX <name> <hex>" so the firmware receives exactly the same IEEE-754
%   values as the MEX/M models. Values are written in passes because each
%   write is validated against the whole set (e.g. az_max < az_fault).
map = v5_param_names();
todo = map;
for pass = 1:4
    failed = {};
    for k = 1:size(todo, 1)
        [field, idx, name] = todo{k, :};
        v = p.(field);
        if ~isempty(idx), v = v(idx(1), idx(2)); end
        r = lk.query(sprintf('PX %s %s', name, bits(v)), ["OK P" "ERR P"]);
        if startsWith(r, "ERR")
            failed(end+1, :) = todo(k, :); %#ok<AGROW>
        end
    end
    if isempty(failed), return; end
    todo = failed;
end
error('v5_params_sync: board rejected %s', strjoin(todo(:, 3), ', '));
end

function h = bits(v)
switch class(v)
    case 'single', h = sprintf('%08X', typecast(v, 'uint32'));
    case 'int8',   h = sprintf('%X', typecast(int32(v), 'uint32'));
    otherwise,     h = sprintf('%X', uint32(v));
end
end
