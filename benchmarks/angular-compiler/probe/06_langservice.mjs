// Point 5b: @angular/language-service: typings, where getComponentLocationsForTemplate comes from, and an attempt to drive it from a script.
import { fs, q } from './_lib.mjs';
import path from 'node:path';
import ts from 'typescript';
const nm = '/fixture/node_modules/@angular/language-service';
for (const f of ['index.d.ts', 'private.d.ts', 'plugin-factory.d.ts']) console.log(`--- ${f}\n${fs.readFileSync(path.join(nm, f), 'utf8')}`);
const api = fs.readFileSync(path.join(nm, 'api.d.ts'), 'utf8');
for (const needle of ['getComponentLocationsForTemplate', 'getTemplateLocationForComponent', 'interface NgLanguageService', 'Entry point']) {
  const i = api.indexOf(needle);
  console.log(`--- api.d.ts ${needle}: ${i < 0 ? 'NOT FOUND' : '\n' + api.slice(Math.max(0, i - 400), i + 500)}`);
}
console.log('bundles:', fs.readdirSync(path.join(nm, 'bundles')));
// Where the implementation gets its answer
for (const f of fs.readdirSync(path.join(nm, 'bundles')).filter((x) => x.endsWith('.js'))) {
  const t = fs.readFileSync(path.join(nm, 'bundles', f), 'utf8');
  for (const needle of ['getComponentLocationsForTemplate(', 'getTemplateLocationForComponent(']) {
    let i = t.indexOf(needle), n = 0;
    while (i >= 0 && n < 3) { console.log(`--- bundles/${f} ${needle} @${i}:\n${t.slice(Math.max(0, i - 100), i + 700)}`); i = t.indexOf(needle, i + 1); n++; }
  }
}
console.log('\nts.server present:', typeof ts.server, 'ProjectService:', typeof ts.server?.ProjectService, 'sys.require:', typeof ts.sys.require);

// Drive it: a ProjectService with the Angular plugin as a global plugin.
const logger = { close() {}, hasLevel: () => false, loggingEnabled: () => false, perftrc() {}, info() {}, startGroup() {}, endGroup() {}, msg() {}, getLogFileName: () => undefined };
const pendingEvents = [];
let ps;
try {
  ps = new ts.server.ProjectService({
    host: ts.sys, logger, cancellationToken: ts.server.nullCancellationToken, useSingleInferredProject: false, useInferredProjectPerProjectRoot: false,
    typingsInstaller: ts.server.nullTypingsInstaller, session: undefined, eventHandler: (e) => pendingEvents.push(e.eventName),
    globalPlugins: ['@angular/language-service'], pluginProbeLocations: ['/fixture/node_modules'], allowLocalPluginLoads: true, suppressDiagnosticEvents: true,
  });
  console.log('ProjectService created');
} catch (e) { console.log('ProjectService threw', e.stack.split('\n').slice(0, 4).join(' | ')); }
if (ps) {
  const tsFile = '/fixture/src/app/app.component.ts';
  const htmlFile = '/fixture/src/app/app.component.html';
  try {
    const r = ps.openClientFile(tsFile);
    console.log('openClientFile ->', JSON.stringify({ configFileName: r.configFileName, errors: r.configFileErrors?.length }));
    await new Promise((res) => setTimeout(res, 1500));
    const project = ps.getDefaultProjectForFile(ts.server.toNormalizedPath(tsFile), true);
    console.log('project:', project?.constructor.name, project?.getProjectName?.());
    const ls = project.getLanguageService();
    console.log('language service has getComponentLocationsForTemplate:', typeof ls.getComponentLocationsForTemplate, ' getTemplateLocationForComponent:', typeof ls.getTemplateLocationForComponent);
    const where = (s) => `${path.relative('/fixture', s.fileName)} start=${s.textSpan.start} length=${s.textSpan.length}`;
    if (typeof ls.getComponentLocationsForTemplate === 'function') {
      const comps = ls.getComponentLocationsForTemplate(htmlFile);
      console.log(`getComponentLocationsForTemplate(${htmlFile}) ->`, comps.map(where), comps.map((s) => q(fs.readFileSync(s.fileName, 'utf8').slice(s.textSpan.start, s.textSpan.start + s.textSpan.length).slice(0, 80))));
      const tsText = fs.readFileSync(tsFile, 'utf8');
      const pos = tsText.indexOf('export class AppComponent') + 20;
      const tpl = ls.getTemplateLocationForComponent(tsFile, pos);
      console.log(`getTemplateLocationForComponent(${tsFile}, ${pos}) ->`, tpl ? where(tpl) : tpl);
      // and the handler -> method question, through go-to-definition in the template
      const html = fs.readFileSync(htmlFile, 'utf8');
      for (const needle of ['save()"', 'svc.cancel()', 'busy ? close()']) {
        const off = html.indexOf(needle) + (needle.startsWith('svc') ? 5 : 0);
        try {
          const d = ls.getDefinitionAndBoundSpan(htmlFile, off);
          console.log(`getDefinitionAndBoundSpan(html, ${off} "${needle}") ->`, d ? JSON.stringify({ textSpan: d.textSpan, defs: d.definitions?.map((x) => `${path.relative('/fixture', x.fileName)} ${x.name} ${x.kind} start=${x.textSpan.start}`) }) : d);
        } catch (e) { console.log('getDefinitionAndBoundSpan threw', e.message); }
      }
    }
  } catch (e) { console.log('driving threw', e.stack.split('\n').slice(0, 6).join(' | ')); }
  console.log('tsserver events seen:', [...new Set(pendingEvents)]);
}
process.exit(0);
