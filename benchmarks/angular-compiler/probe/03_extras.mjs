// Extras: duplicates for *ngFor, escapes, errors, CRLF, other syntax, API status, host helpers.
import { C, fs, events, walk, reportEvents, cmpSpan, expectedFor, collectCalls, render, q, p, HTML_EVENTS } from './_lib.mjs';
import path from 'node:path';

const nm = '/fixture/node_modules';
const htmlFile = '/fixture/src/app/app.component.html';
const html = fs.readFileSync(htmlFile, 'utf8');

console.log('=== A. *ngFor: the event on the element that carries the structural directive ===');
{
  const t = C.parseTemplate(html, htmlFile, {});
  const li = [...walk(t.nodes)].filter((w) => w.node.outputs?.some((o) => o.handler.source === 'liClick(o)'));
  const [tpl, el] = li.map((w) => w.node);
  console.log('nodes owning the event:', li.map((w) => w.kind + '<' + (w.node.name ?? w.node.tagName) + '>').join(' , '));
  console.log('same BoundEvent object on both:', tpl.outputs[0] === el.outputs[0]);
  console.log('Template.outputs[0].sourceSpan', p(tpl.outputs[0].sourceSpan.start), p(tpl.outputs[0].sourceSpan.end), ' Element.outputs[0].sourceSpan', p(el.outputs[0].sourceSpan.start), p(el.outputs[0].sourceSpan.end));
  console.log('Template<li>.attributes:', tpl.attributes.map((a) => `${a.name}=${q(a.value)}`), 'inputs:', tpl.inputs.map((a) => a.name), 'templateAttrs:', tpl.templateAttrs.map((a) => `${a.constructor.name}:${a.name}`), 'variables:', tpl.variables.map((v) => v.name));
  console.log('Template<li>.sourceSpan', p(tpl.sourceSpan.start), p(tpl.sourceSpan.end), '; inner Element<li>.sourceSpan', p(el.sourceSpan.start), p(el.sourceSpan.end));
  console.log('Template<li> keys:', Object.keys(tpl).join(','));
}

console.log('\n=== B. escapes: Text values with escapedString true vs false (inline template with \\\' and \\n) ===');
{
  const file = '/fixture/src/app/inline.component.ts';
  const text = fs.readFileSync(file, 'utf8');
  const startPos = text.indexOf("'It\\'s") + 1;
  const endPos = text.indexOf("</button>'", startPos) + "</button>".length;
  const startLine = text.slice(0, startPos).split('\n').length - 1;
  const startCol = startPos - (text.lastIndexOf('\n', startPos) + 1);
  const range = { startPos, startLine, startCol, endPos };
  for (const esc of [true, false]) {
    const t = C.parseTemplate(text, file, { range, escapedString: esc });
    console.log(`escapedString=${esc}: top-level nodes: ${t.nodes.map((n) => `${n.constructor.name}(${q(n.value ?? n.name)}) ${p(n.sourceSpan.start)}..${p(n.sourceSpan.end)}`).join(' | ')}`);
  }
}

console.log('\n=== C. errors and broken templates ===');
const BROKEN = {
  'unterminated call  (click)="save("': '<button (click)="save(">x</button>',
  'empty handler      (click)=""': '<button (click)="">x</button>',
  'unclosed element': '<div><button (click)="a()">x</button>',
  'unclosed @if block': '@if (x) { <button (click)="a()">x</button>',
  'unknown block @foo': '@foo { <button (click)="a()">x</button> }',
  'two statements, bad second  save(); close(': '<button (click)="save(); close(">x</button>',
  'duplicate attribute': '<button (click)="a()" (click)="b()">x</button>',
  'handler with pipe  (click)="a() | p"': '<button (click)="a() | p">x</button>',
};
for (const [label, src] of Object.entries(BROKEN)) {
  for (const always of [false, true]) {
    try {
      const t = C.parseTemplate(src, 'broken.html', { alwaysAttemptHtmlToR3AstConversion: always });
      const evs = [...events(t.nodes)].map((e) => e.ev.handler.source + ' [' + (e.ev.handler.ast?.constructor.name) + ']');
      console.log(`${label} | always=${always}: errors=${t.errors ? JSON.stringify(t.errors.map((e) => `${e.level === 1 ? 'ERROR' : e.level} ${e.msg.split('\n')[0]} @${p(e.span.start)}`)) : 'null'} ; events=${JSON.stringify(evs)}`);
    } catch (e) { console.log(`${label} | always=${always}: THREW ${e.constructor.name}: ${String(e.message).split('\n')[0]}`); }
  }
}

console.log('\n=== D. CRLF copy of app.component.html ===');
{
  const crlf = html.replace(/\n/g, '\r\n');
  for (const opts of [{}, { preserveLineEndings: true }]) {
    const t = C.parseTemplate(crlf, htmlFile, opts);
    let exact = 0, offOnly = 0, bad = 0, total = 0;
    const examples = [];
    for (const { ev } of events(t.nodes)) {
      const exp = HTML_EVENTS.find(([, , h]) => h === ev.handler.source);
      if (!exp) continue;
      const e = expectedFor(crlf, exp[0], exp[2], exp[1]);
      for (const [l, s, x] of [['sourceSpan', ev.sourceSpan, e.source], ['keySpan', ev.keySpan, e.key], ['handlerSpan', ev.handlerSpan, e.handler]]) {
        total++;
        const c = cmpSpan(crlf, s, x);
        if (c.exact) exact++; else if (c.offsetsOK) offOnly++; else { bad++; if (examples.length < 3) examples.push(`${exp[0]} ${l}: ${c.text}${c.delta}`); }
      }
    }
    console.log(`options ${JSON.stringify(opts)}: spans checked ${total}: exact ${exact}, offsets right but line:col differ ${offOnly}, wrong ${bad}`);
    for (const x of examples) console.log('   ', x);
    const first = [...events(t.nodes)][0].ev;
    console.log('   first event handlerSpan covers', q(crlf.slice(first.handlerSpan.start.offset, first.handlerSpan.end.offset)), ' ; a label Text node value:', q([...walk(t.nodes)].find((w) => w.kind === 'Text').node.value));
  }
}

