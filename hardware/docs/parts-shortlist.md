# Key Parts Shortlist (rev 0.4, 2026-10-10)

**rev 0.4 (2026-10-10): hard requirement - no chips/modules from Chinese-headquartered or Chinese-owned companies.** All Quectel (Shanghai) and Fibocom (Shenzhen) rows below are marked EXCLUDED and kept only for traceability. Replacements, the vendor HQ/ownership check and the BOM audit are in [rev 0.4 at the bottom](#rev-04-no-chinese-company-chipsmodules-2026-10-10).

rev 0.2: added the PCIe switch / triple-modem / spin-1 parts (new tables at the bottom). The ZED-F9K is marked superseded. Prices are in `bom-estimate.md`.

Eval-board names marked "confirm" were not individually verified. Every part number was checked on vendor pages.

Legend, **KiCad std lib** = present in the KiCad 9.0.2 stock libraries installed on the box (checked by grep):
- Y = symbol + footprint available
- ~ = a pin-compatible or sibling part exists, or only the generic package footprint exists
- N = need a vendor/3rd-party model (SnapEDA / Ultra Librarian / SamacSys) or a hand-made library

| Function | Manufacturer | Part number | Host interface | Grade | Eval board / reference design | KiCad std lib | Source |
|---|---|---|---|---|---|---|---|
| Application processor | NXP | **MIMX9596AVZXNAC** (i.MX 95, 19x19, auto, 6x A55) | n/a (host) | Automotive (IMX95AEC) | FRDM-i.MX95 (PF09+PF53), i.MX 95 EVK | N | [product](https://www.nxp.com/products/i.MX95), [part](https://www.nxp.com/part/MIMX9596AVZXNAC), [auto DS](https://www.nxp.com/docs/en/data-sheet/IMX95AEC.pdf) |
| Alt. processor (low cost) | NXP | i.MX 8DXL, e.g. MIMX8DL1AVNFZAB | n/a | AEC-Q100 Gr2 | MCIMX8DXL-EVK | N | [product](https://www.nxp.com/products/iMX8XLite) |
| Rejected: no PCIe | NXP | i.MX 93 | n/a | AEC-Q100 Gr3 | MCIMX93AUTO-EVK | N | [product](https://www.nxp.com/products/i.MX93) |
| Rejected: not auto, 2 CAN, 1 PCIe | NXP | i.MX 8M Plus (MIMX8ML8…) | n/a | Industrial | EVK | N | [product](https://www.nxp.com/products/i.MX8MPLUS) |
| SoM option (spin 1) | Compulab / Toradex / Variscite | MCM-iMX95 / Verdin iMX95 / DART-MX95 | n/a | Industrial -40..85 °C | Vendor carrier boards | N | [Compulab](https://www.compulab.com/products/computer-on-modules/mcm-imx95-nxp-i-mx-95-som-smd-system-on-module/), [Toradex](https://www.toradex.com/computer-on-modules/verdin-arm-family/nxp-imx95), [Variscite](https://variscite.com/system-on-module-som/i-mx-9/i-mx-95/dart-mx95/) |
| PMIC | NXP | **PF09** (9-ch) + **PF53** (core, 8/12/15 A) | I2C | Automotive (ASIL D for PF53) | Used on FRDM-i.MX95 | N | [PF09 DS](https://www.nxp.com/docs/en/data-sheet/PF09.pdf), [PF53](https://www.nxp.com/products/PF53) |
| Ethernet switch | NXP | **SJA1110A** (6x int. 100BASE-T1, 4x SGMII, 2x 2.5G) | SGMII/2500BASE-X uplink, SPI mgmt | AEC-Q100, ASIL B, LFBGA256 | SJA1110-MGS-EVM, SJA1110 example board; mainline Linux DSA driver | N | [product](https://www.nxp.com/products/SJA1110), [Linux DSA doc](https://docs.kernel.org/networking/dsa/sja1105.html) |
| Alt. multi-gig switch | Microchip | LAN9692 (66G, 10x 10G SerDes, A53) | RGMII/SGMII/USXGMII, PCIe | AEC-Q100 | EV09P11A / EVB-LAN9692-LM (7x LAN8870 T1) | N | [product](https://www.microchip.com/en-us/product/lan9692), [brief](https://ww1.microchip.com/downloads/aemDocuments/documents/UNG/ProductDocuments/ProductBrief/LAN9691-LAN9692-LAN9693-Product-Brief-00004861.pdf) |
| 1000BASE-T1 PHY | NXP | **TJA1120B** (SGMII), TJA1120A (RGMII); HVQFN36 | SGMII / RGMII | AEC-Q100 Gr1, ASIL B | TJA11xx-SDBS / SDBR | ~ (generic QFN-36 6x6 fp) | [product](https://www.nxp.com/products/TJA1120) |
| 100BASE-T1 PHY (pin-compat.) | NXP | TJA1103B (SGMII, e.g. TJA1103BHN/0Z) / TJA1103A (RGMII) | SGMII / RGMII | Automotive, ASIL B | TJA11xx-SDB | ~ | [DS](https://www.nxp.com/docs/en/data-sheet/TJA1103.pdf), [part](https://www.nxp.com/part/TJA1103BHN) |
| 1000BASE-T1 2nd source | TI | DP83TG720S-Q1 (pin-compat w/ DP83TC812S-Q1) | RGMII / SGMII | AEC-Q100 | TI EVM (name to confirm on product page) | ~ (TI RHA/RHH VQFN-36 fp present) | [product](https://www.ti.com/product/DP83TG720S-Q1), [DP83TC812S-Q1](https://www.ti.com/product/DP83TC812S-Q1) |
| 1000BASE-T PHY (sat terminal WAN) | Microchip | **KSZ9131RNXV** (Gr2) / KSZ9131RNXU (Gr3) | RGMII | AEC-Q100 | Microchip EVB (confirm on product page) | N | [product](https://www.microchip.com/en-us/product/KSZ9131) |
| **EXCLUDED (rev 0.4, Chinese HQ)** 5G modem (production) | Quectel | **AG55xQ** (AG551Q / AG552Q; AG550Q / AG553Q add C-V2X), LGA 54.5x53 mm, SA515M | PCIe 3.0, USB 3.1, RGMII | Automotive (IATF 16949, AEC-Q100 chipset), -40..85 °C | Quectel EVB (via sales) | N | [product](https://www.quectel.com/product/5g-c-v2x-ag55xq-automotive-module/), [spec](https://www.quectel.com/content/uploads/2024/03/Quectel_AG55xQ_Series_Automotive_Module_Specification_V1.7-1.pdf) |
| **EXCLUDED (rev 0.4, Chinese HQ)** 5G modem (prototype) | Quectel | **RM520N-GL** (M.2 Key B, 30x52 mm) | PCIe Gen4 x1 / USB 3.1 | Industrial | 5G M.2 EVB, many USB/PCIe adapters | ~ (Bus_M.2_Socket_B symbol; connector fp not in lib) | [product](https://www.quectel.com/product/5g-rm520n-series/), [spec](https://www.quectel.com/content/uploads/2024/03/Quectel_RM520N_Series_5G_Module_Specification_V1.4.pdf?wpId=127081) |
| **EXCLUDED (rev 0.4, Chinese HQ)** NTN satellite modem (opt.) | Quectel | BG95-S5 (Rel-17 IoT-NTN n256/n23/n255 + LTE-M/NB-IoT + GNSS, Skylo-certified) | UART / USB2 | Industrial | Quectel EVB | N | [product](https://www.quectel.com/product/bg95-s5-satellite-communication-module/) |
| NTN alt. | u-blox | SARA-S528NM10 (Rel-17 IoT-NTN + M10 GNSS) | UART / USB2 | Industrial | EVK | N | [summary](https://content.u-blox.com/sites/default/files/documents/SARA-S528NM10_ProductSummary_UBXDOC-686885345-2111.pdf) |
| Wi-Fi 6 + BT 5.4 | u-blox | **JODY-W5** series (NXP AW611); M2-JODY-W5 for prototyping | SDIO 3.0 + UART (+PCM) | Automotive | EVK / M.2 Key E card | N | [product](https://www.u-blox.com/en/product/jody-w5-series), [DS](https://content.u-blox.com/sites/default/files/documents/JODY-W5_DataSheet_UBX-23002865.pdf), [AW611](https://www.nxp.com/products/wireless-connectivity/wi-fi-plus-bluetooth-plus-802-15-4/2-4-5-ghz-dual-band-1x1-wi-fi-6-802-11ax-plus-bluetooth-5-4-automotive-solution:AW611) |
| GNSS | u-blox | ~~ZED-F9K~~ **superseded:** u-blox product URL now redirects to **ZED-X20K** (X20 all-band automotive DR); SparkFun lists its F9K breakout as retired | UART x2, 1PPS | Automotive | u-blox EVK (confirm) | ~ (ZED-F9P symbol in RF_GPS; verify pinout) | [product](https://www.u-blox.com/en/product/zed-f9k-module) |
| GNSS (cost-down) | u-blox | NEO-M9V (UDR/ADR, single-band) | UART/I2C/SPI/USB | Professional, -40..85 °C | u-blox EVK (confirm) | ~ (NEO-M9N symbol in RF_GPS) | [product](https://www.u-blox.com/en/product/neo-m9v-module) |
| CAN-FD transceiver | NXP | **TJA1463** (CAN SIC, 8 Mbit/s, sleep + INH; SO14/HVSON14) | TXD/RXD to FlexCAN | AEC-Q100 | NXP eval board (confirm) | ~ (pin-compat. TJA1043T/TK symbols in Interface_CAN_LIN) | [product](https://www.nxp.com/products/TJA1463), [DS](https://www.nxp.com/docs/en/data-sheet/TJA1463.pdf) |
| Reverse / load-dump protection | TI | **LM74800-Q1** (LM7480-Q1 family) ideal-diode controller | n/a | AEC-Q100 | LM74800EVM-CS | N | [product](https://www.ti.com/product/LM7480-Q1), [EVM UG](https://www.ti.com/lit/ug/slvubu4/slvubu4.pdf) |

## Not yet selected (need a decision or quote)
- 40 V automotive buck controllers for 5V/3V8 (TI LMQ6xxx-Q1 / LM5143-Q1 class, ADI LT8xxx). Pick after the power budget is fixed.
- LPDDR4X/LPDDR5 x32 and eMMC (pick from NXP's i.MX 95 validated-memory list, automotive grade).
- RF connectors (Rosenberger HFM / FAKRA), H-MTD / MATEnet headers, main harness connector, T1 common-mode chokes (must be OPEN Alliance qualified).
- Secure element / TPM (optional).

## Notes on reference designs
- NXP **i.MX 95 EVK** and **FRDM-i.MX95** provide the processor + PF09/PF53 + LPDDR reference schematics/layout.
- NXP's **SJA1110-MGS-EVM** shows SJA1110 + TJA1121 (1000BASE-T1) + TJA1104 (100BASE-T1) + VR5510 power. It's the closest Ethernet reference.
- The Microchip **EVB-LAN9692-LM** user guide is a full reference if going multi-gig.


## Added in rev 0.2: triple-modem WWAN and spin-1 bench parts

| Function | Manufacturer | Part number | Interface | Grade | Eval / reference | KiCad std lib | Spin | Source |
|---|---|---|---|---|---|---|---|---|
| **PCIe Gen3 packet switch (chosen)** | Diodes | **PI7C9X3G606GP** (orderable PI7C9X3G606GPBFCAEX); automotive **PI7C9X3G606GPQ** | 6 lanes / 6 ports, x1-x2 upstream, up to 5 downstream; integrated refclk buffer; 2.5 W typ; FCA144 10x10 BGA | GP: industrial -40..85 °C. GPQ: **AEC-Q100 Gr3**, PPAP | Ask Diodes for EVB/ref schematic | N | 1 (GP), 2 (GPQ) | [GP](https://www.diodes.com/part/view/PI7C9X3G606GP), [GPQ](https://www.diodes.com/part/view/PI7C9X3G606GPQ), [auto family brief](https://www.diodes.com/assets/Databriefs/PI7C9X3G606GPQ-3G808GPQ-3G816GPQ-3G1632GPQ-Product-Brief.pdf) |
| PCIe switch alt. (low cost, QFN) | ASMedia | ASM2806 | Gen3, x1/x2 up, 4x x1 down, QFN88 10x10 | Commercial (no auto) | Open hobby design: github.com/will127534/PCIe3_Hub | N | 1 (fallback) | [ASMedia](https://www.asmedia.com.tw/product/012Yq70sX2zI9xN5/7c5YQ79xz8urEGr1.html) |
| PCIe switch alt. (auto Gen4) | Microchip | Switchtec PCI1003 (PCI1003-V/5CWVAO) | Gen4 16 lanes, 2x x2 DFP, 353-ball 16x16 | **AEC-Q100 Gr2**, ASIL-B ready | ChipLink tools | N | overkill | [product](https://www.microchip.com/en-us/product/PCI1003), [brief](https://ww1.microchip.com/downloads/aemDocuments/documents/UNG/ProductDocuments/ProductBrief/PCI1001-3-4-5-Product-Brief-DS00005055.pdf) |
| Spin-1 host | NXP | **FRDM-IMX95** | 15x15 i.MX 95, 8 GB LPDDR4X, M.2 Key-M (PCIe Gen3 x1), 2x GbE, 2x CAN, USB3-C, IW612 M.2 | dev board | Design files on NXP site | n/a | 1 | [NXP](https://www.nxp.com/design/design-center/development-boards-and-designs/FRDM-IMX95) |
| Spin-2 SoM | Compulab | **MCM-iMX95** (eval kit EVAL-MCM-iMX95) | 2x PCIe Gen3 x1, 10GbE (XFI / SGMII 2.5G & 1G / USXGMII), 2x RGMII, 5x CAN, USB3 | -40..85 °C | SB-MCMIMX95 carrier | N | 2 | [reference guide](https://www.compulab.com/wp-content/uploads/2025/09/mcm-imx95_reference-guide_2026-08-13.pdf), [kit](https://www.compulab.com/products/som-evaluation-kits/mcm-imx95-evaluation-kit/) |
| Spin-2 SoM alt. | Toradex | SMARC iMX95 | 2x PCIe Gen3 x1, SERDES SGMII/USXGMII | -40..85 °C (IT) | Toradex carriers | N | 2 | [datasheet](https://docs.toradex.com/116802-smarc_imx95_datasheet.pdf) |
| Not suitable | Toradex | Verdin iMX95 | **1x PCIe, no 10GbE** (15x15) | IT | | | n/a | [datasheet](https://docs.toradex.com/200007-verdin_imx95_datasheet.pdf) |
| **EXCLUDED (rev 0.4, Chinese HQ)** 5G modem (spin 1) | Quectel | **RM520N-GL** | PCIe Gen4 x1 (runs Gen3) / USB 3.1; 4 antennas, GNSS L1 on ANT3; VCC 3.135-4.4 V (3.7 V nom), ≥3 A cont / 4 A peak; dual SIM (DSSS); Linux mhi_pci_generic | Industrial | Quectel EVB | ~ (Bus_M.2_Socket_B symbol) | 1 | [HW design V1.3](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6382/Quectel_RM520N_Series_Hardware_Design_V1.3.pdf), [mainline MHI](https://github.com/torvalds/linux/blob/master/drivers/bus/mhi/host/pci_generic.c) |
| **EXCLUDED (rev 0.4, Chinese HQ)** LTE Cat 6 modem (budget) | Quectel | **EM060K-GL** | M.2 Key-B 30x42, 300/50 Mb/s, VCC 3.135-4.4 V | Industrial | Quectel EVB | ~ | 1 | [product](https://www.quectel.com/product/lte-a-em060k-series/) |
| **EXCLUDED (rev 0.4, Chinese HQ)** 5G RedCap (watch) | Quectel | RG255C-GL M.2 | 223/123 Mb/s, USB2 / PCIe 2.0 | Industrial | | ~ | n/a (30-wk lead) | [product](https://www.quectel.com/product/5g-redcap-rg255c-gl-m2/) |
| USB3 hub (fallback) | Microchip | USB5744 | 4-port USB 3.2 Gen1, 56-VQFN 7x7 | Industrial (**not** AEC-Q100) | Microchip EVB (confirm) | N | 1 (opt.) | [product](https://www.microchip.com/en-us/product/usb5744) |
| Per-modem 3.7 V buck | TI | LMQ61460-Q1 (or in-stock AEC-Q100 equivalent) | 3-36 V in, 6 A sync buck | AEC-Q100 | TI EVM | N | 1, 2 | [product](https://www.ti.com/product/LMQ61460-Q1) (Digi-Key backorder, ETA Mar 2027) |
| M.2 → PCIe x1 cable (**bench fixture; ADT-Link is Shenzhen-based - see rev 0.4 audit**) | ADT-Link | M41 series | M.2 Key-M → PCIe x1 slot, Gen4-rated | n/a | | n/a | 1 | [ADT-Link](https://www.adt.link/product/M41V4-Shop.html) |

## Added rev 0.3: MediaTek-based M.2 modem evaluation (2026-10-09)

| Module | Vendor / chipset | Form factor & host IF | Power | US carriers / certs | Linux | Price & availability | Verdict |
|---|---|---|---|---|---|---|---|
| **EXCLUDED (rev 0.4, Chinese HQ)** **FM350-GL** | Fibocom / **MediaTek T700** | M.2 **3052 Key-B**, **PCIe Gen3 x1** is the primary data path. USB 2.0 is "debug", USB 3.1 Gen1 is "reserved", but the module enumerates as USB (ttyUSB + RNDIS/NCM) when PCIe isn't brought up (community-proven on BPI-R4). 4x MHF4, 4x4 MIMO, dual SIM (one built-in eSIM) | 3.135-4.4 V, **typ 3.3 V**; **peak > 3.5 A** at max 5G throughput; ripple < 300 mV | Listed carrier certs include AT&T, Verizon, T-Mobile (reseller/T-Mobile datasheet). PTCRB on record (2023-09-28). Normal op **-10..+55 °C** (ext. -30..+75) | Mainline **`mtk_t7xx`** since **5.19** (PCI 14c3:4d75), MBIM + AT ports. **ARM64 alignment-fault fix** landed Mar 2024 ("Split 64bit accesses", in 6.9; check that your NXP BSP kernel has it). ModemManager supports it, but OEM pulls are **FCC-locked** and need the `14c3` FCC-unlock script linked | Amazon US ~$64-88 (marketplace, mostly laptop pulls), Amazon UK £55.99, cartft €189 (new, in stock) | **Good secondary modem**: cheap 5G 4x4, mainline driver |
| **EXCLUDED (rev 0.4, Chinese HQ)** FM350-GL-16 | Fibocom / MediaTek T700 | Same M.2 3052 Key-B | same | **LTE-only** variant. FCC ID ZMOFM350GL16. Verizon ODI-approved. PTCRB 2023-10-16 | same t7xx | Amazon US ~$34 | The only MediaTek-based **LTE** M.2 option found. Cheap LTE filler |
| **EXCLUDED (rev 0.4, Chinese HQ)** FG360 / FG370 / FG190W | Fibocom / MediaTek T750 / T830 | **LGA**, not M.2 (FWA/CPE modules with USXGMII) | 3.3-4.4 V, typ 3.8 V | n/a | n/a | n/a | **Not M.2**. Not usable in our slot |
| **EXCLUDED (rev 0.4, Chinese HQ)** RG620T | Quectel / MediaTek T830 | FWA module (USXGMII, PCIe 4.0, USB 3.2). M.2 form factor not confirmed | n/a | FCC/IC/CE/RCM | n/a | n/a | Not a drop-in M.2 card |
| **EXCLUDED (rev 0.4, Chinese HQ)** RM551E-GL | Quectel / **Qualcomm SDX75** (not MediaTek) | M.2 3052, PCIe 4.0 / USB 3.1 | 3.135-4.4 V, typ 3.7 V | ES stage per community wiki | MHI | samples | Not MediaTek. Ignore for now |
| **EXCLUDED (rev 0.4, Chinese HQ)** FM190W-GL | Fibocom / **Qualcomm SDX75** | M.2 3052 | n/a | n/a | n/a | n/a | Not MediaTek |
| MediaTek T300 RedCap | MediaTek | No M.2 Key-B card found | n/a | n/a | n/a | n/a | n/a |

Sources:
- [FM350 HW guide v1.0.8](https://tylk.cc/file_dowmload/FM350GL/fibocom_fm350gl_hardware_guide_generic_v1.0.8.pdf)
- [FM350 HW guide (FCC)](https://fccid.io/m/3390c2be46a85ef8d08a7ac318ad7fcef876b9f96a1a4c7dd80a55e24b2de36c.pdf)
- [T-Mobile FM350 datasheet](https://www.t-mobile.com/content/dam/tfb/pdf/tfb-iot/FIBOCOM_FM350-GL_datasheet_V1.2.pdf)
- [cartft listing](https://www.cartft.com/en/catalog/il/3532)
- [Verizon ODI FM350-GL-16](https://opendevelopment.verizonwireless.com/design-and-build/approved-modules/module/25651)
- [FCC ID ZMOFM350GL16](https://fccid.io/ZMOFM350GL16)
- [device.report certs](https://device.report/fibocom-wireless/fm350-gl)
- [kernel t7xx doc](https://docs.kernel.org/6.16/networking/device_drivers/wwan/t7xx.html)
- [LKDDb MTK_T7XX](https://cateee.net/lkddb/web-lkddb/MTK_T7XX.html)
- [ARM64 alignment fix](https://github.com/kdave/btrfs-devel/commit/7d5a7dd5a35876f0ecc286f3602a88887a788217)
- [ModemManager FCC unlock](https://modemmanager.org/docs/modemmanager/fcc-unlock/)
- [OpenWrt FM350 thread](https://forum.openwrt.org/t/fibocom-fm350-gl-support/142682/425)
- [BPI-R4 FM350 thread](https://forum.banana-pi.org/t/fm350-gl-and-be14-finally-works-on-bpi-r4/19170)
- [Amazon US FM350](https://www.amazon.com/Yunseity-4-67Gbps-Downlink-1-25Gbps-Supported/dp/B0CFPRSPS7)
- [Amazon US FM350-GL-16](https://www.amazon.com/Network-FM350-1Gbps-Support-Module/dp/B0DDJSBL8C)
- [Amazon UK](https://www.amazon.co.uk/Fibocom-FM350-GL-Network-module-Desktop/dp/B0CXHYVKVN)
- [Fibocom FG370](https://www.fibocom.com/en/SeriesProduct/info_itemid_81.html)
- [Quectel RG620T](https://www.quectel.com/news-and-pr/mediatek-t830-5g-module-global-certifications-fwa/)
- [RM551E spec](https://muziot.com/wp-content/uploads/2026/09/rm551e_spec.pdf)

### MediaTek vs Qualcomm for bonding

(rev 0.4: the Quectel/Fibocom modules in this comparison are excluded; the chipset-level points - MHI/QMI vs t7xx/MBIM - still apply to the replacements in rev 0.4.)

| Aspect | Qualcomm (RM520N-GL, EM060K) | MediaTek (FM350-GL) |
|---|---|---|
| Kernel path | `mhi_pci_generic` + `mhi_net` / `mhi_wwan_ctrl` (PCIe); `qmi_wwan` / `cdc_mbim` / `option` (USB) | `mtk_t7xx` (PCIe, mainline). USB mode uses `rndis_host` / `cdc_ncm` + `option` |
| Control protocol | **QMI + MBIM + AT**, so `qmicli` gives rich per-modem radio telemetry | **MBIM + AT only** (no QMI) |
| Radio telemetry / control for the bonding scheduler | Mature Quectel AT set (serving-cell/neighbour info, band lock, CA info) + QMI NAS signal info | Fibocom `AT+GT*` set; documented less widely |
| Firmware update on Linux | Quectel QFirehose (Linux tool) | Mostly via **Windows SP Flash Tool / Microsoft Update images**. t7xx devlink/fastboot flashing exists in the kernel, but community tooling is immature |
| Gotchas | Lenovo-branded pulls may carry OEM firmware | OEM pulls **FCC-locked** (ModemManager `14c3` unlock script needed); may ship in **eSIM mode** (`AT+GTDUALSIM=0`); ARM64 kernel-panic history on PCIe (fixed in ≥ 6.9; reports of occasional stalls) |
| Multiple identical units behind a PCIe switch | MHI multi-device is common in multi-modem routers | **No public report found of 3x t7xx behind a PCIe switch**. Each unit does appear as its own `wwanN`. Treat as an untested risk |
| Temperature | -30..+75 °C (ext. -40..+85 °C) | -10..+55 °C normal (ext. -30..+75 °C), laptop-class |
| Automotive path | ~~Quectel AG55xQ~~ (excluded rev 0.4) | ~~none found~~ superseded: **WNC UMC-STD35FFx (MediaTek MT2735, automotive LGA, eCall/NG eCall)** - see rev 0.4 |
| Bonding upside | | **Chipset diversity:** a Qualcomm + MediaTek mix means baseband firmware bugs and stalls are less likely to hit all links at once |

## rev 0.4: no Chinese-company chips/modules (2026-10-10)

**Supply-chain rule (2026-10-10):** no chips or modules from companies headquartered in, or controlled from, the PRC. Chipset vendors MediaTek (Taiwan) and Qualcomm (US) are acceptable; MediaTek is preferred. Quectel and Fibocom are out, including the FM350-GL chosen for spin 1 and the AG56xN / AR588MA / AG55xQ eCall candidates. This rule is about **company HQ/ownership**. Country of *manufacture* (many Taiwanese/US parts are built in PRC plants) is a separate question I have not ruled on; it is flagged where known.

**NDAA Section 889, briefly:** Sec. 889 bars US federal agencies (and, under 889(a)(1)(B), federal contractors) from procuring or using "covered telecommunications equipment" from Huawei, ZTE, Hytera, Hikvision, Dahua and their subsidiaries/affiliates. **Quectel and Fibocom are not named in Sec. 889**, and as of this check they are not on the FCC Covered List either (Quectel's April 2026 FCC filings attest to that; confirm at https://www.fcc.gov/supplychain/coveredlist). The exclusion here is therefore a **personal policy choice**, the same one many OEMs and US government-adjacent buyers already apply to Chinese cellular modules after congressional and think-tank pressure (e.g. FDD memo, Apr 2026: https://www.fdd.org/wp-content/uploads/2026/04/fdd-memo-the-risks-of-chinese-produced-cellular-modules.pdf). I will not describe it as an 889 requirement.

### Vendor HQ / ownership check

| Vendor | HQ / owner (as checked 2026-10-10) | OK? | Source |
|---|---|---|---|
| Quectel | Shanghai, PRC | **No** | (company) |
| Fibocom | Shenzhen, PRC (FM350 press release datelined Shenzhen) | **No** | https://www.fibocom.com/en/newscenter/fibocom-launches-fm350.html?id=2325 |
| Telit Cinterion | Irvine, CA (moved from London); private, controlled by DBAY Advisors, Thales holds ~25% after selling its Cinterion IoT business to Telit (closed Dec 2022 / Jan 2023). **Note:** Telit's *automotive* unit was sold to TUS International (PRC) in 2019, so current Telit Cinterion has no automotive eCall line; the TUS-owned successor is excluded | Yes | https://www.telit.com/press/telit-and-thales-announce-the-creation-of-the-leading-western-iot-solutions-provider-telit-cinterion/, https://www.ocbj.com/oc-homepage/telit-ceo-scores-big-iot-acquisition-with-thales-unit/, https://en.globes.co.il/en/article-tus-completes-acquisition-of-telits-automotive-division-1001276606 |
| Thales / Gemalto (Cinterion) | Cellular IoT modules now part of Telit Cinterion (above) | Yes (via Telit) | same |
| Sierra Wireless | Acquired by **Semtech** (Camarillo, CA, US) in Jan 2023; EM-series M.2 cards still sold under the Sierra brand | Yes | https://www.sierrawireless.com/iot-modules/5g-modules/ |
| Sierra AirPrime **AR** automotive series | Divested 2020 to **Rolling Wireless** (below), not Semtech | see Rolling | https://www.sec.gov/Archives/edgar/data/1111863/000134100420000313/ex99-1.htm |
| **Rolling Wireless** | Luxembourg. Created 2020 from Sierra's automotive business by a **Fibocom-led consortium**; Fibocom held 100% by 2022; **Fibocom sold 100% on 26 Jul 2024** to a fund "predominantly from Europe and North America" (MarketScreener names Europa Solare S.R.L.), which also bought assets of the Shenzhen subsidiary | **Open decision**: now non-Chinese-owned on paper, but Chinese-owned until 2024 and with a Shenzhen engineering history. My current leaning: allowed only as fallback, after an ownership/R&D-location statement from Rolling | https://www.rollingwireless.com/en/news/new-owner, https://in.marketscreener.com/quote/stock/FIBOCOM-WIRELESS-INC-37560500/news/Europa-Solare-S-R-L-completed-the-acquisition-of-Rolling-Wireless-S-ar-l-and-Certain-Assets-of-Ro-47494503/ |
| u-blox | Thalwil, Switzerland. **Announced phase-out of its whole cellular business (Jan 2025)**: no new products; existing products shipped while demand lasts | OK by HQ, **not for new designs** | https://content.u-blox.com/sites/default/files/documents/u-blox-announces-strategic-decision.pdf |
| WNC (Wistron NeWeb) | Hsinchu Science Park, Taiwan (Wistron group) | Yes | https://www.wnc.com.tw/en/automotive/cellular-module/5g-4g-3g-2g-lga-module |
| Advantech (AIW modules) | Taipei, Taiwan; AIW-357 is stated "made in Taiwan, catering to customers sensitive to products made in China" | Yes | https://www.advantech.com/en-us/resources/news/transforming-smart-railway-applications-with-advantech-aiw-357 |
| LG Innotek | Seoul, Korea | Yes, but sells 5G automotive modules/TCUs into OEM programs, not through distribution | https://www.lginnotek.com/news/pressView.do?idx=5524&locale=en&rowSize=15 |
| Nordic Semiconductor | Trondheim, Norway | Yes | https://www.nordicsemi.com/Nordic-news/2025/12/Nordic-Semiconductor-secures-Skylo-certification-for-nRF9151-module-enabling-global-IoT-connectivity |
| Sequans | Paris, France (LTE-M/NB-IoT/NTN chips + modules) | Yes (not 5G eMBB) | (company) |
| Lantronix, Murata, Ezurio (ex-Laird Connectivity) | US, Japan, US/UK respectively | Yes; no 5G M.2 eMBB card from them was found that beats the ones below | (not individually researched) |
| MediaTek / Qualcomm (chipsets) | Hsinchu, Taiwan / San Diego, US | Yes | n/a |

### (A) Spin-1 bench modem: non-Chinese M.2 Key-B 5G cards

| Card | Vendor (HQ) / chipset | Form factor, host IF | VCC range / peak | US carrier certs | Linux driver | Price (single unit, 2026-10-10) | Verdict |
|---|---|---|---|---|---|---|---|
| **Sierra EM9291** | Sierra/Semtech (US) / **Qualcomm Snapdragon X62** (EM92 family = X62/X65) | **M.2 3052-S3 Key-B**, PCIe Gen3 x1 + USB 3.1; 2 SIM | 3.135-4.4 V (3.3 typ); **peak 3.0 A** (EM92xx PTS Rev 5, Jan 2025) | **PTCRB, AT&T (FirstNet), T-Mobile, Verizon** (Verizon ODI listing) | Mainline **`mhi_pci_generic`** ("EM929x (sdx65), use the same configuration as EM919x", 17cb:0308 sub 18d7:0301) + `mhi_wwan_mbim`/`mhi_wwan_ctrl`; QMI/MBIM; USB: `qmi_wwan`/`cdc_mbim` | **$366.97** Digi-Key (EM9291_1105285, 20-wk std lead) | **Recommended spin-1 5G modem** (certs, mainline, fits 3.7 V rail, most drop-in pin behaviour) |
| **Telit Cinterion FN990A28** | Telit Cinterion (US) / **Qualcomm Snapdragon X62** (FN990A40 = X65) | M.2 3052 Key-B, PCIe Gen3 + USB 3.1 Gen2 | 3.135-4.4 V (3.3 typ); **peak 4 A** (FN990 HW design guide) | **PTCRB, AT&T, FirstNet, T-Mobile US, VzW** (Telit page) | Mainline `mhi_pci_generic` ("telit-fn990") | **€311.39** Digi-Key IE (FN990A28H06T060100, **28-wk lead**); RS UK £277.05; Compulab kit w/ antennas $355.61 | Second source. Needs pin-20 change (below) for PCIe |
| Telit FN990B34 / FN990B40 | Telit / Qualcomm **X72** (Rel-17) | M.2 3052, PCIe Gen3 / USB 3.1 Gen2, -40..85 °C | n/a | n/a | Mainline ("telit-fn990b40", sdx72) | not priced | Future upgrade; same pinout family as FN990A |
| Sierra EM9191 | Sierra/Semtech / Qualcomm SDX55 | M.2 3042-S3-B (52 mm), PCIe Gen3 / USB 3.1 | 3.135-4.4 V; peak 2.7 A | carrier-certified | Mainline (sierra-em919x) | $461.06 Digi-Key, **Last Time Buy 11/27/2026** | **Don't use** (LTB) |
| **Advantech AIW-357 DK-G1P** | Advantech (Taiwan) / **MediaTek T700** (same chipset as FM350) | M.2 3052 Key-B; **G1P = PCIe**, G2U = USB-only SKU | **3.135-3.63 V** (3.3 typ); 2.26 A | **FCC only found; no PTCRB / AT&T / VzW / T-Mobile certification found** | Mainline **`mtk_t7xx`** (expected to bind on 14c3:4d75; **VERIFY** the AIW PCI ID) | **€393.23** (PF Electronic, PL); other distributors quote-only | **Only non-Chinese MediaTek M.2 card found.** Optional MediaTek link if budget allows. Needs 3.3 V on its slot. -30..70 °C |
| Sierra **EM7411** (LTE, budget filler) | Sierra/Semtech / Qualcomm (LTE Cat 7) | **M.2 3042-S3** Key-B, **USB 3.0/2.0 only (no PCIe)** | 3.135-4.4 V (3.7 typ) | Americas SKU (certs **VERIFY** per carrier) | `qmi_wwan` / `cdc_mbim` + `option` | **€117.47** Digi-Key IE (EM7411 Q-M2M-1104680, 20-wk lead) | Replaces the excluded EM060K-GL as the cheap LTE filler; needs the USB hub path and a 42 mm standoff |
| Telit LN920A6-WW (LTE Cat 6) | Telit / Qualcomm SDX12 | M.2 3042 | n/a | n/a | n/a | ~$73 third-party; **discontinued at Digi-Key** | Don't use |

No non-Chinese **MediaTek 5G M.2** card other than the AIW-357 was found. Foxconn (Hon Hai, Taiwan) T99W-series laptop cards are all **Qualcomm** (T99W175 = SDX55, T99W373 = SDX65, in mainline MHI). Dell DW5933e/HP DRMR-H01 MediaTek cards seen in the t7xx ID table are OEM-badged; their module maker was not established, so they are **not** recommended.

#### Pin compatibility with the rev 0.2 slot (FM350-wired) and required schematic changes

The rev 0.2 slot uses only standard PCI-SIG WWAN pins: VCC (2/4/70/72/74 on +3V7_Sn), FCPO# (6), W_DISABLE1# (8, open-drain), LED1# (10), USB2 (7/9), USB3 (29/31/35/37), SIM1 (30/32/34/36 + 66 detect), PCIe (41/43/47/49/53/55), PERST# (50, 74LVC1G08 push-pull), CLKREQ# (52), PEWAKE# (54), RESET# (67, open-drain). Pins 22/28 go only to test points (FM350 UART). CONFIG_0..3, 20, 24, 26, 38, 40-48, 56-68 (others) are unconnected. Comparison (sources: FN990 HW design guide Rev 3; Sierra EM92XX PTS Rev 5; AIW-357 user manual 2023-08):

| Pin | rev 0.2 net | EM9291 | FN990A28 | AIW-357 | Change needed |
|---|---|---|---|---|---|
| 2/4/70/72/74 | +3V7_Sn (3.7 V) | VCC 3.135-4.4 | VPH_PWR 3.135-4.4 | **3.135-3.63 V** | **Per-slot option: 3.3 V for AIW-357.** LM61460 FB = 1.0 V; top R204/R210/R216 = 100k, bottom R205/R211/R217 = 36.5k (3.74 V). Fit **43.2k** for 3.31 V on an AIW slot (BOM variant, not a topology change) |
| 24, 38, 68 | NC | **extra VCC pins (optional, may be NC)** | 24 TGPIO_07, 68 TGPIO_01 (1.8 V) | NC / I2S | Leave NC (connecting VCC would short Telit GPIOs) |
| 20 | NC | PCIE_DIS (internal PD, high = disable PCIe, 1.8 V max 2.1 V) | **USB_PCIE_SWITCH (internal 10k PU, high = USB-only, low = PCIe)**, sampled at power-on | I2S0_BCK (1.8 V) | **Required for Telit:** add a 2N7002 open-drain pull-down on pin 20 per slot, gate from the existing SLOTn_PCIE_EN (via R406/R506/R606 net) so "PCIe enabled" = pin 20 low before FCPO# rises. Harmless for Sierra (already PD) and AIW (pin is an I2S clock only when audio is used - **VERIFY** the module tolerates it pulled low; else DNP the FET on AIW slots) |
| 22 | TP401 (FM350 UART_TX) | **VBUS_SENSE (PD, high = USB present, 1.6-5.25 V)** | TGPIO_06 (1.8 V) | I2S | **For USB operation of Sierra cards (EM7411 especially, and EM9291 USB fallback):** add a **DNP** 10k from +3V3 to pin 22, fitted only on Sierra slots. Never fit with Telit (1.8 V GPIO). **VERIFY** EM7411 pin 22 definition in its PTS |
| 28 | TP402 | PLA_S2_N (output) | TGPIO_08 | I2S | none |
| 66 | SIM1_DETECT to CD switch (NO to GND) | SIM detect, polarity configurable | UIM1_PRESENT (1.8 V, PU) | SIM detect (1.8 V) | none in hardware; set detect polarity by AT command per vendor (**VERIFY**) |
| 40-48 | NC (FM350 symbol: I2C/NC) | UIM2 (second SIM) | UIM2 | NC | none (single SIM). Optional: route a 2nd SIM later |
| 56/58 | NC | RFFE | I2C (1.8 V, 2.2k PU) | NC | none |
| 50/52/54/67/6/8/10 | as above | standard (PERST in, CLKREQ/PEWAKE OC, RESET_N PU, FCPO PD, W_DISABLE PU, LED OC) | standard (FCPO 47k PD, SYS_RESIN_N 1.8 V PU, LED open-drain) | standard (RESET# 1.8 V) | none. The rev 0.2 open-drain RESET#/W_DISABLE# and 47k FCPO# pull-down suit all three |
| 73 | NC | n/a | n/a | VIO_CFG: NC = sideband 1.8 V, tolerant of 3.3 V | none |
| Mechanics | H401/H501/H601 at 52 mm | 3052 | 3052 | 3052 | **Add a second standoff (42 mm position) per slot** for 3042 cards (EM7411, EM9191) |
| Firmware/power-up timing | FM350 numbers in power-reset-sequencing.md | EM92 PTS sec. "Power On/Off Timing" | FN990 HDG | AIW manual | Re-derive t_on / PERST# / RESET# timings per module; carrierctl constants (OI-15) |

Also: the schematic title block, slot symbols (pin names UART_TX/RX etc. are FM350-specific) and the generated docs still say "FM350-GL". Rename to generic M.2 WWAN pin names in rev 0.3 (no netlist change except the items above).

### (B) Spin-2 eCall modem: automotive, non-Chinese, with eCall claims

| Module | Vendor (HQ) / chipset | Grade, temp | eCall claim (source) | Audio | Form factor / IF | Availability | Verdict |
|---|---|---|---|---|---|---|---|
| **WNC UMC-STD35FFx** (FCC model UMC-STD35FFN, FCC ID NKR-UMCSTD35FFN, granted 2026) | **WNC (Taiwan) / MediaTek MT2735** (MT2735V/MZA) + MT6635 GNSS RFIC | "Automotive 5G-NR NAD"; reliability per **AEC-Q104** test groups A/B/C/E/H; **-40..85 °C ambient, eCall to 95 °C** | Product spec R1 (FCC filing): **3GPP CS eCall, EU CS eCall, EU IMS eCall, 3GPP IMS eCall in NG eCall, ERA-GLONASS eCall** all "Supported" | **I2S0, I2S2, PCM0** | LGA 52 x 62 x 3.46 mm (DSDA); USB 2.0/3.1, PCIe, UART, SPI, I2C, SDIO; SKUs EU / CHN / NA / RoW / LATAM | Not in distribution: **WNC automotive sales / NDA** | **Recommended spin-2 eCall modem** (MediaTek, Taiwan, explicit NG eCall + ERA-GLONASS) |
| Rolling Wireless RN93xx / RN94xx | Rolling Wireless (Luxembourg; ex-Fibocom until Jul 2024) / **Qualcomm SA522M / SA525M** | Automotive-grade, IATF 16949, **-40..95 °C, up to 105 °C for eCall** | "eCall IVS Smart Application": EU 112 eCall, private eCall, "upcoming" NG eCall (software add-on; NG eCall certification not stated) | PCM, I2S, eAVB | LGA 45 x 45 (48 x 48 with C-V2X); PCIe 3.0 x2, USB 3.1, SGMII/USXGMII | Sales/NDA; certs FCC, IC, PTCRB, RED, GCF, AT&T (others "planned") | **Qualcomm fallback; ownership still an open decision** |
| LG Innotek 5G automotive module / LG TCU | LG Innotek / LG (Korea) / Qualcomm Snapdragon Automotive 5G | Automotive | LG standalone TCU: 5G Rel-16, **NG eCall**, V2X | n/a | TCU / captive NAD | OEM programs only | Not sold as a merchant module |
| u-blox TOBY-L4 | u-blox (Switzerland) / chipset **VERIFY** | Automotive LTE | eCall support (u-blox press release) | yes | LGA | **Cellular phase-out announced Jan 2025** | Don't use for a new design |
| Sierra AirPrime AR759x / AR8 | now Rolling Wireless | Automotive LTE | legacy | yes | LGA | Rolling Wireless | Superseded by RN93xx at Rolling |
| Telit automotive (LE940 etc.) | Sold to TUS International (**PRC**) in 2019 | - | - | - | - | - | **Excluded** |
| Telit Cinterion LE910C1 | Telit Cinterion / Qualcomm | -40..85 °C, but **not** AEC/IATF automotive per results found | no eCall claim found | yes | LGA | distribution | Not eCall |

### (C) BOM audit (rev 0.2 BOM CSV + spin-1 bench items)

| Ref / item | Current part (maker) | Maker HQ / owner | Finding | Proposed substitute |
|---|---|---|---|---|
| Modems J401/J501/J601 | Fibocom FM350-GL | Shenzhen, PRC | **Excluded** | Sierra EM9291 (+ optional Advantech AIW-357, Sierra EM7411 LTE) - see (A) |
| Q101, Q102 | **Nexperia** BUK7Y4R8-60E (LFPAK56) | Nijmegen, NL, but **owned by Wingtech (PRC)**. Dutch state intervention (Oct 2025) since suspended; shares held by a court-appointed administrator, Enterprise Chamber inquiry report due Dec 2026 | **Flag: Chinese-owned** (control disputed) | **onsemi NVMFS5C646NL** (60 V, 4.7 mΩ @10 V, AEC-Q101, SO-8FL 5x6) - footprint differs from LFPAK56: **VERIFY** land pattern and LM74800 gate-drive/SOA. Alt: Infineon/TI automotive 60 V FETs |
| U302 | Nexperia 74LVC1G07GW | as above | **Flag** | **TI SN74LVC1G07DCKR** (already listed alternate; SC-70-5 same footprint) |
| U401/U501/U601 | Nexperia 74LVC1G08GW | as above | **Flag** | **TI SN74LVC1G08DCKR** (or -Q1) |
| Q401..Q807 | 2N7002-7-F / "2N7002K-Q AEC" | Diodes Inc. (Plano, TX) | OK - but pin the alternate to **Diodes 2N7002KQ-7**; generic "2N7002K" gets substituted with PRC brands at assemblers | specify MPN, no substitutes |
| U301 | Diodes PI7C9X3G606GP | Diodes Inc. (US); Pericom heritage (Taiwan) | OK | - |
| J401/J501/J601 | LOTES APCI0026-P001A M.2 socket | **Keelung, Taiwan** (TWSE 3533) - verified | OK by HQ; LOTES has PRC plants (country of origin **VERIFY** if that matters) | Alt: TE / Amphenol / Foxconn Interconnect M.2 Key-B sockets |
| J402/J502/J602 | CUI Devices NSIM-2-C | Lake Oswego, OR, US | OK by HQ (CUI sources from partners; origin **VERIFY**) | Alt: Amphenol / Molex nano-SIM |
| J101 | Molex 43650-0200 | Lisle, IL, US (Koch) | OK | - |
| J701 | Amphenol 12401610E4#2A | US | OK | - |
| J801, JP401/501/601 | 2.54 mm headers, **no MPN** | - | **Unspecified** - assemblers default to PRC generics | Specify Samtec TSW / Amphenol FCI / Würth (DE) |
| H401-H601 | M.2 standoffs, **no MPN** | - | Unspecified | Specify PEM / Würth SMT standoffs (and add 42 mm position) |
| C401..C602 | KEMET T520D227M006ATE015 | KEMET (US) owned by **Yageo (Taiwan)** | OK | - |
| C106 | Panasonic EEE-FK1V101P | Japan | OK | - |
| F101 | Littelfuse 0466007.NR | US | OK | - |
| D101, D701 | SMBJ33CA / SMAJ5.0A, **maker not specified** | - | **Unspecified** (many PRC second sources) | **Littelfuse SMBJ33CA / SMAJ5.0A** or Vishay |
| D102.., D808/809 | Lite-On LTST-C191 | Taiwan | OK | - |
| D301-D304 | Kingbright APHHS1005 | Taiwan (New Taipei) | OK by HQ | - |
| FB301.. | Murata BLM18PG221SN1D | Japan | OK | - |
| L101..L104 | Coilcraft XAL | US | OK | - |
| Y701 | Abracon ABM8 | US | OK | - |
| U101-U104, U402.., U701.., U704, U801/802, U304 | TI | US | OK | - |
| U303, U705 | Microchip | US | OK | - |
| All R and most C (**no MPN**) | generic 0201/0402/0603/1206 | - | **Unspecified** - JLCPCB "basic" parts are largely PRC brands (e.g. UNI-ROYAL, FH/Fenghua) | Pin MPNs: resistors Yageo RC/Panasonic ERJ/Vishay/KOA; MLCCs Murata GRM/GCM, TDK, Samsung EM (KR), KEMET, Yageo. Add a BOM rule "no substitution without approval" |
| Bench: M.2 Key-M → PCIe x1 cable | **ADT-Link M41** | **Shenzhen, PRC** | **Excluded** (bench fixture, not on the module - I still need to confirm whether fixtures count) | No non-PRC off-the-shelf riser identified. Option: own M.2 2280 Key-M paddle card on the same PCB order + Samtec/Amphenol PCIe-rated cable (quote needed), est. $40-90 |
| Bench: MHF4 → SMA pigtails | rfsupplier.com (origin not established) | unknown | **Flag** | I-PEX (Japan) or Amphenol RF MHF4 assemblies via Digi-Key/Mouser, est. $10-15 each |
| Bench: antennas | Taoglas TG.64.8113 | Ireland | OK | - |
| Bench: M.2→USB adapter (FM350 flashing) | Waveshare (Shenzhen) / Rework | PRC / unknown | **Drop** - only needed for FM350 Windows flashing | Not needed with Sierra/Telit (Linux tools) |
| Optional NTN | Quectel BG95-S5 | PRC | **Excluded** | **Nordic nRF9151** (Skylo-certified Dec 2025, NTN fw mfw_nrf9151-ntn_1.0.x) or Sequans-based modules. u-blox SARA-S528NM10 is in the u-blox cellular phase-out |
| Host | NXP FRDM-IMX95 | NXP (Eindhoven, NL) | OK by HQ | - |
| **PCB fab + assembly** | JLCPCB | **Shenzhen, PRC** | **Separate open question** (not a chip/module, but the boards are made and parts sourced there) | Non-PRC options: Eurocircuits (BE), Advanced Circuits / Sierra Circuits / MacroFab (US), Taiwanese fabs via a broker. Expect several hundred $ more for 6L + BGA assembly - quote needed |

## rev 0.5: NTN-capable 5G modems, 3x 5G kept (2026-10-10)

Decision (2026-10-10): keep **3x 5G modems** (the $1,500 cap no longer drives the design); the target is **NTN-enabled 5G** (3GPP Rel-17+ NR-NTN and/or NB-NTN), likely not yet in production. The no-Chinese-company rule still applies. Marks: **[V]** = verified on a primary or vendor source linked here; **[S]** = secondary source (press or trade site) only; **[U]** = unverified or inferred.

### NTN bands (3GPP FR1-NTN, TS 38.101-5 sec. 5.2.2) [S]
| Band | UL | DL | Typical operator |
|---|---|---|---|
| n255 (L-band) | 1626.5-1660.5 MHz | 1525-1559 MHz | GEO L-band (Viasat/Inmarsat, Ligado; Skylo uses these) [U for operator mapping] |
| n256 (S-band) | 1980-2010 MHz | 2170-2200 MHz | EU 2 GHz MSS (EchoStar/Viasat) [U] |
| n254 (Rel-18) | 1610-1626.5 MHz | 2483.5-2500 MHz | Globalstar band [U] |
Source: https://itecspec.com/3gpp/38.101-5/s/5.2.2. Rel-18 adds 30 MHz channels on n255/n256 [S].

### Chipsets with integrated 5G NTN: status

| Chipset | NTN mode | Status (date) | Mark | Source |
|---|---|---|---|---|
| **MediaTek MT2739 "Dimensity Auto Connect"** | **NB-NTN + NR-NTN**, Rel-17/18, AEC-Q100 Grade 2 | Announced 23 Apr 2025 "ready for OEM integration"; NR-NTN demo at MWC 2026 (Mar 2026); Hirain TBox-P on MT2739 said to have "fully entered mass production" (May 2026) | [V] announce/AEC; [S] mass production | https://www.mediatek.com/press-room/mediatek-unveils-flagship-dimensity-auto-platforms-defining-the-future-of-the-intelligent-cockpit, https://www.mediatek.com/tek-talk-blogs/mediatek-at-mwc-2026-ai-automotive, https://en.hirain.com/news_detail/c-_detailId%3D2054763225336401920.html |
| MediaTek **M90** modem (in **T930** FWA platform) | IoT-NTN + NR-NTN integrated in the modem | Announced 2025; T930 shipping status not established | [V] NTN claim; [U] status | https://www.mediatek.com/technology/5g/m90-modem, https://www.mediatek.com/products/5g-broadband/mediatek-t930 |
| MediaTek M80 / T830 | **No NTN** (Rel-16) | in production | [V] | https://www.mediatek.com/technology/5g/m80-modem |
| MediaTek T900 (FR1+FR2, Rel-18 client) | NTN not listed on product page | n/a | [V] (absence on page) | https://www.mediatek.com/products/5g-mobile-modems/mediatek-t900 |
| MediaTek NR-NTN (Rel-19, chipset unnamed) | NR-NTN over Ku-band OneWeb LEO, 50 MHz, conditional handover | Trial only (3 Nov 2025) | [V] | https://www.mediatek.com/press-room/esa-mediatek-eutelsat-airbus-sharp-itri-and-rs-announce-worlds-first-rel-19-5g-advanced-nr-ntn-connection-over-oneweb-leo-satellites |
| Qualcomm **X75** | NTN not claimed | in production | [U] | - |
| Qualcomm **X80** | **NB-NTN** integrated ("first 5G modem with integrated NB-NTN"), Rel-17/18 | Sampling Feb 2024, devices H2 2024 | [V] | https://docs.qualcomm.com/doc/87-73875-1/87-73875-1_REV_C_Snapdragon_X80_5G_Modem-RF_System_Product_Brief.pdf |
| Qualcomm **X85 / X82** | "Satellite" listed; NB-NTN per module makers (Telit FE990D60 = X85 with NB-NTN) | Sampling Mar 2025, devices H2 2025 | [V] sampling; NB-NTN [V] via Telit brief | https://www.qualcomm.com/news/releases/2025/03/introducing-qualcomm-x85--the-world-s-leading-modem-rf-for-unpre, https://www.telit.com/wp-content/uploads/2026/02/TC_FE990D60_Product_Brief.pdf |
| Qualcomm NR-NTN (X105 class, Rel-19) | NR-NTN reportedly shipped **disabled** until LEO networks exist | - | [U] (search synthesis only) | - |
| Qualcomm **Snapdragon Auto 5G Modem-RF Gen 2** (SA522M / **SA525M**) | NTN satellite support (NB-NTN) claimed for Gen 2 | Announced Feb 2023, sampling, commercial late 2023, vehicles 2025 | [S] | https://www.eenewseurope.com/en/qualcomm-rolls-next-generation-of-its-snapdragon-automotive-5g-platform/, https://futurumgroup.com/insights/qualcomm-snapdragon-latest-auto-5g-modem-rf-unveiled-at-mwc/ |
| Qualcomm 9205S / 212S | NB-NTN (Rel-17 IoT-NTN, GEO), LTE-M/NB-IoT | in production | [V] | https://docs.qualcomm.com/doc/87-64336-1/87-64336-1_REV_D_Qualcomm_9205s_Modem_Product_Brief.pdf |
| Nordic **nRF9151** | NB-NTN (Rel-17 IoT-NTN) + LTE-M/NB-IoT; NTN firmware mfw_nrf9151-ntn 1.0.x | **Skylo-certified Dec 2025** | [V] | https://www.nordicsemi.com/Nordic-news/2025/12/Nordic-Semiconductor-secures-Skylo-certification-for-nRF9151-module-enabling-global-IoT-connectivity |
| Sequans Monarch 2 (GM02S/GM02SP) | **No NTN** on the GM02SP per Verizon ODI listing | in production | [S] | https://opendevelopment.verizonwireless.com/design-and-build/approved-modules/module/30716 |

### Non-Chinese modules on NTN chipsets

| Module | Vendor (HQ) / chipset | Form factor | NTN mode / bands | Automotive / eCall | Status | Mark | Source |
|---|---|---|---|---|---|---|---|
| **Telit Cinterion FN990D** series | Telit Cinterion (US) / Qualcomm **X85/X82** | **M.2** (size/key not stated; FN990 family is 3052 Key-B [U]) | **NB-NTN** (bands not published) | No (industrial) | Announced 4 Mar 2025. No product page (telit.com/devices/fn990d = 404), no datasheet or sample date found | [V] announce; [U] everything else | https://www.telit.com/press/telit-cinterion-launches-ai-powered-5g-modules-and-data-cards-with-qualcomms-cutting-edge-modem/ |
| Telit Cinterion FE990D60 / FE990D50 | Telit / Qualcomm X85 (Dragonwing FWA Gen 4 Elite) | **LGA 52 x 52 x 2.9 mm** | **NB-NTN: Yes** (both regional variants); bands not stated; antennas: 4 cellular + 1 GNSS pad (no separate NTN port listed) | No; -40..85 °C | ES: FE990D50-NAD now (Mar 2026), FE990D60-NAD Apr 2026, FE990D60-RWD Q3 2026 | [V] | https://www.telit.com/press/telit-cinterion-expands-5g-leadership-with-new-3gpp-release-18-modules-and-frmcs-ready-variant/, https://www.telit.com/wp-content/uploads/2026/02/TC_FE990D60_Product_Brief.pdf |
| **Semtech/Sierra EM9492** | Semtech (US) / Qualcomm **X85** | EM series = M.2 [U: size] | NTN **not mentioned** in the launch release | No | Announced 3 Mar 2025, customer sampling "late 2025"; current status not found | [V] announce; [U] NTN | https://www.semtech.com/company/press/strengthens-5g-leadership-expanded-module-portfolio |
| **LG Innotek 3rd-gen automotive 5G module** | LG Innotek (Korea) / chipset **not disclosed** | module (captive / OEM programs) | **NR-NTN** (~30 MHz, tens of Mb/s), Rel-17 | Automotive; eCall not stated in release | Announced 9 Jun 2025, mass production planned **Q1 2026**, marketed to NA/JP automakers | [V] | https://www.prnewswire.com/news-releases/lg-innotek-unveils-worlds-first-automotive-5g-broadband-satellite-communication-module-302476121.html |
| Rolling Wireless **RN951Y** | Rolling Wireless (Luxembourg; ex-Fibocom, see rev 0.4) / Qualcomm **SA525M** | LGA 52 x 53 x 3.8 mm | **NB-NTN**; Skylo cert "planned" | Automotive, IATF 16949, -40..95 °C (105 °C eCall); **NG-eCall option**; 3x PCM/I2S | Production date not on product page (one secondary summary says 2027 [U]) | [V] page | https://www.rollingwireless.com/en/solutions/5g-solutions/rn951Y |
| WNC UMC-STD35FFx | WNC (Taiwan) / MediaTek MT2735 | LGA | **No NTN** (MT2735) | Automotive, NG eCall | FCC grant 2026 | [V] | see rev 0.4 |
| WNC / Advantech on MT2739 or M90 | - | - | - | - | **None found** - ask WNC for an MT2739 roadmap | [U] | - |
| Murata Type 1SC-NTN, Telit ME310M1, Semtech HL7810/HL7812, u-blox SARA-S528NM10 | Murata (JP) / Telit / Semtech / u-blox (CH) | LGA (LPWA) | NB-NTN (Skylo-certified per Skylo/Monogoto lists); HL781x GA planned Nov 2025 | No | in production (u-blox: cellular phase-out) | [S] | https://www.skylo.tech/certified-devices, https://docs.monogoto.io/ntn-satellite-networks/ntn-certified-devices/ntn-certified-modules, https://www.skylo.tech/newsroom/semtech-launches-industrys-first-single-vendor-device-to-cloud-cellular-and-satellite-iot-solution-with-skylo |
| Thales, Advantech, Lantronix, Ezurio, Sequans 5G | - | - | No 5G NTN module found | - | - | [U] | - |

**Bottom line:** no non-Chinese **NR-NTN M.2 card** is announced. The only announced non-Chinese **NTN M.2 card** is Telit **FN990D** (X85/X82, **NB-NTN only**), with no public datasheet, pinout or sample date. NR-NTN is available today only as automotive LGA modules (LG Innotek, captive; MT2739-based modules from Chinese vendors, excluded).

### Operator programs (context, not modem requirements)
- **Skylo** (NB-NTN over GEO L/S-band partners): requires a Skylo-certified chipset/module (Rel-14 plus selected Rel-17 NTN features) and GCF/PTCRB NTN certification [V] https://www.skylo.tech/knowledge-base/device-conformance. None of the 5G M.2 cards above is on Skylo's list yet [U].
- **T-Mobile T-Satellite (Starlink Direct-to-Cell):** commercial; works with **unmodified phones in terrestrial spectrum** (texting, location, selected apps). It is **not 3GPP NTN** and needs no NTN modem; whether IoT modules or M.2 cards are supported is not stated [V for phones] https://www.t-mobile.com/coverage/satellite-phone-service, https://www.t-mobile.com/news/network/t-satellite-data-ready-app-expansion
- **AST SpaceMobile:** also targets unmodified 4G/5G devices; commercial D2D deferred to **early 2027** [S] https://satnews.com/2026/07/16/ast-spacemobile-defers-commercial-direct-to-device-timeline-to-early-2027/
- So a **terrestrial-band D2C path (Starlink/AST) may work with today's X62 cards** with no hardware change. That is carrier-provisioning dependent [U].

### Design strategy: build ahead of NTN module availability

1. **Keep three M.2 3052 Key-B slots (PCI-SIG WWAN, Socket 2 config state 6).** Populate today with Sierra **EM9291** or Telit **FN990A28** (X62) and swap in NTN cards (FN990D, EM9492 if it gets NTN) later. Rationale: the FN990D is announced as M.2, and Telit's FN990 family to date has kept the same 3052 pinout (FN990A uses pin 20 USB_PCIE_SWITCH, UIM2 on 40-48, TGPIO on 22/24/28/62-68) [V for FN990A, **U for FN990D**]. **No NTN-specific M.2 pins exist** in the PCI-SIG WWAN pinout, and NTN radio paths are on the card's coax connectors, not the edge connector [U: no FN990D pinout published].
2. **Make the slot vendor-neutral** (rev 0.4 changes): pin-20 open-drain pull-down (Telit PCIe select), DNP pin-22 pull-up (Sierra VBUS_SENSE), leave 24/38/68 NC, open-drain RESET#/W_DISABLE#, 42 mm + 52 mm standoffs. Add a **bottom-side keep-out under each card** sized for double-sided (D3/S3) cards: X85 cards may be double-sided [U]. Check the LOTES socket height variant.
3. **Power:** keep a **6 A per-slot buck at 3.7 V** (range 3.135-4.4 V on all Qualcomm cards). FN990A peaks at 4 A [V]. X85 cards and NTN uplink (PC3 23 dBm, longer bursts) are unknown [U]. Keep 220 µF low-ESR bulk per slot and add footprint room for more.
4. **Antennas per slot:** plan **6 coax per slot** (4x cellular MHF4 + 1x GNSS + 1x spare for NTN/aux). That is 18 bulkhead SMAs total, so the panel and enclosure must allow it.
   - **NTN band coverage:** n255 (1525-1660 MHz) and n256 (1980-2200 MHz) fall inside the range of wideband 600-6000 MHz cellular antennas. GEO NB-NTN links, however, want a sky-facing, ideally RHCP, antenna with good low-elevation gain. Plan for an **L+S-band NTN antenna** such as Kyocera AVX AP822601/AP822602 (1525-1660 / 1980-2200 MHz) on a roof-facing port. Which card port carries NTN is per-module and not published [U].
   - **GNSS is mandatory for NTN UEs** (position for timing advance and Doppler pre-compensation; Qualcomm 9205S brief: "integrated GNSS to provide location for 5G IoT NTN") [V for 9205S; standard requirement S]. **GNSS antennas are passive by default, per `docs/antenna-gnss-plan.md` (reconciled 2026-10-10, supersedes the earlier "active antenna per slot" text):** the carrier has no GNSS bias-tee or LNA, and **no active / DC-biased antenna or DC-passing splitter may ever connect to an EM9291's shared ports (ANT0-ANT3; GNSS is on shared ANT1)** - Sierra EM92XX PTS Rev 5 A.2: DC on ANT0-ANT3 damages the module [V]. The Telit FN990 has an internal GNSS bias LDO (2.9-3.15 V, 100 mA, FN990 HDG Rev 3 Table 18) and the guide says it supports active antennas, but it also says an active antenna needs an external supply circuit and does not state which port carries bias [U, OI-32]. So an active GNSS antenna is allowed **only on a Telit-fitted slot's dedicated GNSS port, and only after OI-32 confirms bias on that port**; otherwise passive (FN990 has an integrated LNA + SAW). No shared active antenna with a powered splitter across slots. Keep GNSS L1 (1575 MHz) **isolated from n255 uplink (1626.5-1660.5 MHz)** and from co-located slots' transmitters. Expect desense; plan filtering and physical separation [U: magnitude].
   - Source for the L/S antenna: https://datasheets.kyocera-avx.com/AP822601-AP822602.pdf [S]
5. **Software:** Qualcomm X85 cards use mainline `mhi_pci_generic` once their IDs are added (FN990B40 and EM929x are already in; FN990D/EM9492 IDs are not yet in mainline [U]). Keep the bonding scheduler aware that NTN links are **low-rate and high-latency** (NB-NTN: hundreds of kb/s, seconds of latency; NR-NTN: tens of Mb/s, hundreds of ms per LG Innotek [V]). They are not peers of terrestrial 5G links.
6. **NB-NTN backup now (optional):** a small **Nordic nRF9151** (Skylo-certified) footprint on the carrier, on UART/USB to the host or MCU, gives working satellite messaging before any 5G NTN card exists. Its antenna and GNSS needs are the same as above. (**Decision still open - not added to rev 0.3.**)
7. **Spin 2 (automotive, eCall + NTN):** use a solder-down LGA, not M.2.
   - **No non-Chinese module offers both NR-NTN and certified eCall today.** Options:
     - **LG Innotek 3rd-gen** (NR-NTN, automotive, OEM channel; ask for availability and eCall)
     - **Rolling Wireless RN951Y** (NB-NTN + NG-eCall, Qualcomm SA525M; subject to the ownership decision in rev 0.4)
     - Ask **WNC** for an **MT2739** module (MediaTek, NR-NTN + NB-NTN). WNC's current MT2735 eCall module has no NTN.
   - Keep the eCall slot footprint decision open until one of these answers.
