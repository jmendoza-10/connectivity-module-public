# Carrier Host Interface (CHI) - spec v0.1 (issue #2)

Status: **design proposal**. Marks: [V] verified on linked source 2026-10-10, [U] unverified. Rev 0.3 carrier on `main`
(3x M.2 Key-B WWAN slots, Sierra EM9291 / Telit FN990A28, PI7C9X3G606GP switch, USB5744 hub) is the "FRDM host profile" and must
keep working.

## 1. Logical interface

| Group | Signal | Dir (host view) | Level | Required | Notes |
|---|---|---|---|---|---|
| PCIe | PETp0/n0, PERp0/n0 | out / in | PCIe Gen3 8 GT/s, AC-coupled on TX side | **yes** | upstream of PI7C (x1 today) |
| PCIe | PETp1/n1, PERp1/n1 | out / in | Gen3 | optional (x2) | needs a PI7C port mode with x2 upstream - **[U]** DS43484 port-config table |
| PCIe | REFCLK+/- | out | HCSL 100 MHz | yes | common clock. SRIS/local clock option = DNP 100 MHz generator on carrier [U] |
| PCIe | PERST# | out | 3.3 V, OD/push-pull | yes | carrier ANDs it with MCU_PERST_EN (power-MCU issue #1) |
| PCIe | CLKREQ# | bidir | 3.3 V OD | optional | ASPM L1 substates (low-power issue #3) |
| PCIe | WAKE# | in | 3.3 V OD | yes | OR of slot PEWAKE# (via switch/MCU) |
| USB | USB 3.x SS TX/RX + USB2 D+/D- | - | USB 3.2 Gen1 | yes | USB5744 upstream; fallback/debug path |
| Mgmt | I2C SCL/SDA | - | 3.3 V, 100/400 kHz | yes | MCU I2C target 0x42 (+ expanders on bench) |
| Mgmt | CARRIER_IRQ# | in | 3.3 V OD | yes | today EXP_INT_N |
| Mgmt | CARRIER_RESET# | out | 3.3 V OD | yes | today EXP_RESET_N; on MCU builds = MCU reset |
| Mgmt | UART TX/RX | - | 3.3 V | yes (spin 2) | MCU bootloader / console |
| Mgmt | HOST_RESET# / HOST_PWR_EN | in (to host) | 3.3 V OD | optional | host watchdog action from the MCU |
| Sideband | CARRIER_PRESENT# | in | GND on carrier | yes | |
| Sideband | 1PPS | in or out | 3.3 V | optional | gPTP (issue #4, OI-37) |
| Power | +12V (VBAT after carrier protection) or host-supplied +12V | - | 9-16 V [U: 24 V trucks?] | profile | see sec. 3 |
| Power | GND | - | - | yes | >= 1 GND per differential pair neighbour |

## 2. Physical options

| Option | Connector (real P/N) | Pros | Cons | Mark |
|---|---|---|---|---|
| **A. Board-to-board (recommended for spin 2)** | **Samtec ERF8-030-05.0-S-DV-K-TR** (socket, 60 pos, 0.8 mm, 5 mm, rugged latching) on the carrier + **ERM8-030-05.0-L-DV-K-TR** (terminal) on the host. 60 pins cover sec. 1 with x2 PCIe + USB3 + GND shielding | High-speed rated (Edge Rate family rated far above 8 GT/s), rugged/latching variants, automotive-qualified ("A-series") versions exist | Custom host board needed; Samtec is US (OK) | [V] samtec.com product pages; automotive variant P/N [U] |
| B. PCIe card edge (today) | x1 gold finger (BUS_PCIexpress_x1) + riser (ADT-Link, believed PRC-based [U] - **bench only, OI-26 d**) | No new host hardware | No mgmt/power on it; riser SI (OI-08) | - |
| C. Carrier as module baseboard | **SMARC 2.1.1** (4x PCIe x1 lanes, up to 2 USB3, MXM3 314-pin edge) or **COM-HPC Mini** (PICMG, PCIe Gen4/5) | Swappable hosts from many vendors (Kontron DE, congatec DE, Advantech TW, SECO IT) | Carrier becomes a full baseboard; MXM3 sockets mostly from Aces (TW) [U] | [U] spec summaries |
| D. M.2 Key-M "host side" adapter | M.2 Key-M edge -> carrier | Works with any dev board with an M.2 Key-M | x1-x4 PCIe only; no USB/mgmt | - |

Recommendation: keep **B** for the FRDM bench; define **A** as the spin-2 CHI with the 60-pin pinout above; reserve C as a hedge.

## 3. Power and sequencing contract

- Carrier self-powered from vehicle 12 V (current design, LM74800-Q1 front end) is the default. Host-powered profile is optional (A: 12 V on 4 connector pins at 0.5-1 A each [U: Samtec ERx8 per-pin current rating]).
- Contract: the carrier (MCU) powers configured slots, waits PERST#-ready (>= 150 ms after PG + card boot), then releases switch PERST_L. Host PERST# is ANDed, so either side can hold the tree in reset. Host must tolerate endpoints appearing after boot (rescan or `pci=realloc`/hot-plug windows, OI-12).
- Carrier never back-drives host I/O when unpowered: all mgmt lines OD with pull-ups on the host side.

## 4. Host candidates

| Host | PCIe (per vendor) | Ethernet / vehicle I/O | Linux MHI status | Fit | Mark |
|---|---|---|---|---|---|
| **NXP i.MX 95** (FRDM-IMX95 today) | **2x PCIe Gen3 x1** controllers | 10GbE + 2x GbE (SoC), CAN-FD | mainline/NXP BSP; `mhi_pci_generic` entries to check (OI-10) | Baseline, bench | [V] NXP AN14760 |
| **NXP S32G274A / S32G3** | 2 SerDes x 2 lanes, **PCIe Gen3** (x1/x2) or SGMII per lane; RDB3 routes SerDes1_L0 to an M.2 slot as x1 | CAN-FD x many, LLCE, PFE Ethernet; pairs with SJA1110 | NXP BSP (Linux 6.x) [U: MHI on S32G] | **Best automotive fit** (spin 2) | [V] S32G2 DS / S32G-VNP-RDB fact sheet / microsys manual |
| NXP **LS1028A** | 2x PCIe Gen3 controllers | integrated TSN switch, 4x CAN-FD? [U] | mainline | Industrial router; TSN | [U] carry from draft |
| Qualcomm **IPQ9574** | 4x PCIe Gen3 (2x x1, 2x x2) | 10G Ethernet, Wi-Fi 7 | mainline PCIe since 2024; Qualcomm host + SDX modems common | Router/FWA | [U] LWN patch series |
| Marvell OCTEON TX2 CN9130 | PCIe 3.0 one x4 + two x1 | router-class Ethernet | mainline | Gateway | [U] product brief |

MediaTek note: MediaTek hosts (e.g. Dimensity Auto / MT2739 class) integrate their own modem; not a fit for a 3x M.2 carrier
unless used as host-only [U].

## 5. Software contract (host side)

Kernel: `mhi_pci_generic` with EM929x (18d7:0301) and FN990 (1c5d:2010) entries, `mhi_wwan_ctrl`, `mhi_wwan_mbim`, `mhi_net`;
USB fallback `option`, `cdc_mbim`, `qmi_wwan`; PCIe switch with hot-plug or reserved windows; `carrierctl` (I2C) or a daemon
speaking the MCU register map (power-mcu.md sec. 2.1). ModemManager >= 1.22.

## 6. Schematic impact (not done)

New CHI connector footprint (ERF8 60-pos) in parallel with the x1 gold finger (DNP per build), x2 upstream needs a PI7C port-mode
strap change (verify), 1PPS and UART routing, host-power option pins.
