# Spin 1 (bench) BOM and budget estimate, cap **< $1,500** (rev 0.4, 2026-10-10)

## rev 0.4: no Chinese-company chips/modules

Hard requirement (2026-10-10): no chips/modules from PRC-headquartered or PRC-owned companies. Quectel and Fibocom are out, so **configs A-F below (rev 0.3) are all void**: every one used RM520N-GL, EM060K-GL or FM350-GL. Vendor checks, pin-compatibility and the full BOM audit are in [parts-shortlist.md, rev 0.4](parts-shortlist.md#rev-04-no-chinese-company-chipsmodules-2026-10-10). Prices are single-unit, found 2026-10-10, ex-VAT. EUR converted at ~1.16 USD/EUR (approx.). Re-quote before ordering.

### Replacement modem line items

| # | Item | Unit price | Source |
|---|---|---|---|
| 3g | **Sierra EM9291** 5G (Qualcomm X62), M.2 3052, PCIe + USB; PTCRB/AT&T/T-Mobile/Verizon | **$366.97** (Digi-Key US, EM9291_1105285, 20-wk std lead; stock not confirmed) | [Digi-Key](https://www.digikey.com.mx/en/products/detail/sierra-wireless/EM9291-1105285/28741814), [Octopart $364.40](https://octopart.com/part/sierra-wireless/EM9291_1105285) |
| 3h | Telit Cinterion **FN990A28** 5G (Qualcomm X62), M.2 3052 (second source) | €311.39 ≈ $361 (Digi-Key IE, **28-wk lead**); £277.05 RS UK; $355.61 Compulab (with 2 antennas) | [Digi-Key](https://www.digikey.ie/en/products/detail/telit-iot-products-llc/FN990A28H06T060100/28167345), [RS](https://uk.rs-online.com/web/p/wi-fi-modules/0285568), [Compulab](https://edge.compulab.com/store/5g-m-2-3052-key-b-modem-for-use-worldwide-for-fitlet3/) |
| 3i | **Advantech AIW-357 DK-G1P** 5G (**MediaTek T700**), M.2 3052, PCIe; FCC only, no US carrier certs found | €393.23 ≈ $456 (PF Electronic, PL); others quote-only | [PF Electronic](https://sklep.pf-electronic.pl/en_US/p/AIW-357DK-G1P-5G-Sub6-GNSS-M.2-3052-Key-B%2C-PCIe-only-sku/22678360) |
| 3j | **Sierra EM7411** LTE Cat 7 (Qualcomm), M.2 3042, **USB only** | €117.47 ≈ $136 (Digi-Key IE, 20-wk lead) | [Digi-Key](https://www.digikey.ie/en/products/detail/sierra-wireless-airlink/EM7411-Q-M2M-1104680/13557052) |
| - | Sierra EM9191 | $461.06 Digi-Key US, **Last Time Buy 11/27/2026** - not used | [Digi-Key](https://www.digikey.com/en/products/detail/sierra-wireless/EM9191-1104903/16538756) |

### Non-modem changes for the rule

| Change | Delta vs rev 0.3 | Note |
|---|---|---|
| ADT-Link M41 riser (Shenzhen) → own M.2 Key-M paddle card + Samtec/Amphenol PCIe cable | +$25 to +$75 est. | quote needed; or keep ADT-Link if I rule bench fixtures out of scope |
| MHF4→SMA pigtails → I-PEX / Amphenol RF assemblies (12x) | +$80 to +$140 est. | $10-15 each est. |
| Nexperia FETs/logic → onsemi NVMFS5C646NL + TI SN74LVC1G07/08; pin MPNs for generic R/C, headers, TVS, standoffs | +$10 to +$20 est. | |
| Schematic additions: pin-20 2N7002 per slot, DNP pin-22 resistor, 42 mm standoffs, 43.2k FB option | +$5 est. | |
| M.2→USB adapter (item 3f, only for FM350 Windows flashing) | -$25 | not needed |
| **Subtotal non-modem (items 1, 2, 4-14 + deltas)** | **≈ $860-1,160 with 2 carriers assembled; ≈ $750-1,050 with 1** | JLCPCB fab/assembly still in these numbers |

### Totals (modems + non-modem, 1 carrier assembled / 2 carriers assembled)

| Config | Modems | Modem cost | Total, 1 carrier | Total, 2 carriers | Verdict |
|---|---|---|---|---|---|
| **N1 (recommended)** | 1x EM9291 (5G) + 2x EM7411 (LTE) | ≈ $639 | **≈ $1,390-1,690** | ≈ $1,500-1,800 | **Fits only at the low end** with one carrier assembled and JLCPCB kept. Same idea as rev 0.3 config B (one 5G anchor + LTE links for bonding development) |
| N2 | 2x EM9291 (two 5G links, slot 3 empty) | ≈ $734 | ≈ $1,480-1,780 | ≈ $1,590-1,890 | Borderline/over |
| N3 | 1x AIW-357 (MediaTek) + 2x EM7411 | ≈ $728 | ≈ $1,480-1,780 | ≈ $1,590-1,890 | Borderline/over. Honors the MediaTek preference, but no US carrier certs and a 3.3 V slot variant |
| N4 | 3x EM7411 (LTE only) | ≈ $408 | ≈ $1,160-1,460 | ≈ $1,270-1,570 | **Fits.** Cheapest way to develop bonding software, no 5G |
| N5 | 2x EM9291 + 1x AIW-357 (three 5G, Qualcomm + MediaTek) | ≈ $1,190 | ≈ $1,940-2,240 | ≈ $2,050-2,350 | **Over.** Closest to the old config D; needs the cap raised to ~$2,300 |
| N6 | 3x EM9291 | ≈ $1,101 | ≈ $1,850-2,150 | ≈ $1,960-2,260 | Over |

**Budget impact:** rev 0.3 config D was ≈ $1,100-1,390. Losing the $64-88 marketplace FM350s and the ~$95 EM060K means non-Chinese cards cost $136 (LTE) to $370-460 (5G) each. **Three 5G links no longer fit under $1,500 (≈ +$750-950 vs config D).** One 5G + two LTE (N1) fits only at the low end. **If the fab must also move off JLCPCB**, add an estimated several hundred dollars (6-layer + BGA assembly at a US/EU house; quote needed), and nothing with 5G stays under $1,500.

**Recommendation:** buy for N1 now (1x EM9291 + 2x EM7411; assemble one carrier) and keep FN990A28 as the second-source 5G card. Add the AIW-357 as the MediaTek link (N3/N5) if I raise the cap or want MediaTek on the bench. The MediaTek preference is met where it matters most, in spin 2 (WNC MT2735 eCall modem).

---

*Everything below is the rev 0.3 estimate, kept for history. Quectel/Fibocom items (3a-3e) and configs A-F are void under rev 0.4.*


rev 0.3: adds MediaTek (Fibocom FM350-GL) modem options D/E/F and updates the recommendation.

Prices are single-unit list prices found on 2026-10-09 (USD unless noted). "est." marks my estimates where no distributor price was found. Shipping, tariffs and data plans are listed separately. Prices move, so re-quote before ordering.

## Line items

| # | Item | Qty | Unit price | Ext. | Source |
|---|---|---|---|---|---|
| 1 | **NXP FRDM-IMX95** dev board (host) | 1 | $210.00 (NXP list, "pending stock"). Digi-Key AU lists $321.05, 0 in stock, ETA 4-Dec-2026. Octopart shows ~$213-225 | **$210** | [NXP](https://www.nxp.com/design/design-center/development-boards-and-designs/FRDM-IMX95), [Digi-Key](https://www.digikey.com.au/en/products/detail/nxp-usa-inc/FRDM-IMX95/29285213), [Octopart](https://octopart.com/it/part/nxp-semiconductors/FRDM-IMX95) |
| 2 | ADT-Link M41 M.2 Key-M → PCIe x1 extension cable (FRDM M.2 → carrier x1 edge) | 1 | $15-17 | **$16** | [ADT-Link](https://www.adt.link/product/M41V4-Shop.html) |
| 3a | Quectel **RM520N-GL** 5G M.2 | 3 | $209.99 (CDW, Lenovo-branded 4XC1Q34839) to $270.99 (Waveshare); Digi-Key $280.49 @100, 0 stock | $630-813 | [CDW](https://www.cdw.com/product/quectel-rm520n-gl-wireless-cellular-modem-5g/8258056), [Waveshare](https://www.waveshare.com/product/rm520n-gl.htm), [Digi-Key](https://www.digikey.com/en/product-highlight/q/quectel/rm520n-5g-nr-sub-6-ghz-module) |
| 3b | Quectel **EM060K-GL** LTE-A Cat 6 M.2 (300/50 Mb/s), pin/footprint-family compatible with RM520N | 3 | $98.19 (Waveshare), $93.11 (Amazon) | $280-295 | [Waveshare](https://www.waveshare.com/product/em060k-gl.htm) |
| 3c | Quectel RG255C-GL 5G RedCap M.2 (223/123 Mb/s) | n/a | €129.92 (TOP-electronics, *out of stock*); Digi-Key $266 @250, **30-week lead** | not recommended now | [TOP](https://www.top-electronics.com/en/5g-redcap-rg255c-gl-m-2), [Digi-Key](https://www.digikey.sg/en/products/detail/quectel/RG255CGL00AB-4M2-SGASA/24349398) |
| 3d | Fibocom **FM350-GL** 5G M.2 3052 (MediaTek T700, PCIe; 4x4 MIMO) | 3 | ~$64-88 Amazon US (marketplace, mostly laptop pulls, may be OEM FCC-locked); £55.99 Amazon UK; €189 new at cartft | $192-264 (US marketplace) | [Amazon US](https://www.amazon.com/Yunseity-4-67Gbps-Downlink-1-25Gbps-Supported/dp/B0CFPRSPS7), [Amazon UK](https://www.amazon.co.uk/Fibocom-FM350-GL-Network-module-Desktop/dp/B0CXHYVKVN), [cartft](https://www.cartft.com/en/catalog/il/3532) |
| 3e | Fibocom FM350-GL-16 (MediaTek T700, **LTE-only**) | n/a | ~$34 Amazon US | n/a | [Amazon US](https://www.amazon.com/Network-FM350-1Gbps-Support-Module/dp/B0DDJSBL8C) |
| 3f | M.2 Key-B → USB3 adapter enclosure (for FM350 firmware flashing on a Windows PC, and for bench-testing modems standalone) | 1 | est. $20-30 | $25 est. | e.g. [Rework MH2U](https://www.rework.network/products/mh2u-v7), [Waveshare](https://www.waveshare.com/usb-to-m.2-b-key.htm?sku=23252) |
| 4 | Carrier PCB, 6-layer, ~100x160 mm, 5 pcs, JLCPCB | 1 lot | from $35.10 for 5x 100x100 6L; larger size + gold-finger edge est. $60-100 | $60-100 est. | [JLCPCB](https://jlcpcb.com/resources/multiple-layer-pcb) |
| 5 | JLCPCB PCBA fees (setup $8.18, stencil $1.53, BGA X-ray $1.64/board, joints, extended-part fees) for 2 boards | 1 lot | | $40-80 est. | [JLCPCB assembly pricing](https://jlcpcb.com/help/article/pcb-assembly-price) |
| 6 | **Diodes PI7C9X3G606GP** PCIe Gen3 switch | 2 | $35.09 (Digi-Key, PI7C9X3G606GPBFCAEX) | $70 | [Findchips (Digi-Key/Mouser)](https://www.findchips.com/search/PI7C9X3G606GPBFCAEX) |
| 7 | Microchip USB5744 USB3 hub (fallback path, optional) | 2 | €6.15 (RS) | ~$14 | [RS](https://ie.rs-online.com/web/p/usb-interface-ics/8938310) |
| 8 | TI **LM74800-Q1** ideal-diode controller (12 V reverse/OVP, AEC-Q100) + 2x N-FET + TVS | 2 | £2.40 (Digi-Key UK) + FETs/TVS ~$4 | ~$14 | [Digi-Key](https://www.digikey.co.uk/en/products/detail/texas-instruments/LM74800QDRRRQ1/13627158) |
| 9 | Bucks: 3x 3.7 V/6 A (one per modem) + 3.3 V + 0.95 V, AEC-Q100 class, with inductors | 2 sets | ~$4-6 per rail est. | $40-60 est. | (LMQ61460-Q1 is backordered at Digi-Key; pick an in-stock equivalent) |
| 10 | 3x M.2 Key-B sockets (3042/3052 standoffs), 3x nano-SIM holders, 6x 220 µF low-ESR polymer caps, ESD, passives, fan header, 12 V jack | 2 sets | est. | $50-70 est. | LCSC / Digi-Key |
| 11 | MHF4 → SMA-F bulkhead pigtails | 12 | $3.19-3.56 | $38-43 | [rfsupplier](https://rfsupplier.com/ipex-mhf4-mh4-female-ra-to-sma-bulkhead-panel-female-connector-pigtail-cable-081mm-rf-mhf4-cable-rf-coaxial-cable_p9437.html), [data-alliance](https://www.data-alliance.net/mhf4-to-sma-female-cable-1-inch-2-inch-4-in-6-in-8-in-10-in-1-ft-14-in-16-in-18-in-24-inches/) |
| 12 | 600-6000 MHz SMA dipole antennas (e.g. Taoglas TG.64.8113) | 12 | $9.47 | $114 | (search result price; verify at Digi-Key/Mouser) |
| 13 | Heatsinks x3 + 12 V fan + standoffs/plate | 1 | est. | $20-30 est. | |
| 14 | Shipping (JLCPCB DHL, distributors) + US import duties on PCBA | 1 | est. | $50-100 est. | |

Not included (assumed owned or recurring): 12 V/5 A bench supply, USB-C PD supply for the FRDM, test SIMs and data plans for three carriers, and the satellite terminal.

## Totals by modem choice (1 working unit, 2 assembled carriers, 5 bare PCBs)

| Configuration | Low | High | Verdict |
|---|---|---|---|
| **A: 3x RM520N-GL (full 5G triple bonding)** | ≈ $1,370 | ≈ $1,730 | **Borderline / over.** Fits only if you get all three RM520N at ~$210, assemble **one** carrier, and keep shipping low. The Lenovo-branded CDW units may carry Lenovo firmware/USB IDs, so verify they work in a generic Linux host before relying on that price |
| **B: 1x RM520N-GL + 2x EM060K-GL (5G + 2x LTE Cat 6)** | ≈ $1,140 | ≈ $1,390 | **Fits** with ~$110-360 margin. Recommended: tests bonding with heterogeneous links (a realistic case) and keeps one 5G path. Swap the EM060Ks for RM520Ns later; same M.2 Key-B socket, Quectel lists the families as compatible |
| **C: 3x EM060K-GL (3x LTE Cat 6)** | ≈ $1,020 | ≈ $1,220 | **Fits comfortably.** Cheapest way to develop the bonding/scheduler software. Max aggregate ~900 Mb/s DL / 150 Mb/s UL |

| **D: 1x RM520N-GL + 2x FM350-GL (5G x3, Qualcomm + MediaTek)** | ≈ $1,100 | ≈ $1,390 | **Fits. New recommendation.** Three 5G 4x4 links for less than config B. Qualcomm unit is the reference/telemetry anchor, and the chipset mix gives failure diversity |
| E: 3x FM350-GL (all MediaTek 5G) | ≈ $960 | ≈ $1,210 | Fits comfortably, but carries all the MediaTek risks: untested 3x t7xx behind a switch, FCC-lock/eSIM-mode quirks on marketplace pulls, Windows-only firmware flashing, -10..55 °C normal range |
| F: 1x RM520N-GL + 1x FM350-GL + 1x EM060K-GL | ≈ $1,130 | ≈ $1,400 | Fits. Three different basebands (X62 / T700 / LTE Cat 6) for maximum diversity testing |

(Low/high sums: items 1, 2, 4-14 ≈ $740-920, with items 6-10 for 2 boards, plus the modem set. Assembling only 1 carrier saves ≈ $110, which brings config A to ≈ $1,260 at the lowest modem prices. Configs D/E/F include the item-3f adapter, $25.)

## What does NOT fit under $1,500 (defer to spin 2 or buy later)

| Item | Why it's out of spin 1 | Cost seen |
|---|---|---|
| Compulab MCM-iMX95 eval kit as host (instead of FRDM) | 19x19 / 2 PCIe / 10G, but $545 + 3 modems + carrier exceeds the cap | $545 ([Compulab shop](https://shop.compulab.com/product/mcm-imx95-evaluation-kit/)) |
| Full custom carrier with SoM + SJA1110 + T1 PHYs + 5x CAN | 8-10 layers, SoM single-unit price, much more assembly. The FRDM can't feed an SJA1110 (no exposed SGMII/RGMII) | SJA1110AEL $18.66-22.87 @1, TJA1120BHN $4.50-4.59 @1, TJA1463 $1.68 @1 ([Findchips SJA1110](https://www.findchips.com/detail/SJA1110AEL%2F1Y/NXP-Semiconductors), [TJA1120](https://www.findchips.com/detail/TJA1120BHN%2F0J/NXP-Semiconductors), [TJA1463](https://www.findchips.com/detail/TJA1463ATK%2F0Z/NXP-Semiconductors)). Chips are cheap; the board around them isn't |
| Standalone high-precision GNSS | ZED-F9K is effectively replaced (u-blox page now redirects to ZED-X20K). A SparkFun ZED-F9R breakout is $299.95. Use modem GNSS in spin 1 | [SparkFun F9R](https://www.sparkfun.com/sparkfun-gps-rtk-dead-reckoning-breakout-zed-f9r-qwiic-gps-22693.html) |
| NTN modem (BG95-S5 / SARA-S528NM10) + Skylo plan | Not core to bonding. Defer | not priced |
| Separate Wi-Fi module (JODY-W5) | FRDM already has IW612 Wi-Fi 6/BT | n/a |
| Automotive LGA modems (AG55xQ) | Sales-channel/NDA, LGA RF layout | quote only |
| 100/1000BASE-T1 media converters (to test T1 on the bench) | Commercial converters are typically a few hundred $ each | not priced |

## Budget-driven recommendations
1. **Use the FRDM-IMX95 + a single-purpose WWAN carrier** (PCIe switch + 3x M.2 + power + SIM). Don't build a full custom i.MX 95 board for spin 1.
2. **Modems: configuration D** (1x RM520N-GL + 2x FM350-GL), which supersedes B: 5G on all three links within budget. Fall back to B or C (EM060K) if marketplace FM350s turn out FCC-locked and unflashable, or t7xx misbehaves behind the switch. Buy FM350s from a seller that states the unit is unlocked or generic (not Lenovo/HP/Dell), and budget one spare.
3. **Keep the AEC-Q100 parts where cost is negligible** so the schematic carries over: LM74800-Q1, AEC-Q100 bucks, PI7C9X3G606GP footprint = GPQ automotive part. The USB5744 hub is the exception (industrial only; it's a test fallback).
4. **Defer** SJA1110/T1, standalone GNSS, NTN and JODY-W5 to spin 2. Use the FRDM's GbE for the satellite terminal and its CAN/Wi-Fi.
5. **Fab:** JLCPCB 6-layer with PCBA (they assemble the 10x10 BGA with X-ray). Order 5 bare boards, assemble 2 (or 1 to save ~$120), and hand-fit the M.2 sockets if they are not in JLC's parts library.
6. If the BGA is a concern, the ASM2806 (QFN88) is a cheaper, easier alternative switch. It isn't automotive-grade, so you'd lose carry-over.
