'use strict';
// Fake-clock sandbox for REV TONHE-BHUTAN-3 (step4).
// Runs the real Node-RED function code of "Calculate Power/Current", "function 4" (R6 state machine)
// and the MQTT "Store ..." nodes from both flows, with a controllable Date.now(), against a simple
// plant model of 2+2 Tonhe modules (1.0-1.9 s start-up delay, 150 A/s slew) and an EV.
// usage: node sim_step4.js <deployed_backup.json (rev1)> <step4.json (rev2)>
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const TAB = 'fa01cebbd0f3dec2';
const T0 = Date.UTC(2026, 10, 9, 14, 32, 8);      // session A: CurrentDemand at T0+30 s
const V_BAT = 373;                                // measured bus voltage during CC (log 09/11: 371-373 V)
const FLOWS = { rev1: process.argv[2], rev2: process.argv[3] };
const LABEL = { rev1: 'deployed (rev1)', rev2: 'step4    (rev2)' };
const cache = {};
const flowOf = p => cache[p] || (cache[p] = JSON.parse(fs.readFileSync(p, 'utf8')));
const fmt = ms => (ms === null || ms === undefined) ? '-' : (ms / 1000).toFixed(2) + ' s';
let failures = 0;
function check(cond, text) { console.log('   ' + (cond ? 'PASS' : 'FAIL') + '  ' + text); if (!cond) failures++; }

function makeEnv(rev) {
    const flow = flowOf(FLOWS[rev]);
    const one = (name, re) => {
        const r = flow.filter(n => n.z === TAB && n.type === 'function' && (re ? re.test(n.name || '') : n.name === name));
        if (r.length !== 1) throw new Error(rev + ': ' + (name || re) + ' -> ' + r.length);
        return r[0];
    };
    const N = {
        cfg: one(null, /^set min\/max limits \+ sinexcel_cfg/), calc: one('Calculate Power/Current'), f4: one('function 4'),
        trace: one('ARCH2/session trace (on change)'),
        conn0: one('Store connector0'), lp1: one('Store limitpower1'), lp2: one('Store limitpower2'),
        lc1: one('Store limitcurrent1'), lc2: one('Store limitcurrent2'), cp1: one('Store cp_state1'), cp2: one('Store cp_state2')
    };
    const E = { rev, T: T0, G: new Map(), warns: [], N, calcRuns: 0 };
    const ctxs = new Map(), fns = new Map(), flowMap = new Map();
    class FakeDate extends Date {
        constructor(...a) { if (a.length) super(...a); else super(E.T); }
        static now() { return E.T; }
    }
    const gctx = { get: k => E.G.get(k), set: (k, v) => { E.G.set(k, v); } };
    const fctx = { get: k => flowMap.get(k), set: (k, v) => flowMap.set(k, v) };
    E.run = (n, msg) => {
        if (!fns.has(n.id)) fns.set(n.id, vm.runInNewContext('(function (msg, node, context, flow, global, Date) {\n' + n.func + '\n})', { Buffer }));
        if (!ctxs.has(n.id)) { const m = new Map(); ctxs.set(n.id, { get: k => m.get(k), set: (k, v) => m.set(k, v) }); }
        const node = {
            warn: m => E.warns.push({ t: E.T, n: n.name, m: typeof m === 'string' ? m : JSON.stringify(m) }),
            error: m => E.warns.push({ t: E.T, n: n.name, m: 'ERROR ' + m }), status: () => {}, send: () => {}, log: () => {}
        };
        return fns.get(n.id)(msg || { payload: '' }, node, ctxs.get(n.id), fctx, gctx, FakeDate);
    };
    E.g = k => E.G.get(k);
    E.s = (k, v) => E.G.set(k, v);
    E.calc = () => { E.calcRuns++; return E.run(N.calc, { payload: 'x' }); };
    E.f4 = () => E.run(N.f4, { payload: {} });
    // MQTT "Store ..." node -> wired straight into Calculate (cp_state also reaches function 4 via link "cp_state")
    E.store = (which, payload) => { E.run(N[which], { payload }); E.calc(); if (which === 'cp1' || which === 'cp2') E.f4(); };
    E.setCfg = (k, v) => { const c = E.g('sinexcel_cfg'); c[k] = v; E.s('sinexcel_cfg', c); };
    return E;
}

