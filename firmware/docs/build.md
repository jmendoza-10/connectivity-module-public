# Build notes (planned)

- **IDE / SDK:** NXP **S32 Design Studio for S32 Platform** (3.5 or later) with the **S32K3 Real-Time Drivers (RTD)** package
  (AUTOSAR MCAL + non-AUTOSAR drivers) and S32 Config Tools for pins/clocks. NXP **HSE firmware** and **Safety Software Framework
  (SAF)** require NXP account / licence acceptance (some under NDA) - **not** stored in this repo. [U: exact versions]
- **Command-line build:** CMake + `arm-none-eabi-gcc` (NXP-supplied GCC for S32 or Arm GNU Toolchain), linker script per slot
  (`boot.ld`, `app_slot_a.ld`, `app_slot_b.ld`). Generated RTD config sources go to `config/generated/` (committed, reviewed).
- **CI (future):** build unsigned debug images + MISRA static analysis (e.g. cppcheck MISRA addon for screening; a qualified
  checker such as PC-lint Plus / Polyspace / Helix QAC for the safety case [U: tool choice]). No target hardware in CI.
- **Signing:** `tools/sign_image.py` wraps the offline HSM; CI never sees private keys.
- **Debug:** SWD/JTAG via PEmicro Multilink or Lauterbach TRACE32 (lockstep/HSE debug support) [U].
