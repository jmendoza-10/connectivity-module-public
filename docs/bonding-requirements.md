# Multi-link bonding - requirements template

Status: **TEMPLATE / DRAFT.** Structure and generic engineering requirements only. Every `TODO` needs a value or a decision.
Personal design: generic engineering targets only, with nothing carried over from any prior implementation.

Scope: bench system = FRDM-IMX95 + carrier with 3x 5G M.2 cards (Sierra EM9291 / Telit FN990A28, spin 1); requirements should be written so they carry over to the
spin 2 vehicle unit with automotive modules.

## 1. Use cases and traffic classes

| ID | Traffic class | Example | Direction | Priority | Latency budget (p99) | Loss tolerance | Needs session continuity across link change? |
|---|---|---|---|---|---|---|---|
| TC-1 | Control / telemetry | vehicle status, heartbeats | UL mostly | TODO | TODO | TODO | TODO |
| TC-2 | Real-time video | remote assistance / teleop camera streams | UL | TODO | TODO | TODO | TODO |
| TC-3 | Bulk upload | logs, sensor snapshots | UL | TODO | best effort | none (reliable) | no |
| TC-4 | Bulk download | maps, OTA | DL | TODO | best effort | none | resumable |
| TC-5 | Interactive / voice | TODO | both | TODO | TODO | TODO | TODO |

TODO: add/remove classes; define which classes may be duplicated across links (redundancy) vs aggregated (throughput).

## 2. Link model

| Item | Requirement |
|---|---|
| Links | 3 cellular (wwan0..2; map to slots via PCI path, not index) + optional Wi-Fi/Ethernet on the bench. TODO: count spin 2 links |
| Operators | TODO: one SIM per operator? which operators? eSIM vs physical |
| Link identity | stable name per slot (udev), carries operator, RAT (LTE/NR NSA/SA), band, cell ID in metrics |
| Addressing | per-link IPv4/IPv6 from the bearer; CGNAT assumed; no inbound reachability assumed |
| Policy routing | one routing table per link, `ip rule` by source address/fwmark; default route not used for bonded traffic |

## 3. Link health

Requirements (values TODO unless stated as a placeholder):

| ID | Requirement | Placeholder / TODO |
|---|---|---|
| LH-1 | Active probing per link at interval `T_probe` to `N` probe targets on independent networks | T_probe = TODO (e.g. 100-500 ms) |
| LH-2 | Metrics per link: RTT (min/avg/p95), jitter, loss %, goodput UL/DL, queue delay, probe-timeout count | - |
| LH-3 | Radio metrics per link from ModemManager/MBIM: RSRP, RSRQ, SINR, RAT, band, serving cell, registration state | sample period TODO |
| LH-4 | Link state machine: UP / DEGRADED / DOWN / ADMIN-DOWN with hysteresis (enter/exit thresholds and hold times) | thresholds TODO |
| LH-5 | Hardware health inputs: SLOTn_PG, module AT responsiveness, PCIe link state (AER events), USB fallback state | from carrierctl |
| LH-6 | Recovery ladder for a DOWN link: re-attach bearer -> modem reset (RESET#) -> slot power-cycle (power-reset-sequencing.md sec. 6) -> mark failed; max attempts / backoff TODO | TODO |
| LH-7 | Recovery actions on one slot must not interrupt the other links (verified in test T5.4) | - |

## 4. Failover and scheduling

| ID | Requirement | TODO |
|---|---|---|
| FO-1 | Detection time for a hard link loss | <= TODO ms |
| FO-2 | Time to move TC-1/TC-2 flows to remaining links after detection | <= TODO ms |
| FO-3 | No session reset for TC-1/TC-2 on single-link loss (requires bonding layer that hides per-link addresses) | confirm |
| FO-4 | Scheduler modes: (a) min-RTT, (b) weighted by measured capacity, (c) redundant (duplicate on 2+ links) per traffic class | which per class: TODO |
| FO-5 | Reordering tolerance at receiver; max reorder buffer | TODO ms |
| FO-6 | Congestion control per sub-path, coupled or uncoupled | TODO |
| FO-7 | Behaviour with 0 links: queue, drop, or signal upper layer | TODO |
| FO-8 | Data-cap / cost awareness per SIM | TODO |

## 5. Metrics and observability

- Export per-link and per-bond metrics (Prometheus text format or similar) at 1 s resolution; store raw on the bench.
- Event log: link state transitions, recovery actions, modem resets/power-cycles with timestamps (monotonic + UTC).
- Bench KPIs: aggregate goodput vs sum of links, p99 latency per class, failover gap (ms of no delivery), duplicate overhead.
- TODO: retention, privacy constraints on location/cell data.

## 6. Architecture options (to evaluate, not decided)

| Option | How | Pros | Cons / open questions |
|---|---|---|---|
| A. MPTCP (Linux kernel, `ip mptcp`, mptcpd) | Client opens subflows on each wwan; server side needs MPTCP (kernel >= 5.6) or an MPTCP-capable proxy | In-kernel, mature, standard (RFC 8684); per-subflow CC; schedulers being extended (BPF) | TCP only (no UDP video unless tunnelled); middleboxes may strip options; scheduler control limited; needs server/proxy we control |
| B. Tunnel bonding (UDP-based, user space or kernel) | Encapsulate all traffic in a tunnel with per-packet scheduling over N UDP paths to an aggregation server (e.g. WireGuard per link + custom scheduler, or an open-source bonding tunnel such as OpenMPTCProuter's approach, MPQUIC-based designs) | Carries any traffic incl. UDP/RTP; full control of scheduling, duplication, FEC | Must build/operate the server; reordering/jitter buffer design; per-packet overhead; security design |
| C. MP-QUIC / application-level multipath | Applications (e.g. video) use multipath QUIC directly | Per-application control, encryption built in | Spec still maturing (IETF multipath QUIC); every app must adopt |
| D. Per-flow load balancing (ECMP / policy routing) | Pin each flow to one link, re-pin on failure | Trivial | No aggregation for a single flow; failover breaks sessions |

Decision criteria (weights TODO): latency for TC-2, session continuity, UDP support, server-side effort, vehicle use
(security, certification), licensing.

## 7. Bench validation requirements

- Network emulation (tc netem / a programmable attenuator or shield box) to inject loss, delay, and outages per link.
- Reproducible drive-log replays: TODO - source of real per-link traces.
- Pass/fail thresholds come from sections 3-4; test steps in bringup-test-plan.md stage T8.

## 8. Open decisions

1. Primary bonding option (A/B/C/D or hybrid, e.g. B for TC-2 + A for TC-3).
2. Aggregation server location and ownership.
3. Traffic-class latency/loss numbers.
4. Which operators / SIMs, data plans.
5. Personal design: which lessons to write down as requirements.
