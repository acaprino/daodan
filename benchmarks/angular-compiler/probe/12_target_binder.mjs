// Which name a call with no object before it stands for: a method of the class, or a name the template declares
// (`let-c`, `@let`, the variable of an `@for`)? `R3TargetBinder.bind({template}).getExpressionTarget(expression)`.
import { C, fs, q } from './_lib.mjs';

console.log('exports:', ['R3TargetBinder', 'SelectorMatcher', 'TmplAstVariable', 'TmplAstReference', 'TmplAstLetDeclaration'].map((n) => `${n}:${typeof C[n]}`).join(' '));
const types = ['compiler.d.ts', '_index-chunk.d.ts'].map((f) => fs.readFileSync(`/fixture/node_modules/@angular/compiler/types/${f}`, 'utf8')).join('\n');
for (const needle of ['declare class R3TargetBinder', 'getExpressionTarget(']) {
  const i = types.indexOf(needle);
  console.log(`--- ${needle}: ${i < 0 ? 'NOT FOUND' : '\n' + types.slice(Math.max(0, i - 300), i + 700)}`);
}

const file = '/fixture/src/app/scoped.component.ts';
const ts = fs.readFileSync(file, 'utf8');
const start = ts.indexOf('template: `') + 'template: `'.length;
const text = ts.slice(start, ts.indexOf('`,', start));
const parsed = C.parseTemplate(text, 'scoped.html', {});
console.log('parse errors:', parsed.errors ? parsed.errors.map(String) : null);

const calls = [];
class Calls extends C.RecursiveAstVisitor {
  visitCall(ast, ctx) { if (ast.receiver.constructor.name === 'PropertyRead') calls.push(ast.receiver); return super.visitCall(ast, ctx); }
}
class Events extends C.TmplAstRecursiveVisitor {
  visitBoundEvent(ev) { new Calls().visit(ev.handler.ast ?? ev.handler); }
}
C.tmplAstVisitAll(new Events(), parsed.nodes);
for (const matcher of [null, new C.SelectorMatcher()]) {
  console.log(`\n=== new R3TargetBinder(${matcher === null ? 'null' : 'new SelectorMatcher()'}) ===`);
  try {
    const bound = new C.R3TargetBinder(matcher).bind({ template: parsed.nodes });
    console.log('BoundTarget methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(bound)).join(', '));
    for (const callee of calls) {
      const target = bound.getExpressionTarget(callee);
      console.log(`${callee.receiver.constructor.name === 'ImplicitReceiver' ? '' : '(this) '}${callee.name}() -> ${target ? `${target.constructor.name} name=${q(target.name)}` : target}`);
    }
  } catch (e) { console.log('threw:', e.stack.split('\n').slice(0, 4).join(' | ')); }
}
