// Follow-up 3: escaped double quotes inside the string, CRLF inside an inline template, language service without a sleep.
import { C, fs, events, cmpSpan, q, p, lc } from './_lib.mjs';
import path from 'node:path';
import ts from 'typescript';

const file = '/fixture/src/app/inline.component.ts';
const lf = fs.readFileSync(file, 'utf8');

function literalOf(text, cls) {
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true);
  let init;
  const visit = (n) => {
    if (ts.isClassDeclaration(n) && n.name.text === cls) {
      const call = ts.getDecorators(n)[0].expression;
      for (const pr of call.arguments[0].properties) if (pr.name.getText() === 'template') init = pr.initializer;
    }
    ts.forEachChild(n, visit);
  };
  visit(sf);
  const startPos = init.getStart() + 1, endPos = init.getEnd() - 1;
  const { line, character } = sf.getLineAndCharacterOfPosition(startPos);
  return { init, range: { startPos, startLine: line, startCol: character, endPos } };
}

console.log('=== A. double-quoted string with \\" inside: InlineDoubleQuotedComponent ===');
{
  const { init, range } = literalOf(lf, 'InlineDoubleQuotedComponent');
  console.log('source text of the literal:', q(lf.slice(range.startPos - 1, range.endPos + 1)), '; cooked value:', q(init.text));
  const attr = '(click)=\\"dq()\\"';   // as written in the .ts: backslash before each quote
  const i = lf.indexOf(attr);
  console.log('attribute as written in the .ts found at', i, q(lf.slice(i, i + attr.length)));
  const exp = { source: [i, i + attr.length], key: [i + 1, i + 6], handler: [i + 10, i + 14] };
  for (const esc of [true, false]) {
    const t = C.parseTemplate(lf, file, { range, escapedString: esc });
    console.log(`escapedString=${esc}: errors=${t.errors ? JSON.stringify(t.errors.map((e) => e.msg.split('\n')[0])) : 'null'}`);
    for (const { ev } of events(t.nodes)) {
      console.log(`   event ${ev.name} handler.source=${q(ev.handler.source)}`);
      for (const [l, s, x] of [['sourceSpan', ev.sourceSpan, exp.source], ['keySpan', ev.keySpan, exp.key], ['handlerSpan', ev.handlerSpan, exp.handler]]) {
        const c = cmpSpan(lf, s, x);
        console.log(`      ${l.padEnd(11)} ${c.exact ? 'EXACT' : c.offsetsOK ? 'offset-exact, line:col differ' : 'DIFFERS'} ${c.text}${c.delta}`);
      }
    }
    const t0 = t.nodes[0];
    if (!t0) { console.log('   (no nodes returned; events found: ' + [...events(t.nodes)].length + ')'); continue; }
    console.log(`   label children of the button: ${t0.children.map((c) => `${c.constructor.name}(${q(c.value)}) ${p(c.sourceSpan.start)}..${p(c.sourceSpan.end)}`).join(' | ')}`);
  }
}

console.log('\n=== B. CRLF inside an inline .ts template (whole inline.component.ts converted to CRLF) ===');
{
  const crlf = lf.split('\n').join('\r\n');
  for (const [cls, attrs] of [['InlineComponent', [['(click)="go()"', 'go()'], ['(click)="this.goThis()"', 'this.goThis()']]]]) {
    const { range } = literalOf(crlf, cls);
    for (const esc of [true, false]) {
      for (const preserve of [false, true]) {
        const t = C.parseTemplate(crlf, file, { range, escapedString: esc, preserveLineEndings: preserve });
        const res = [];
        for (const { ev } of events(t.nodes)) {
          const [attr, h] = attrs.find(([, hh]) => hh === ev.handler.source);
          const i = crlf.indexOf(attr);
          const exp = { source: [i, i + attr.length], key: [i + 1, i + 6], handler: [i + 9, i + 9 + h.length] };
          for (const [l, s, x] of [['sourceSpan', ev.sourceSpan, exp.source], ['keySpan', ev.keySpan, exp.key], ['handlerSpan', ev.handlerSpan, exp.handler]]) {
            const c = cmpSpan(crlf, s, x);
            res.push(`${h}.${l}=${c.exact ? 'EXACT' : c.offsetsOK ? 'offset-exact,line:col-differ' : 'DIFF ' + c.delta}`);
          }
        }
        console.log(`escapedString=${esc} preserveLineEndings=${preserve}: ${res.join(' ')}`);
      }
    }
  }
}

console.log('\n=== C. language service with NO sleep after openClientFile ===');
{
  const logger = { close() {}, hasLevel: () => false, loggingEnabled: () => false, perftrc() {}, info() {}, startGroup() {}, endGroup() {}, msg() {}, getLogFileName: () => undefined };
  const ps = new ts.server.ProjectService({
    host: ts.sys, logger, cancellationToken: ts.server.nullCancellationToken, useSingleInferredProject: false, useInferredProjectPerProjectRoot: false,
    typingsInstaller: ts.server.nullTypingsInstaller, session: undefined, eventHandler: () => {},
    globalPlugins: ['@angular/language-service'], pluginProbeLocations: ['/fixture/node_modules'], allowLocalPluginLoads: true, suppressDiagnosticEvents: true,
  });
  const tsFile = '/fixture/src/app/app.component.ts';
  const htmlFile = '/fixture/src/app/app.component.html';
  const t0 = Date.now();
  ps.openClientFile(tsFile);
  const project = ps.getDefaultProjectForFile(ts.server.toNormalizedPath(tsFile), true);
  const ls = project.getLanguageService();
  console.log(`immediately after openClientFile (${Date.now() - t0} ms): getComponentLocationsForTemplate is ${typeof ls.getComponentLocationsForTemplate}`);
  const html = fs.readFileSync(htmlFile, 'utf8');
  try {
    const d = ls.getDefinitionAndBoundSpan(htmlFile, html.indexOf('save()"') + 1);
    console.log(`definition of save with no sleep (${Date.now() - t0} ms):`, d ? JSON.stringify(d.definitions?.map((x) => `${path.relative('/fixture', x.fileName)} ${x.name} ${x.kind}`)) : d);
  } catch (e) { console.log('threw', e.message); }
  try { console.log('getComponentLocationsForTemplate no sleep:', JSON.stringify(ls.getComponentLocationsForTemplate?.(htmlFile))); } catch (e) { console.log('threw', e.message); }
}
process.exit(0);
