# Connectivity Module: Architecture (rev 0.2, 2026-10-09)

**Changes vs rev 0.1:**
- Triple-modem bonding (3x 5G) via a PCIe Gen3 packet switch.
- Phased build: a bench prototype (spin 1) first, then a vehicle spin (spin 2).
- Spin 1 must cost **under $1,500**.
- Prefer AEC-Q parts for transceivers, PHYs and protection, so the schematic carries over to spin 2.
- The 10G-to-SJA1110 question is resolved.
- The u-blox ZED-F9K is no longer offered (see section 9).

Diagrams:
- Target / vehicle architecture: `block-diagram.png` (source `block-diagram.mmd`).
- Spin 1 bench build: `block-diagram-v1-bench.png` (source `block-diagram-v1-bench.mmd`).

Every price and part number is cited in `parts-shortlist.md` and `bom-estimate.md`.

---

## 1. Phasing

| | **Spin 1: bench prototype (≤ $1,500)** | **Spin 2: vehicle-intent** |
|---|---|---|
| Host | **NXP FRDM-IMX95 dev board** ($210 at NXP). 15x15 i.MX 95, 8 GB LPDDR4X, 2x GbE RJ45, 2x CAN (TJA1051), USB3 Type-C, **M.2 Key-M = PCIe Gen3 x1**, IW612 Wi-Fi 6/BT M.2 | i.MX 95 19x19 SoM (Compulab MCM-iMX95, solder-down) on a custom carrier, later chip-down MIMX9596AVZXNAC |
| What we build | **"WWAN carrier" PCB**, cabled to the FRDM M.2 Key-M slot: PCIe switch + 3x M.2 Key-B modem sockets + per-modem 3.7 V rails + 3x SIM + 12 V front end + USB3 hub fallback | Full carrier: everything in spin 1 plus the SJA1110 T1 switch, T1 PHYs, 5x CAN-FD, GNSS, Wi-Fi module, NTN option |
| Fab | JLCPCB / PCBWay, 6-layer, PCBA with BGA X-ray | 8-10 layer carrier (SoM). Chip-down needs 10-12 layer HDI |
| Grade | Industrial modules OK. **Protection, power and PCIe-switch parts chosen AEC-Q100 where cost is similar**, so the schematic pages carry over | AEC-Q throughout, plus automotive modems (Quectel AG55xQ LGA) |

Why a dev board plus an interface carrier for spin 1:
- Custom i.MX 95 carrier/SoM boards need 8+ layers and an expensive SoM or eval kit. The Compulab eval kit alone is $545.
- The FRDM board already gives you Wi-Fi/BT, 2 CAN, 2 GbE (one for the satellite terminal, one for LAN), the PF09/PF53 power design, and a working NXP Yocto BSP.
- The only thing it can't do is three modems, so spin 1 builds exactly that. The modem/PCIe/power/SIM pages become spin 2's schematic pages unchanged.

---

## 2. Processor and SoM: PCIe and 10G exposure (verified)

| Board / SoM | SoC package | PCIe Gen3 x1 exposed | 10G SerDes (SGMII/2.5G/USXGMII) | CAN-FD | Temp | Fit |
|---|---|---|---|---|---|---|
| **NXP FRDM-IMX95** | 15x15 | **1** (M.2 Key-M) | No (15x15 has no 10GbE) | 2 (TJA1051 on board) | commercial dev board | **Spin 1 host** |
| **Compulab MCM-iMX95** | 19x19 | **2** | **Yes: "XFI, SGMII (2.5G and 1G), 10G-USXGMII"** | up to 5 | -40..85 °C (industrial) | **Spin 2 SoM** (solder-down, no connector) |
| Toradex SMARC iMX95 | 19x19 | 2 | Yes (SGMII or USXGMII on SERDES) | 2 SMARC + alternate-function | -40..85 °C (IT) | Good alternative, MXM edge connector |
| Variscite DART-MX95 | 19x19 | 2 | Yes (10GbE) | up to 5 | industrial | Alternative (datasheet download was blocked; specs from vendor page/search) |
| Toradex Verdin iMX95 | **15x15** | **1** | **No** | 5 | IT | **Not suitable** (one PCIe, no 10G) |

