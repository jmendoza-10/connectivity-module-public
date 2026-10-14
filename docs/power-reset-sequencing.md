# Power, reset and per-modem sequencing - WWAN carrier rev 0.3

Status: **design intent, not bench-verified.** No rev 0.3 board has been built. Every timing below is either taken from a module
document (cited, with the table/figure) or marked **UNVERIFIED** (engineering choice / needs measurement or vendor confirmation).

Rev 0.3 replaces the Fibocom FM350-GL (MediaTek T700) timings of rev 0.2 with the spin-1 cards: **Sierra Wireless EM9291**
and **Telit FN990A28** (both Qualcomm SDX65-class, `mhi_pci_generic` on Linux). The slot is vendor-neutral; the sequence below is
the **union** of both vendors' requirements, so one firmware procedure works for either card in any slot.

Pin names, expander addresses and bit positions are in [hw-sw-interface.md](hw-sw-interface.md) (generated from the netlist).
`carrierctl.py` in `software/tools/` implements these procedures and reads its pin map from the generated `carrier_map.json`.

## Sources

| Tag | Document | Sections used |
|---|---|---|
| [EM92] | Sierra Wireless EM92XX Product Technical Specification, 41114313 **Rev 5 (January 2025)** | Table 2-1 (pin levels), 2.6.3 Table 2-9 (FCPO#/RESET_N), 2.6.4 PLA_S2_N, 2.7 PCIE_DIS, 4.3.2.1 Fig. 4-2 + Table 4-8 (PCIe timing), 4.3.2.2 Table 4-9 (USB timing), 4.3.2.4 required shutdown sequence, 4.3.3 supply noise |
| [FN990] | Telit FN990 Family Hardware Design Guide, 1VV0301752 **Rev 3 (2022-10-07)** | pin tables, Table 18 (GNSS bias LDO), 6.2.1 power on (Figs. 3-5), 6.2.2 power off (Figs. 6-8), 6.2.3 reset (Figs. 9-10), Table 29 host interface switch |
| [PI7C] | Diodes PI7C9X3G606GP datasheet DS43484 Rev 5-2 | 10 Power sequence, DC table (PERST_L slew) |
| [USB5744] | Microchip USB5744 datasheet DS00001855J | 5.1 hub stages (SOC_CFG), 10.6 power/reset timing (Tables 10-5 to 10-7) |
| [TCA] | TI TCA6416A datasheet SCPS194F | power-on reset, register defaults |
| [LM61460] | TI LM61460 datasheet | EN threshold, PGOOD |

Not available to us (flagged where it matters): the Telit FN990 power-on/off **figures** are images; their numeric content (e.g.
PERST# delay in PCIe EP mode, total shutdown time) did not survive text extraction and is marked **UNVERIFIED** below. Telit's
FN990**A28** variant-specific notes (if any) were not found; the HDG covers the FN990 family.

## 1. Board power tree and hardware-sequenced rails

```
+12V in -> F101 -> U101 LM74800-Q1 ideal-diode controller (Q101/Q102 onsemi NVMFS5C646NL) -> +12V
  +12V -> U102 LM61460 -> +3V3 ---- PG_3V3 (open drain, 10 k pull-up) --+--> EN U103 TPS568230 -> +0V95 (PI7C core)
                                                                       +--> EN U104 TPS62130  -> +1V8  (PI7C I/O, EEPROM)
                                                                       +--> EN U105 TPS62130  -> +1V2  (USB5744 core)
  +12V -> U201/U202/U203 LM61460 -> +3V7_S1/S2/S3  (EN = SLOTn_PWR_EN from expander U801, 100 k pull-down = OFF by default)
```

Slot rail: 3.74 V nominal. Both cards accept 3.135-4.4 V ([EM92] Table 2-1 VCC; [FN990] VPH_PWR). Peak current 3.0 A
([EM92] Table 4-5) / 4 A ([FN990]); the LM61460 is a 6 A part. Ripple limits: EM92 100 mVpp 1-100 kHz ([EM92] 4.3.3); **FN990 30 mV max ([FN990] Table 15)** - the tighter one governs; **measure** (OI-36).

Hardware guarantees (no software involvement):

1. +3V3 comes up first; +0V95, +1V8 and +1V2 start only after `PG_3V3` releases (unchanged from rev 0.2; OI-07 USB5744
   VDD12/VDD33 order still open - see section 8).
2. The PI7C switch PERST_L comes from the host (FRDM-IMX95) via the riser (unchanged; power the carrier before or with the host).
3. All three slot rails default **off** (SLOTn_PWR_EN 100 k pull-down; expander pins are inputs after POR [TCA]).
4. Per-slot defaults with the expander still in POR state (rev 0.3):
   - FCPO# **low** (47 k pull-down) - card off.
   - RESET / WDIS NFET gates off (100 k pull-downs) - RESET#/W_DISABLE1# not driven.
   - **PCIE_EN low (rev 0.3: 10 k pull-DOWN, was a pull-up in rev 0.2)** - slot PERST# held low, so the SN74LVC1G08 never drives
     3.3 V into an unpowered card ([EM92] 4.3.2.1: "host must not drive any signals to the module until >100 ms from the start of the
     power-on sequence"; [FN990] 6.2.1 back-powering note).
   - **PCIE_SEL high (10 k pull-up)** - pin-20 NFET on, M.2 pin 20 low = PCIe host interface on both cards.

## 2. Signal conventions (expander level -> pin at the card)

| Expander net | Write 1 means | Card pin effect |
|---|---|---|
| `SLOTn_PWR_EN` | slot buck on | +3V7_Sn on card VCC (pins 2/4/70/72/74). Pins 24/38/68 (EM92 optional VCC) are **NC** |
| `SLOTn_FCPO_N` | **release** FCPO# | FULL_CARD_POWER_OFF# (pin 6) high -> card boots; low -> graceful shutdown (both vendors) |
| `SLOTn_RESET` | **assert** reset | 2N7002 pulls RESET# (pin 67) low. Open drain only: [EM92] "should not be driven or pulled to a logic high"; [FN990] "do not use any pull-up resistor ... only open-collector" |
| `SLOTn_WDIS` | **assert** RF disable | 2N7002 pulls W_DISABLE1# (pin 8) low (internal PU on both cards) |
| `SLOTn_PCIE_EN` | **allow** PERST# | slot PERST# (pin 50) = host PERST# AND PCIE_EN; 0 holds PERST# low. JPx01 fitted = hard hold |
| `SLOTn_PCIE_SEL` (rev 0.3) | **PCIe** host interface | 2N7002 pulls pin 20 low. Telit USB_PCIE_SWITCH low = PCIe (+USB debug); Sierra PCIE_DIS low = PCIe |
| `HUB_RESET_N` | **release** hub reset | USB5744 RESET_N high |

Why PCIE_SEL is a separate line (change vs the rev 0.3 brief, which proposed driving the pin-20 FET from `SLOTn_PCIE_EN`):
both cards **sample pin 20 at boot** ([FN990] Table 29 "at the beginning of the power on sequences"; [EM92] 2.7 "when the module
boots"), so pin 20 must already be low when FCPO# rises, while PERST# must stay low until >= 150 ms after power valid
([EM92] Table 4-8 T_pvpgl). One signal cannot do both. PCIE_SEL uses three of the four spare U802 pins (P1.4-P1.6).

## 3. Timing parameters (union of both cards)

| Parameter | Sierra EM92XX | Telit FN990 | Carrier value | Notes |
|---|---|---|---|---|
| Rail valid -> first host signal | > 100 ms ([EM92] 4.3.2.1 "Important") | back-power note only ([FN990] 6.2.1) | FCPO# may rise at PG; **no other signal** for 150 ms | FCPO# is the control input both vendors tie to VCC in always-on designs ([EM92] Table 2-9) |
| VCC/VPH -> FCPO# high | - | "power-on trigger time", may be 0 ms ([FN990] 6.2.1 note) | at `SLOTn_PG` | |
| Power valid -> PERST# high | **>= 150 ms** (T_pvpgl, Table 4-8) | in Fig. 4 (PCIe EP) - **UNVERIFIED** (figure not extracted) | **200 ms** after PG | covers EM92 min + margin |
| REFCLK stable -> PERST# high | >= 100 µs (T_perst_clk) | - | switch REFCLKOn assumed running | **UNVERIFIED**: PI7C REFCLKO gating vs CLKREQ# (OI-12) |
| PERST# high -> PLA_S2_N high | 760 typ / 950 max ms (T_rst_pla) | n/a (pin 28 = TGPIO_08) | - | PLA_S2_N only on test point TPx02 in rev 0.3 |
| PERST# high -> link/enumeration | not specified | not specified | rescan at +1 s, retry every 1 s up to **10 s** | **UNVERIFIED**; MHI devices link in SBL, firmware loads later |
| Power-on sequence (to host interface ready) | 43 typ / 53 max s PCIe; 52 / 62 s USB (Tables 4-8, 4-9) | "at least 50 s" to activation ([FN990] 6.2.1.1) | ModemManager waits; don't power-cycle for **65 s** | |
| Graceful off: FCPO# low -> safe to remove power | T_pwr_off_seq 8 typ / 12 max s PCIe; 6 / 10 s USB; done when PLA_S2_N low | shutdown done when VREG_L6B_1P8 (pin 65) drops; total time in Fig. 6 - **UNVERIFIED** | **15 s** fixed wait (no PLA/VREG monitor in rev 0.3) | [FN990] FCPO# shutdown "only effective after module boots up completely" |
| FCPO# low during boot | card finishes boot (T_pwr_on_seq) then shuts down (Table 4-8 note d) | not effective until booted | worst case 53 + 12 = **65 s** before power removal | carrierctl `off` refuses to cut power earlier unless `hard-off` |
| PERST# low before FCPO# low | 0 s min, any time up to FCPO# low (T_rst_poff) | - | PERST# first, then FCPO# | |
| RESET# pulse | >= 450 ms ([EM92] Table 2-9) | > 1 s ([FN990] 6.2.3.1) | **1.2 s** | emergency only (both vendors) |
| RESET# during power-up | do not hold (draws power in reset) | must **not** be low at power-on (>1 s low = reset; low = power-on trigger) | **released** (rev 0.2 held it low - removed) | |
| Host-interface select (pin 20) | PCIE_DIS: low/open = PCIe, high (1.8 V, max 2.1 V) = USB; mode change needs power cycle | USB_PCIE_SWITCH: int. 10 k PU 1.8 V; high = USB only, low = PCIe + USB debug | PCIE_SEL set **before** FCPO# rises | Sierra USB needs DNP R pin20->+1V8 fitted |
| Off time before re-power | not specified | not specified | **1 s** | **UNVERIFIED** (rail bleed-down, no active discharge) |

## 4. Carrier power-up (once per boot)

Unchanged from rev 0.2 except the new defaults in 1.4:

```mermaid
sequenceDiagram
    autonumber
    participant PSU as 12 V supply
    participant HW as Carrier rails (hardware)
    participant HOST as FRDM-IMX95 (Linux)
    participant EXP as TCA6416A U801/U802
    participant SW as PI7C9X3G606GP
    participant HUB as USB5744
    PSU->>HW: +12V on
    HW->>HW: +3V3 up, PG_3V3 -> +0V95/+1V8/+1V2 up
    HW->>EXP: POR: pins are inputs; pulls: slots OFF, FCPO# low, PERST# held, pin 20 low (PCIe)
    Note over HUB: RESET_N high via RC -> straps latched (SMBus mode),<br/>hub waits in SOC_CFG [USB5744 5.1.5]
    HOST->>SW: host PERST# released by pci-imx6 probe
    SW-->>HOST: switch upstream + downstream ports enumerate (no endpoints yet)
    HOST->>EXP: pca953x probe / carrierctl init: OUTPUT regs first, then CONFIG regs
    HOST->>EXP: HUB_RESET_N pulse (workaround OI-07)
    HOST->>HUB: SMBus attach
    HOST->>HOST: per-slot bring-up (section 5), slot 1, then 2, then 3 (2 s stagger, UNVERIFIED)
```

## 5. Per-slot bring-up (PCIe mode, either card)

Preconditions: slot fully off (`PWR_EN=0, FCPO_N=0, RESET=0, WDIS=0, PCIE_EN=0, PCIE_SEL=1`).

| Step | Action | Wait | Source |
|---|---|---|---|
| 1 | `PCIE_EN=0` (PERST# held), `PCIE_SEL=1` (pin 20 low = PCIe), `RESET=0`, `WDIS=0`, `FCPO_N=0` | - | [EM92] 2.7, [FN990] Table 29: pin 20 sampled at boot |
| 2 | `PWR_EN=1` | until `SLOTn_PG=1`, timeout 50 ms (**UNVERIFIED**) | [LM61460] PGOOD = "power valid" |
| 3 | `FCPO_N=1` (card boots) | - | [EM92] Fig. 4-2, [FN990] 6.2.1 |
| 4 | `PCIE_EN=1` (PERST# follows host PERST#, already high) | **200 ms after PG** (EM92 T_pvpgl >= 150 ms) | [EM92] Table 4-8; [FN990] Fig. 4 UNVERIFIED |
| 5 | `echo 1 > /sys/bus/pci/rescan` (switch hot-plug disabled) | first at +1 s, then every 1 s up to 10 s until the endpoint appears (**UNVERIFIED**) | Linux |
| 6 | `mhi-pci-generic` binds (17cb:0308, sub 18d7:0301 EM929x / 1c5d:2010 FN990), MHI loads firmware stages; MBIM/AT ports appear | up to 53 s (EM92 max) / >= 50 s (FN990) | [EM92] Table 4-8, [FN990] 6.2.1.1 |
| 7 | ModemManager detects the modem | - | linux-bringup.md |

```
              step: 2  3        4 (PG+200ms)        5..6
+3V7_Sn   ____/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
pin20     ______________________________________________   (low the whole time = PCIe; PCIE_SEL=1)
FCPO#     _______/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
RESET#    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾   (not driven; card-internal pull-up)
PERST#    _____________________________/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
                 |<-- T_pvpgl >= 150 ms -->|
```

PERST# edge: the slot PERST# is a SN74LVC1G08 push-pull output (3.3 V; EM92 VIH 1.5 V..VCC; FN990 PERST# is in the VPH domain).

## 6. Per-slot orderly shutdown (either card)

| Step | Action | Wait | Source |
|---|---|---|---|
| 1 | `mmcli -m N --disable` (or inhibit) | - | - |
| 2 | Optional `AT+CFUN=0` on the AT port | until `OK`, 5 s cap (**UNVERIFIED** cap for these cards) | - |
| 3 | `echo 1 > /sys/bus/pci/devices/<BDF>/remove` | - | Linux; avoids surprise-down |
| 4 | `PCIE_EN=0` (PERST# low) | - | [EM92] T_rst_poff >= 0 before FCPO# low |
| 5 | `FCPO_N=0` (graceful shutdown trigger, both cards) | **15 s** fixed (EM92 T_pwr_off_seq max 12 s; FN990 figure UNVERIFIED) | [EM92] 4.3.2.4, [FN990] 6.2.2.1.1 |
| 6 | `PWR_EN=0` | - | [EM92] 4.3.2.4 step 3 "Remove power" |
| 7 | leave `PCIE_SEL=1` (pin-20 FET holds the pin low, no 1.8 V into the unpowered card if the Sierra DNP pull-up is fitted), `RESET=0`, `WDIS=0` | - | back-power avoidance |

If the card has not finished booting when FCPO# drops, both vendors delay shutdown until boot completes: wait up to 65 s, or use
`hard-off` (rail removal; file-system corruption risk on the card - [EM92] 4.3.2.4 "Important", [FN990] 6.2.2 warning).

Rev 0.4 candidate (OI-27): level-shift PLA_S2_N (EM92 pin 28) / VREG_L6B_1P8 (FN990 pin 65) into U802 P1.7 so firmware can wait for
the actual "safe to remove power" indication instead of a fixed 15 s.

## 7. Power cycle / reset (single slot)

- **Power cycle** (`carrierctl slot cycle n`): section 6, then >= 1 s off (**UNVERIFIED**), then section 5. Also the only way to change
  the host interface (pin 20 is sampled at boot).
- **Hardware reset** (`warm-reset`, emergency only): pci remove, `RESET=1` for **1.2 s** (FN990 > 1 s; EM92 >= 450 ms), `RESET=0`,
  then rescan as in section 5 step 5. Both vendors say to use it only when the host interface is unresponsive.
- Do not toggle FCPO# again within the off sequence time (12 s EM92) of de-asserting it.

## 8. USB host-interface mode (per slot)

| Card | Hardware | Firmware |
|---|---|---|
| Telit FN990 | nothing to fit | `PCIE_SEL=0` **before** `FCPO_N=1` (pin 20 floats to 1.8 V via the card's 10 k PU = USB only, [FN990] Table 29). Keep `PCIE_EN=0`. |
| Sierra EM92xx | fit **Rx08** (10 k pin 20 -> +1V8, PCIE_DIS high = USB) and **Rx09** (10 k pin 22 VBUS_SENSE -> slot rail, USB present). **Never fit Rx09 with a Telit card** (pin 22 = 1.8 V TGPIO_06). | `PCIE_SEL=0` before `FCPO_N=1`; `PCIE_EN=0`. |

**UNVERIFIED:** EM92 internal PCIE_DIS pull-down strength (the 10 k to +1V8 must win; pin 20 has no test point - measure at the
Qx03 drain / Rx08). Whether EM92 tolerates PERST# held low in USB mode (Table 4-9 does not mention PERST#).
USB timings: [EM92] Table 4-9: power-on sequence 52 typ / 62 max s; off 6 / 10 s.

## 9. USB5744 hub reset and attach

Unchanged from rev 0.2 (see git history): `HUB_RESET_N=0` >= 5 ms (RC), `HUB_RESET_N=1`, wait 10 ms (tcsh + RC), SMBus attach to
0x2D (**UNVERIFIED** address). trstia unit in [USB5744] Table 10-7 still **UNVERIFIED** (garbled in extraction). OI-07 open.

## 10. TCA6416A initialisation rule

[TCA]: after POR or RESET# all ports are inputs and the output registers read back 0xFF. Writing the configuration register first
would drive every output high (all slots on, FCPO# released, cards in reset, RF disabled, PERST# allowed, PCIe selected)
simultaneously. **Always** write output registers 0x02/0x03 with the values from hw-sw-interface.md *before* configuration registers
0x06/0x07. `EXP_RESET_N` (header pin 6) returns all pins to inputs; the board pulls then remove every slot's power without a graceful
shutdown (emergency use only).