function boot(E, lp) {
    E.run(E.N.cfg, { payload: 1 });
    E.s('emerActive', false); E.s('arch2Enabled', true);
    E.store('cp1', 'state_a'); E.store('cp2', 'state_a');
    E.store('conn0', { connector0: 0 });
    E.store('lp1', { limitpower: lp }); E.store('lp2', { limitpower: lp });     // CP.py idle publish = 60 kW (log 21:32:03)
    E.store('lc1', { limitcurrent: 400 }); E.store('lc2', { limitcurrent: 400 });
    E.f4(); E.calc();
}
// CP.py burst at transaction start: connector0 + limitpower1/2 + limitcurrent1/2 (5 MQTT msgs -> 5 Calculate runs in ~20 ms)
function burstEvents(E, at, lp) {
    const items = [['conn0', { connector0: 0 }], ['lp1', { limitpower: lp }], ['lp2', { limitpower: lp }],
        ['lc1', { limitcurrent: 400 }], ['lc2', { limitcurrent: 400 }]];
    return items.map(([w, p], k) => ({ at: at + 5 * k, fn: () => E.store(w, p) }));
}

// ---------------- plant: EV + Tonhe groups ----------------
function newHead(o) {
    return { phase: '', tCD: 0, tReq5: 0, I: 0, firstDelay: o.firstDelay || 1500,
        wish: o.wish || (tau => tau < 1 ? 12 : Math.min(500, 41 + (tau - 1) * 60)) };   // log: 12 A -> 41 A -> ramps
}
function makePlant(o) {
    return { h: { 1: newHead(o.h1 || {}), 2: newHead(o.h2 || {}) }, noLoad: o.noLoad || (() => false),
        vetoAt: null, vetoWhy: '', sdAt: null, r6: [], lastTie: 'init', maxI: { 1: [], 2: [] } };
}
function setPhase(E, P, h, phase) {
    const sfx = h === 1 ? '' : '2', H = P.h[h];
    H.phase = phase;
    E.s('pep.charging_state' + sfx, phase);
    E.s('session_state_head' + h, 'VSECCLIB_SST_DIN_' + ({ cableCheck: 'CableCheck', preCharge: 'PreCharge', charge: 'CurrentDemand', '': 'SessionStop' }[phase]));
    if (phase === 'charge') H.tCD = E.T;
    E.calc();                                     // link "session_state changed"
}
function plantStep(E, P, dt) {
    const tie = E.g('dcl.tieClosed') === true, busy = E.g('dcl.tieBusy') === true;
    for (const h of [1, 2]) {
        const H = P.h[h], sfx = h === 1 ? '' : '2';
        let tgt = 0;
        if (H.phase === 'charge') {
            tgt = Math.min(H.wish((E.T - H.tCD) / 1000), Number(E.g('pm.max_current' + sfx)) || 0);   // EV respects EVSE max current
            if (tgt >= 5 && !H.tReq5) H.tReq5 = E.T;
        } else H.tReq5 = 0;
        E.s('pep.target_current' + sfx, tgt);
        E.s('pep.target_voltage' + sfx, H.phase ? 430.4 : 0);          // Tesla: target = 430.4 V for the whole session
        let want = (H.phase === 'charge' && E.g('holdActive' + h) !== true && !busy) ? tgt : 0;  // tieBusy: Head V/I presses 0 A
        if (want > 0 && (!H.tReq5 || E.T - H.tReq5 < H.firstDelay)) want = 0;   // Tonhe start-up delay
        if (want > 0 && P.noLoad(h, tie, E)) want = 0;                          // broken DC path
        const up = 150 * dt / 1000, dn = 400 * dt / 1000;
        H.I = want > H.I ? Math.min(want, H.I + up) : Math.max(want, H.I - dn);
    }
    const a = P.h[1].I, b = P.h[2].I;
    E.s('pm.measured_current', tie ? (a + b) / 2 : a);                // R6 closed: DYNSHARE 2:2 over both groups
    E.s('pm.measured_current2', tie ? (a + b) / 2 : b);
    const on1 = !!P.h[1].phase, on2 = !!P.h[2].phase;
    E.s('pm.measured_voltage', (on1 || (tie && on2)) ? V_BAT : 0);
    E.s('pm.measured_voltage2', (on2 || (tie && on1)) ? V_BAT : 0);
}
function observe(E, P) {
    const rel = E.T - T0;
    if (E.g('dcl.tieVeto') === true && P.vetoAt === null) { P.vetoAt = rel; P.vetoWhy = String(E.g('dcl.tieVetoReason') || ''); }
    if (E.g('dcl.shareDegraded') === true && P.sdAt === null) P.sdAt = rel;
    const tie = E.g('dcl.tieClosed');
    if (tie !== P.lastTie) { P.r6.push([rel, tie]); P.lastTie = tie; }
}
function runTimeline(E, P, untilMs, events) {
    events = events.slice().sort((x, y) => x.at - y.at);
    let i = 0;
    const DT = 10;
    for (let t = 0; t <= untilMs; t += DT) {
        while (i < events.length && events[i].at <= t) { E.T = T0 + events[i].at; events[i].fn(); i++; observe(E, P); }
        E.T = T0 + t;
        plantStep(E, P, DT);
        if (t % 250 === 0) E.f4();                                    // link "pep_ws values updated"
        if (t >= 370 && (t - 370) % 1000 === 0) E.calc();             // inject "ARCH2: recalc limits ทุก 1 วิ"
        observe(E, P);
    }
}
const r6str = (P, from) => P.r6.filter(([t]) => t >= from).map(([t, v]) => (v ? 'CLOSE' : 'OPEN') + '@' + fmt(t)).join(', ') || 'no change';
const kW = I => (I * V_BAT / 1000).toFixed(1);

