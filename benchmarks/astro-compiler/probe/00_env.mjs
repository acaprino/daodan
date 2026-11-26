// The versions, how the compiler is reached from the project, what it exports, and what its own README says about positions.
import fs from 'node:fs';
import path from 'node:path';
import { loadCompiler } from './_lib.mjs';

const { name, compiler, version, entry, manifest, packageDir, astro } = await loadCompiler();
console.log('node', process.version);
console.log(`astro ${astro} | ${name} ${version} | entry ${path.relative(process.cwd(), entry)}`);
console.log('exports of the package:', JSON.stringify(manifest.exports));
console.log('dependencies:', JSON.stringify(manifest.dependencies), 'optional:', JSON.stringify(Object.keys(manifest.optionalDependencies ?? {})));
console.log('exported by the module:', Object.keys(compiler).join(', '));
console.log('--- README lines that mention position, span, incomplete, incorrect, parse or AST');
const readmePath = path.join(packageDir, 'README.md');
if (fs.existsSync(readmePath)) {
  for (const line of fs.readFileSync(readmePath, 'utf8').split('\n')) if (/position|span|incomplete|incorrect|wrong|parse|AST/.test(line)) console.log('  ' + line.slice(0, 260));
} else console.log('  (no README.md in the package)');
const files = [];
const visit = (d, depth) => { for (const e of fs.readdirSync(d, { withFileTypes: true })) { if (e.name === 'node_modules') continue; const f = path.join(d, e.name); if (e.isDirectory() && depth < 3) visit(f, depth + 1); else if (/\.d\.[cm]?ts$/.test(e.name)) files.push(f); } };
visit(packageDir, 0);
console.log('--- type declarations:', files.map((f) => path.relative(packageDir, f)).join(', '));
for (const f of files.filter((f) => /(ast|shared[\/]types)\.d\.ts$/.test(f))) {
  console.log(`--- ${path.relative(packageDir, f)}`);
  console.log(fs.readFileSync(f, 'utf8').slice(0, 5000));
}
