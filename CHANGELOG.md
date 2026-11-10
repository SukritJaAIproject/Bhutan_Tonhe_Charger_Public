# Changelog

All revisions of the Tonhe flow for the Bhutan 120 kW cabinet. Times are local (UTC+7).

## REV 3 — 10 Nov 2026 · published

Flow revision `TONHE-BHUTAN-3`. Deployed in the cabinet at 11:11 and [field-tested](README.md#field-results) the same day: 119 kW on each connector alone, 59 kW each with two cars.

- **FIX#NOLOAD rev2** — the "bus tie closed but no current" watchdog now decides on real time (5 s of continuous < 1 A, with start-up grace) instead of counting node runs. This removes the false veto that left connector 1 at 60 kW.
- **FIX#SHARE rev2** — the "helper group delivers 0 A" watchdog uses the same real-time rule.
- **FIX#PCAPV rev1** — kW → A conversion uses the measured bus voltage, so the car is offered the full 120 kW instead of about 103 kW.
- **Trace v3** — `vsecc/pe/arch2` adds `maxP`, `lp`, `lc`, `conn0`, `vetoWhy`, `noload`, `shareDegraded`.

Details: [REV 3 engineering notes](docs/ENGINEERING_NOTES_REV3.md).

## REV 2 — 09 Nov 2026

Running in the cabinet from 09 Nov 21:11 until REV 3.

- Group 2 uses CAN addresses 3 and 4 (found in the logs).
- **FIX#DYNSHARE** — the target is split over the modules that are actually online and not faulted.
- **FIX#AUTHBOUNCE / FIX#AUTHWD** — no duplicate authorization when the control pilot bounces on plug-in; a watchdog re-sends the token if authorization is stuck.
- **FIX#HMIFLAGS** — the HMI button flags are cleared when the cable is unplugged.
- Module faults caused by an open AC contactor are no longer reported as faults.
- New traces: `vsecc/pe/arch2`, `vsecc/pe/tonhe_health`.

## REV 1 — 09 Nov 2026

First Tonhe version, deployed 09 Nov 20:24.

- Step 1: Tonhe CAN layer — frame parsing, command frames, group Set V/I, keep-alive, Fault Monitor.
- Step 2: fallback values and Tonhe fault codes in *External Fault MQTT*.

## Original — 15 Sep 2026

Sinexcel SER100040K3B flow, the starting point of the conversion.

---

Only REV 3 is published in this repository.
