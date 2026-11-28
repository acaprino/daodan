// Daodan's script for `angular.py`, run in Daodan's container, in the folder of an Angular project whose packages are
// restored. The last argument is the path of the JSON list of templates to read, `{f: file, c: [[file, class, line], ...]}` or
// `{f: file, r: [row, column, row, column], c: ...}` (`r`: the content of a `template` written in a decorator, the file is
// read whole, as the compiler takes it with `range`; `c`: the components that use the template).
//
// Without a flag it calls the `parseTemplate` of the `@angular/compiler` the project installed (resolved from the working
// folder, not from this script's) and prints, as JSON, for each template its parse errors and each event it binds: where,
// the name as written, and the calls its handler makes with the object each is made on (null: the component itself; "this").
// A call with no object before it names a method of the class unless the template declares the name (`let-c` of an
// ng-template, an `@let`, the variable of an `@for`): `parseTemplate` does not resolve scopes, the compiler's own binder does
// (`R3TargetBinder`, `getExpressionTarget`), and that call carries its `scope`. What the script cannot read is in `unread`.
// Exit 3: the project has no `@angular/compiler`. Exit 4: the one it has lacks what this script calls.
// shortcut: the first pass needs only `@angular/compiler`, which every Angular project has, so it does not ask the type-checker
// for the template (`ttc.getTemplate`), which needs the project's program; a project whose program does not build still gives
// its events. The `host` metadata and `@HostListener` of a component are not read, and an event of the DOM is not told from an
// output of a child component (the type-checker tells both: `getHostElement`, `getSymbolOfNode` of an event); do it when a
// project's entries are measured to miss them.
//
// With `--types` it asks the project's own template type-checker (`@angular/compiler-cli`, over the `tsconfig.json` of the
// working folder, or over the projects it references when that has no file of its own: a solution-style `tsconfig.json`) which
// declaration each call on another object is, for each component of each template: `getTemplate` gives the nodes the compiler
// holds, `getSymbolOfNode` the symbol of a call's method and `getTsSymbolOfSymbol` its TypeScript declaration,
// `{f: file relative to the folder, l: line, n: name}`. What it cannot give is an `error` that names the package, the file or
// the component.
// shortcut: the type-checker is refused unless its internal option `_enableTemplateTypeChecker` is on
// (`benchmarks/angular-compiler/results/10_symbols_options.txt`) and `getTsSymbolOfSymbol` is a method Angular does not document;
// a version that changes them gives an `error` for each call. A `tsconfig.json` with no `files` and no `include` makes the
// program of the whole folder: the cost grows with the project, bounded by the time `angular.py` gives the command.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

function stop(message, code) {
  process.stderr.write(`daodan-angular: ${message}\n`);
  process.exit(code);
}
const first = (error) => String(error?.message ?? error).split('\n')[0].slice(0, 300);

const args = process.argv.slice(2);
const types = args[0] === '--types';
const jobs = JSON.parse(args.length ? fs.readFileSync(args.at(-1), 'utf8') : stop('no list of templates was given', 2));
const folder = process.cwd();
const require = createRequire(`${folder}/`);
let compiler;
try {
  const loaded = await import(pathToFileURL(require.resolve('@angular/compiler')).href);
  compiler = typeof loaded.parseTemplate === 'function' ? loaded : loaded.default;
} catch (error) {
  stop(`@angular/compiler is not installed for ${folder}: ${first(error)}`, 3);
}
const wanted = ['parseTemplate', 'tmplAstVisitAll', 'TmplAstRecursiveVisitor', 'RecursiveAstVisitor', 'R3TargetBinder'];
const lacking = wanted.filter((name) => !compiler?.[name]);
if (lacking.length) stop(`this @angular/compiler exports no ${lacking.join(', ')}`, 4);
const versionOf = (name) => { try { return require(`${name}/package.json`).version; } catch { return null; } };

// The object a call is made on, as the name chain the template writes: `svc` in `svc.cancel()`.
function chain(ast) {
  const kind = ast.constructor.name;
  if (kind === 'ImplicitReceiver') return '';
  if (kind === 'ThisReceiver') return 'this';
  if (kind === 'PropertyRead' || kind === 'SafePropertyRead') {
    const on = chain(ast.receiver);
    return (on ? `${on}${kind === 'SafePropertyRead' ? '?.' : '.'}` : '') + ast.name;
  }
  return `<${kind}>`;
}

