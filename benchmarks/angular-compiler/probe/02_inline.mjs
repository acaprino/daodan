// Point 2: templates that live inside a string of a .ts file, and the `host` metadata.
import ts from 'typescript';
import { C, fs, events, reportEvents, cmpSpan, expectedFor, q, p, lc } from './_lib.mjs';

const EXPECT = {
  'inline.component.ts': {
    InlineComponent: [['(click)="go()"', 'click', 'go()'], ['(click)="this.goThis()"', 'click', 'this.goThis()']],
    InlineDoubleQuotedComponent: [],
    InlineEscapedComponent: [['(click)="esc()"', 'click', 'esc()'], ['(click)="esc2()"', 'click', 'esc2()']],
  },
  'editor.component.ts': { EditorComponent: [["(click)=\"saved.emit('done')\"", 'click', "saved.emit('done')"]] },
};

// How the template literal and its decorator are found: TypeScript's own parser (Daodan would use tree-sitter).
function components(file) {
  const text = fs.readFileSync(file, 'utf8');
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true);
  const out = [];
  const visit = (n) => {
    if (ts.isClassDeclaration(n)) {
      for (const d of ts.getDecorators(n) ?? []) {
        const call = d.expression;
        if (!ts.isCallExpression(call) || call.expression.getText() !== 'Component') continue;
        const obj = call.arguments[0];
        const rec = { cls: n.name.text, text, sf, template: null, host: null };
        for (const pr of obj.properties) {
          const name = pr.name?.getText();
          if (name === 'template') rec.template = pr.initializer;
          if (name === 'host') rec.host = pr.initializer;
        }
        out.push(rec);
      }
    }
    ts.forEachChild(n, visit);
  };
  visit(sf);
  return out;
}

function range(c) {
  const init = c.template;
  const startPos = init.getStart() + 1, endPos = init.getEnd() - 1;
  const { line, character } = c.sf.getLineAndCharacterOfPosition(startPos);
  return { startPos, startLine: line, startCol: character, endPos };
}

function compact(label, nodes, text, expList, shift) {
  const evs = [...events(nodes)];
  console.log(`  ${label}: ${evs.length} events`);
  for (const { ev } of evs) {
    const src = ev.handler.source;
    const exp = expList.find((e) => e[2] === src);
    if (!exp) { console.log(`    ?? handler ${q(src)} matches no expectation; sourceSpan ${p(ev.sourceSpan.start)}`); continue; }
    const e = expectedFor(text, exp[0], exp[2], exp[1]);
    const res = [['sourceSpan', ev.sourceSpan, e.source], ['keySpan', ev.keySpan, e.key], ['handlerSpan', ev.handlerSpan, e.handler]].map(([l, s, x]) => {
      const c = cmpSpan(text, s, x, shift);
      return `${l}=${c.exact ? 'EXACT' : c.offsetsOK ? 'offset-exact, line:col differ' : 'DIFF'}`;
    });
    const s0 = ev.sourceSpan;
    console.log(`    ${q(src)}  ${res.join(' ')}  sourceSpan start ${p(s0.start)} (+shift ${shift} => offset ${s0.start.offset + shift}), expected offset ${expectedFor(text, exp[0], exp[2], exp[1]).source[0]}`);
  }
}