// ======================= A) H1 solo session, CP.py burst vs first current =======================
function sessionH1(rev, o) {
    const E = makeEnv(rev), P = makePlant({ h1: { firstDelay: o.firstDelay }, noLoad: o.noLoad });
    const CD = 30000;
    const ev = [
        { at: 0, fn: () => boot(E, 60000) },
        { at: 2000, fn: () => E.store('cp1', 'state_b') },
        { at: 5000, fn: () => E.s('startCommanded1', true) },                     // RemoteStart1 (ARCH2)
        { at: 6000, fn: () => { E.store('cp1', 'state_c'); setPhase(E, P, 1, 'cableCheck'); } },
        { at: 20000, fn: () => setPhase(E, P, 1, 'preCharge') },
        { at: CD, fn: () => setPhase(E, P, 1, 'charge') },
        ...burstEvents(E, CD + o.burstAt, 120000)
    ];
    runTimeline(E, P, CD + (o.until || 90000), ev);
    return { E, P, CD };
}
function reportSession(tag, r) {
    const { E, P, CD } = r;
    const I = P.h[1].I;
    console.log(`   ${LABEL[E.rev]}: tieVeto ${P.vetoAt === null ? 'never' : 'at CD+' + fmt(P.vetoAt - CD)}; R6 after CD: ${r6str(P, CD)}; `
        + `pm.max_current=${E.g('pm.max_current')} A, pm.max_power=${E.g('pm.max_power') / 1000} kW -> H1 ${I.toFixed(0)} A = ${kW(I)} kW`);
    if (P.vetoWhy) console.log('      vetoWhy: ' + P.vetoWhy);
    if (process.env.DUMP) E.warns.filter(w => w.t - T0 >= CD - 1000).forEach(w => console.log('      [' + fmt(w.t - T0 - CD) + ' ' + w.n + '] ' + w.m.slice(0, 160)));
    return { veto: P.vetoAt !== null, vetoRel: P.vetoAt === null ? null : P.vetoAt - CD, I, maxI: E.g('pm.max_current'), tie: E.g('dcl.tieClosed') };
}

