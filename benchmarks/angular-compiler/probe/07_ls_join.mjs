// Point 5b, systematic: for every handler call that parseTemplate finds, ask the Angular language service
// (driven from a script through ts.server.ProjectService) for the definition at the method-name position.
import { C, fs, events, collectCalls, q, p } from './_lib.mjs';
import path from 'node:path';
import ts from 'typescript';

const logger = { close() {}, hasLevel: () => false, loggingEnabled: () => false, perftrc() {}, info() {}, startGroup() {}, endGroup() {}, msg() {}, getLogFileName: () => undefined };
const ps = new ts.server.ProjectService({
  host: ts.sys, logger, cancellationToken: ts.server.nullCancellationToken, useSingleInferredProject: false, useInferredProjectPerProjectRoot: false,
  typingsInstaller: ts.server.nullTypingsInstaller, session: undefined, eventHandler: () => {},
  globalPlugins: ['@angular/language-service'], pluginProbeLocations: ['/fixture/node_modules'], allowLocalPluginLoads: true, suppressDiagnosticEvents: true,
});
const tsFile = '/fixture/src/app/app.component.ts';
const t0 = Date.now();
ps.openClientFile(tsFile);
await new Promise((res) => setTimeout(res, 1500));
const project = ps.getDefaultProjectForFile(ts.server.toNormalizedPath(tsFile), true);
const ls = project.getLanguageService();
console.log(`project ${project.getProjectName()} loaded in ${Date.now() - t0} ms; Angular methods present: ${typeof ls.getComponentLocationsForTemplate}`);

const lcOf = (text, off) => { let line = 0, col = 0; for (let i = 0; i < off; i++) { if (text[i] === '\n') { line++; col = 0; } else col++; } return `${line}:${col}`; };
function def(file, off) {
  try {
    const d = ls.getDefinitionAndBoundSpan(file, off);
    if (!d) return 'null';
    const txt = fs.readFileSync(file, 'utf8');
    return `boundSpan ${q(txt.slice(d.textSpan.start, d.textSpan.start + d.textSpan.length))} -> ` + (d.definitions ?? []).map((x) => {
      const t = fs.readFileSync(x.fileName, 'utf8');
      return `${path.relative('/fixture', x.fileName)}:${lcOf(t, x.textSpan.start)} ${x.kind} ${q(x.name)} container=${q(x.containerName)}`;
    }).join(' ; ');
  } catch (e) { return 'THREW ' + String(e.message).split('\n')[0]; }
}

console.log('\n=== external template: every event, key position and every call ===');
{
  const f = '/fixture/src/app/app.component.html';
  const text = fs.readFileSync(f, 'utf8');
  const seen = new Set();
  for (const { ev } of events(C.parseTemplate(text, f, {}).nodes)) {
    if (seen.has(ev)) continue; seen.add(ev);
    console.log(`\n${q(ev.sourceSpan.start.offset + ':' + ev.handler.source)}  event ${ev.name}${ev.target ? '@' + ev.target : ''}`);
    console.log(`   definition at the event name (keySpan.start ${ev.keySpan.start.offset}): ${def(f, ev.keySpan.start.offset)}`);
    const calls = collectCalls(ev.handler);
    for (const c of calls) console.log(`   call ${q(c.callee)}: ${c.nameSpan ? def(f, c.nameSpan.start) : '(no nameSpan)'}`);
    if (calls.length === 0) console.log(`   (no call) definition at handlerSpan.start ${ev.handlerSpan.start.offset}: ${def(f, ev.handlerSpan.start.offset)}`);
  }
}

console.log('\n=== inline templates in .ts: positions from parseTemplate (range + escapedString) given to the language service ===');
for (const [name, file] of [['InlineComponent', '/fixture/src/app/inline.component.ts'], ['EditorComponent', '/fixture/src/app/editor.component.ts']]) {
  const text = fs.readFileSync(file, 'utf8');
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true);
  const tmpls = [];
  const visit = (n) => { if (ts.isPropertyAssignment(n) && n.name.getText() === 'template' && (ts.isStringLiteral(n.initializer) || ts.isNoSubstitutionTemplateLiteral(n.initializer))) tmpls.push(n.initializer); ts.forEachChild(n, visit); };
  visit(sf);
  for (const init of tmpls) {
    const startPos = init.getStart() + 1, endPos = init.getEnd() - 1;
    const { line, character } = sf.getLineAndCharacterOfPosition(startPos);
    const t = C.parseTemplate(text, file, { range: { startPos, startLine: line, startCol: character, endPos }, escapedString: true });
    for (const { ev } of events(t.nodes)) {
      console.log(`\n${path.basename(file)} event ${ev.name} ${q(ev.handler.source)}  (sourceSpan.start ${ev.sourceSpan.start.offset})`);
      console.log(`   definition at the event name: ${def(file, ev.keySpan.start.offset)}`);
      for (const c of collectCalls(ev.handler)) console.log(`   call ${q(c.callee)}: ${c.nameSpan ? def(file, c.nameSpan.start) : '(no nameSpan)'}`);
    }
  }
}

console.log('\n=== host: {...} listeners: definition at the handler text inside the string ===');
{
  const file = '/fixture/src/app/inline.component.ts';
  const text = fs.readFileSync(file, 'utf8');
  for (const needle of ['onHost', 'onEsc', 'active']) {
    const off = text.indexOf(`'${needle}`) + 1;
    const off2 = needle === 'active' ? text.indexOf("'active'") + 1 : off;
    console.log(`${needle} (offset ${off2}): ${def(file, off2)}`);
  }
}

console.log('\n=== getTemplateLocationForComponent for the inline component ===');
{
  const file = '/fixture/src/app/inline.component.ts';
  const text = fs.readFileSync(file, 'utf8');
  for (const cls of ['InlineComponent', 'InlineEscapedComponent']) {
    const pos = text.indexOf(`export class ${cls}`) + 14;
    const r = ls.getTemplateLocationForComponent(file, pos);
    console.log(`${cls}: ${r ? `${path.relative('/fixture', r.fileName)} textSpan ${JSON.stringify(r.textSpan)} covers ${q(fs.readFileSync(r.fileName, 'utf8').slice(r.textSpan.start, r.textSpan.start + r.textSpan.length).slice(0, 60))}...` : r}`);
  }
}
process.exit(0);
