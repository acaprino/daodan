// How `astro/astro-jsx.d.ts` (shipped by every `astro`) declares event attributes: the lines around the first `onclick` and each `onend`,
// and the interfaces that hold them. Printed as the file says it; no reading of the code is done here.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(`${process.cwd()}/`);
const file = path.join(path.dirname(require.resolve('astro/package.json')), 'astro-jsx.d.ts');
const lines = fs.readFileSync(file, 'utf8').split('\n');
console.log(`${lines.length} lines`);
const interfaces = [];
lines.forEach((l, i) => { if (l.includes('interface ') || l.startsWith('declare namespace') || l.includes('namespace ')) interfaces.push(`${i + 1}: ${l.trim().slice(0, 100)}`); });
console.log('interfaces and namespaces:');
for (const l of interfaces.slice(0, 80)) console.log('  ' + l);
const start = lines.findIndex((l) => l.includes('interface DOMAttributes'));
console.log(`--- the first lines of interface DOMAttributes (line ${start + 1}) and the last before the next interface`);
for (let j = start; j < start + 6; j++) console.log(`${j + 1}: ${lines[j]}`);
const next = lines.findIndex((l, i) => i > start && l.includes('interface '));
for (let j = next - 8; j < next; j++) console.log(`${j + 1}: ${lines[j]}`);
const members = lines.slice(start + 1, next).filter((l) => l.includes('?:'));
const notOn = members.filter((l) => !l.trim().startsWith('on'));
console.log(`members of DOMAttributes: ${members.length}; their names that do not start with on: ${notOn.map((l) => l.trim().split('?')[0]).join(', ') || 'none'}`);
for (const needle of ['onclick', 'onend']) {
  lines.forEach((l, i) => {
    if (!l.includes(needle)) return;
    console.log(`--- "${needle}" at line ${i + 1}`);
    for (let j = Math.max(0, i - 6); j < Math.min(lines.length, i + 7); j++) console.log(`${j + 1}: ${lines[j]}`);
  });
}