**Resolved: i.MX 95 10G port to SJA1110A.** Compulab's MCM-iMX95 reference guide states the 10 GbE controller supports **XFI, SGMII (2.5G and 1G) and 10G-USXGMII**. Toradex's SMARC datasheet confirms SGMII/USXGMII on that SERDES. SJA1110A ports 3/4 support SGMII and 2500BASE-X.

The 1G SGMII uplink is supported on both sides. For the 2.5G uplink, both ends must use the same 2.5G flavour without in-band autoneg (Linux `phy-mode = "2500base-x"`). That's a bring-up check, not a blocker. This needs the **19x19 package** (spin 2), so spin 1 has no SJA1110.

---

## 3. Triple-modem WWAN subsystem

### 3.1 PCIe packet switch: chosen part

**Diodes PI7C9X3G606GP (bench) / PI7C9X3G606GPQ (AEC-Q100 Grade 3, same FCA144 package)**

| Item | Detail |
|---|---|
| Ports / lanes | 6 ports / 6 lanes PCIe Gen3. Upstream x1 or x2, up to 5 downstream x1/x2 |
| Our config | **x1 upstream ← i.MX 95 PCIe1, 3x x1 downstream → modems, 2 spare x1** (NVMe log storage, 4th modem or a PCIe Wi-Fi later) |
| Clocking | **Integrated PCIe ref-clock buffer**, so no separate 100 MHz fan-out buffer is needed |
| Power | 2.5 W typ (full load), rails 0.95 V + 1.8 V |
| Package | 144-ball FC-LFBGA 10x10 mm (JLCPCB/PCBWay assemble BGA with X-ray) |
| Grade | GP: -40..85 °C industrial. **GPQ: AEC-Q100 Grade 3, PPAP, IATF 16949** |
| Price | Digi-Key $35.09 @ 1 (PI7C9X3G606GPBFCAEX) |
| Linux | Transparent switch, enumerated by the standard `pcieport` driver; no vendor driver. Modems use mainline `mhi_pci_generic` (RM520N-GL is in the PCI ID table; the newer RM520N-GLAP ID was a 2025 patch, so check your kernel). Diodes' PCIBUDDY / PHY Eye tools help with debug |
| Reference design | Contact Diodes for the EVB/reference schematic (not publicly downloadable) |

**Alternatives considered**

| Part | Why not the primary |
|---|---|
| ASMedia ASM2806 (Gen3, x1/x2 up, 4x x1 down, QFN88 10x10) | Cheaper and easier to assemble (QFN), with an open hobby reference design (github will127534/PCIe3_Hub). **No automotive grade**, so the schematic wouldn't carry over. Good fallback if the BGA worries you for spin 1 |
| Microchip Switchtec PCI1003 (Gen4, 16 lanes, AEC-Q100 Grade 2, ASIL-B ready) | Overkill: 353-ball 16x16 FCCSP, x2-minimum ports, higher cost and power. Revisit only if you go Gen4 / multi-host |
| Diodes PI7C9X3G808GPQ (8 lanes) | Only if more than 5 downstream endpoints are needed |

### 3.2 Lane allocation options

i.MX 95 19x19 has 2 PCIe Gen3 x1 controllers; the FRDM (15x15) has 1.

