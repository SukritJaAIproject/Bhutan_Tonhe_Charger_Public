// Validate a Node-RED flow export: JSON, wires/links resolve, all function code compiles (same wrapper shape as Node-RED).
const fs = require('fs'); const vm = require('vm');
const file = process.argv[2];
const flow = JSON.parse(fs.readFileSync(file, 'utf8'));
const ids = new Set(flow.map(n => n.id));
let bad = 0, fnCount = 0;
for (const n of flow) {
    if (Array.isArray(n.wires)) {
        for (const port of n.wires) for (const w of port) if (!ids.has(w)) { console.log('DANGLING WIRE', n.id, n.name, '->', w); bad++; }
    }
    if (Array.isArray(n.links)) for (const l of n.links) if (!ids.has(l)) { console.log('DANGLING LINK', n.id, n.name, '->', l); bad++; }
    if (n.z && !ids.has(n.z)) { console.log('ORPHAN z', n.id, n.name, n.z); bad++; }
    if (n.g && !ids.has(n.g)) { console.log('ORPHAN g', n.id, n.name, n.g); bad++; }
    if (n.type === 'function') {
        fnCount++;
        for (const key of ['func', 'initialize', 'finalize']) {
            const code = n[key]; if (!code) continue;
            try { new vm.Script('(async function(msg,__send__,__done__,node,context,flow,global,RED,env,util,Buffer,console,setTimeout,clearTimeout,setInterval,clearInterval){\n' + code + '\n})'); }
            catch (e) { console.log('SYNTAX ERROR in', n.id, JSON.stringify(n.name), key, ':', e.message); bad++; }
        }
    }
}
const types = {}; for (const n of flow) types[n.type] = (types[n.type] || 0) + 1;
console.log(file.split('/').pop(), '| nodes', flow.length, '| function nodes', fnCount, '| problems', bad);
process.exit(bad ? 1 : 0);
