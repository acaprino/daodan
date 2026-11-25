// The probe of the three open points of task 13f (plan 2026-11-20-ingressi-e-flussi.md, "Aperto" of Angular): what the project's own
// template type-checker (`@angular/compiler-cli`) gives for
//   A. the listeners of `host: {...}` and `@HostListener` (`getHostElement`): where each lies, what it calls, and whether its
//      calls resolve to a declaration;
//   B. an event of the DOM, the output of a component or a directive, an output the project's own component declares under the name of
//      a DOM event: what `getSymbolOfNode` of the event says its bindings are (`target`, `isComponent`, `selector`, the declaration);
//   C. a call whose method is an arrow-function property, an inherited method, a bound method and a signal: the declaration, its kind,
//      and the kind of its initializer.
// It builds a small project of its own (the cases below, written under /tmp, `node_modules` linked to the fixture's) so the recorded
// answers of the fixture (`tests/fixtures/premap/angular/`) do not change. Nothing here is a source of Daodan: it only prints.
import fs from 'node:fs';
import path from 'node:path';
import ts from 'typescript';
import { C, q, events } from './_lib.mjs';

const root = '/tmp/open-cases';
fs.rmSync(root, { recursive: true, force: true });
fs.mkdirSync(`${root}/src`, { recursive: true });
fs.symlinkSync('/fixture/node_modules', `${root}/node_modules`);
const cases = {
  'tsconfig.json': JSON.stringify({
    compilerOptions: { rootDir: './src', strict: true, skipLibCheck: true, isolatedModules: true, experimentalDecorators: true,
      importHelpers: true, target: 'ES2022', module: 'preserve', moduleResolution: 'bundler', types: [] },
    angularCompilerOptions: { strictTemplates: true },
    files: ['src/main.ts'],
  }),
  'src/main.ts': `export * from './host';\nexport * from './outputs';\nexport * from './parent';\n`,
  // A: `host: {...}` of a component and of a directive, `@HostListener` with and without a target, and a handler that calls a method of another object
  'src/host.ts': `
import { Component, Directive, HostListener } from '@angular/core';
import { OrderService } from './service';

@Component({
  selector: 'app-host',
  host: { '(click)': 'onHost()', '(window:keydown.escape)': 'onEsc($event)', '(dblclick)': 'svc.cancel()', '[class.on]': 'on' },
  template: '',
})
export class HostComponent {
  on = false;
  svc = new OrderService();
  onHost() {}
  onEsc(e: Event) {}
  @HostListener('window:resize', ['$event'])
  onResize(e: Event) {}
  @HostListener('document:keydown')
  onKey() {}
}

@Directive({ selector: '[appHostDir]', host: { '(focus)': 'onFocus()' } })
export class HostDirective {
  onFocus() {}
  @HostListener('blur') onBlur() {}
}
`,
  'src/service.ts': `export class OrderService { cancel(): void {} }\n`,
  // B: a component with an output (signal and decorator), one with an output named as a DOM event, one with no output, a directive with an
  // output that another one also declares
  'src/outputs.ts': `
import { Component, Directive, EventEmitter, Output, output } from '@angular/core';

@Component({ selector: 'app-editor', template: '<button (click)="saved.emit(1)">x</button>' })
export class EditorComponent {
  saved = output<number>();
  @Output() legacy = new EventEmitter<string>();
}

@Component({ selector: 'app-clicky', template: '' })
export class ClickyComponent {
  click = output<void>();
}

@Component({ selector: 'app-plain', template: '' })
export class PlainComponent {}

@Directive({ selector: '[appTwin]' })
export class TwinDirective {
  saved = output<number>();
}
`,
  // the parent: every case, one event each
  'src/parent.ts': `
import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { EditorComponent, ClickyComponent, PlainComponent, TwinDirective } from './outputs';
import { HostComponent, HostDirective } from './host';

declare global { interface HTMLElementEventMap { 'my-event': CustomEvent; } }

export class Base {
  inherited() {}
}

@Component({
  selector: 'app-parent',
  imports: [FormsModule, EditorComponent, ClickyComponent, PlainComponent, TwinDirective, HostComponent, HostDirective],
  template: \`
    <button (click)="domClick()">dom</button>
    <app-editor (saved)="onSaved($event)" (legacy)="onLegacy($event)" (click)="onEditorDomClick()"></app-editor>
    <app-clicky (click)="onClickyOutput()"></app-clicky>
    <app-plain (click)="onPlainClick()"></app-plain>
    <app-editor appTwin (saved)="onTwinSaved($event)"></app-editor>
    <form (ngSubmit)="submit()"><input [(ngModel)]="q" name="q" (change)="onChange()"></form>
    <div (my-event)="onMine()" (window:resize)="onResize()"></div>
    <button (click)="arrow()">arrow</button>
    <button (click)="inherited()">inherited</button>
    <button (click)="bound()">bound</button>
    <button (click)="count.set(1)">signal</button>
    <button (click)="optional?.()">optional call</button>
    <app-host appHostDir></app-host>
  \`,
})
export class ParentComponent extends Base {
  q = '';
  count = signal(0);
  optional: (() => void) | undefined;
  arrow = () => {};
  bound = this.target.bind(this);
  domClick() {}
  onSaved(n: number) {}
  onLegacy(s: string) {}
  onEditorDomClick() {}
  onClickyOutput() {}
  onPlainClick() {}
  onTwinSaved(n: number) {}
  submit() {}
  onChange() {}
  onMine() {}
  onResize() {}
  target() {}
}
`,
};
for (const [file, text] of Object.entries(cases)) fs.writeFileSync(`${root}/${file}`, text);

