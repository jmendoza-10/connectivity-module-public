# Firmware state-machine specification (normative, v0.1)

Source of truth for the firmware; diagrams are duplicated in docs/design/power-mcu.md (sec. 3, 6). Timings in ms unless noted;
module-specific values come from the active module profile.

## 1. Carrier state machine

| State | Entry actions | Exit conditions |
|---|---|---|
| OFF | SBC Sleep (V1 off) | wake: KL15, CAN WUP/WUF, RTC -> BOOT |
| BOOT | STCU2 self-test, HSE secure boot done, NVM config CRC check | ok -> RAILS_UP; fail -> FAULT |
| RAILS_UP | EN +3V3 sys; then +1V2 before +3V3 to hub (OI-07), +0V95, +1V8; check PGs within 20 ms each | all PG -> RUN; timeout -> FAULT |
| RUN | slots per config (slot SM); host power (host SM); release switch PERST_L when host ready | PARK cmd / KL15 off timeout -> PARK or SHUTDOWN |
| PARK | all slots except always-on slot -> S_OFF; host -> H_SHDN -> H_OFF; infrastructure rails off; MCU STANDBY; SBC Standby | wake source -> RUN |
| SHUTDOWN | all slots graceful off, host graceful off | done -> OFF |
| FAULT | outputs to safe state (sec. 4), log, IRQ | recovery policy -> RAILS_UP or latch |

## 2. Slot state machine (per slot)

| State | Entry actions | Transitions |
|---|---|---|
| S_OFF | PWR_EN=0, PCIE_EN=0, FCPO#=0, PCIE_SEL=1, RESET=0, WDIS=0 | ON_PCIE/ON_USB -> S_PWR |
| S_PWR | PCIE_SEL=mode, PWR_EN=1 | PG within t_pg (50) -> S_BOOT; else S_FAULT |
| S_BOOT | FCPO#=1, start t_perst (200 after PG) | PCIe: t_perst -> S_LINK; USB: -> S_UP |
| S_LINK | PCIE_EN=1, IRQ host "rescan" | host confirms endpoint -> S_UP; t_enum (10 s) -> S_FAULT |
| S_UP | - | OFF -> S_SHDN; RESET -> S_RESET |
| S_SHDN | PCIE_EN=0, FCPO#=0 | shutdown indicator or t_shdn (15 s) -> PWR_EN=0 -> S_OFF |
| S_RESET | RESET=1 for t_rst (1200) | -> S_BOOT |
| S_FAULT | PWR_EN=0, report | host ack -> S_OFF |

## 3. Host power state machine

| State | Entry actions | Transitions |
|---|---|---|
| H_OFF | HOST_EN=0 | RUN and config "host on" -> H_ON (retry limit 3/h) |
| H_ON | HOST_EN=1; check FLT and VOUT within 10 | ok -> wait heartbeat; fail -> H_FAULT |
| H_ALIVE | heartbeat seen | miss > wdt_timeout -> H_WARN; PARK/OFF -> H_SHDN |
| H_WARN | IRQ pre-warning | heartbeat -> H_ALIVE; t_warn -> H_RESET |
| H_RESET | HOST_RESET# pulse | heartbeat within t_boot -> H_ALIVE; else H_CUT (only if no HOST_BUSY lease) |
| H_CUT | HOST_EN=0, wait t_off (5 s) | -> H_ON (retry) or latch |
| H_SHDN | request host shutdown | host "halted" or t_shdn (60 s) **and no lease** -> H_OFF |
| H_FAULT | HOST_EN=0, latch, log | host/service clear -> H_OFF |

**Overriding rules:** protection cuts (over-current, battery UV, over-temperature) are immediate and ignore the HOST_BUSY lease;
the lease (max 600 s) defers only watchdog and graceful-off cuts.

## 4. Safe states

| Output | Safe state | Mechanism on MCU reset / FCCU fault |
|---|---|---|
| Slot PWR_EN, PCIE_EN, FCPO# | off / low | hardware pull-downs |
| PCIE_SEL | high (PCIe) | pull-up |
| Host EN | **TBD by HARA** (SG-1 vs SG-2, design doc sec. 7) | hold circuit [U] |
| Rail ENs | off | pull-downs |
