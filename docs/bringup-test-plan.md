# Bring-up test plan - power-on to three bonded links

Status: **plan; nothing executed.** Each stage gates the next. Record results (date, board serial, BSP/kernel/MM versions,
module FW `AT+CGMR`, pass/fail, notes, scope captures) in `docs/results/<date>-<stage>.md` (TODO: create when testing starts).

Equipment: bench PSU 12 V / >= 6 A with current limit, DMM, 4-ch scope (>= 200 MHz), I2C analyser optional, thermal camera
or thermocouple, USB-C cable (USB 3), ADT-Link M41 riser, 3x 5G M.2 cards (Sierra EM9291 and/or Telit FN990A28), 3x nano-SIM, up to 18 antennas/pigtails per docs/antenna-gnss-plan.md (passive GNSS antenna for EM9291), fan.

References: [hw-sw-interface.md](hw-sw-interface.md), [power-reset-sequencing.md](power-reset-sequencing.md),
[linux-bringup.md](linux-bringup.md), [open-issues.md](open-issues.md).

## T0 - Bare board (no modules, no host)

| Test | Procedure | Pass criteria |
|---|---|---|
| T0.1 Visual / shorts | Inspect; measure resistance +12V, +3V3, +0V95, +1V8, +1V2, +3V7_S1..3 to GND | No rail < 10 ohm (record values; +0V95 will be lowest) |
| T0.2 First power | 12 V, current limit 0.5 A | Input current < 300 mA (TODO refine), no hot parts |
| T0.3 Rails | DMM at TP105/107/108/109 | +3V3 3.20-3.40 V; +0V95 0.92-0.98 V; +1V8 1.75-1.85 V; +1V2 1.16-1.24 V (TODO tighten vs PI7C/USB5744 limits) |
| T0.4 Hardware sequencing | Scope +3V3, PG_3V3 (TP106), +0V95, +1V2 at 12 V turn-on | Secondary rails start only after PG_3V3; capture for OI-07 (USB5744 VDD33 vs VDD12) |
| T0.5 Slot rails default off | DMM TP201-203 | < 0.1 V (PWR_EN pull-downs) |
| T0.6 PG LEDs | Observe | D801-D804 on; D805-D807 off; D102 on |
| T0.7 Defaults | DMM: FCPO# pins (module side, J401/501/601 pin 6) | 0 V |

## T1 - Host attach, I2C (no modules)

| Test | Procedure | Pass criteria |
|---|---|---|
| T1.1 Header wiring | Connect J801 to FRDM pins chosen in OI-01; check CARRIER_3V3_SENSE on host GPIO | reads 1 with carrier powered, 0 without |
| T1.2 I2C scan | `i2cdetect -y N` | 0x20, 0x21 present; 0x2D (USB5744) and 0x6F or 0x68 (PI7C via PCA9306) present - record actual addresses, close OI-04/OI-05 |
| T1.3 Expander init | `carrierctl.py --backend smbus --bus N init` then `status` | outputs read back per hw-sw-interface.md init values; no slot rail comes on (scope TP201-203 during init: no glitch > 0.5 V) |
| T1.4 Inputs | `status` | pg-3v3/0v95/1v8/1v2 = 1; slotN-pg = 0; wake-n = 1 |
| T1.5 LEDs | `led 1 on`, `led 2 on` | D808/D809 light |
| T1.6 Interrupt | short a WAKE# pull-up node to GND briefly via 1 k (slot empty) | EXP_INT_N goes low; with DT overlay, IRQ count in /proc/interrupts increases |
| T1.7 DT overlay | apply overlay | `gpiodetect` shows 2 pca953x; `gpioinfo` names match; close OI-02 |

## T2 - Slot power without modules

| Test | Procedure | Pass criteria |
|---|---|---|
| T2.1 Slot rail | `slot on-usb 1` (no module) | +3V7_S1 3.6-3.8 V; SLOT1_PG = 1 within 50 ms; D805 on |
| T2.2 Sequence capture | scope FCPO# (pin 6), RESET# (pin 67, will float high only with module - use expander side SLOT1_RESET), PERST# (TP403) during `slot on 1` | order and delays match power-reset-sequencing.md sec. 4 within +-10 % |
| T2.3 Off | `slot off 1` | sequence matches sec. 5; +3V7_S1 < 0.3 V within 100 ms |
| T2.4 Repeat for slots 2, 3 | | same |
| T2.5 Load test | electronic load 3.5 A pulses (577 us / 4.6 ms GSM-like burst, or 1 A -> 3.5 A steps) on +3V7_Sn via a dummy M.2 card or test leads | droop stays > 3.3 V (EM92/FN990 min 3.135 V); ripple < 30 mV at the card ([FN990] Table 15; EM92 allows 100 mVpp) - close OI-36 |

## T3 - USB path (no modules)

