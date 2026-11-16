// The checker's pass over the program scip-typescript indexed, in the container after it (`typescript.py`):
// each member of the project's code the checker binds no declaration to, where the index has no occurrence, and
// why. One JSON line each, `[path, line (1-based), column (UTF-16), kind, the receiver's type]`, kind `any` (the
// receiver's type is any), `index` (an index signature holds the member), `mapped` (a member the checker made,
// with no declaration: a mapped or a spread type's) or `undeclared` (the type declares no such member). A type
// names a module by its package, or by its path in the project, never by the container's path.
//
//     node typescript_unbound.js /work "$(readlink -f <scip-typescript's bin>)" > unbound.jsonl
'use strict';
const fs = require('fs');
const path = require('path');

const [work, indexer] = process.argv.slice(2);
// The TypeScript scip-typescript runs on: the program is the one it indexed.
const ts = require(require.resolve('typescript', { paths: [path.dirname(fs.realpathSync(indexer))] }));
const config = ts.getParsedCommandLineOfConfigFile(path.join(work, 'tsconfig.json'), {},
  { ...ts.sys, onUnRecoverableConfigFileDiagnostic() {} });
const program = ts.createProgram({ rootNames: config.fileNames, options: config.options,
  projectReferences: config.projectReferences });
const checker = program.getTypeChecker();
const named = (type) => checker.typeToString(type, undefined, ts.TypeFormatFlags.UseFullyQualifiedType)
  .replace(/import\("[^"]*"\)\./g, '')
  .replace(/import\("([^"]*)"\)/g, (_, module) => {
    const pack = module.match(/.*\/node_modules\/((?:@[^/]+\/)?[^/]+)/);
    return `import("${pack ? pack[1] : path.relative(work, module).split(path.sep).join('/')}")`;
  })
  .slice(0, 80);

for (const file of program.getSourceFiles()) {
  const rel = path.relative(work, file.fileName).split(path.sep).join('/');
  if (file.isDeclarationFile || rel.startsWith('../') || rel.split('/').includes('node_modules')) continue;
  const lines = [];
  const visit = (node) => {
    if (ts.isPropertyAccessExpression(node)) {
      const symbol = checker.getSymbolAtLocation(node.name);
      if (!symbol || !(symbol.declarations || []).length) {
        const receiver = checker.getNonNullableType(checker.getTypeAtLocation(node.expression));
        const apparent = checker.getApparentType(receiver);
        const kind = receiver.flags & ts.TypeFlags.Any ? 'any' : symbol ? 'mapped'
          : checker.getIndexInfosOfType(apparent).length ? 'index' : 'undeclared';
        const { line, character } = file.getLineAndCharacterOfPosition(node.name.getStart(file));
        lines.push(JSON.stringify([rel, line + 1, character, kind, kind === 'any' ? '' : named(apparent)]));
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(file);
  if (lines.length) process.stdout.write(lines.join('\n') + '\n');
}
