"""Build host tests, Cortex-M3/M4 core objects, and standalone F103C8 firmware."""
from pathlib import Path
import subprocess,json,struct,os
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'build';OUT.mkdir(exist_ok=True)
GCC=Path(r'C:\msys64\ucrt64\bin\gcc.exe')
ARM=Path(r'E:\STM32CubeIDE\STM32CubeIDE_1.19.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.13.3.rel1.win32_1.0.0.202411081344\tools\bin')
logs=[]
def run(args):
    p=subprocess.run([str(a) for a in args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    logs.append(dict(command=[str(a) for a in args],returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
    print(p.stdout+p.stderr,flush=True)
    if p.returncode:
        (OUT/'build_log.json').write_text(json.dumps(logs,indent=2),encoding='utf-8')
        raise SystemExit(p.returncode)
    return p.stdout

run([GCC,'-std=c11','-O2','-Wall','-Wextra','-Werror','test_fuzzy.c','fuzzy_controller.c','-lm','-o','build/test_fuzzy.exe'])
result=run([OUT/'test_fuzzy.exe','build/fuzzy_C_vectors.csv'])
for core in ('cortex-m3','cortex-m4'):
    run([ARM/'arm-none-eabi-gcc.exe','-std=c11','-Os','-mcpu='+core,'-mthumb','-mfloat-abi=soft',
         '-Wall','-Wextra','-Werror','-c','fuzzy_controller.c','-o','build/fuzzy_'+core+'.o'])
run([ARM/'arm-none-eabi-gcc.exe','-std=c11','-Os','-mcpu=cortex-m3','-mthumb',
     '-ffunction-sections','-fdata-sections','-Wall','-Wextra','-Werror',
     'startup_f103.S','stm32f103_main.c','fuzzy_controller.c','-T','stm32f103c8.ld',
     '-nostartfiles','--specs=nano.specs','--specs=nosys.specs','-Wl,--gc-sections',
     '-Wl,-Map,build/antenna_f103.map','-lm','-o','build/antenna_f103.elf'])
size=run([ARM/'arm-none-eabi-size.exe','build/antenna_f103.elf'])
for fmt,suffix in [('binary','bin'),('ihex','hex')]:
    run([ARM/'arm-none-eabi-objcopy.exe','-O',fmt,'build/antenna_f103.elf','build/antenna_f103.'+suffix])
binary=(OUT/'antenna_f103.bin').read_bytes();stack,reset=struct.unpack('<II',binary[:8])
assert stack==0x20005000 and reset&1 and 0x08000000<reset<0x08010000
assert len(binary)<65536
row=size.strip().splitlines()[-1].split();text,data,bss=map(int,row[:3])
assert data+bss<20480
report=dict(status='PASS_COMPILED_AND_HOST_TESTED',host_tests=result.strip(),
    fuzzy_core_compiled_for=['Cortex-M3 soft float','Cortex-M4 soft float'],
    firmware_target='STM32F103C8T6, 64 KB Flash, 20 KB SRAM, HSI 8 MHz',
    flash_binary_bytes=len(binary),static_ram_plus_reserved_stack_bytes=data+bss,
    reserved_stack_bytes=2048,vector_stack_hex=hex(stack),vector_reset_hex=hex(reset),
    hardware_flashed=False,hardware_timing_measured=False,
    limitations=['Compiled firmware is a commissioning prototype; no physical I/O has been tested.',
                 'F4 requires its own peripheral/startup layer; the F103 HEX must not be flashed onto F4.',
                 'FIS numerical equivalence to MATLAB is checked by the later MATLAB simulation suite.'])
(OUT/'firmware_build_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
CAD_AUDIT=ROOT.parent/'3D Print'/'Antenna_TheGioiIC_v3'/'audit'
if CAD_AUDIT.is_dir():
    (CAD_AUDIT/'firmware_build_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(OUT/'build_log.json').write_text(json.dumps(logs,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