console.log('== A) ซ้ำเหตุการณ์ 21:32:38 หัว 1: ชุด limit CP.py มาถึง CD+1.38 s ก่อนกระแสแรก CD+1.50 s');
const A = {};
for (const rev of ['rev1', 'rev2']) A[rev] = reportSession('A', sessionH1(rev, { burstAt: 1380, firstDelay: 1500 }));
check(A.rev1.veto && A.rev1.vetoRel < 2000, 'rev1 ตัด R6 ผิดพลาดทันทีที่ชุด limit มาถึง (เหมือน log)');
check(A.rev1.maxI === 138 && Math.round(A.rev1.I) === 138, 'rev1 หัว 1 เหลือ 138 A ≈ 51 kW (ตรงกับ log 21:32:38-21:36:58)');
check(!A.rev2.veto && A.rev2.tie === true, 'rev2 ไม่ตัด R6, บัสขนานตลอด session');
check(A.rev2.maxI === 318 && Math.round(A.rev2.I) === 318, 'rev2 หัว 1 ได้ 318 A ≈ 118.6 kW');

console.log('== A\') session แบบ 21:12:47: กระแสแรก CD+1.29 s ก่อนชุด limit CD+2.18 s');
const A2 = {};
for (const rev of ['rev1', 'rev2']) A2[rev] = reportSession('A2', sessionH1(rev, { burstAt: 2180, firstDelay: 1290 }));
check(!A2.rev1.veto && A2.rev1.maxI === 278, 'rev1 ไม่ตัด R6 แต่ได้แค่ 278 A ≈ 103.7 kW (สูตร V = max(วัด, target 430.4))');
check(!A2.rev2.veto && A2.rev2.maxI === 318, 'rev2 ได้ 318 A ≈ 118.6 kW');

console.log('== A\'\') ไล่ระยะห่าง: ชุด limit มาก่อนกระแสแรกกี่ ms ถึงจะ trip (ticks เฟส 0.37 วิ)');
for (const rev of ['rev1', 'rev2']) {
    const rows = [];
    for (const lead of [-600, -300, -120, 0, 120, 300]) {     // burstAt - firstCurrent
        const r = sessionH1(rev, { burstAt: 1500 + lead, firstDelay: 1500, until: 15000 });
        rows.push((lead >= 0 ? '+' : '') + lead + 'ms:' + (r.P.vetoAt === null ? 'ok' : 'TRIP'));
    }
    console.log('   ' + LABEL[rev] + ' (burst - first current) ' + rows.join('  '));
    if (rev === 'rev2') check(rows.every(x => x.endsWith('ok')), 'rev2 ไม่ trip ไม่ว่าชุด limit จะมาเมื่อไร');
}

// ======================= B) เหตุจริง 09/09: หัว 1 ถอด -> R6 ปิด -> หัว 2 จ่ายไม่ออก =======================
console.log('== B) no-load จริงหลัง R6 ปิด (แบบ 09/09 21:40:41): หัว 2 ชาร์จ 120 A, หัว 1 ถอดที่ 60 s, เส้นทาง DC ขาดเมื่อขนาน');
const B = {};
for (const rev of ['rev1', 'rev2']) {
    const E = makeEnv(rev);
    const P = makePlant({ h1: { wish: () => 120 }, h2: { wish: () => 120 }, noLoad: (h, tie) => h === 2 && tie });
    const ev = [
        { at: 0, fn: () => boot(E, 120000) },
        { at: 1000, fn: () => { E.s('startCommanded1', true); E.s('startCommanded2', true); E.store('cp1', 'state_c'); E.store('cp2', 'state_c'); } },
        { at: 3000, fn: () => { setPhase(E, P, 1, 'charge'); setPhase(E, P, 2, 'charge'); } },
        { at: 60000, fn: () => { setPhase(E, P, 1, ''); E.s('startCommanded1', false); E.store('cp1', 'state_a'); } }
    ];
    let busyOff = null;
    const ev2 = ev.concat([{ at: 60001, fn: () => {} }]);
    runTimeline(E, P, 100000, ev2);
    const close = P.r6.find(([t, v]) => t >= 60000 && v === true);
    const reopen = P.r6.find(([t, v]) => close && t > close[0] && v === false);
    const settleEnd = close ? close[0] + 400 : null;
    B[rev] = { close: close && close[0], veto: P.vetoAt, reopen: reopen && reopen[0], I2: P.h[2].I };
    console.log(`   ${LABEL[rev]}: R6 ${r6str(P, 60000)}; tieVeto at ${fmt(P.vetoAt)} (= R6 ปิด+settle ${P.vetoAt === null ? '-' : fmt(P.vetoAt - settleEnd)}); หัว 2 ตอนจบ ${P.h[2].I.toFixed(0)} A`);
    if (P.vetoWhy) console.log('      vetoWhy: ' + P.vetoWhy);
}
check(B.rev2.veto !== null && B.rev2.veto - (B.rev2.close + 400) >= 5000 && B.rev2.veto - (B.rev2.close + 400) <= 6100,
    'rev2 ยังจับ no-load จริงได้ ~5-6 วิหลัง R6 ปิดเสร็จ');
