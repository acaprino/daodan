// The project's own Tailwind says which class tokens are its utilities, `getClassOrder` giving null for a token
// Tailwind does not generate. Each entry is read with the Tailwind installed where Node resolves it from the entry's
// folder (`node_modules/tailwindcss` there or above, as in a workspace's package), else the root's. Tailwind 3: a
// context built from the project's config. Tailwind 4: the design system of each CSS entry that imports Tailwind
// (`@theme`, `@utility`, `@custom-variant`, `@source`, `@plugin`, `@config` read by Tailwind itself), through
// `@tailwindcss/node` when the project has it beside Tailwind, else Tailwind's own loader with files and packages
// resolved from the entry. Loading a config or a plugin runs the project's code, as its build does.
// usage: node css_tailwind.js CONFIG.json OUT.json; CONFIG: {"tailwind": the root's package folder, "config":
// path|null, "entries": [{"path", "text"}], "tokens": [...]}; OUT: {"version", "valid": {token: the version of the
// Tailwind that generates it}, "error"}
"use strict";
const fs = require("fs");
const path = require("path");

const [configPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(configPath, "utf8"));
// Paths are relative to the project's root, where the script runs.
cfg.tailwind = path.resolve(cfg.tailwind);
cfg.config = cfg.config ? path.resolve(cfg.config) : null;
for (const entry of cfg.entries || []) entry.path = path.resolve(entry.path);
const root = process.cwd();

// The Tailwind Node resolves from a folder: `node_modules/tailwindcss` there or in a folder above, up to the root.
function installed(from) {
  for (let dir = from; ; dir = path.dirname(dir)) {
    const folder = path.join(dir, "node_modules", "tailwindcss");
    if (fs.existsSync(path.join(folder, "package.json"))) return folder;
    if (dir === root || path.dirname(dir) === dir) break;
  }
  return fs.existsSync(path.join(cfg.tailwind, "package.json")) ? cfg.tailwind : null;
}

function sheet(id, base, tailwind) {
  const local = id.startsWith(".") || id.startsWith("/") ? path.resolve(base, id) : null;
  const candidates = local ? [local, local + ".css"] : [];
  if (!local) {
    const [pkg, ...rest] = id.startsWith("@") ? [id.split("/").slice(0, 2).join("/"), ...id.split("/").slice(2)] : id.split("/");
    const folder = id === "tailwindcss" || pkg === "tailwindcss" ? tailwind : path.join(path.dirname(tailwind), pkg);
    const meta = fs.existsSync(path.join(folder, "package.json")) ? JSON.parse(fs.readFileSync(path.join(folder, "package.json"), "utf8")) : {};
    candidates.push(rest.length ? path.join(folder, ...rest) : path.join(folder, meta.style || "index.css"));
    if (rest.length) candidates.push(path.join(folder, ...rest) + ".css");
  }
  const file = candidates.find((c) => fs.existsSync(c) && fs.statSync(c).isFile());
  if (!file) throw new Error(`cannot load stylesheet ${id} from ${base}`);
  return { path: file, base: path.dirname(file), content: fs.readFileSync(file, "utf8") };
}

async function designSystem(entry, tailwind) {
  const base = path.dirname(entry.path);
  // Packages are found from the node_modules that holds this Tailwind, through their `exports`.
  const from = { paths: [path.dirname(path.dirname(tailwind))] };
  const nodePackage = path.join(path.dirname(tailwind), "@tailwindcss", "node");
  if (fs.existsSync(path.join(nodePackage, "package.json"))) {
    const node = require(require.resolve("@tailwindcss/node", from));
    return node.__unstable__loadDesignSystem(entry.text, { base });
  }
  const engine = require(require.resolve("tailwindcss", from));
  return engine.__unstable__loadDesignSystem(entry.text, {
    base,
    loadStylesheet: async (id, from) => sheet(id, from, tailwind),
    loadModule: async (id, from) => {
      const file = require.resolve(id, { paths: [from, base] });
      return { path: file, base: path.dirname(file), module: require(file) };
    },
  });
}

(async () => {
  const result = { version: null, valid: null, error: null };
  const valid = {}, errors = [], versions = new Set(), contexts = new Map();
  // What each Tailwind says of the tokens: a context per config (3), a design system per entry (4).
  async function orders(tailwind, entry) {
    const version = require(path.join(tailwind, "package.json")).version;
    versions.add(version);
    if (version.startsWith("3.")) {
      if (!contexts.has(tailwind)) {
        const resolveConfig = require(path.join(tailwind, "resolveConfig"));
        const loadConfig = require(path.join(tailwind, "loadConfig"));
        const { createContext } = require(path.join(tailwind, "lib/lib/setupContextUtils"));
        // The config is the project's code: loading it runs it.
        contexts.set(tailwind, createContext(resolveConfig(cfg.config ? loadConfig(cfg.config) : {})));
      }
      return [version, contexts.get(tailwind).getClassOrder(cfg.tokens)];
    }
    if (version.startsWith("4.")) {
      if (!entry) throw new Error("Tailwind 4: no CSS entry imports tailwindcss");
      return [version, (await designSystem(entry, tailwind)).getClassOrder(cfg.tokens)];
    }
    throw new Error(`Tailwind ${version}: only Tailwind 3 and 4 are read`);
  }
  const targets = (cfg.entries || []).length ? cfg.entries : [null];
  for (const entry of targets) {
    const from = entry ? path.dirname(entry.path) : cfg.config ? path.dirname(cfg.config) : root;
    const where = path.relative(root, entry ? entry.path : cfg.config || root).split(path.sep).join("/") || ".";
    const tailwind = installed(from);
    if (!tailwind) {
      errors.push(`${where}: no tailwindcss installed where Node resolves it`);
      continue;
    }
    try {
      const [version, found] = await orders(tailwind, entry);
      for (const [token, order] of found) if (order !== null && !(token in valid)) valid[token] = version;
    } catch (error) {
      errors.push(`${where}: ${String(error.message || error).split(/\r?\n/)[0]}`);
    }
  }
  result.version = [...versions].sort().join(" + ") || null;
  result.valid = errors.length < targets.length ? valid : null;
  result.error = errors.length ? errors.join("; ").slice(0, 600) : null;
  result.seconds = (Date.now() - begun) / 1000;
  fs.writeFileSync(outPath, JSON.stringify(result));
})();