for (const [f, byClass] of Object.entries(EXPECT)) {
  const file = `/fixture/src/app/${f}`;
  for (const c of components(file)) {
    const expList = byClass[c.cls];
    console.log(`\n##### ${f} :: ${c.cls}  template literal kind=${ts.SyntaxKind[c.template.kind]}`);
    const r = range(c);
    const cooked = c.template.text;
    const raw = c.text.slice(r.startPos, r.endPos);
    console.log(`  range ${JSON.stringify(r)} ; cooked length ${cooked.length}, raw length ${raw.length}, cooked===raw: ${cooked === raw}`);
    console.log(`  raw: ${q(raw)}`);

    // A: the cooked string alone, no options
    try { const t = C.parseTemplate(cooked, file, {}); compact('A cooked string, no options (offsets are inside the string)', t.nodes, cooked, expList.map(([a, n, h]) => [a, n, h]), 0); console.log(`     errors: ${t.errors ? t.errors.map((e) => e.msg) : 'null'}`); } catch (e) { console.log('  A threw', e.message); }

    // B: the cooked string alone WITH range+escapedString (range is relative to the .ts, text is not the .ts)
    try { const t = C.parseTemplate(cooked, file, { range: r, escapedString: true }); compact('B cooked string + range + escapedString', t.nodes, c.text, expList, 0); console.log(`     errors: ${t.errors ? t.errors.map((e) => e.msg) : 'null'}`); } catch (e) { console.log('  B threw', e.message); }

    // C: the whole .ts text, range of the literal contents, escapedString true
    for (const esc of [true, false]) {
      try {
        const t = C.parseTemplate(c.text, file, { range: r, escapedString: esc });
        compact(`C whole .ts text + range + escapedString=${esc}`, t.nodes, c.text, expList, 0);
        console.log(`     errors: ${t.errors ? t.errors.map((e) => e.msg) : 'null'}`);
      } catch (e) { console.log(`  C(${esc}) threw`, e.message); }
    }

    // E: the raw slice of the literal, escapedString true (offsets relative to the slice; add startPos)
    try { const t = C.parseTemplate(raw, file, { escapedString: true }); compact('E raw slice + escapedString=true (offsets inside the slice, shift = startPos)', t.nodes, c.text, expList, r.startPos); console.log(`     errors: ${t.errors ? t.errors.map((e) => e.msg) : 'null'}`); } catch (e) { console.log('  E threw', e.message); }
  }
}

// Full verbose report for the best-looking variant (C, escapedString true) on the two components of inline.component.ts
console.log('\n\n=== VERBOSE: variant C (whole .ts + range + escapedString=true) ===');
for (const c of components('/fixture/src/app/inline.component.ts')) {
  console.log(`\n##### ${c.cls}`);
  const t = C.parseTemplate(c.text, '/fixture/src/app/inline.component.ts', { range: range(c), escapedString: true });
  reportEvents(t.nodes, c.text, EXPECT['inline.component.ts'][c.cls]);
  const first = [...events(t.nodes)][0];
  if (first) console.log(`\n   file the spans point at: sourceSpan.start.file.url=${q(first.ev.sourceSpan.start.file.url)} content===.ts text: ${first.ev.sourceSpan.start.file.content === c.text}`);
}

// Label of an inline-template control: text children
console.log('\n=== label children, inline (variant C) ===');
for (const c of components('/fixture/src/app/inline.component.ts')) {
  const t = C.parseTemplate(c.text, '/fixture/src/app/inline.component.ts', { range: range(c), escapedString: true });
  for (const { ev, owner } of events(t.nodes)) {
    console.log(`${c.cls} <${owner.name}> ${ev.handler.source}: children=${owner.children.map((x) => `${x.constructor.name}(${q(x.value ?? '')}) ${p(x.sourceSpan.start)}`).join(' | ')}`);
  }
}

// Host metadata
console.log('\n=== host metadata ===');
console.log('exports mentioning host:', Object.keys(C).filter((n) => /host/i.test(n)).join(', '));
for (const c of components('/fixture/src/app/inline.component.ts')) {
  if (!c.host) continue;
  console.log(`${c.cls} host literal text: ${c.host.getText()}`);
  const obj = {};
  for (const pr of c.host.properties) obj[pr.name.text ?? pr.name.getText().slice(1, -1)] = pr.initializer.text;
  console.log('as a JS object:', JSON.stringify(obj));
  try {
    const r = C.parseHostBindings(obj);
    console.log('parseHostBindings ->', JSON.stringify(r, (k, v) => (typeof v === 'object' && v && v.constructor?.name !== 'Object' && !Array.isArray(v) ? `<${v.constructor.name}>` : v), 1));
  } catch (e) { console.log('parseHostBindings threw', e.message); }
  try { console.log('TmplAstHostElement source:', C.TmplAstHostElement.toString().slice(0, 600)); } catch (e) { console.log('TmplAstHostElement threw', e.message); }
}