check(B.rev2.reopen !== null && B.rev2.I2 > 100, 'rev2 เปิด R6 กลับ -> หัว 2 กลับมาจ่ายด้วย G2');

// ======================= C) no-load ตั้งแต่เริ่ม CurrentDemand (R6 ปิดอยู่) =======================
console.log('== C) no-load ตั้งแต่เริ่ม CurrentDemand (หัว 1 solo, R6 ปิด, เส้นทาง DC ขาดเมื่อขนาน)');
const C = {};
for (const rev of ['rev1', 'rev2']) {
    const r = sessionH1(rev, { burstAt: 1380, firstDelay: 1500, until: 30000, noLoad: (h, tie) => h === 1 && tie });
    C[rev] = { vetoRel: r.P.vetoAt === null ? null : r.P.vetoAt - r.CD, I: r.P.h[1].I };
    console.log(`   ${LABEL[rev]}: tieVeto at CD+${fmt(C[rev].vetoRel)}; R6 ${r6str(r.P, r.CD)}; หัว 1 ตอนจบ ${C[rev].I.toFixed(0)} A`);
}
check(C.rev2.vetoRel !== null && C.rev2.vetoRel >= 8000 && C.rev2.vetoRel <= 9100, 'rev2 ตัดสินหลังพ้นช่วงผ่อนผัน 8 วิ แล้วหัว 1 ได้กระแสจาก G1');

// ======================= D) tieBusy (กำลังสับ R6) ห้ามนับ =======================
console.log('== D) tieBusy ค้าง 20 วิ (กดกระแส 0 A ตั้งใจ) + ชุด limit 2 รอบ แล้วปล่อย tieBusy แต่กระแสยังไม่มา');
const D = {};
for (const rev of ['rev1', 'rev2']) {
    const E = makeEnv(rev); E.T = T0; boot(E, 120000);
    Object.entries({ cp_state_head1: 'state_c', cp_state_head2: 'state_a', 'dcl.tieClosed': true, 'dcl.tieBusy': true, startCommanded1: true,
        'pep.charging_state': 'charge', session_state_head1: 'VSECCLIB_SST_DIN_CurrentDemand', 'pep.target_current': 50, 'pep.target_voltage': 430.4,
        'pm.measured_current': 0, 'pm.measured_current2': 0, 'pm.measured_voltage': 373 }).forEach(([k, v]) => E.s(k, v));
    let vetoAt = null;
    for (let t = 0; t <= 32000; t += 10) {
        E.T = T0 + t;
        if (t === 20000) E.s('dcl.tieBusy', false);
        if ((t - 370) % 1000 === 0 || t === 3000 || t === 3005 || t === 3010 || t === 10000 || t === 10005) E.calc();
        if (vetoAt === null && E.g('dcl.tieVeto') === true) vetoAt = t;
    }
    D[rev] = vetoAt;
    console.log(`   ${LABEL[rev]}: tieVeto at ${fmt(vetoAt)}`);
}
check(D.rev1 !== null && D.rev1 < 20000, 'rev1 trip ระหว่าง tieBusy (ไม่รู้จัก tieBusy)');
check(D.rev2 !== null && D.rev2 >= 25000 && D.rev2 <= 26400, 'rev2 ไม่นับระหว่าง tieBusy, trip ~5 วิหลังปล่อย');

