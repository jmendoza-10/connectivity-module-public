# Carrier power-management MCU firmware (skeleton)

Target: **NXP S32K344** (S32K344EHT1MPBST, lockstep Cortex-M7, HSE-B) on WWAN carrier **rev 0.4** (design:
[docs/design/power-mcu.md](../docs/design/power-mcu.md), issue #1). Functional-safety target **ASIL-B**; secure boot required.

> **Status: skeleton only.** Directory layout, interfaces and specs. No hardware exists; nothing here has been compiled for the
> target. Stubs return "not implemented". Do not flash.

## Layout

| Path | Content |
|---|---|
| `boot/` | Secure bootloader (HSE-verified, A/B slot selection, rollback) - stub |
| `app/src/`, `app/include/` | Application: carrier/slot/host-power state machines, host interface, watchdog, wake, safety - stubs |
| `common/include/` | Shared definitions: register map, image header, module timing profiles |
| `config/` | Board/pin configuration (to be generated with NXP S32 Config Tools from the rev 0.4 schematic) |
| `docs/state-machines.md` | Normative state-machine spec (carrier, slot, host power) |
| `docs/build.md` | Toolchain / build notes (S32 Design Studio, RTD, CMake) |
| `docs/coding-rules.md` | MISRA C:2012 and safety coding rules |
| `docs/provisioning.md` | HSE key provisioning and lifecycle (no keys in repo) |
| `tools/` | Host-side helpers (image signing wrapper - stub; never contains private keys) |

## Rules

- MISRA C:2012 (see `docs/coding-rules.md`); deviations documented per rule.
- **No secrets in the repository**: signing keys live in an offline HSM; CI builds unsigned development images only.
- Timings come from the module profiles in `common/include/module_profiles.h`, which mirror `docs/power-reset-sequencing.md`.
- The register map in `common/include/carrier_regs.h` is the contract with `software/tools/carrierctl.py` (MCU backend, future).
