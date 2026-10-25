# Antenna V5 azimuth fuzzy controller - Zephyr application
# Board: stm32_min_dev@blue (STM32F103C8 "Blue Pill")
cmake_minimum_required(VERSION 3.20.0)

set(BOARD stm32_min_dev@blue CACHE STRING "Target board")

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(antenna_v5)

target_include_directories(app PRIVATE core src)
target_sources(app PRIVATE
  core/antenna_core.c
  core/stepgen.c
  core/link_proto.c
  src/main.c
  src/hw_stepper.c
  src/hw_mt6701.c
  src/hw_servo.c
  src/uart_link.c
  src/params_store.c
)
# Same numerical behaviour as the host/MEX builds: no fast-math, no implicit doubles.
target_compile_options(app PRIVATE -Wdouble-promotion -fno-fast-math)