// ======================= E) FIX#SHARE =======================
console.log('== E) FIX#SHARE: (1) G2 ขึ้นกระแสช้ากว่า G1 ~1 วิ ตอนเริ่ม + ชุด limit  (2) G2 ค้าง 0 A ทั้ง session');
function shareRun(rev, g2Lag) {
    const E = makeEnv(rev); E.T = T0; boot(E, 120000);
    Object.entries({ cp_state_head1: 'state_c', cp_state_head2: 'state_a', 'dcl.tieClosed': true, 'dcl.tieBusy': false, startCommanded1: true,
        session_state_head1: 'VSECCLIB_SST_DIN_CurrentDemand', 'pep.target_voltage': 430.4, 'pm.measured_voltage': 373, 'pm.measured_voltage2': 373,
        sinexcel_state: { groups: { '1': { capable_count: 2 }, '2': { capable_count: 2 } } } }).forEach(([k, v]) => E.s(k, v));
    let sdAt = null;
    for (let t = 0; t <= 30000; t += 10) {
        E.T = T0 + t;
        const tgt = t < 1000 ? 12 : 41;
        E.s('pep.charging_state', 'charge'); E.s('pep.target_current', tgt);
        E.s('pm.measured_current', t >= 800 ? tgt / 2 : 0);                     // G1 ส่วนของตัวเอง
        E.s('pm.measured_current2', (g2Lag !== null && t >= 800 + g2Lag) ? tgt / 2 : 0);
        if ((t - 370) % 1000 === 0) E.calc();
        if (t === 1380) for (let k = 0; k < 5; k++) E.calc();               // ชุด limit 5 ข้อความจาก CP.py
        if (sdAt === null && E.g('dcl.shareDegraded') === true) sdAt = t;
    }
    return sdAt;
}
const E1 = {}, E2 = {};
for (const rev of ['rev1', 'rev2']) {
    E1[rev] = shareRun(rev, 1200); E2[rev] = shareRun(rev, null);
    console.log(`   ${LABEL[rev]}: (1) shareDegraded ${E1[rev] === null ? 'never' : 'at ' + fmt(E1[rev])}  (2) shareDegraded ${E2[rev] === null ? 'never' : 'at ' + fmt(E2[rev])}`);
}
check(E1.rev1 !== null && E1.rev1 < 2000, 'rev1 latch ผิดพลาดตอนชุด limit มาถึงขณะ G2 ยังไม่ขึ้นกระแส');
check(E1.rev2 === null, 'rev2 ไม่ latch เพราะ G2 ช้าแค่ตอนเริ่ม');
check(E2.rev2 !== null && E2.rev2 >= 8000 && E2.rev2 <= 9400, 'rev2 latch เมื่อ G2 ค้าง 0 A จริง (หลังผ่อนผัน 8 วิ)');