console.log('\n=== E. other syntax, one template ===');
{
  const src = [
    '<button (click)="$any(x).go()">a</button>',
    '<button (click)="a?.b()">b</button>',
    '<button (click)="items[0].run()">c</button>',
    '<button on-click="canon()">d</button>',
    '<button (click)="svc.a.b.c()">e</button>',
    '<button (click)="fn(1)(2)">f</button>',
    '<button (click)="a = b; c()">g</button>',
    '<button (click)="count.set(count() + 1)">h</button>',
    '<button (click)="x.y = 1">i</button>',
    '<button (click)="$event.stopPropagation()">j</button>',
    '<button (click)="cond && (a() || b())">k</button>',
    '<button (click)="a ?? b()">l</button>',
    '@switch (m) { @case (1) { <button (click)="inCase()">m</button> } @default { <button (click)="inDefault()">n</button> } }',
    '@defer (on idle) { <button (click)="inDefer()">o</button> } @placeholder { <button (click)="inPlaceholder()">p</button> }',
    '@let v = compute(); <button (click)="useLet(v)">q</button>',
    '<ng-container *ngIf="ok; else other"><button (click)="inIfDirective()">r</button></ng-container>',
    '<app-card (opened)="onOpened()" (closed)="onClosed($event)"></app-card>',
    '<button (@fade.done)="anim()">s</button>',
  ].join('\n');
  const t = C.parseTemplate(src, 'x.html', {});
  console.log('errors:', t.errors ? JSON.stringify(t.errors.map((e) => e.msg.split('\n')[0])) : 'null');
  for (const { ev, path: pth } of events(t.nodes)) {
    const calls = collectCalls(ev.handler).map((c) => `${c.receiver ?? '?'}.${c.method}${c.kind === 'SafeCall' ? ' (SafeCall)' : ''}`);
    console.log(`${q(ev.handler.source).padEnd(34)} name=${ev.name}${ev.target ? '@' + ev.target : ''}${ev.phase ? ' phase=' + ev.phase : ''} type=${ev.type}  AST=${ev.handler.ast.constructor.name}  calls=${JSON.stringify(calls)}  path=${pth}`);
  }
  console.log('\nAST of a few:');
  for (const { ev } of events(t.nodes)) if (['$any(x).go()', 'a?.b()', 'items[0].run()', 'fn(1)(2)', 'count.set(count() + 1)', 'x.y = 1', 'a ?? b()'].includes(ev.handler.source)) console.log(`  ${ev.handler.source} => ${render(ev.handler)}`);
}

console.log('\n=== F. API status of what we use ===');
for (const [label, dir, files] of [['@angular/compiler', `${nm}/@angular/compiler`, ['types/compiler.d.ts', 'types/_index-chunk.d.ts']], ['@angular/compiler-cli', `${nm}/@angular/compiler-cli`, ['index.d.ts']], ['@angular/language-service', `${nm}/@angular/language-service`, ['api.d.ts', 'index.d.ts', 'private.d.ts']]]) {
  for (const f of files) {
    const t = fs.readFileSync(path.join(dir, f), 'utf8');
    console.log(`${label}/${f}: ${t.length} chars, '@publicApi' occurrences ${t.split('@publicApi').length - 1}, '@internal' ${t.split('@internal').length - 1}, 'private' (case-insens) ${t.toLowerCase().split('private').length - 1}`);
  }
}
{
  const t = fs.readFileSync(`${nm}/@angular/compiler/types/compiler.d.ts`, 'utf8');
  const c = fs.readFileSync(`${nm}/@angular/compiler/types/_index-chunk.d.ts`, 'utf8');
  for (const [n, needle] of [['parseTemplate', 'declare function parseTemplate('], ['BoundEvent', 'declare class BoundEvent ']]) {
    for (const [f, src] of [['compiler.d.ts', t], ['_index-chunk.d.ts', c]]) {
      const i = src.indexOf(needle);
      if (i >= 0) console.log(`${n} in ${f}: the 300 chars before the declaration: ${q(src.slice(Math.max(0, i - 300), i))}`);
    }
  }
  const mjs = fs.readFileSync(`${nm}/@angular/compiler/fesm2022/compiler.mjs`, 'utf8');
  for (const needle of ['private', 'experimental']) {
    let i = -1, n = 0;
    while ((i = mjs.indexOf(needle, i + 1)) >= 0 && n < 400) { n++; const ctx = mjs.slice(Math.max(0, i - 120), i + 120).replace(/\s+/g, ' '); if (/All compiler apis|experimental and private/.test(ctx)) { console.log(`fesm2022/compiler.mjs mentions ${q(ctx)}`); break; } }
  }
}

console.log('\n=== G. host helpers: createHostElement / verifyHostBindings typings ===');
{
  const c = fs.readFileSync(`${nm}/@angular/compiler/types/_index-chunk.d.ts`, 'utf8') + fs.readFileSync(`${nm}/@angular/compiler/types/compiler.d.ts`, 'utf8');
  for (const needle of ['declare function createHostElement', 'declare function parseHostBindings', 'interface ParsedHostBindings', 'declare class HostElement']) {
    const i = c.indexOf(needle);
    console.log(`--- ${needle}: ${i < 0 ? 'NOT FOUND' : '\n' + c.slice(i, i + 900)}`);
  }
}