| Option | How | Pros | Cons |
|---|---|---|---|
| **A (recommended): switch on lane 1, all 3 modems behind it; lane 2 kept free** | PCIe1 → PI7C9X3G606 → M1/M2/M3 | Identical data path, latency and driver for all three bonded links, which makes bonding scheduler tuning easier. Works on the 1-lane FRDM *today*. Lane 2 stays free for NVMe or a 4th radio. 2 spare switch ports | Shared upstream: Gen3 x1 ≈ 7.9 Gb/s raw (~6.5 Gb/s usable). Three real-world 5G links (typically < 1 Gb/s each) fit easily, though 3x theoretical peak (3x 2.4 Gb/s SA DL) would not |
| B: lane 1 → M1 direct, lane 2 → switch → M2/M3 | Split | Removes switch latency on one modem | Asymmetric latency hurts bonding. Uses both lanes, so there's no room for NVMe without the switch anyway. Not possible on FRDM |
| C: lane 1 → M1, lane 2 → M2, USB3 → M3 (no switch) | No switch | Cheapest BOM, no BGA | Mixed MHI + USB (QMI/MBIM) stacks with different latency/jitter. The i.MX 95's only USB3 port is consumed. Not possible on FRDM (1 lane) |
| D: all 3 over USB3 via hub (USB5744) | FRDM USB3 Type-C → 4-port USB 3.2 Gen1 hub | Very cheap (~€6 hub IC), no PCIe SI risk | 5 Gb/s shared, higher CPU overhead and latency than PCIe/MHI. USB5744 is **not** AEC-Q100 |

**Decision:** Option A as primary. The spin-1 carrier also **routes each M.2 socket's USB 3.x/2.0 to a USB5744 hub** (Option D) as a populate-option fallback. M.2 Key-B sockets carry both PCIe and USB anyway, so this costs about $6 and lets you A/B-test PCIe vs USB bonding latency. On spin 2, drop the hub or swap in an automotive hub.

---

## 4. Power: 3-modem budget and 3.7 V rail sizing

### 4.1 Per-modem requirement (source: Quectel RM520N Hardware Design V1.3, §3.3 Power Supply, §6.1 Table 42, §6.2 Table 43)
- VCC range 3.135-4.4 V, **nominal 3.7 V**. VCC must never dip below 3.135 V during TX bursts. Ripple max 100 mV.
- **Supply capability ≥ 3.0 A continuous and ≥ 4 A peak**, per modem.
- Bulk: **2x 220 µF low-ESR** + MLCC array (100 nF / 6.8 nF / 220 pF / 68 pF ...) at the socket VCC pins.
- Measured averaged current, RM520N-GL (Table 43):

| Mode | Current |
|---|---|
| Sleep | ~9.5 mA |
| Idle, SA, USB3 active | 60 mA |
| LTE B1 @ 24 dBm | 1080 mA |
| LTE UL 1CA 256QAM (CA_1A-3A-7A) | **1512 mA (worst listed)** |
| NR n1 @ 23 dBm | 970 mA |
| NR n78 @ 26 dBm | 480 mA |
| EN-DC (DC_3A_n78A) | 1168 mA |

### 4.2 Rail architecture

```
12 V bench / KL30 ─► TVS ─► LM74800-Q1 + 2x N-FET (reverse + OVP; AEC-Q100, carries to spin 2)
                    ─► π-filter ─► 12 V bus (bulk ≥ 100 µF)
                        ├─► BUCK_M1: 3.7 V / 6 A (AEC-Q100, e.g. TI LMQ61460-Q1) ─► LC/ferrite ─► M.2 #1 VCC (2x220 µF + MLCC)
                        ├─► BUCK_M2: 3.7 V / 6 A ─► M.2 #2
                        ├─► BUCK_M3: 3.7 V / 6 A ─► M.2 #3
                        ├─► 3.3 V / 2 A: PCIe switch I/O, USB hub, SIM, misc. LDOs: 1.8 V
                        └─► 0.95 V / 2 A (PCIe switch core)
Each modem buck EN ← GPIO (FRDM EXPI header / I2C GPIO expander) so the host can hard power-cycle a hung modem independently.
```