// ======================= F) FIX#PCAPV ตัวเลข =======================
console.log('== F) FIX#PCAPV: เพดานกระแสจาก limitpower (CP.py 120 kW) ที่แรงดันต่าง ๆ, target 430.4 V');
function pcap(rev, o) {
    const E = makeEnv(rev); E.T = T0; boot(E, 120000);
    if (o.src) E.setCfg('pcap_v_source', o.src);
    const dual = o.mode === 'dual';
    Object.entries({ cp_state_head1: 'state_c', cp_state_head2: dual ? 'state_c' : 'state_a', 'dcl.tieClosed': !dual, 'dcl.tieBusy': false,
        startCommanded1: true, startCommanded2: true, 'pep.charging_state': o.chg || 'charge', 'pep.charging_state2': dual ? (o.chg || 'charge') : '',
        'pep.target_voltage': 430.4, 'pep.target_voltage2': dual ? 430.4 : 0, 'pep.target_current': 100, 'pep.target_current2': dual ? 100 : 0,
        'pm.measured_current': 100, 'pm.measured_current2': 100, 'pm.measured_voltage': o.mv, 'pm.measured_voltage2': o.mv,
        limitpower1: o.lp || 120000, limitpower2: o.lp || 120000 }).forEach(([k, v]) => E.s(k, v));
    E.calc();
    const out = [E.g('pm.max_current'), E.g('pm.max_current2')];
    if (o.mv2 !== undefined) { E.s('pm.measured_voltage', o.mv2); E.s('pm.measured_voltage2', o.mv2); E.T += 1000; E.calc(); out.push(E.g('pm.max_current')); }
    return out;
}
const F = [
    ['solo 371 V', { mode: 'solo', mv: 371 }, { rev1: 278, rev2: 320 }],
    ['solo 373 V', { mode: 'solo', mv: 373 }, { rev1: 278, rev2: 318 }],
    ['dual 371 V', { mode: 'dual', mv: 371 }, { rev1: 138, rev2: 160 }],
    ['dual 373 V', { mode: 'dual', mv: 373 }, { rev1: 138, rev2: 158 }],
    ['solo 371 V, pcap_v_source=max', { mode: 'solo', mv: 371, src: 'max' }, { rev1: 278, rev2: 278 }],
    ['dual 371 V, pcap_v_source=max', { mode: 'dual', mv: 371, src: 'max' }, { rev1: 138, rev2: 138 }],
    ['solo preCharge 300 V', { mode: 'solo', mv: 300, chg: 'preCharge' }, { rev1: 278, rev2: 278 }],
    ['solo 200 V (ค่าวัดเพี้ยน < 0.6 x target)', { mode: 'solo', mv: 200 }, { rev1: 278, rev2: 278 }],
    ['solo 280 V -> ชนเพดานซอฟต์แวร์ 400 A', { mode: 'solo', mv: 280 }, { rev1: 278, rev2: 400 }]
];
for (const [name, o, exp] of F) {
    const r1 = pcap('rev1', o)[0], r2 = pcap('rev2', o)[0];
    const kw2 = (r2 * o.mv / 1000).toFixed(1);
    console.log(`   ${name.padEnd(44)} rev1 ${String(r1).padStart(3)} A | rev2 ${String(r2).padStart(3)} A (= ${kw2} kW ที่ ${o.mv} V)`);
    check(r1 === exp.rev1 && r2 === exp.rev2, `${name}: คาด rev1 ${exp.rev1} / rev2 ${exp.rev2}`);
}
const hy = pcap('rev2', { mode: 'solo', mv: 373, mv2: 373.8 }), hy2 = pcap('rev2', { mode: 'solo', mv: 373, mv2: 375 });
console.log(`   hysteresis: 373 -> 373.8 V: ${hy[0]} -> ${hy[2]} A | 373 -> 375 V: ${hy2[0]} -> ${hy2[2]} A`);
check(hy[2] === hy[0] && hy2[2] === 316, 'hysteresis 1.5 V กันเพดานกระพริบ, เปลี่ยนจริงเมื่อแรงดันขยับ');

// ======================= G) trace node =======================
console.log('== G) ARCH2/session trace (rev2) หลัง session A rev1-style veto');
{
    const r = sessionH1('rev2', { burstAt: 1380, firstDelay: 1500, until: 30000, noLoad: (h, tie) => h === 1 && tie });
    const out = r.E.run(r.E.N.trace, { payload: 1 });
    const snap = JSON.parse(out.payload);
    console.log('   ' + out.payload.slice(0, 400) + (out.payload.length > 400 ? ' ...' : ''));
    check(snap.tieVeto === true && /NOLOAD H1/.test(snap.vetoWhy) && snap.noload === true && snap.h1.lp === 120 && typeof snap.h1.maxP === 'number',
        'trace มี tieVeto/vetoWhy/noload/lp/maxP');
}

// errors raised inside nodes?
console.log(failures ? `\n${failures} FAIL` : '\nALL PASS');
process.exit(failures ? 1 : 0);