const cli = await import('@angular/compiler-cli');
const config = cli.readConfiguration(`${root}/tsconfig.json`);
config.options._enableTemplateTypeChecker = true;
const program = cli.createProgram({ rootNames: config.rootNames, options: config.options, host: cli.createCompilerHost({ options: config.options }) });
await program.loadNgStructureAsync();
const ttc = program.compiler.getTemplateTypeChecker();
const tsProgram = program.getTsProgram();
const first = (e) => String(e?.message ?? e).split('\n')[0].slice(0, 200);
const rel = (file) => path.relative(root, file);
const where = (node) => {
  const sf = node.getSourceFile();
  const { line, character } = sf.getLineAndCharacterOfPosition((node.name ?? node).getStart(sf));
  return `${rel(sf.fileName)}:${line + 1}:${character + 1}`;
};
const classOf = (file, name) => {
  let found;
  const visit = (n) => { if (ts.isClassDeclaration(n) && n.name?.text === name) found = n; ts.forEachChild(n, visit); };
  visit(tsProgram.getSourceFile(`${root}/${file}`));
  return found;
};
const span = (s) => (s ? `${s.start.file?.url ? rel(s.start.file.url) : '?'}:${s.start.line + 1}:${s.start.col + 1}..${s.end.line + 1}:${s.end.col + 1} covers ${q(s.toString?.() ?? '')}` : String(s));
const declOf = (symbol) => {
  const tsSymbol = ttc.getTsSymbolOfSymbol(symbol);
  if (!tsSymbol) return `no ts symbol`;
  const declarations = tsSymbol.declarations ?? [];
  if (!declarations.length) return `ts symbol ${tsSymbol.name} with no declaration`;
  return declarations.map((d) => {
    const owner = d.parent && (ts.isClassDeclaration(d.parent) || ts.isInterfaceDeclaration(d.parent)) ? d.parent.name?.text : d.parent ? ts.SyntaxKind[d.parent.kind] : '?';
    const init = d.initializer ? `, initializer ${ts.SyntaxKind[d.initializer.kind]}` : '';
    return `${tsSymbol.name} ${ts.SyntaxKind[d.kind]} of ${owner} at ${where(d)}${init}; default lib: ${tsProgram.isSourceFileDefaultLibrary(d.getSourceFile())}`;
  }).join(' | ');
};

