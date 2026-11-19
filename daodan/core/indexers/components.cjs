// Written by Daodan (`indexers/components.py`): each Vue component of the copy turned into the TypeScript Vue's
// own tool generates, beside it, for scip-typescript, with the map back to it; Svelte components scip-typescript
// turns itself, with the svelte2tsx it depends on, which is named.
//
//     node components.cjs COMPONENTS_JSON WORK OURS OUT_JSON INDEXER
//
// COMPONENTS_JSON lists `{rel, kind, ts}`. Vue's tool is the project's, found from the component's folder or
// through the package that depends on it (pnpm keeps it there), else the one Daodan installed under OURS, also in
// place of a project's tool older than its language plugin (2.0), whose version the record keeps (`instead`); it reads
// with the project's TypeScript, else with the indexer's (INDEXER, scip-typescript's package folder). Then the
// imports of a component the program's TypeScript resolves to nothing, with the module resolution that left them.
// OUT_JSON gets the tools used and, per component, its generated file and map, or the tool's error.
"use strict";
const fs = require("fs");
const path = require("path");
const { createRequire } = require("module");

const [list, work, ours, output, indexer] = process.argv.slice(2);
const VUE = ["@vue/language-core", ["vue-tsc", "@vue/language-server", "@vue/typescript-plugin"]];  // and dependents

function packageOf(entry) {  // the folder of the package.json above a resolved file
  let folder = path.dirname(entry);
  while (!fs.existsSync(path.join(folder, "package.json")) && path.dirname(folder) !== folder) {
    folder = path.dirname(folder);
  }
  return folder;
}

function resolve(from, name) {
  try {
    return createRequire(path.join(from, "noop.js")).resolve(name);
  } catch {
    return null;
  }
}

function version(entry) {
  return JSON.parse(fs.readFileSync(path.join(packageOf(entry), "package.json"), "utf8")).version;
}

function vueTool(folder) {  // `{entry, from}` of the tool for a component in `folder`, `instead` the project's left
  const [name, via] = VUE;
  const bases = [folder, ...via.map((other) => resolve(folder, other)).filter(Boolean).map(packageOf)];
  let instead = null;
  for (const base of bases) {
    const entry = resolve(base, name);
    if (!entry) continue;
    // Before 2.0 the tool has no language plugin (1.8.8 exports createVueLanguage): Daodan's then, and said.
    let plugin = null;
    try {
      plugin = require(entry).createVueLanguagePlugin;
    } catch {}
    if (typeof plugin === "function") return { entry, from: "project" };
    instead = version(entry);
    break;
  }
  const entry = resolve(ours, name);
  return entry ? { entry, from: "daodan", ...(instead ? { instead } : {}) } : null;
}

function starts(text) {  // the offset of each line's first character, in UTF-16 code units
  const out = [0];
  for (let i = 0; i < text.length; i++) if (text[i] === "\n") out.push(i + 1);
  return out;
}

const plugins = new Map();  // tool entry and tsconfig -> the language plugin

function vue(found, file, text) {
  const core = require(found.entry);
  const ts = require(resolve(path.dirname(file), "typescript") || resolve(indexer, "typescript"));
  let config = path.dirname(file);
  while (!fs.existsSync(path.join(config, "tsconfig.json")) && config !== work && path.dirname(config) !== config) {
    config = path.dirname(config);
  }
  config = path.join(config, "tsconfig.json");
  const key = `${found.entry}|${config}`;
  if (!plugins.has(key)) {
    const parsed = fs.existsSync(config) ? core.createParsedCommandLine(ts, ts.sys, config) : { options: {} };
    plugins.set(key, core.createVueLanguagePlugin(ts, parsed.options || {},
                                                  parsed.vueOptions || core.getDefaultCompilerOptions(), (id) => id));
  }
  const virtual = plugins.get(key).createVirtualCode(file, "vue", ts.ScriptSnapshot.fromString(text),
                                                     { getAssociatedScript: () => undefined });
  let script = null;
  (function find(code) {
    for (const item of code.embeddedCodes || []) {
      if (!script && /^script_(js|jsx|ts|tsx)$/.test(item.id)) script = item;
      find(item);
    }
  })(virtual);
  if (!script) throw new Error("no script generated");
  const code = script.snapshot.getText(0, script.snapshot.getLength());
  const spans = [];
  for (const mapping of script.mappings) {
    if (!mapping.data || !mapping.data.navigation) continue;  // the positions a definition is asked at
    mapping.sourceOffsets.forEach((source, i) => {
      const length = mapping.lengths[i];
      if (!mapping.generatedLengths || mapping.generatedLengths[i] === length) {
        spans.push([mapping.generatedOffsets[i], source, length]);
      }
    });
  }
  return { code, extension: /x$/.test(script.id) ? ".tsx" : ".ts", map: { kind: "volar", spans, starts: starts(code) } };
}