- **Separate buck per modem, not one shared 3.7 V rail.** It isolates TX-burst droop and conducted noise between modems, allows independent power cycling (essential for bonding robustness), and spreads the heat.
- Size each buck for **≥ 4 A peak / 3 A continuous** (Quectel requirement). A 6 A part gives margin at 85 °C. LMQ61460-Q1 (3-36 V in, 6 A, AEC-Q100) was **backordered at Digi-Key (ETA Mar 2027)** when checked, so pick an in-stock AEC-Q100 5-6 A buck from LCSC/Digi-Key at order time. The schematic block is otherwise the same.
- Put an M.2 3.3 V-pin-compatible note in the schematic: we deliberately feed 3.7 V (within the 3.135-4.4 V range of RM520N and EM060K). **Don't plug 3.3 V-only M.2 cards** (e.g. SSDs) into these sockets.

### 4.3 System budget

| Load | Typical (connected, moderate traffic) | Worst-case average | Supply capability to design for |
|---|---|---|---|
| 3x RM520N-GL @ 3.7 V | 3x ~0.5-1.0 A ≈ 5.5-11 W | 3x 1.512 A x 3.7 V ≈ **16.8 W** | 3x 3 A cont / 4 A peak = 9 A / 12 A ≈ **33 W cont / 44 W peak** |
| PCIe switch | 2.5 W (Diodes typ) | 2.5 W | 3 W |
| USB hub (if fitted) | ~0.5 W | 1 W | 1.5 W |
| FRDM-IMX95 (SoC, LPDDR4X, Wi-Fi, PHYs) | ~4-6 W (estimate; refine with NXP AN14449) | ~10 W | own supply (USB-C PD) |
| **Carrier total @ 12 V** | ≈ 9-15 W (0.8-1.3 A) | ≈ 21 W (~1.9 A at 90 % eff.) | **size 12 V input/protection for ≥ 4 A cont, 5 A peak** |

Spin 2 adds: SJA1110 + PHYs ~2-3.5 W, GNSS + NTN ~0.5-2 W, i.MX 95 module ~3-8 W, giving roughly **30-35 W worst-case average and ~50 W supply capability**. Plan for a cold-crank behaviour decision (the modems will brown out below ~6 V input unless you add a boost stage).

---

## 5. Thermal
- Worst-case modem dissipation is ≈ 5.6 W each (≈ 17 W for three) plus 2.5 W for the switch, concentrated in about 3x 30x52 mm.
- Quectel guidance: soft thermal pad between the module shield and a heatsink, heatsink base larger than the module, and a heatsink attached to the shield cover (Hardware Design §6.5). The module is specified to -40..85 °C, and 3GPP performance degrades above its normal range.
- **Spin 1 (bench):** stick-on aluminium heatsinks on each modem plus one 40-60 mm 12 V fan across the M.2 row. Space sockets ≥ 10 mm apart. Put a thermistor near each modem, read through the host (or use `AT+QTEMP`).
- **Spin 2:** modems on the board's bottom side with thermal pads straight to a die-cast lid. Keep the modem heat path separate from the i.MX 95 and the PCIe switch. Budget about 25-30 W into the enclosure, which means a finned enclosure or forced air in a sealed box.

---

## 6. Antennas, RF isolation, connectors

### 6.1 Antenna count

| Radio | Ports | Notes |
|---|---|---|
| Modem 1-3 (RM520N-GL) | **4 each = 12** (ANT0-ANT3, MHF4 on module) | RM520N-GL GNSS L1 rides on ANT3 and L5 on another main port (diplexed in the module), so **each modem's ANT3 antenna must also cover GNSS L1**. Cat 6 EM060K: check its antenna table (fewer MIMO ports) |
| GNSS (standalone, spin 2) | 1 (active, L1/L5) | Not needed in spin 1 (modem GNSS) |
| Wi-Fi/BT | 2 | FRDM IW612 M.2 in spin 1 |
| NTN (optional, spin 2) | 1 (L/S-band) | |
| **Total** | **12 cellular + 2 Wi-Fi in spin 1; 12 + 1 GNSS + 2 Wi-Fi + 1 NTN = 16 in spin 2** | |