// The calls of a handler whose callee is a name: `found` for the output, `nodes` the callees in the same order; a call it cannot
// read is in `unread`, with why.
class Calls extends compiler.RecursiveAstVisitor {
  found = [];
  nodes = [];
  unread = [];
  note(ast) {
    const callee = ast.receiver;
    const kind = callee.constructor.name;
    if (kind !== 'PropertyRead' && kind !== 'SafePropertyRead') {
      this.unread.push(`the callee of a call is no name (${kind}): the call is not read`);
      return;
    }
    const on = chain(callee.receiver);
    this.found.push({ on: on === '' ? null : on, name: callee.name });
    this.nodes.push(callee);
  }
  visitCall(ast, context) { this.note(ast); return super.visitCall(ast, context); }
  visitSafeCall(ast, context) { this.note(ast); return super.visitSafeCall(ast, context); }
  // shortcut: Angular up to 12 writes a call as `MethodCall`, not `Call`; those versions are not read, and the template says so.
  visitMethodCall(ast, context) { this.unread.push('this version of Angular writes a call as MethodCall: it is not read'); return super.visitMethodCall?.(ast, context); }
  visitSafeMethodCall(ast, context) { this.unread.push('this version of Angular writes a call as SafeMethodCall: it is not read'); return super.visitSafeMethodCall?.(ast, context); }
}

const SCOPES = { Variable: 'variable', Reference: 'reference', LetDeclaration: '@let' };

class Events extends compiler.TmplAstRecursiveVisitor {
  constructor(text, bound) { super(); this.text = text; this.bound = bound; this.found = []; this.nodes = new Map(); this.seen = new Set(); }
  visitBoundEvent(event) {
    const at = event.sourceSpan.start;
    if (this.seen.has(at.offset)) return; // an element with `*ngFor` holds the same event on itself and on its template
    this.seen.add(at.offset);
    const calls = new Calls();
    calls.visit(event.handler.ast ?? event.handler);
    this.nodes.set(`${at.line + 1}:${at.col}`, calls.nodes);
    // a call with no object before it: the name may be one the template declares, which the binder knows and the parser does not
    const found = calls.found.map((call, index) => {
      const target = this.bound && call.on === null ? this.bound.getExpressionTarget(calls.nodes[index]) : null;
      return target ? { ...call, scope: SCOPES[target.constructor.name] ?? target.constructor.name } : call;
    });
    this.found.push({
      line: at.line + 1, col: at.col, name: this.text.slice(event.keySpan.start.offset, event.keySpan.end.offset),
      type: event.type, target: event.target, handler: event.handler.source ?? null, calls: found,
      ...(calls.unread.length ? { unread: calls.unread } : {}),
    });
  }
}

const texts = new Map();
const read = (file) => { if (!texts.has(file)) texts.set(file, fs.readFileSync(file, 'utf8')); return texts.get(file); };

// The template of a job parsed by the compiler: its parse errors and the events with their calls.
function parseJob(job) {
  const text = read(job.f);
  let options = {};
  if (job.r) {
    const starts = [0];
    for (let i = 0; i < text.length; i++) if (text[i] === '\n') starts.push(i + 1);
    const [startLine, startCol, endLine, endCol] = job.r;
    options = { range: { startPos: starts[startLine] + startCol, startLine, startCol, endPos: starts[endLine] + endCol }, escapedString: true };
  }
  const parsed = compiler.parseTemplate(text, job.f, options);
  const bound = new compiler.R3TargetBinder(null).bind({ template: parsed.nodes });
  if (typeof bound.getExpressionTarget !== 'function') throw new Error('this @angular/compiler has no BoundTarget.getExpressionTarget');
  const visitor = new Events(text, bound);
  compiler.tmplAstVisitAll(visitor, parsed.nodes);
  const errors = parsed.errors ? parsed.errors.slice(0, 3).map((error) => String(error).slice(0, 300)) : null;
  return { errors, events: visitor.found };
}

const record = (job) => ({ f: job.f, ...(job.r ? { r: job.r } : {}) });

if (!types) {
  const templates = [];
  for (const job of jobs) {
    try {
      templates.push({ ...record(job), ...parseJob(job) });
    } catch (error) {
      templates.push({ ...record(job), error: first(error) });
    }
  }
  process.stdout.write(JSON.stringify({ compiler: versionOf('@angular/compiler'), templates }));
} else {
  process.stdout.write(JSON.stringify(await resolveTypes()));
}

