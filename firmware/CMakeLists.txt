# Placeholder build - host-side syntax check of the skeleton only (not a target build).
cmake_minimum_required(VERSION 3.20)
project(carrier_mcu_fw C)
add_library(carrier_app STATIC
  app/src/carrier_fsm.c app/src/slot_fsm.c app/src/host_fsm.c app/src/hostif.c app/src/safety.c app/src/module_profiles.c)
target_include_directories(carrier_app PUBLIC app/include common/include)
