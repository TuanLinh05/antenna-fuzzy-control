function v5_ensure_mex()
%V5_ENSURE_MEX Build antenna_core_mex if it is missing or older than the C sources.
here = fileparts(mfilename('fullpath'));
mexfile = fullfile(here, ['antenna_core_mex.' mexext]);
core = fullfile(here, '..', 'Firmware', 'antenna_zephyr', 'core');
src = [dir(fullfile(core, '*.c')); dir(fullfile(core, '*.h')); ...
    dir(fullfile(here, 'mex_src', '*.c'))];
if ~isfile(mexfile)
    v5_build_mex();
    return
end
info = dir(mexfile);
if any([src.datenum] > info.datenum)
    clear('antenna_core_mex');
    v5_build_mex();
end
end