// The declaration of each call on another object, by component: asked of the type-checker of `@angular/compiler-cli`.
async function resolveTypes() {
  const started = Date.now();
  const done = (more) => ({ compiler_cli: versionOf('@angular/compiler-cli'), seconds: (Date.now() - started) / 1000, resolved: [], ...more });
  // which calls are on another object, by the parse the compiler gives: if none, no program is built
  const asked = [];
  for (const job of jobs) {
    let parsed;
    try { parsed = parseJob(job); } catch { continue; } // the parse command says why
    for (const event of parsed.events) {
      const calls = event.calls.map((call, index) => (call.on === null || call.on === 'this' ? -1 : index)).filter((index) => index >= 0);
      for (const component of calls.length ? job.c ?? [] : []) asked.push({ job, component, event, calls });
    }
  }
  if (!asked.length) return done({ note: 'no call is made on another object' });
  let cli;
  let ts;
  try { cli = await import(pathToFileURL(require.resolve('@angular/compiler-cli')).href); } catch (error) {
    return done({ error: `@angular/compiler-cli is not installed for ${folder}: ${first(error)}` });
  }
  try { ts = require('typescript'); } catch (error) {
    return done({ error: `typescript is not installed for ${folder}: ${first(error)}` });
  }
  const configFile = path.join(folder, 'tsconfig.json');
  if (!fs.existsSync(configFile)) return done({ error: `tsconfig.json is not in ${folder}` });
  // The programs to look a component up in: the folder's `tsconfig.json`, or, when it has no file of its own (solution-style: `files`
  // is empty and `references` lists the projects), each project it references. Each is built when a component is not in the ones before.
  const files = [configFile];
  try {
    const raw = ts.readConfigFile(configFile, ts.sys.readFile).config ?? {};
    const own = cli.readConfiguration(configFile).rootNames.length;
    if (!own && Array.isArray(raw.references) && raw.references.length) {
      files.length = 0;
      for (const reference of raw.references) {
        const target = path.resolve(path.dirname(configFile), reference.path);
        files.push(fs.existsSync(target) && fs.statSync(target).isDirectory() ? path.join(target, 'tsconfig.json') : target);
      }
    }
  } catch (error) {
    return done({ error: `${configFile} was not read: ${first(error)}` });
  }
  const programs = files.map((file) => ({ file, built: null }));
  const build = async (entry) => {
    if (!entry.built) {
      entry.built = (async () => {
        const config = cli.readConfiguration(entry.file);
        config.options._enableTemplateTypeChecker = true;
        const program = cli.createProgram({ rootNames: config.rootNames, options: config.options, host: cli.createCompilerHost({ options: config.options }) });
        await program.loadNgStructureAsync();
        return { roots: config.rootNames.length, ttc: program.compiler.getTemplateTypeChecker(), tsProgram: program.getTsProgram() };
      })();
    }
    return entry.built;
  };
  const classIn = (tsProgram, file, name, line) => {
    const source = tsProgram.getSourceFile(path.resolve(folder, file));
    if (!source) return null;
    const found = [];
    const visit = (node) => { if (ts.isClassDeclaration(node) && node.name?.text === name) found.push(node); ts.forEachChild(node, visit); };
    visit(source);
    return found.find((node) => source.getLineAndCharacterOfPosition(node.name.getStart(source)).line + 1 === line) ?? (found.length === 1 ? found[0] : null);
  };
  // the component, in the first program that has it, with the template nodes the compiler holds for it: asked once
  const held = new Map();
  const find = async ([file, name, line]) => {
    const tried = [];
    for (const entry of programs) {
      let built;
      try { built = await build(entry); } catch (error) { tried.push(`${path.relative(folder, entry.file)} (not built: ${first(error)})`); continue; }
      tried.push(`${path.relative(folder, entry.file)} (${built.roots} root files)`);
      const node = classIn(built.tsProgram, file, name, line);
      if (!node) continue;
      try {
        const template = built.ttc.getTemplate(node);
        if (!template) return { why: `the type-checker holds no template for ${name}` };
        const events = new Events('', null);
        compiler.tmplAstVisitAll(events, template);
        return { node, ttc: built.ttc, events };
      } catch (error) { return { why: `the type-checker did not give the template of ${name}: ${first(error)}` }; }
    }
    return { why: `${name} (${file}:${line}) is not in the program of ${tried.join(', ')}` };
  };
  const resolved = [];
  for (const { job, component, event, calls } of asked) {
    const base = { ...record(job), c: component, line: event.line, col: event.col };
    const fail = (index, error) => resolved.push({ ...base, i: index, decl: null, error });
    const key = component.join('::');
    if (!held.has(key)) held.set(key, await find(component));
    const have = held.get(key);
    const callees = have.events?.nodes.get(`${event.line}:${event.col}`);
    for (const index of calls) {
      if (!callees || !callees[index]) { fail(index, have.why ?? `the type-checker's template of ${component[1]} has no such call at ${event.line}:${event.col}`); continue; }
      try {
        const symbol = have.ttc.getSymbolOfNode(callees[index], have.node);
        const declared = symbol ? (typeof have.ttc.getTsSymbolOfSymbol === 'function' ? have.ttc.getTsSymbolOfSymbol(symbol) : symbol.tsSymbol) : null;
        const declaration = declared?.declarations?.[0];
        if (!declaration) { fail(index, `the type-checker gives no declaration for ${event.calls?.[index]?.name ?? 'the call'}`); continue; }
        const source = declaration.getSourceFile();
        const at = source.getLineAndCharacterOfPosition((declaration.name ?? declaration).getStart(source));
        resolved.push({ ...base, i: index, decl: { f: path.relative(folder, source.fileName).split(path.sep).join('/'), l: at.line + 1, n: declared.name }, error: null });
      } catch (error) { fail(index, `the type-checker failed on the call: ${first(error)}`); }
    }
  }
  return done({ resolved });
}
