"""Build and run the host tests of the portable control core.

    python run_host_tests.py            (from any folder)

Uses the PC gcc (MSYS2 UCRT64 by default, or GCC env var / PATH). Builds:
  out/test_core.exe      unit + closed-loop tests, writes out/fuzzy_C_vectors.csv
  out/virtual_board.exe  the link protocol on stdin/stdout (used by MATLAB PIL tests)
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
# gcc (MinGW) mishandles non-ASCII absolute paths: build with relative paths from HERE.
CORE = Path("..") / ".." / "core"

gcc = os.environ.get("GCC") or (r"C:\msys64\ucrt64\bin\gcc.exe"
                                 if Path(r"C:\msys64\ucrt64\bin\gcc.exe").exists()
                                 else shutil.which("gcc"))
if not gcc:
    sys.exit("gcc not found: set GCC=path\\to\\gcc.exe")

FLAGS = ["-std=c99", "-O2", "-Wall", "-Wextra", "-Werror", "-Wdouble-promotion",
         "-Wshadow", "-fno-fast-math", "-I", str(CORE)]
SOURCES = [str(CORE / n) for n in ("antenna_core.c", "stepgen.c", "link_proto.c")]


def run(args, **kw):
    print(">", " ".join(str(a) for a in args), flush=True)
    p = subprocess.run([str(a) for a in args], capture_output=True, text=True, cwd=HERE,
                       encoding="utf-8", errors="replace", **kw)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    return p


log = {}
p = run([gcc, *FLAGS, "test_core.c", *SOURCES, "-lm", "-o", "out/test_core.exe"])
if p.returncode:
    sys.exit("build of test_core failed")
p = run([gcc, *FLAGS, "virtual_board.c", *SOURCES, "-lm", "-o",
         "out/virtual_board.exe"])
if p.returncode:
    sys.exit("build of virtual_board failed")
p = run([str(OUT / "test_core.exe"), "out"])
log["test_core"] = {"returncode": p.returncode, "stdout": p.stdout.splitlines()}
(OUT / "host_test_result.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
sys.exit(p.returncode)
