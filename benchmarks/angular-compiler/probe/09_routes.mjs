// Routes: is there anything in Angular that gives the Routes array without running the app? Attempt: the compiler's own static evaluator.
import { fs, q } from './_lib.mjs';
import path from 'node:path';
import ts from 'typescript';

const cli = await import('@angular/compiler-cli');
const mig = await import('@angular/compiler-cli/private/migrations');
console.log('private/migrations exports include PartialEvaluator:', typeof mig.PartialEvaluator, 'TypeScriptReflectionHost:', typeof mig.TypeScriptReflectionHost, 'DynamicValue:', typeof mig.DynamicValue);
const config = cli.readConfiguration('/fixture/tsconfig.json');
const host = cli.createCompilerHost({ options: config.options });
const program = cli.createProgram({ rootNames: config.rootNames, options: config.options, host });
const tsProgram = program.getTsProgram();
const checker = tsProgram.getTypeChecker();
const reflection = new mig.TypeScriptReflectionHost(checker);
const evaluator = new mig.PartialEvaluator(reflection, checker, null);

function show(v, depth = 0) {
  const pad = '  '.repeat(depth);
  if (v === null || ['string', 'number', 'boolean', 'undefined'].includes(typeof v)) return JSON.stringify(v);
  if (Array.isArray(v)) return '[\n' + v.map((x) => pad + '  ' + show(x, depth + 1)).join(',\n') + '\n' + pad + ']';
  if (v instanceof Map) return '{\n' + [...v].map(([k, x]) => `${pad}  ${k}: ${show(x, depth + 1)}`).join(',\n') + '\n' + pad + '}';
  const name = (v.constructor?.name ?? '').replace(/^_/, '');
  if (name === 'Reference') return `Reference(${v.node?.name?.text ?? '?'} in ${path.relative('/fixture', v.node.getSourceFile().fileName)})`;
  if (name === 'DynamicValue') return `DynamicValue(${v.reason?.constructor?.name ?? ''}; node ${q(v.node.getText().slice(0, 70))})`;
  if (typeof v === 'function') return 'function';
  return `${name}(${Object.keys(v).join(',')})`;
}

for (const [file, names] of [['/fixture/src/app/app.routes.ts', ['routes']], ['/fixture/src/app/app.config.ts', ['appConfig']], ['/fixture/src/app/legacy.module.ts', []]]) {
  const sf = tsProgram.getSourceFile(file);
  for (const n of names) {
    let init;
    const visit = (node) => { if (ts.isVariableDeclaration(node) && node.name.getText() === n) init = node.initializer; ts.forEachChild(node, visit); };
    visit(sf);
    console.log(`\n--- evaluate ${path.basename(file)} :: ${n}`);
    try { console.log(show(evaluator.evaluate(init))); } catch (e) { console.log('threw', e.stack.split('\n').slice(0, 4).join(' | ')); }
  }
}
// RouterModule.forChild([...]) inside an @NgModule decorator
{
  const sf = tsProgram.getSourceFile('/fixture/src/app/legacy.module.ts');
  let arg;
  const visit = (node) => { if (ts.isCallExpression(node) && node.expression.getText() === 'RouterModule.forChild') arg = node.arguments[0]; ts.forEachChild(node, visit); };
  visit(sf);
  console.log('\n--- evaluate the argument of RouterModule.forChild(...) in legacy.module.ts');
  try { console.log(show(evaluator.evaluate(arg))); } catch (e) { console.log('threw', e.message); }
}
