<div align="center">

# Bhutan 120 kW DC Charger — Tonhe Power-Module Flow

**Node-RED flow (Vector vSECC) for the two-connector standalone charger in Bhutan,<br>converted from Sinexcel SER100040K3B to four Tonhe 30 kW power modules.**

![Flow](https://img.shields.io/badge/flow-REV%20TONHE--BHUTAN--3-2a78d6)
![Modules](https://img.shields.io/badge/modules-4%20%C3%97%20Tonhe%2030%20kW-eb6834)
![Cabinet](https://img.shields.io/badge/cabinet-120%20kW%20%C2%B7%202%20connectors-1a7f37)
![Runtime](https://img.shields.io/badge/runs%20on-vSECC%20%2B%20Node--RED-59636e)
![Status](https://img.shields.io/badge/REV%203-field%20tested%2010%20Nov%202026-1a7f37)
![Measured](https://img.shields.io/badge/measured-119%20kW%20per%20connector-2a78d6)
[![License](https://img.shields.io/badge/license-MIT-59636e)](LICENSE)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/bus-tie-sharing-dark.gif">
  <img alt="Animation: one car gets all four modules through the R6 bus tie (120 kW); a second car makes R6 open after ramping below 5 A, so each connector gets its own two modules (60 kW)" src="docs/images/bus-tie-sharing-light.gif" width="100%">
</picture>

</div>

## At a glance

| Item | Details |
|---|---|
| **Cabinet** | Standalone two-connector DC charger, Bhutan (not the DC Link master/follower pair) |
| **Power modules** | 4 × Tonhe 30 kW on CAN (protocol V1.3) — group 1 = CAN addr **1, 2** → connector 1 · group 2 = CAN addr **3, 4** → connector 2 |
| **Sharing** | R6 bus tie (`d_out/7`) closes while exactly one car is charging → up to **120 kW** on that connector; two cars → **60 kW** each |
| **Software** | Node-RED on the Vector vSECC; OCPP 1.6J by `CP.py` on the EdgeBox RPI200 |
| **Flow in this repository** | [`flows_Bhutan_120kW_Tonhe_REV3_public.json`](flows_Bhutan_120kW_Tonhe_REV3_public.json) — **REV TONHE-BHUTAN-3**, 10 Nov 2026, public copy with a placeholder admin PIN and broker address ([details](#public-copy--what-was-changed)) |
| **Running in the cabinet** | **REV 3** since 10 Nov 2026 11:11 (UTC+7) |
| **Field result (10 Nov 2026)** | connector 1 alone **119.2 kW**, connector 2 alone **119.1 kW**, both together **59 kW each** — see [Field test](#field-test--10-nov-2026) |

<details>
<summary><b>สรุปภาษาไทย</b></summary>

- flow ของตู้ Bhutan แบบ standalone 2 หัว เปลี่ยนจาก Sinexcel เป็น Tonhe 30 kW × 4 ตัว (หัวละ 2 ตัว) — G1 = address 1, 2 (หัว 1), G2 = address 3, 4 (หัว 2)
- R6 (`d_out/7`) ขนานบัสเมื่อมีรถคันเดียว → หัวนั้นได้ 4 โมดูล สูงสุด 120 kW; มีรถสองคัน → R6 เปิด หัวละ 60 kW
- **REV 3 (10/11/2026)** แก้อาการ "หัว 1 จ่าย kW น้อยกว่าหัว 2": watchdog FIX#NOLOAD เดิมนับจำนวนครั้งที่โหนดทำงาน ชุด limit 5 ข้อความจาก CP.py ทำให้นับครบ 3 ก่อนโมดูลขึ้นกระแส → เปิด R6 ผิด → หัว 1 เหลือ 60 kW (138 A) ทั้ง session; REV 3 ตัดสินด้วยเวลาจริง และแปลง kW → A ด้วยแรงดันวัดจริง (หัวเดียว ~318–320 A ≈ 119 kW)
- **ผลทดสอบหน้างาน 10/11/2026 (REV 3 ในตู้จริง):** หัว 1 ชาร์จหัวเดียวได้ 119.2 kW (286 A), หัว 2 ชาร์จหัวเดียวได้ 119.1 kW (288 A), ชาร์จสองหัวพร้อมกันได้หัวละ 59 kW, R6 ไม่ถูกสั่งเปิดผิดเลยทั้ง log
- ตู้ตัดการชาร์จเองเมื่อ SoC ถึง 90% (แท็บ `SoC Cutoff 90%`, `TARGET_SOC = 90`) — ไม่ใช่ RemoteStop จาก OCPP
- ไฟล์ flow ใน repo นี้: [`flows_Bhutan_120kW_Tonhe_REV3_public.json`](flows_Bhutan_120kW_Tonhe_REV3_public.json) — เป็นฉบับเผยแพร่ ใส่ PIN หน้าจอ admin เป็นค่าตัวอย่าง `0000` และที่อยู่ MQTT broker ภายนอกเป็น `broker.example.invalid` ต้องตั้งค่าของตัวเองก่อน Deploy
- flow นี้เขียนสำหรับตู้นี้โดยเฉพาะ ใช้เป็นตัวอย่างอ้างอิง ต้องตรวจสอบกับฮาร์ดแวร์ของตัวเองก่อนใช้งานจริง (ไฟฟ้าแรงสูง)

</details>

## Contents

- [Field test — 10 Nov 2026](#field-test--10-nov-2026)
- [REV 3 — why connector 1 delivered less than connector 2](#rev-3--why-connector-1-delivered-less-than-connector-2)
- [How power is shared](#how-power-is-shared)
- [Power topology](#power-topology)
- [Control architecture](#control-architecture)
- [Tonhe CAN protocol (as used)](#tonhe-can-protocol-as-used)
- [Module setup](#module-setup)
- [Configuration](#configuration)
- [Repository contents](#repository-contents)
- [Version history](#version-history)
- [Deploying a flow](#deploying-a-flow)
- [Troubleshooting from the logs](#troubleshooting-from-the-logs)
- [Tools](#tools)
- [Public copy — what was changed](#public-copy--what-was-changed)
- [Safety and license](#safety-and-license)

## Field test — 10 Nov 2026

REV 3 was deployed in the cabinet at 11:11 and tested with two cars. Each connector on its own reaches the full cabinet power, and with two cars each connector gets its own group.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/field-test-rev3-dark.png">
  <img alt="Line chart of the power delivered by each connector on 10 Nov 2026 between 13:04 and 13:25. Connector 2 alone reaches 119.1 kW, connector 1 alone 119.2 kW and 118.6 kW, connector 2 alone again 118.9 kW. From 13:21 both connectors charge at the same time at 59 kW each." src="docs/images/field-test-rev3-light.png" width="100%">
</picture>

<sub>Data: vSECC `power-electronics-com-1/2.log`, 1 s averages — table in [`docs/data/field_test_rev3_20261110.csv`](docs/data/field_test_rev3_20261110.csv). Times are local (UTC+7); the vSECC logs themselves are in UTC.</sub>

| Test | Time (UTC+7) | Connector 1 | Connector 2 | R6 |
|---|---|---|---|---|
| Connector 2 alone | 13:04:48 – 13:06:33 | — | **119.1 kW** · 288 A at 414 V | closed |
| Connector 1 alone | 13:07:40 – 13:10:30 | **119.2 kW** · 286 A at 417 V | — | closed |
| Connector 1 alone | 13:11:25 – 13:12:49 | **118.6 kW** · 284 A at 417 V | — | closed |
| Connector 2 alone | 13:13:47 – 13:15:58 | — | **118.9 kW** · 284 A at 418 V | closed |
| Both connectors | 13:21:13 – 13:23:39 | **59.5 kW** · 160 A at 371 V | **59.1 kW** · 144 A at 410 V | open |

- The car asked for exactly the announced limit in every single-connector test, so the cabinet limit (120 kW ÷ measured voltage × 1.01) set the power: about 99 % of the 120 kW rating.
- `tieVeto`, `noload` and `shareDegraded` stayed `false` in the whole log: R6 was never opened by mistake.
- The two-car test ended at 13:23:39 because the car on connector 1 reached 90 % state of charge and the cabinet's *SoC Cutoff Guard* stopped it — see [Troubleshooting](#troubleshooting-from-the-logs).

## REV 3 — why connector 1 delivered less than connector 2

Both module groups deliver the same power: whenever R6 stayed closed, a single car got **278 A ≈ 103–104 kW** on either connector.
The difference came from the flow **opening R6 by mistake** in some connector-1 sessions, leaving that connector with only its own two modules for the rest of the session.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/connector1-current-dark.png">
  <img alt="Line chart of connector-1 current in the first 60 s of two sessions on 09 Nov 2026. Session 21:12:47 (R6 closed) ramps to 278 A, about 103 kW. Session 21:32:38 dips to 0 A at 3 s when R6 opens after a false veto and stays at 138 A, about 51 kW. A dotted line marks the expected REV 3 limit of about 318 A." src="docs/images/connector1-current-light.png" width="100%">
</picture>

<sub>Data: vSECC `power-electronics-com-1.log`, 09 Nov 2026 — table in [`docs/data/connector1_current_20261109.csv`](docs/data/connector1_current_20261109.csv).</sub>

**Single-car sessions on 09 Nov 2026**

| Session | Connector | Peak | R6 | CP.py limit burst vs. first module current |
|---|---|---|---|---|
| 20:25:18 ¹ | 1 | 138 A · 50 kW | **vetoed 20:25:21 → open** | burst +1.37 s, current +1.50 s |
| 21:12:47 | 1 | 278 A · 103 kW | closed | current +1.29 s, burst +2.18 s |
| 21:31:30 | 1 | 264 A · 95 kW (30 s session) | closed | current +1.74 s, burst +2.25 s |
| 21:32:38 | 1 | 138 A · 51 kW for 4.3 min | **vetoed 21:32:40 → open 21:32:41** (latched until 21:37:02) | burst +1.38 s, current +1.50 s |
| 21:14:55 · 21:24:00 | 2 | 278 A · 104 kW | closed | current first, burst later (every session) |

<sub>¹ REV 1 flow, before the group-2 address fix. Times are seconds after CurrentDemand started.</sub>

### Root cause

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/rev3-race-dark.png">
  <img alt="Timeline of the race: the CP.py limit burst arrives at +1.38 s, the first module current at +1.50 s. The REV 2 watchdog counts three node runs within the burst, sets tieVeto, ramps to 0 A and opens R6 at +2.85 s, leaving 60 kW / 138 A. The REV 3 watchdog uses real time, resets when current flows at +1.50 s and keeps R6 closed." src="docs/images/rev3-race-light.png" width="100%">
</picture>

1. **FIX#NOLOAD rev1 tripped falsely.** The "R6 closed but no current" watchdog counted how many times *Calculate Power/Current* ran and tripped at 3.
   That node is woken not only by the 1 s tick but by every `topic/connector0`, `limitpower1/2` and `limitcurrent1/2` message — and CP.py sends those five as a burst when the transaction starts.
   Tonhe modules need 1.0–1.9 s after the car asks ≥ 5 A before current flows, so when the burst arrived first the count reached 3 within 0.05 s → `dcl.tieVeto = true` → function 4 opened R6.
   Connector 2 never hit it only because in its sessions the burst happened to arrive after the first current.
2. **kW → A used the wrong voltage.** `_capV` used `max(measured, target)`; the Tesla sends its maximum, 430.4 V, as target for the whole constant-current phase while the battery sits at ~371–373 V.
   120 kW therefore became 278 A (≈ 103 kW real) and 60 kW became 138 A (≈ 51 kW real) on both connectors.

### What REV 3 changes (5 nodes changed, none added or removed)

| Change | Node | Detail |
|---|---|---|
| **FIX#NOLOAD rev2** | Calculate Power/Current | Trips only after **≥ 5 s of continuous < 1 A** while the car asks ≥ 5 A, at least **8 s** after that connector entered charge and **4 s** after R6 closed, never while R6 is being switched (`dcl.tieBusy`). The reason is kept in `dcl.tieVetoReason`. |
| **FIX#SHARE rev2** | Calculate Power/Current | The "helper group delivers 0 A" watchdog had the same count-based weakness (not seen in these logs); now real-time with the same grace, shares from the modules actually available. |
| **FIX#PCAPV rev1** | Calculate Power/Current | While charging, kW → A uses the **measured bus voltage × 1.01** (1.5 V hysteresis). Cable check, pre-charge or an implausible reading (< 0.6 × target) keep the old formula. `pcap_v_source: 'max'` restores it everywhere. |
| New settings | `set min/max limits + sinexcel_cfg (…, rev3)` | `pcap_v_source`, `noload_trip_ms`, `noload_grace_charge_ms`, `noload_grace_tie_ms` |
| **Trace v3** | ARCH2/session trace | `vsecc/pe/arch2` (stored in `vsecc.log`) adds `maxP`, `lp`, `lc`, `conn0`, `vetoWhy`, `noload`, `shareDegraded` |

**Current limits** (CP.py limit 120 kW per connector, car target 430.4 V) — calculated values; the [field test](#field-test--10-nov-2026) measured 284–288 A at 414–418 V (≈ 119 kW) and 160 A at 371 V (≈ 59 kW):

| Situation | REV 2 | REV 3 @ 371 V | REV 3 @ 373 V |
|---|---|---|---|
| One car — R6 closed, 4 modules | 278 A ≈ 103 kW | **320 A ≈ 118.7 kW** | 318 A ≈ 118.6 kW |
| Two cars — R6 open, 2 modules each | 138 A ≈ 51 kW each | **160 A ≈ 59.4 kW each** | 158 A ≈ 58.9 kW each |
| `pcap_v_source: 'max'` | — | 278 A / 138 A (as REV 2) | |

> [!IMPORTANT]
> REV 3 raises the real current from 278 A to about **320 A per connector** at low battery voltage (up to 288 A was measured in the field test at 414 V). Confirm that the CCS cables and connectors are rated for it.
> If not, cap it with `limitcurrent1/2` (CP.py / HMI) or `CURRENT_LIMIT_A` in the config node, or set `pcap_v_source: 'max'`.
> The software ceiling stays at 400 A, as in the original Sinexcel flow. The car (Tesla) reported a maximum of 550 A / 237 kW.

**Sandbox tests** — [`tools/sim_step4.js`](tools/sim_step4.js) runs the real code of *Calculate Power/Current*, *function 4* and the MQTT store nodes from the REV 2 and REV 3 flows with a controllable clock (all pass):

| Case | REV 2 (deployed) | REV 3 |
|---|---|---|
| Replay of 21:32:38 (burst 120 ms before current) | veto at +1.38 s → R6 open → 138 A ≈ 51 kW | no veto, R6 closed → 318 A ≈ 118.6 kW |
| Burst timing swept −600 … +300 ms around the first current | trips whenever the burst comes first | never trips |
| Real no-load after R6 closes (09 Sep pattern) | veto 2.5 s after R6 settled | veto 5.5 s after R6 settled → R6 reopens, connector 2 resumes on its own group |
| No current at all from the start of CurrentDemand | veto at +1.4 s | veto at +8.4 s |
| `tieBusy` held for 20 s | veto during the switch | ignored; veto 5 s after release if still 0 A |
| Group 2 starts 1 s after group 1, with the burst | `shareDegraded` latched at +1.38 s | no latch (a real 0 A helper latches at 8.4 s) |

## How power is shared

| Connector 1 | Connector 2 | R6 | Connector 1 gets | Connector 2 gets |
|---|---|---|---|---|
| car (B / C / D) | free (A) | **closed** | 4 modules · up to 120 kW | — |
| free (A) | car (B / C / D) | **closed** | — | 4 modules · up to 120 kW |
| car | car | open | 2 modules · 60 kW | 2 modules · 60 kW |
| car | fault (E / F) | open | 2 modules · 60 kW | — |
| free | free | open | both announce 120 kW in advance | |

- **Switching (FIX#TIE, function 4):** the wanted state must be stable for 400 ms; `dcl.tieBusy` makes *Head 1/2 V/I* press the current to 0 A; R6 switches when the total current is below **5 A** (after 6 s it switches anyway and warns); 400 ms settle, then current is released. Function 4 is the only writer of `dcl.tieClosed` / `dcl.tieBusy`.
- **Veto (FIX#NOLOAD):** if R6 is closed and the only car gets no current, `dcl.tieVeto` keeps R6 open until both connectors are free again.
- **Share watchdog (FIX#SHARE):** with R6 closed, if the helper group delivers 0 A the primary group takes the whole target (`dcl.shareDegraded`) until R6 opens.
- **Dynamic share (FIX#DYNSHARE, REV 2):** the target is split over the modules that are actually online and not faulted (`sinexcel_state.groups[g].capable_count`).

## Power topology

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/power-topology-dark.png">
  <img alt="Power topology: AC mains feeds group 1 through R1 and group 2 through R2; each group has two Tonhe 30 kW modules; DC bus 1 goes through R3/R4 to connector 1 and DC bus 2 through R7/R8 to connector 2; R6 ties the two buses; the vSECC drives all modules over CAN2." src="docs/images/power-topology-light.png" width="100%">
</picture>

| Relay / input | vSECC I/O | Purpose |
|---|---|---|
| R1 · R2 | `d_out/1` · `d_out/2` | AC (Mag) contactors for group 1 · group 2 — feedback on `d_in/7` · `d_in/6` |
| R3 · R4 | `d_out/3` · `d_out/4` | DC+ / DC− contactors, connector 1 |
| R7 · R8 | `d_out/5` · `d_out/6` | DC+ / DC− contactors, connector 2 |
| R6 | `d_out/7` | DC bus tie (group 1 ↔ group 2) |
| Fan | `d_out/11` | cabinet fan |
| Emergency stop | `d_in/8` | cuts both connectors (`ESTOP_IS_GLOBAL = true`, 400 ms debounce) |

## Control architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/control-architecture-dark.png">
  <img alt="Control architecture: CSMS talks OCPP to CP.py, which publishes limit topics over MQTT to Node-RED. Calculate Power/Current sends limits to pep_ws and the vSECC charging manager; EV targets flow back to Head V/I and Group Set V/I, which drive the Tonhe modules over CAN; parse_tonhe_can returns measured values; function 4 drives R6." src="docs/images/control-architecture-light.png" width="100%">
</picture>

Global names were kept from the Sinexcel flow (`sinexcel_cfg`, `sinexcel_state`, `pm.*`, `pep.*`) so the downstream nodes (Head/Group V/I, Calculate, pep_ws, Monitor, External Fault MQTT) did not need rewiring; the Tonhe settings live in `sinexcel_cfg.tonhe`.

## Tonhe CAN protocol (as used)

CAN2 (`vxcan1`), 125 kbit/s, 29-bit extended IDs, little-endian, monitor address `0xA0`.

| Direction | ID | Content |
|---|---|---|
| module → vSECC | `0x1801A0xx` | status every 0.5 s: state (`00` off · `01` on · `11` fault-off), voltage 0.1 V, current 0.01 A, fault word, PFC byte |
| module → vSECC | `0x0802A0xx` | command confirmation |
| module → vSECC | `0x180BA0xx` | AC phase voltages Va / Vb / Vc + ambient temperature |
| module → vSECC | `0x1C91A0xx` | extended status / fault |
| vSECC → module | `0x0806{addr}A0` | **main command**: start `AA` / stop `55`, mode byte, voltage 0.1 V, current 0.01 A |
| vSECC → all | `0x0803FFA0` | broadcast stop |
| vSECC → all | `0x1805FFA0` | timing frame, every 5 s |

`0x1004FFA0` is not used (limited to 750 V). New fault codes in *External Fault MQTT*: `THF` (status fault word) F75/F76 · `THP` (PFC byte) F77/F78 · `THX` (extended fault) F85/F86 · `FAULT_OFF` suffix 11.

## Module setup

| Position | CAN address | Module display |
|---|---|---|
| Connector 1 – module 1 | 1 | `01H` |
| Connector 1 – module 2 | 2 | `02H` |
| Connector 2 – module 1 | **3** | `03H` |
| Connector 2 – module 2 | **4** | `04H` |

All modules: group `G01`, running mode `-A-` (automatic), group mode `-F-` (fixed), protocol `P02` (Tonhe).
The setup document lists 5, 6 for connector 2, but the cabinet uses **3, 4** (found in the logs on 09 Nov 2026). If the addresses change, edit `group_addr` — the Fault Monitor reports `Tonhe address not in config: X` otherwise.

## Configuration

Node `set min/max limits + sinexcel_cfg (Tonhe 2+2x30kW, G2 addr 3,4, rev3)` in tab `phoenix_contact_charx`:

| Setting | Default | Meaning |
|---|---|---|
| `tonhe.group_addr` | `{1:[1,2], 2:[3,4]}` | CAN addresses per group |
| `tonhe.mode_byte` | `0x00` | byte 1 of `0x0806` (spec table: `0x00`, appendix example: `0x01`); `0x00` works on this cabinet |
| `tonhe.stop_below_V` | 60 | a set-point below this sends stop (`0x55`) instead, e.g. during welding detection |
| `tonhe.refresh_ms` · `timing_period_ms` | 500 · 5000 | command refresh (keep-alive) · timing frame |
| `tonhe.online_ms` · `stale_ms` | 3000 · 5000 | module online · stale |
| `MODULE_MAX_POWER` · `_CURRENT` · `_VOLTAGE` | 30 kW · 100 A · 1000 V | per module — check the nameplate |
| `CURRENT_LIMIT_A` | 400 | software ceiling per connector |
| `pcap_v_source` | `'measured'` | REV 3 kW → A voltage; `'max'` = REV 2 formula |
| `noload_trip_ms` | 5000 | REV 3 no-load time before a veto |
| `noload_grace_charge_ms` | 8000 | REV 3 grace after the connector enters charge |
| `noload_grace_tie_ms` | 4000 | REV 3 grace after R6 closed |

## Repository contents

| File | What it is |
|---|---|
| [`flows_Bhutan_120kW_Tonhe_REV3_public.json`](flows_Bhutan_120kW_Tonhe_REV3_public.json) | the complete Node-RED flow, **REV TONHE-BHUTAN-3** — public copy ([what was changed](#public-copy--what-was-changed)) |
| [`docs/images/`](docs/images) | README diagrams, charts and the animation (light and dark) |
| [`docs/data/`](docs/data) | the measured series behind the two charts (CSV) |
| [`tools/`](tools) | flow validation, sandbox and log tools |
| [`LICENSE`](LICENSE) | MIT |

Earlier revisions (original Sinexcel flow, REV 1, REV 2) and the cabinet backups are not published.

**Flow tabs**

| Tab | Role |
|---|---|
| `phoenix_contact_charx` | power-module layer (historic name): Tonhe CAN TX/RX, Head/Group V/I, *Calculate Power/Current*, *function 4* (R6), Fault Monitor, traces |
| `pep_ws(Gun1)` · `pep_ws2(Gun2)` | power-electronics websocket to the vSECC charging manager, one per connector |
| `CCS1_connector_check` · `CCS2_connector_check` | per-connector session logic: authorization (FIX#AUTHBOUNCE, FIX#AUTHWD), RemoteStart / Stop, contactors |
| `Digital_i/o` | AC and DC contactors, R6, fan, emergency stop, Mag feedback |
| `MQTT To HMI` · `HMI_flow` · `RFID Routing` | DWIN HMI screen, start / stop buttons, QR display, RFID (FIX#HMIFLAGS); a disabled copy of `RFID Routing` is kept |
| `External Fault MQTT` | exact fault / status values → raised / cleared events with OCPP 1.6J-ready error codes |
| `imd_simulation` · `BlueJay_IMD_Test` | insulation monitoring (Bluejay GYDCG-UBCS1 IMD × 2, switched by CableCheck) |
| `SoC Cutoff 90%` | hard stop at 90 % state of charge (FIX#SOC) |
| `Monitor` · `Loop Lag Monitor` · `dashboard` | portable monitor snapshot (auto-detects the module brand), event-loop lag alarm, Node-RED dashboard |
| `Flow 2` | session-state test injects and helpers |

## Version history

| Revision | Date | Changes |
|---|---|---|
| original | 15 Sep 2026 | Sinexcel SER100040K3B flow |
| REV 1 · step 1 | 09 Nov 2026 | Tonhe CAN layer (parse, frame creation, Set V/I, keep-alive, Fault Monitor) |
| REV 1 · step 2 | 09 Nov 2026 | + fallback values, External Fault MQTT Tonhe codes — deployed 20:24 |
| REV 2 · step 3 | 09 Nov 2026 | group 2 = CAN addr 3, 4; FIX#DYNSHARE; FIX#AUTHBOUNCE / AUTHWD; FIX#HMIFLAGS; AC-off fault handling; `vsecc/pe/arch2` + `tonhe_health` traces — running since 21:11 |
| **REV 3 · step 4** | 10 Nov 2026 | FIX#NOLOAD rev2, FIX#SHARE rev2, FIX#PCAPV, trace v3 — see [REV 3](#rev-3--why-connector-1-delivered-less-than-connector-2). Deployed 10 Nov 11:11, [field-tested](#field-test--10-nov-2026): 119 kW per connector, 59 kW each with two cars. **This is the published flow.** |

## Deploying a flow

1. **Set your own values first** (the public copy carries placeholders): `ADMIN_PASSWORD` in the two *Admin Numpad* function nodes, and the server address of the broker nodes `SukritJa_Broker` and `MON out (dashboard central)` — or disable the nodes that use them.
2. Open the Node-RED editor on the vSECC → menu → **Import** → select the file.
3. When asked about existing nodes choose **Replace** if the cabinet already runs an earlier revision of this flow.
4. **Deploy → Full**.
5. Enter the MQTT broker password if the broker needs one — exports never carry credentials.
6. Check the node status of *Calculate Power/Current* and *function 4*, and that `vsecc/pe/tonhe_health` keeps arriving every 30 s.

> [!WARNING]
> The flow is written for this cabinet: its relays, I/O map, module addresses and HMI. Do not import it into a different cabinet type without reviewing every tab.

## Troubleshooting from the logs

Every `vsecc/#` MQTT message is written to `vsecc.log` (as "NOT HANDLED!"), so the Node-RED traces travel with the vSECC log download.

| Symptom | Look at | Meaning |
|---|---|---|
| one car gets only ~60 kW | `vsecc/pe/arch2` → `"tieVeto":true`, `vetoWhy` | R6 vetoed; `vetoWhy` shows target, measured current and timing |
| present current = half the target | `vsecc/pe/module_fault` → `address not in config` | module address does not match `group_addr` |
| FAULT-OFF / undervoltage after unplugging | `module_fault` with an "AC off" warning | AC (Mag) contactor open, modules unpowered — expected, not sent as a fault |
| car stays at 0 A in CurrentDemand | `vsecc/pe/arch2` → `hold:true`, `start:false` | ARCH2 hold, waiting for RemoteStart / Start button |
| session stops by itself near 90 % | `charging-manager-N.log` → `Charging stop requested, source: MQTT` 3–4 s after `EVRESSOC: 90%`; in `vsecc/pe/arch2`: `start:true→false`, `hold:true`, `hmi_stop` still `false` | *SoC Cutoff Guard (90%)* in tab `SoC Cutoff 90%` (`TARGET_SOC = 90`, 3 s confirm). It latches until the cable is unplugged. |
| who stopped a session | `vsecc/pe/arch2` | `hmi_stop:true` = `topic/RemoteStop{n}` from CP.py (OCPP) · `manualStop:true` = STOP on the HMI screen · no stop request but `SessionStop` in the charging manager = the car ended it |
| which limit the car saw | `power-electronics-com-N.log` (`dynamicLimits`) · `charging-manager-2.log` (`EVSE Charge Limits reported to the EV`, connector 2 logs at DEBUG level) | after REV 3, one car should show ~318–320 A / 120 kW |

Also seen in the logs: every time CP.py (re)connects to the broker it publishes `RemoteStop` for both connectors, and it publishes `limitpower1/2 = 60 kW` while a connector is idle and ≥ 120 kW once the transaction starts, so the car first sees 60 kW during ChargeParameterDiscovery — worth checking the default profile in CP.py / the CSMS.

## Tools

| Script | Use |
|---|---|
| [`tools/validate_flow.js`](tools/validate_flow.js) | `node tools/validate_flow.js <flow.json>` — JSON, wires, links and every function node compiles. The 44 `DANGLING LINK` lines are already in the original flow. |
| [`tools/sim_step4.js`](tools/sim_step4.js) | `node tools/sim_step4.js <REV 2 flow> <REV 3 flow>` — fake-clock sandbox for the REV 3 cases above. It needs the REV 2 flow as the baseline, which is not published; the script is here so the test cases can be read. |
| [`tools/pe_sessions.py`](tools/pe_sessions.py) | `python3 tools/pe_sessions.py <vsecc_logs folder>` — one line per charging session (target / measured current, kW, limits) |
| [`tools/extract_series.py`](tools/extract_series.py) · [`extract_field.py`](tools/extract_field.py) | time series of one session (seconds since CurrentDemand) · per-second power of both connectors, for charts |
| [`tools/arch2_diff.py`](tools/arch2_diff.py) | `python3 tools/arch2_diff.py <vsecc.log> [from] [to]` — prints the `vsecc/pe/arch2` trace as key-by-key changes |
| [`tools/sanitize_flow.js`](tools/sanitize_flow.js) | `node tools/sanitize_flow.js <in.json> <out.json>` — makes the public copy: placeholder PIN and broker address, then checks that neither is left in the output |
| [`tools/make_images.py`](tools/make_images.py) · [`make_chart.py`](tools/make_chart.py) · [`make_field_chart.py`](tools/make_field_chart.py) · [`make_gif.py`](tools/make_gif.py) | regenerate the README images (Inter font, rsvg-convert, ImageMagick, matplotlib, Pillow) |

## Public copy — what was changed

The published flow is the REV 3 flow as delivered to the cabinet, with six fields changed by [`tools/sanitize_flow.js`](tools/sanitize_flow.js). Everything else — all 1437 nodes, their ids and wiring — is identical.

| Where | Public copy |
|---|---|
| `ADMIN_PASSWORD` in *Admin Numpad* (tab `RFID Routing`) and *Admin Numpad (login optional)* (tab `MQTT To HMI`) | `"0000"` — set your own PIN |
| Server of the broker nodes `SukritJa_Broker` and `MON out (dashboard central)` | `broker.example.invalid` — set your own broker |
| Client id of `SukritJa_Broker` | empty (Node-RED generates one) |
| Info text of the comment node in `External Fault MQTT` | broker address replaced |

Local addresses stay as they are: `172.17.0.1` (the vSECC's own MQTT broker) and `192.168.3.11` (the vSECC on the cabinet LAN). MQTT passwords are never part of a Node-RED export, and `flows_cred.json` is excluded by [`.gitignore`](.gitignore).

## Safety and license

This flow controls 1000 V DC power electronics and contactors. It is published as a worked example of a Tonhe conversion with bus-tie power sharing, not as a ready-made product: review and test it against your own hardware, wiring and protection before using any part of it.

Released under the [MIT License](LICENSE), without warranty of any kind.