### 6.2 Connector plan
- **Spin 1:** MHF4 → SMA bulkhead pigtails (12x) on a laser-cut plate. Use cheap dipole/paddle 600-6000 MHz antennas on SMA, and a magnetic-mount multi-element (4-in-1 or 5-in-1) antenna if you test in a car.
- **Spin 2:** Rosenberger **HFM** multi-position headers (e.g. 4-port HFM per modem, giving 3 headers, plus 1 GNSS FAKRA-C/HFM and 1 Wi-Fi 2-port). Rooftop "shark-fin" multi-modem antennas are custom/expensive, so as an interim plan one 4x4 MIMO antenna per modem.

### 6.3 RF isolation between three co-located modems
1. **Antenna separation dominates.** Aim for ≥ 15-20 dB antenna-to-antenna isolation between modems. At 700 MHz, λ/2 ≈ 21 cm, so on the bench spread antennas at least 20-30 cm apart or use orthogonal polarisation.
2. **Band planning:** put the three SIMs on **three different carriers**, which also gives bonding diversity. Avoid two modems TXing in adjacent bands, and lock bands per modem via `AT+QNWPREFCFG` if self-interference appears.
3. **Known desense pair:** the 2nd harmonic of LTE B13/B14 uplink (777-798 MHz) lands near GNSS L1 (1575.42 MHz). With modem GNSS on ANT3, prefer GNSS from a modem that isn't TXing on B13/B14, or use the standalone GNSS in spin 2.
4. **Conducted coupling:** separate bucks (§4.2), a ferrite/LC filter per VCC, a solid ground plane under all three sockets, and no shared return paths with the PCIe switch.
5. **Coax routing:** keep MHF4 pigtails short, don't bundle TX cables of different modems together, and use double-shielded coax.

---

## 7. SIM plan
- Each RM520N-GL has **(U)SIM1 + (U)SIM2 (dual-SIM single-standby)**.
- **Spin 1:** **3x nano-SIM push-push holders** (one per modem on USIM1), each with ESD protection and a SIM-detect line, so you can drop in three carriers' data SIMs.
  - Optional **MFF2 eSIM footprint on USIM2** of each modem (populate later).
- **Spin 2:** **MFF2 (soldered) eSIM per modem** on USIM1 (automotive-grade eUICC, remote-provisioned per carrier). Keep one nano-SIM holder on modem 1 USIM2 for service/testing.
- Data plans: three different carriers (e.g. AT&T / T-Mobile / Verizon) for bonding diversity. Plan costs are not in the hardware budget.

---

## 8. Everything else (target architecture, spin 2), unchanged from rev 0.1 except where noted
- **Ethernet:** SJA1110A on the i.MX 95 10G SerDes. SGMII 1G is confirmed and 2500BASE-X is likely (§2). 6x integrated 100BASE-T1, 2x TJA1120B 1000BASE-T1. The satellite terminal gets a 1GbE MAC + KSZ9131RNXV (routed WAN).
  - *Spin 1:* the FRDM's second RJ45 GbE goes to the satellite terminal. No T1 in spin 1, or use an off-the-shelf T1 media converter if you already have one.
- **CAN-FD:** 5x TJA1463 (spin 2). *Spin 1:* FRDM's 2x CAN (TJA1051), enough for bench bonding/telemetry tests.
- **Wi-Fi/BT:** u-blox JODY-W5 (SDIO + UART), spin 2. *Spin 1:* FRDM's IW612 M.2.
- **GNSS:** spin 1 uses the modems' built-in GNSS (free). For spin 2, see §9.
- **NTN:** Quectel BG95-S5 / u-blox SARA-S528NM10, optional, deferred to spin 2.
- **Memory:** LPDDR4X/LPDDR5 x32 (no DDR4 on i.MX 95) and eMMC are on the SoM.
- **12 V protection:** LM74800-Q1 ideal-diode front end, reused from spin 1.

