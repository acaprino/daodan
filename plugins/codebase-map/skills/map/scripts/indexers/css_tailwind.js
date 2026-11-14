// The project's own Tailwind says which class tokens are its utilities, `getClassOrder` giving null for a token
// Tailwind does not generate. Tailwind 3: a context built from the project's config. Tailwind 4: the design system
// of each CSS entry that imports Tailwind (`@theme`, `@utility`, `@custom-variant`, `@source`, `@plugin`, `@config`
// read by Tailwind itself), through `@tailwindcss/node` when the project has it, else Tailwind's own loader with
// files and packages resolved from the entry. Loading a config or a plugin runs the project's code, as its build does.
// usage: node css_tailwind.js CONFIG.json OUT.json; CONFIG: {"tailwind": package folder, "config": path|null,
// "entries": [{"path", "text"}], "tokens": [...]}
"use strict";
const fs = require("fs");
const path = require("path");

const [configPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(configPath, "utf8"));
const version = require(path.join(cfg.tailwind, "package.json")).version;

function sheet(id, base) {
  const local = id.startsWith(".") || id.startsWith("/") ? path.resolve(base, id) : null;
  const candidates = local ? [local, local + ".css"] : [];
  if (!local) {
    const [pkg, ...rest] = id.startsWith("@") ? [id.split("/").slice(0, 2).join("/"), ...id.split("/").slice(2)] : id.split("/");
    const folder = id === "tailwindcss" || pkg === "tailwindcss" ? cfg.tailwind : path.join(path.dirname(cfg.tailwind), pkg);
    const meta = fs.existsSync(path.join(folder, "package.json")) ? JSON.parse(fs.readFileSync(path.join(folder, "package.json"), "utf8")) : {};
    candidates.push(rest.length ? path.join(folder, ...rest) : path.join(folder, meta.style || "index.css"));
    if (rest.length) candidates.push(path.join(folder, ...rest) + ".css");
  }
  const file = candidates.find((c) => fs.existsSync(c) && fs.statSync(c).isFile());
  if (!file) throw new Error(`cannot load stylesheet ${id} from ${base}`);
  return { path: file, base: path.dirname(file), content: fs.readFileSync(file, "utf8") };
}

async function designSystem(entry) {
  const base = path.dirname(entry.path);
  // Packages are found from the project's node_modules, through their `exports`.
  const from = { paths: [path.dirname(path.dirname(cfg.tailwind))] };
  const nodePackage = path.join(path.dirname(cfg.tailwind), "@tailwindcss", "node");
  if (fs.existsSync(path.join(nodePackage, "package.json"))) {
    const node = require(require.resolve("@tailwindcss/node", from));
    return node.__unstable__loadDesignSystem(entry.text, { base });
  }
  const tailwind = require(require.resolve("tailwindcss", from));
  return tailwind.__unstable__loadDesignSystem(entry.text, {
    base,
    loadStylesheet: async (id, from) => sheet(id, from),
    loadModule: async (id, from) => {
      const file = require.resolve(id, { paths: [from, base] });
      return { path: file, base: path.dirname(file), module: require(file) };
    },
  });
}

(async () => {
  const result = { version, valid: null, error: null };
  try {
    if (version.startsWith("3.")) {
      const resolveConfig = require(path.join(cfg.tailwind, "resolveConfig"));
      const loadConfig = require(path.join(cfg.tailwind, "loadConfig"));
      const { createContext } = require(path.join(cfg.tailwind, "lib/lib/setupContextUtils"));
      // The config is the project's code: loading it runs it.
      const context = createContext(resolveConfig(cfg.config ? loadConfig(cfg.config) : {}));
      result.valid = context.getClassOrder(cfg.tokens).filter(([, order]) => order !== null).map(([token]) => token);
    } else if (version.startsWith("4.")) {
      const valid = new Set();
      const errors = [];
      for (const entry of cfg.entries || []) {
        try {
          const design = await designSystem(entry);
          for (const [token, order] of design.getClassOrder(cfg.tokens)) if (order !== null) valid.add(token);
        } catch (error) {
          errors.push(`${entry.path}: ${String(error.message || error).split("\n")[0]}`);
        }
      }
      result.valid = (cfg.entries || []).length && errors.length < cfg.entries.length ? [...valid] : null;
      result.error = errors.length ? errors.join("; ").slice(0, 600) : (cfg.entries || []).length ? null : "Tailwind 4: no CSS entry imports tailwindcss";
    } else {
      result.error = `Tailwind ${version}: only Tailwind 3 and 4 are read`;
    }
  } catch (error) {
    result.error = String(error.message || error).slice(0, 600);
  }
  result.seconds = (Date.now() - begun) / 1000;
  fs.writeFileSync(outPath, JSON.stringify(result));
})();
