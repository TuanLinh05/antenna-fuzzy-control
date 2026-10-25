function v5_build_mex()
%V5_BUILD_MEX Compile the firmware control core into antenna_core_mex.
%   The C files are the ones built into the Zephyr firmware; nothing is
%   copied or rewritten. MinGW cannot open paths with Vietnamese characters,
%   so the sources are staged in tempdir before compiling.
here = fileparts(mfilename('fullpath'));
core = fullfile(here, '..', 'Firmware', 'antenna_zephyr', 'core');
stage = fullfile(tempdir, 'antenna_v5_mex');
if ~exist(stage, 'dir'), mkdir(stage); end
files = {'antenna_core.c', 'antenna_core.h', 'stepgen.c', 'stepgen.h'};
for k = 1:numel(files)
    copyfile(fullfile(core, files{k}), fullfile(stage, files{k}), 'f');
end
copyfile(fullfile(here, 'mex_src', 'antenna_core_mex.c'), fullfile(stage, 'antenna_core_mex.c'), 'f');
old = cd(stage);
cleanup = onCleanup(@() cd(old));
mex('-silent', 'CFLAGS=$CFLAGS -std=c99 -fno-fast-math -ffp-contract=off', ...
    'antenna_core_mex.c', 'antenna_core.c', 'stepgen.c', '-outdir', stage);
copyfile(fullfile(stage, ['antenna_core_mex.' mexext]), here, 'f');
fprintf('antenna_core_mex.%s built from %s\n', mexext, core);
end
