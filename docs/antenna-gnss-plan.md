# Antenna and GNSS plan - WWAN carrier rev 0.3

Scope: the three M.2 Key-B WWAN slots (J401/J501/J601). **All RF connectors are on the M.2 cards** (MHF4 / MHF 7S receptacles).
The carrier has no RF traces, no RF connectors, no GNSS LNA and no GNSS bias-tee. Antennas reach the enclosure wall through
off-board **pigtails** (MHF4 -> SMA bulkhead, cable bought with the antennas). This document plans how many pigtails each slot needs.

Sources: [EM92] Sierra Wireless EM92XX Product Technical Specification Rev 5 (Jan 2025), sec. 1.9, 3.1.1, Table 1-3, Table 3-1, A.2;
[FN990] Telit FN990 Family Hardware Design Guide 1VV0301752 Rev. 3, sec. 5.x "Internal LDO for GNSS Bias" (Table 18), 7.1, 7.4.

## 1. Per-module antenna ports (verified)

| Module | Cellular ports | GNSS | GNSS bias | Notes |
|---|---|---|---|---|
| Sierra **EM9291** | 4x MHF4 (ANT0-ANT3), 5G/LTE on all four | **shared on ANT1** (L1 + L5) | **none - passive antenna only.** [EM92] A.2: "Do not connect an active antenna/DC presence to any of the shared antennas (ANT0-ANT3). Doing so will damage the module" | ANT1 must be a combined cellular + GNSS (L1/L5) passive antenna, or a diplexed pigtail |
| Sierra EM9293 (if used later) | 4x MHF4 | ANT1 shared **or** dedicated MHF 7S "GNSS" port (software-selectable) | dedicated port supports an active antenna (bias from the module; VCC must stay >= 3.3 V - our rail is 3.74 V) | MHF 7S needs a different pigtail (I-PEX 20980 class) |
| Telit **FN990A28** | 4x MHF4 (ANT0-ANT3) | dedicated MHF4 GNSS connector (#4) **or** shared #1 ([FN990] 7.4.1), selected with `AT$GPSANTPORT` | internal LDO for GNSS bias 2.9-3.15 V, max 100 mA ([FN990] Table 18). "FN990 modems support active GNSS antennas" (7.4) | Same section also says an active antenna needs "an external dedicated power supply circuit" - **contradiction, UNVERIFIED which port carries the internal bias (OI-32)**. Integrated LNA + SAW, so a passive antenna works |

**Conclusion for the carrier:** no GNSS bias circuit or LNA is needed on the carrier for either card. The FN990 provides bias on
its own GNSS port (to be confirmed); the EM9291 must never see DC on any port, so a carrier bias-tee would be a hazard, not a feature.
Default plan: **passive** GNSS antennas on all slots; active antenna only on an FN990 dedicated port after OI-32 is closed.
This plan is authoritative for GNSS antennas; `hardware/docs/parts-shortlist.md` (rev 0.5 NTN strategy, item 4) defers to it.

## 2. Pigtail count per slot

| Pigtail | EM9291 | FN990A28 | Purpose |
|---|---|---|---|
| P1 ANT0 | main (Tx/Rx) | main | 600-6000 MHz cellular |
| P2 ANT1 | cellular + **GNSS L1/L5 (passive only)** | cellular (div / MIMO) | |
| P3 ANT2 | MIMO | MIMO | |
| P4 ANT3 | MIMO | MIMO | |
| P5 GNSS | - (or EM9293 MHF 7S) | dedicated GNSS (#4) | L1 (FN990: 1559-1606 MHz) |
| P6 spare | spare | spare | reserved for an NTN card's extra L/S-band port or an EM9293 MHF 7S lead |

- Bench enclosure: **6 bulkhead holes per slot, 18 total**; fit 4-5 pigtails per slot depending on card.
- Antenna count for the full bench: 12 cellular (4 per card) + up to 3 GNSS = **15 antennas**; GNSS on EM9291 slots shares ANT1,
  so an EM9291-only build needs 12 antennas, of which the three ANT1 antennas must cover L1/L5.
- Cables: MHF4 -> SMA(F) bulkhead, 1.13 mm or 0.81 mm coax, <= 200 mm, from non-PRC makers (e.g. I-PEX, Amphenol RF, Taoglas,
  Molex). **VERIFY** country of manufacture against the supply-chain rule (OI-26 d).
- Mechanical: pigtail exits route away from the M.2 retention screw (3052 or 3042 standoff position, H/H42 on each slot sheet).

## 3. NTN readiness (documentation only - no NTN module on this carrier)

- 3GPP NTN NR bands n255 (L-band, ~1.5-1.6 GHz) and n256 (S-band, ~2 GHz) fall within the 600-6000 MHz range the cellular ports
  and antennas already cover, but NTN links typically want a **higher-gain, sky-facing antenna** (and some modules expose a separate
  NTN port). The P6 spare pigtail position per slot is reserved for that. Antenna choice is **UNVERIFIED** until an NTN M.2 card is chosen.
- Neither the EM9291 nor the FN990A28 is claimed as NTN-capable here. Firmware/hardware NTN support of these exact SKUs is **UNVERIFIED**.
- nRF9151 (NB-NTN): **not added** - decision still open. It is not an M.2 card and would not use these slots.
- Slot pins 24/38/68 are left NC in rev 0.3 so a future NTN M.2 card with different use of these pins cannot be back-driven (OI-35).

## 4. Rules for whoever fits antennas

1. Never connect an active (DC-powered) antenna or a DC-coupled splitter to EM92XX ANT0-ANT3.
2. Terminate or connect every cellular port that the module firmware uses for Tx (ANT0 at least) before `slot on`; [EM92] states
   open/short does not cause permanent damage, but do not rely on it for the FN990 (not stated in [FN990]).
3. Record which physical antenna is on which pigtail per slot in the bench log (needed for T7.5 RF coexistence).
