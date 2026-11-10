# Troubleshooting and tools

[← Back to the README](../README.md)

How to read what the cabinet did from the vSECC logs, and the scripts used for validation and log analysis.

## Troubleshooting from the logs

`CP.py` in this guide is the OCPP charge-point client on the EdgeBox; it is a separate program and not part of this repository.

Every `vsecc/#` MQTT message is written to `vsecc.log` (as "NOT HANDLED!"), so the Node-RED traces travel with the vSECC log download.

| Symptom | Look at | Meaning |
|---|---|---|
| one car gets only ~60 kW | `vsecc/pe/arch2` → `"tieVeto":true`, `vetoWhy` | R6 vetoed; `vetoWhy` shows target, measured current and timing |
| present current = half the target | `vsecc/pe/module_fault` → `address not in config` | module address does not match `group_addr` |
| FAULT-OFF / undervoltage after unplugging | `module_fault` with an "AC off" warning | AC (Mag) contactor open, modules unpowered — expected, not sent as a fault |
| car stays at 0 A in CurrentDemand | `vsecc/pe/arch2` → `hold:true`, `start:false` | ARCH2 hold, waiting for RemoteStart / Start button |
| session stops by itself near 90 % | `charging-manager-N.log` → `Charging stop requested, source: MQTT` 3–4 s after `EVRESSOC: 90%`; in `vsecc/pe/arch2`: `start:true→false`, `hold:true`, `hmi_stop` still `false` | *SoC Cutoff Guard (90%)* in tab `SoC Cutoff 90%` (`TARGET_SOC = 90`, 3 s confirm). It latches until the cable is unplugged. The tab is disabled in the published flow, so this applies only if you enable it. |
| who stopped a session | `vsecc/pe/arch2` | `hmi_stop:true` = `topic/RemoteStop{n}` from CP.py (OCPP) · `manualStop:true` = STOP on the HMI screen · no stop request but `SessionStop` in the charging manager = the car ended it |
| which limit the car saw | `power-electronics-com-N.log` (`dynamicLimits`) · `charging-manager-2.log` (`EVSE Charge Limits reported to the EV`, connector 2 logs at DEBUG level) | after REV 3, one car should show ~318–320 A / 120 kW |

Also seen in the logs: every time CP.py (re)connects to the broker it publishes `RemoteStop` for both connectors, and it publishes `limitpower1/2 = 60 kW` while a connector is idle and ≥ 120 kW once the transaction starts, so the car first sees 60 kW during ChargeParameterDiscovery — worth checking the default profile in CP.py / the CSMS.

## Tools

Paths are relative to the repository root.

| Script | Use |
|---|---|
| [`tools/validate_flow.js`](../tools/validate_flow.js) | `node tools/validate_flow.js <flow.json>` — JSON, wires, links and every function node compiles. The 44 `DANGLING LINK` lines are already in the original flow. |
| [`tools/sim_step4.js`](../tools/sim_step4.js) | `node tools/sim_step4.js <REV 2 flow> <REV 3 flow>` — fake-clock sandbox for the cases in the [REV 3 engineering notes](ENGINEERING_NOTES_REV3.md). It needs the REV 2 flow as the baseline, which is not published; the script is here so the test cases can be read. |
| [`tools/pe_sessions.py`](../tools/pe_sessions.py) | `python3 tools/pe_sessions.py <vsecc_logs folder>` — one line per charging session (target / measured current, kW, limits) |
| [`tools/extract_series.py`](../tools/extract_series.py) · [`extract_field.py`](../tools/extract_field.py) | time series of one session (seconds since CurrentDemand) · per-second power of both connectors, for charts |
| [`tools/arch2_diff.py`](../tools/arch2_diff.py) | `python3 tools/arch2_diff.py <vsecc.log> [from] [to]` — prints the `vsecc/pe/arch2` trace as key-by-key changes |
| [`tools/sanitize_flow.js`](../tools/sanitize_flow.js) | `node tools/sanitize_flow.js <in.json> <out.json>` — makes the public copy: placeholder PINs and broker address, then checks that none is left in the output |
| [`tools/flow_diff.js`](../tools/flow_diff.js) | `node tools/flow_diff.js <old.json> <new.json> [--lines]` — nodes added, removed and changed between two flow files |
| [`tools/make_images.py`](../tools/make_images.py) · [`make_chart.py`](../tools/make_chart.py) · [`make_field_chart.py`](../tools/make_field_chart.py) · [`make_gif.py`](../tools/make_gif.py) · [`make_hero.py`](../tools/make_hero.py) | regenerate the README images (Inter font, rsvg-convert, ImageMagick, matplotlib, Pillow) |