## 9. Part status changes found in this pass
- **u-blox ZED-F9K:** u-blox's product URL now redirects to the **ZED-X20K** (X20 all-band automotive DR module), and SparkFun lists its ZED-F9K breakout as retired. Treat ZED-F9K as **not for new designs**. Spin 2 candidates are ZED-X20K (check availability/price) or NEO-M9V (cheaper UDR).
- **LMQ61460-Q1:** backordered at Digi-Key (ETA Mar 2027) when checked. Choose an equivalent at order time.
- **RG255C-GL (RedCap M.2):** Digi-Key lists it at a 30-week lead time. It's listed out of stock at TOP-electronics (€129.92). Not a reliable spin-1 option right now.

## 10. Key risks (updated)
1. **PCIe over a cable from the FRDM M.2 Key-M slot (spin 1):** Gen3 signal integrity through an M.2-to-cable adapter. Mitigations: short, shielded adapter; keep the switch near the carrier's input connector; force Gen2 (`max-link-speed = <2>`) if link training is flaky. Gen2 x1 (~4 Gb/s) still carries 3 real-world modems.
2. **PERST#/CLKREQ#/refclk handling** through the adapter: the switch regenerates downstream refclk. Confirm the FRDM drives REFCLK on its M.2 Key-M, or run SRIS / use a local 100 MHz clock.
3. **Modem bring-up order and power cycling:** independent buck EN + M.2 FULL_CARD_POWER_OFF# / RESET# GPIOs per modem (I2C GPIO expander), so the host can recover any modem without rebooting.
4. **Thermal and RF self-interference** with three modems in close proximity (§5, §6.3).
5. **Carrier approvals:** fine for bench/R&D on test SIMs. A deployed device needs PTCRB/carrier certification per modem/carrier combination.
6. **Spin 2 risks from rev 0.1** still apply: i.MX 95 pin-mux, automotive EMC, automotive modem availability (AG55xQ via Quectel sales), and secure boot.

## 11. Open design questions
1. **Modem mix for spin 1:** 3x RM520N-GL (true 5G, ~$630-810 for modems alone) puts the build at or just over $1,500. 1x RM520N + 2x EM060K (LTE Cat 6), or 3x EM060K, fits comfortably (see `bom-estimate.md`). I have not decided whether bench bonding-logic testing matters more than 5G peak throughput for v1.
2. I have not decided whether the FRDM-IMX95 + carrier is acceptable for spin 1, or whether spin 1 must already be a single custom board (that would mean MCM-iMX95, about $545 eval kit or a SoM purchase, which will not fit $1,500 with 3x 5G).
3. I have not decided whether T1 Ethernet is needed on the bench in v1, or whether it can wait for spin 2.
4. I have not decided which three carriers / SIMs to use, or whether the bench uses eSIM (MFF2).
5. Bonding stack: MPTCP, a custom tunnel (Speedify-like / GRE + scheduler), or a personal design. This decides whether PCIe/MHI vs USB latency matters enough to justify the switch over a USB hub.
6. I have not confirmed whether a bench 12 V / 5 A supply and an SMA antenna set are already on hand. (Excluded from the budget.)

## 12. rev 0.3: MediaTek (Fibocom FM350-GL, T700) modem compatibility. Carrier changes vs RM520N
> **Superseded (2026-10-10):** Fibocom is excluded (PRC-headquartered). Kept for history; see section 13.
Details and sources are in `parts-shortlist.md` (MediaTek section). Budget options are in `bom-estimate.md` (config D recommended: 1x RM520N-GL + 2x FM350-GL).

