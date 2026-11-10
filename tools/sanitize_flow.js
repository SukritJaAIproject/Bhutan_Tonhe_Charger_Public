// Make a public copy of a Node-RED flow export: placeholder admin PIN, placeholder test PINs in inject nodes,
// placeholder external broker. Exits 1 if any of the removed values is still in the output.
// usage: node sanitize_flow.js <in.json> <out.json>
const fs = require('fs');
const [inF, outF] = process.argv.slice(2);
const raw = fs.readFileSync(inF, 'utf8');
const flow = JSON.parse(raw);
const PLACE_HOST = 'broker.example.invalid';
const PLACE_PIN = '0000';
const isPrivate = h => /^(10\.|127\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|169\.254\.)/.test(h);
const ipRe = /\b(?:\d{1,3}\.){3}\d{1,3}\b/g;
const report = { pin_nodes: 0, test_pins: 0, broker_nodes: 0, clientids: 0, text_ips: 0 };
const pins = new Set();
const zero = v => { pins.add(v); report.test_pins++; return '0'.repeat(v.length); };
const pinField = s => s.replace(/(\\?"(?:pin|password)\\?"\s*:\s*\\?")(\d{4,})/g, (m, a, v) => a + zero(v));
for (const n of flow) {
  if (typeof n.func === 'string' && /const\s+ADMIN_PASSWORD\s*=/.test(n.func)) {
    n.func = n.func.replace(/(const\s+ADMIN_PASSWORD\s*=\s*)(["'])([^"']*)\2\s*;[^\n]*/, (m, a, q, v) => {
      pins.add(v); report.pin_nodes++;
      return a + q + PLACE_PIN + q + '; // <-- PLACEHOLDER (public copy): set your own PIN, digits 0-9 only, before deploying';
    });
  }
  if (n.type === 'inject') {   // test PINs typed into inject nodes
    if (typeof n.payload === 'string') n.payload = pinField(n.payload);
    if (Array.isArray(n.props)) n.props.forEach(pr => { if (typeof pr.v === 'string') pr.v = pinField(pr.v); });
  }
  if (n.type === 'mqtt-broker' && typeof n.broker === 'string') {
    const host = n.broker.replace(/^[a-z]+:\/\//i, '').replace(/[:\/].*$/, '');
    if (/^(?:\d{1,3}\.){3}\d{1,3}$/.test(host) && !isPrivate(host)) { n.broker = PLACE_HOST; report.broker_nodes++; }
    if (n.clientid && n.clientid !== 'node-red') { n.clientid = ''; report.clientids++; }
  }
  for (const k of ['info', 'name', 'func', 'payload', 'topic', 'format', 'template']) {
    if (typeof n[k] === 'string') {
      n[k] = n[k].replace(ipRe, ip => { if (isPrivate(ip)) return ip; report.text_ips++; return PLACE_HOST; });
    }
  }
}
const out = JSON.stringify(flow, null, 4);
// verification on the final text
const leftIps = [...new Set((out.match(ipRe) || []).filter(ip => !isPrivate(ip)))];
let pinLeft = 0;
for (const p of pins) { if (/^0+$/.test(p)) continue; pinLeft += out.split('"' + p + '"').length - 1 + out.split("'" + p + "'").length - 1 + out.split('\\"' + p + '\\"').length - 1; }
report.distinct_old_pins = pins.size;
report.old_pin_quoted_left = pinLeft;
report.public_ips_left = leftIps.length;
report.nodes = flow.length;
fs.writeFileSync(outF, out);
console.log(JSON.stringify(report));
const pinConsts = flow.filter(n => typeof n.func === 'string' && /const\s+ADMIN_PASSWORD\s*=/.test(n.func)).length;
if (pinLeft || leftIps.length || report.pin_nodes < 1 || report.pin_nodes !== pinConsts) { console.error('SANITIZE CHECK FAILED'); process.exit(1); }
