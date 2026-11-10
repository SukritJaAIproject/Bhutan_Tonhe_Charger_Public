// usage: node flow_diff.js <old.json> <new.json> [--lines]   (PIN-like values are masked)
const fs = require('fs');
const [a, b] = [process.argv[2], process.argv[3]].map(f => JSON.parse(fs.readFileSync(f, 'utf8')));
const showLines = process.argv.includes('--lines');
const mask = s => String(s).replace(/(ADMIN_PASSWORD\s*=\s*["'])[^"']*/g, '$1####');
const tabsA = Object.fromEntries(a.filter(n => n.type === 'tab').map(n => [n.id, n.label]));
const tabsB = Object.fromEntries(b.filter(n => n.type === 'tab').map(n => [n.id, n.label]));
const A = new Map(a.map(n => [n.id, n])), B = new Map(b.map(n => [n.id, n]));
const lab = (n, tabs) => `[${tabs[n.z] || (n.type === 'tab' ? 'TAB' : 'config')}] ${n.type} "${n.name || n.label || ''}"`;
const added = b.filter(n => !A.has(n.id)), removed = a.filter(n => !B.has(n.id));
const changed = [];
for (const n of b) { const o = A.get(n.id); if (!o) continue;
  const keys = [...new Set([...Object.keys(o), ...Object.keys(n)])].filter(k => JSON.stringify(o[k]) !== JSON.stringify(n[k]));
  if (keys.length) changed.push({ n, o, keys }); }
console.log(`nodes old ${a.length} new ${b.length} | added ${added.length} removed ${removed.length} changed ${changed.length}`);
const layoutOnly = changed.filter(c => c.keys.every(k => ['x', 'y', 'w', 'h', 'g'].includes(k)));
console.log('layout-only changes:', layoutOnly.length);
console.log('--- ADDED'); added.forEach(n => console.log('  +', lab(n, tabsB), n.func ? `(${n.func.split('\n').length} lines)` : ''));
console.log('--- REMOVED'); removed.forEach(n => console.log('  -', lab(n, tabsA)));
console.log('--- CHANGED (non-layout)');
for (const c of changed) { if (layoutOnly.includes(c)) continue;
  console.log('  *', lab(c.n, tabsB), '| keys:', c.keys.join(','));
  for (const k of c.keys) {
    if (['x', 'y', 'w', 'h'].includes(k)) continue;
    if (k === 'func' || k === 'info' || k === 'format' || k === 'template') {
      const ol = (c.o[k] || '').split('\n'), nl = (c.n[k] || '').split('\n');
      const os = new Set(ol), ns = new Set(nl);
      const minus = ol.filter(l => !ns.has(l)), plus = nl.filter(l => !os.has(l));
      console.log(`      ${k}: ${ol.length} -> ${nl.length} lines, -${minus.length} +${plus.length}`);
      if (showLines) { minus.slice(0, 40).forEach(l => console.log('        - ' + mask(l.trim()).slice(0, 190))); plus.slice(0, 60).forEach(l => console.log('        + ' + mask(l.trim()).slice(0, 190))); }
    } else console.log(`      ${k}: ${mask(JSON.stringify(c.o[k])).slice(0, 110)} -> ${mask(JSON.stringify(c.n[k])).slice(0, 110)}`);
  } }