function unresolved() {  // `{importer: [specifier]}`: the imports of a component the program resolves to nothing
  const ts = require(resolve(indexer, "typescript"));
  const config = ts.getParsedCommandLineOfConfigFile(path.join(work, "tsconfig.json"), {},
    { ...ts.sys, onUnRecoverableConfigFileDiagnostic() {} });
  const out = {};
  for (const file of config ? config.fileNames : []) {
    if (!/\.[cm]?[jt]sx?$/.test(file)) continue;
    const mode = ts.getImpliedNodeFormatForFile ? ts.getImpliedNodeFormatForFile(file, undefined, ts.sys,
                                                                                config.options) : undefined;
    for (const { fileName } of ts.preProcessFile(fs.readFileSync(file, "utf8"), true, true).importedFiles) {
      if (!/\.vue$/.test(fileName)) continue;
      const done = ts.resolveModuleName(fileName, file, config.options, ts.sys, undefined, undefined, mode);
      if (!done.resolvedModule) (out[path.relative(work, file).split(path.sep).join("/")] ||= []).push(fileName);
    }
  }
  return { unresolved: out, resolution: ts.ModuleResolutionKind[ts.getEmitModuleResolutionKind(config.options)] };
}

const components = JSON.parse(fs.readFileSync(list, "utf8"));
const result = { tools: {}, components: {} };
for (const { rel, kind } of components) {
  if (kind === "svelte") {  // scip-typescript's own svelte2tsx reads it
    const entry = resolve(indexer, "svelte2tsx");
    if (entry) {
      const name = `svelte2tsx@${version(entry)}`;
      result.tools[name] = { tool: "svelte2tsx", version: version(entry), from: "scip-typescript" };
      result.components[rel] = { tool: name };
    } else {
      result.components[rel] = { error: "scip-typescript holds no svelte2tsx" };
    }
    continue;
  }
  const file = path.join(work, rel);
  const found = vueTool(path.dirname(file));
  if (!found) {
    result.components[rel] = { error: "@vue/language-core is installed neither by the project nor by Daodan" };
    continue;
  }
  const name = `@vue/language-core@${version(found.entry)}`;
  const tool = (result.tools[name] ||= { tool: "@vue/language-core", version: version(found.entry), from: found.from });
  if (found.instead && !(tool.instead ||= []).includes(found.instead)) tool.instead.push(found.instead);
  try {
    const done = vue(found, file, fs.readFileSync(file, "utf8"));
    const generated = rel + done.extension;
    if (fs.existsSync(path.join(work, generated))) throw new Error(`the project holds ${generated} already`);
    fs.writeFileSync(path.join(work, generated), done.code);
    result.components[rel] = { tool: name, generated, map: done.map };
  } catch (error) {
    result.components[rel] = { tool: name, error: String((error && error.message) || error).split("\n")[0] };
  }
}
if (components.some((item) => item.kind === "vue")) {
  try {
    Object.assign(result, unresolved());
  } catch (error) {
    result.unresolved_error = String((error && error.message) || error).split("\n")[0];
  }
}
fs.writeFileSync(output, JSON.stringify(result));
