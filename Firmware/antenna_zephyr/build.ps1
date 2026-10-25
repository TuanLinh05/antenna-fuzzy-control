<#
  Build the Zephyr firmware for the STM32F103C8 Blue Pill (board stm32_min_dev@blue).

    powershell -ExecutionPolicy Bypass -File build.ps1            # incremental
    powershell -ExecutionPolicy Bypass -File build.ps1 -Pristine  # clean rebuild

  The project path contains Vietnamese characters, which the Windows build of
  the Zephyr SDK toolchain cannot pass through. The script maps this folder to
  a temporary drive letter (subst) so CMake/Ninja/GCC only see ASCII paths,
  and removes the mapping at the end. Outputs are copied to dist\.

  Defaults match this PC; override with environment variables:
    ZEPHYR_BASE (D:\zephyrproject\zephyr), ZEPHYR_SDK_INSTALL_DIR
    (D:\zephyr-sdk\zephyr-sdk-0.16.8), ZEPHYR_VENV (D:\zephyrproject\.venv),
    DTC_DIR (C:\msys64\mingw64\bin), ANTENNA_DRIVE (W:)
#>
param([switch]$Pristine)
$ErrorActionPreference = "Stop"

function Default($value, $fallback) { if ($value) { $value } else { $fallback } }

$App = $PSScriptRoot
$Drive = Default $env:ANTENNA_DRIVE "W:"
$env:ZEPHYR_BASE = Default $env:ZEPHYR_BASE "D:\zephyrproject\zephyr"
$env:ZEPHYR_SDK_INSTALL_DIR = Default $env:ZEPHYR_SDK_INSTALL_DIR "D:\zephyr-sdk\zephyr-sdk-0.16.8"
$env:ZEPHYR_TOOLCHAIN_VARIANT = "zephyr"
$env:PYTHONUTF8 = "1"
$Venv = Default $env:ZEPHYR_VENV "D:\zephyrproject\.venv"
$Dtc = Default $env:DTC_DIR "C:\msys64\mingw64\bin"
$env:PATH = "$Venv\Scripts;$Dtc;" + $env:PATH
$Python = "$Venv\Scripts\python.exe"

if ($Pristine -and (Test-Path "$App\build")) { Remove-Item -Recurse -Force "$App\build" }

$existing = (subst) | Where-Object { $_ -like "$Drive\*" }
if ($existing -and ($existing -notlike "*antenna_zephyr*")) { throw "Drive $Drive is already used: $existing (set ANTENNA_DRIVE)" }
if (-not $existing) { subst $Drive "$App" | Out-Null }
try {
    Push-Location "$Drive\"
    if (-not (Test-Path "$Drive\build\build.ninja")) {
        cmake -GNinja -B "$Drive\build" -S "$Drive\" -DBOARD=stm32_min_dev@blue "-DPython3_EXECUTABLE=$Python"
        if ($LASTEXITCODE) { throw "CMake configure failed" }
    }
    ninja -C "$Drive\build"
    if ($LASTEXITCODE) { throw "Build failed" }
    Pop-Location
} finally {
    if (-not $existing) { subst $Drive /D | Out-Null }
}

$out = "$App\build\zephyr"
New-Item -ItemType Directory -Force "$App\dist" | Out-Null
foreach ($ext in "hex", "bin", "elf", "map") { Copy-Item "$out\zephyr.$ext" "$App\dist\antenna_v5_bluepill.$ext" -Force }
$bin = (Get-Item "$App\dist\antenna_v5_bluepill.bin").Length
$info = [ordered]@{
    board = "stm32_min_dev@blue (STM32F103C8, 64 KB flash, 20 KB RAM)"
    zephyr = "3.7.0"; sdk = (Split-Path $env:ZEPHYR_SDK_INSTALL_DIR -Leaf)
    built = (Get-Date).ToString("s"); flash_image_bytes = $bin
    code_partition_bytes = 61440; nvs_partition = "0x0800F000, 4 KB"
    hardware_tested = $false
}
$info | ConvertTo-Json | Set-Content -Encoding utf8 "$App\dist\build_info.json"
Write-Host "Firmware: $App\dist\antenna_v5_bluepill.hex ($bin bytes)"