1. **Supply:** no change. FM350 range 3.135-4.4 V (typ 3.3 V), peak > 3.5 A, ripple < 300 mV. Our per-slot 3.7 V / 6 A buck (≥ 4 A peak) covers both modems.
2. **Power cycling:** Fibocom expects the module to be powered from PCIe Vmain and controlled through the PCIe protocol. With our per-slot buck, software must remove the device (`echo 1 > /sys/bus/pci/devices/.../remove`) before EN-off, then EN-on and rescan. Route **FULL_CARD_POWER_OFF#, RESET#, PERST#, W_DISABLE#** per slot to the I2C GPIO expander. The PI7C9X3G606 supports downstream hot-plug / surprise removal.
3. **PCIe-disable per slot (new):** add a jumper or GPIO that holds the slot's PERST# / gates its REFCLK (or disables the switch port via SMBus/EEPROM). This forces the FM350 into **USB mode**, the community-proven fallback when t7xx/PCIe misbehaves. The slot's USB 3 pairs already go to the USB5744 hub, so **fit the hub on spin 1** if any FM350 is used.
4. **Thermal:** FM350 normal operating range is only -10..+55 °C, so the heatsink plus fan is mandatory.
5. **SIM:** FM350 has dual SIM with one built-in eSIM, and marketplace units can arrive in eSIM mode. Use `AT+GTDUALSIM=0` to select the external nano-SIM.
6. **Software:** `CONFIG_MTK_T7XX=m`, a kernel with the ARM64 64-bit-access alignment fix (mainline 6.9+, or verify the backport in the NXP lf-6.x BSP), ModemManager ≥ 1.22 (1.24 reported more stable), and the `14c3` FCC-unlock script linked into `/etc/ModemManager/fcc-unlock.d`.
7. **Spin 2 (vehicle):** stay **Qualcomm-based (Quectel AG55xQ)**. No automotive-grade MediaTek M.2/LGA module was found, and FM350's temperature range is laptop-class.

## 13. Schematic rev 0.3 (2026-10-10): vendor-neutral slots for Sierra EM9291 / Telit FN990A28
Modules: pre-certified Qualcomm SDX65 M.2 3052 cards (Sierra EM9291, Telit FN990A28); FM350-GL and all Quectel/Fibocom parts excluded.
Carrier changes (details in `hardware/kicad/README.md`, sequencing in `docs/power-reset-sequencing.md`):
1. **Host-interface select (pin 20)**: per-slot open-drain FET driven by a new expander line `SLOTn_PCIE_SEL` (default PCIe). Sierra
   USB mode needs two DNP resistors fitted (pin 20 PU to 1.8 V, pin 22 VBUS_SENSE PU to the slot rail).
2. **PERST#** gated by `SLOTn_PCIE_EN` (now pull-down default), released >= 150 ms after the slot rail's PG.
3. **Pins 24/38/68 NC, pin 73 GND**, generic M.2 WWAN symbol, 3052 + 3042 standoffs.
4. **Supply**: unchanged 3.74 V / 6 A per slot; FN990 ripple limit 30 mV is the design target to measure (OI-36).
5. **Shutdown**: FCPO# low then fixed 15 s wait; no PLA_S2_N / VREG_L6B monitor yet (OI-27).
6. **Software**: `mhi_pci_generic` (17cb:0308 with EM929x / FN990 subsystem IDs), `mhi_wwan_ctrl`, `mhi_wwan_mbim` / `mhi_net`;
   USB fallback `option` + `cdc_mbim` / `qmi_wwan`. See `docs/linux-bringup.md`.
7. **GNSS/antennas**: no carrier bias or LNA; pigtails per `docs/antenna-gnss-plan.md`.
8. **Supply chain**: Nexperia parts replaced (onsemi NVMFS5C646NL, TI SN74LVC1G07/08, Diodes 2N7002); named non-PRC makers on all passives.
