<#
  Flash dist\antenna_v5_bluepill.hex with STM32CubeProgrammer.

    powershell -ExecutionPolicy Bypass -File flash.ps1               # ST-LINK (SWD)
    powershell -ExecutionPolicy Bypass -File flash.ps1 -Port COM5    # ROM bootloader over UART
                                                                      # (BOOT0=1, reset first)
  Disconnect the 12 V motor supply before flashing. The parameter area
  (0x0800F000-0x0800FFFF) is kept, so the saved zero and tuning survive.
#>
param([string]$Port = "")
$ErrorActionPreference = "Stop"
$cli = if ($env:STM32_PROGRAMMER_CLI) { $env:STM32_PROGRAMMER_CLI } else { "E:\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe" }
$hex = Join-Path $PSScriptRoot "dist\antenna_v5_bluepill.hex"
if (-not (Test-Path $hex)) { throw "Build first: $hex not found" }
# Copy to an ASCII path: the programmer does not accept the Vietnamese folder name.
$tmp = Join-Path $env:TEMP "antenna_v5_bluepill.hex"
Copy-Item $hex $tmp -Force
if ($Port) {
    & $cli -c port=$Port br=115200 -w $tmp -v -g 0x08000000
} else {
    & $cli -c port=SWD mode=UR -w $tmp -v -rst
}
if ($LASTEXITCODE) { throw "Flashing failed ($LASTEXITCODE)" }