| Test | Procedure | Pass criteria |
|---|---|---|
| T3.1 Hub attach | USB-C to FRDM; `hub-reset`; `hub-attach` | `lsusb -t` shows USB5744 (USB2 + USB3 hubs, 3 ports each enabled, port 4 disabled); close OI-05/OI-07 |
| T3.2 Without attach | power-cycle, no attach | hub absent (expected SOC_CFG behaviour) |
| T3.3 Cable flip | reverse USB-C | hub enumerates at SuperSpeed both orientations (HD3SS3220) |

## T4 - PCIe path (no modules, then one module)

| Test | Procedure | Pass criteria |
|---|---|---|
| T4.1 Switch enumeration | boot FRDM with carrier powered first | `lspci -tvnn`: 12d8:c008 upstream + 5 downstream bridges; record BDFs and LNKCAP port numbers -> close OI-11 |
| T4.2 Link speed | `lspci -vv` upstream LnkSta | 8 GT/s x1 (accept 5 GT/s, record, see OI-08); no AER errors in 10 min idle |
| T4.3 One module | fit EM9291 or FN990A28 in slot 1; `slot on 1` | 17cb:0308 (sub 18d7:0301 EM929x / 1c5d:2010 FN990, record actual - OI-10) appears behind P1 within the 10 s rescan window; mhi-pci-generic binds; `/dev/wwan0mbim0`, `wwan0at0` within 60 s (EM92 power-on max 53 s); PORTGOOD LED D302 on (steady at 8 GT/s); scope PERST# >= 150 ms after SLOT1_PG (close OI-28 for FN990) |
| T4.4 Late-power BAR assignment | as T4.3 but slots powered after Linux boot | BARs assigned; if not, try options in linux-bringup.md known issue 1; close OI-12 |
| T4.5 AT | `AT+CGMR`, `AT+CFUN?` on wwan0at0 | responses OK |

## T5 - Single modem data, then lifecycle

| Test | Procedure | Pass criteria |
|---|---|---|
| T5.1 Registration | SIM in slot 1, antennas, `mmcli -m 0 --enable`, FCC unlock if needed | registered; `mmcli -m 0` shows operator, RAT; FCC lock state recorded (OI-09) |
| T5.2 Data | `mmcli -m 0 --simple-connect='apn=...'`, iperf3 UL/DL 60 s to a server we control | throughput recorded (no threshold yet, TODO); no driver errors |
| T5.3 Power-cycle loop | `slot cycle 1` x 20 | 20/20 modem re-appears and re-registers; no kernel oops/hang; record time per cycle |
| T5.4 Isolation | slots 1+2 up with traffic on 2; cycle slot 1 x 10 | slot 2 iperf continues with no gap > 1 s (TODO threshold); no AER escalation on slot 2 |
| T5.5 Warm reset | `slot warm-reset 1` x 10 | 10/10 recover |
| T5.6 RF disable | `slot rf-off 1` / `rf-on 1` | modem reports RF off/on (MM state), link recovers |
| T5.7 Thermal | full-rate UL+DL for 30 min with fan | module < TODO °C (vendor operating range, OI-19); no throttling events |

## T6 - USB fallback

| Test | Procedure | Pass criteria |
|---|---|---|
| T6.1 USB mode | `slot on-usb 1` (PCIE_SEL=0, PERST# held). Sierra only: fit DNP pin-20 PU and pin-22 VBUS_SENSE PU first (never with Telit) | module enumerates on hub port 1 (FN990A 1bc7:107x, EM9291 1199:90e3; record interfaces); no PCIe device for slot 1; close OI-03 |
| T6.2 Data over USB | MBIM/NCM via MM | data works; throughput recorded |
| T6.3 Mixed | slot 1 USB, slots 2/3 PCIe | all three usable simultaneously |

## T7 - Three modems

| Test | Procedure | Pass criteria |
|---|---|---|
| T7.1 Staggered power-on | `slot on all` | three 17cb:0308 endpoints, three wwan devices, three modems in MM; 12 V input current peak recorded |
| T7.2 Simultaneous load | iperf3 on all three, 10 min | aggregate throughput recorded; no PCIe errors; 12 V input current, rail droop recorded |
| T7.3 Stability | 12 h idle-registered + periodic traffic | no modem loss; recover counts logged |
| T7.4 Stable naming | reboot x5 | udev names map to the same physical slots every time |
| T7.5 RF coexistence | all three on different operators / bands; measure per-link throughput with others idle vs active | degradation recorded (TODO acceptance) |

## T8 - Bonding

Pass/fail thresholds are TODO until bonding-requirements.md sections 3-4 are filled in.

| Test | Procedure | Pass criteria |
|---|---|---|
| T8.1 Aggregation | chosen bonding option over 3 links, single bulk flow | aggregate goodput >= TODO % of sum of individual links |
| T8.2 Hard failover | pull antenna / `slot hard-off n` mid-stream | gap <= FO-1 + FO-2 targets; TC-1/TC-2 sessions survive |
| T8.3 Degradation | netem loss/delay on one link | scheduler shifts traffic within TODO s; latency p99 of TC-2 within budget |
| T8.4 Recovery ladder | force a modem hang (or simulate) | LH-6 ladder executes; other links unaffected |
| T8.5 Long run | 24 h mixed traffic | no leaks/crashes; metrics complete |
