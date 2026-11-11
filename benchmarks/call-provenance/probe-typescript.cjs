// Run: node benchmarks/call-provenance/probe-typescript.cjs /path/to/typescript/lib/typescript.js
// Virtual sources only; the provider is outside the project inventory.
const assert = require('node:assert/strict');
const ts = require(require('node:path').resolve(process.argv[2]));
const files = {
  '/project/app.ts': 'import { make, keep } from "../packages/provider";\nfunction local(s: string) { return s; }\nconst { t } = make();\nconst alias = keep(local);\nt("title");\nalias("title");\n',
  '/packages/provider.ts': 'export function make() { return { t: (s: string) => s }; }\nexport function keep<T>(fn: T): T { return fn; }',
};
const host = {
  getScriptFileNames: () => Object.keys(files),
  getScriptVersion: () => '0',
  getScriptSnapshot: path => files[path] === undefined ? undefined : ts.ScriptSnapshot.fromString(files[path]),
  getCurrentDirectory: () => '/',
  getCompilationSettings: () => ({ noLib: true, module: ts.ModuleKind.CommonJS }),
  getDefaultLibFileName: () => '',
  fileExists: path => path in files,
  readFile: path => files[path],
};
const service = ts.createLanguageService(host);
const source = files['/project/app.ts'];
const definitions = position => service.getDefinitionAtPosition('/project/app.ts', position) || [];
const holder = source.indexOf('{ t }') + 2;
const call = definitions(source.lastIndexOf('t("'));
assert(call.some(item => item.fileName === '/project/app.ts' && item.textSpan.start === holder));
const target = definitions(holder);
assert(target.length > 0 && target.every(item => item.fileName === '/packages/provider.ts'));
const local = source.indexOf('local(');
const callback = definitions(source.lastIndexOf('alias("'));
assert(callback.some(item => item.fileName === '/project/app.ts' && item.textSpan.start === local));
console.log(JSON.stringify({ typescript: ts.version, externalHolderFollowed: true, internalCallbackPreserved: true }));