class Calls extends C.RecursiveAstVisitor {
  nodes = [];
  visitCall(ast, ctx) { this.nodes.push(ast.receiver); return super.visitCall(ast, ctx); }
  visitSafeCall(ast, ctx) { this.nodes.push(ast.receiver); return super.visitSafeCall(ast, ctx); }
}
const callsOf = (handler) => { const v = new Calls(); v.visit(handler.ast ?? handler); return v.nodes; };
const describeCalls = (handler, component) => {
  const lines = [];
  for (const callee of callsOf(handler)) {
    let line = `   call ${callee.constructor.name}${callee.name ? ` "${callee.name}"` : ''}: `;
    try {
      const symbol = ttc.getSymbolOfNode(callee, component);
      line += symbol ? `getSymbolOfNode kind ${symbol.kind}; ${declOf(symbol)}` : 'getSymbolOfNode -> null';
    } catch (e) { line += `THREW ${first(e)}`; }
    lines.push(line);
  }
  return lines;
};

console.log('=== A. getHostElement: the listeners of `host` and of @HostListener ===');
for (const [file, name] of [['src/host.ts', 'HostComponent'], ['src/host.ts', 'HostDirective']]) {
  const node = classOf(file, name);
  let host;
  try { host = ttc.getHostElement(node); } catch (e) { console.log(`${name}: getHostElement THREW ${first(e)}`); continue; }
  if (!host) { console.log(`${name}: getHostElement -> ${host}`); continue; }
  console.log(`${name}: HostElement keys [${Object.keys(host)}], ${host.listeners.length} listeners, ${host.bindings.length} bindings`);
  for (const [i, l] of host.listeners.entries()) {
    console.log(` [#${i}] ${l.constructor.name} keys [${Object.keys(l)}]`);
    console.log(`   name=${q(l.name)} type=${l.type} target=${q(l.target)} phase=${q(l.phase)} handler.source=${q(l.handler?.source ?? null)} handler AST ${l.handler?.ast?.constructor.name ?? l.handler?.constructor.name}`);
    for (const key of ['sourceSpan', 'keySpan', 'handlerSpan']) console.log(`   ${key.padEnd(11)} ${l[key] ? span(l[key]) : '(none)'}`);
    try {
      const symbol = ttc.getSymbolOfNode(l, node);
      console.log(`   getSymbolOfNode(listener) -> ${symbol ? `kind ${symbol.kind}, bindings ${symbol.bindings?.length}` : symbol}`);
    } catch (e) { console.log(`   getSymbolOfNode(listener) THREW ${first(e)}`); }
    for (const line of describeCalls(l.handler, node)) console.log(line);
  }
}

console.log('\n=== B and C. every event of the parent template: its bindings, and the declaration of each call ===');
{
  const node = classOf('src/parent.ts', 'ParentComponent');
  const seen = new Set();
  for (const { ev } of events(ttc.getTemplate(node))) {
    if (seen.has(ev)) continue;
    seen.add(ev);
    console.log(`\nevent (${ev.name}) = ${q(ev.handler.source)}  type=${ev.type} target=${q(ev.target)} phase=${q(ev.phase)}`);
    try {
      const symbol = ttc.getSymbolOfNode(ev, node);
      console.log(`   getSymbolOfNode: ${symbol ? `kind ${symbol.kind}, ${symbol.bindings?.length} binding(s), keys [${Object.keys(symbol)}]` : symbol}`);
      for (const [i, b] of (symbol?.bindings ?? []).entries()) {
        const t = b.target;
        const target = t ? `${t.constructor?.name ?? '?'} kind ${t.kind}${'isComponent' in t ? `, isComponent ${t.isComponent}` : ''}${t.selector ? `, selector ${q(t.selector)}` : ''}${t.tsSymbol ? `, class ${t.tsSymbol.name}` : ''}` : 'no target';
        console.log(`   binding ${i}: kind ${b.kind}, keys [${Object.keys(b)}]; target: ${target}; ${declOf(b)}`);
      }
    } catch (e) { console.log(`   getSymbolOfNode(event) THREW ${first(e)}`); }
    for (const line of describeCalls(ev.handler, node)) console.log(line);
  }
}
