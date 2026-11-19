// The sheets of the packages the project's imports name, which only the restore holds. For each [folder, name], the
// package Node finds from that folder (`node_modules/<name>` there or above, pnpm's link followed) comes back with its
// package.json and its stylesheets, under the path where it was found, the one the graph looks at; a package one of
// those sheets imports by name comes back nested in the importing package's folder, where the graph's walk up from
// that folder finds it as Node finds it from the package's real one. A link to a folder of the project (a workspace
// package) is the project's own: not copied. Only files are read: nothing of the project runs.
// usage: node css_packages.js CONFIG.json OUT.json; CONFIG: {"packages": [[folder, name], ...]}; OUT: {"files":
// {path: text}, "missing": [[folder, name]], "workspace": [[folder, name]], "error"}
"use strict";
const fs = require("fs");
const path = require("path");

const SHEETS = /\.(css|scss|sass|less|styl)$/i;
const IMPORTS = /@(?:import|use|forward)\s+(?:url\(\s*)?["']([^"']+)["']/g;
const LIMIT = 64 * 2 ** 20;  // the text copied back, at most
const [configPath, outPath] = process.argv.slice(2);
const cfg = JSON.parse(fs.readFileSync(configPath, "utf8"));
const root = process.cwd();
const files = {}, missing = [], workspace = [], seen = new Set();
let size = 0;

// The folder Node finds a package in from the absolute folder `from`: `node_modules/<name>` there or above.
function located(from, name) {
  for (let dir = from; ; dir = path.dirname(dir)) {
    const at = path.join(dir, "node_modules", name);
    if (fs.existsSync(path.join(at, "package.json"))) return at;
    if (dir === root || path.dirname(dir) === dir) return null;
  }
}

// The package a bare specifier names (`@scope/name/sub`, `name/sub`, `~name`), else null.
function named(spec) {
  const clean = spec.replace(/^~/, "").split(/[?#]/)[0];
  if (/^(\.|\/|[a-z][\w+.-]*:)/i.test(clean)) return null;
  const parts = clean.split("/");
  return clean.startsWith("@") ? (parts.length > 1 ? parts.slice(0, 2).join("/") : null) : parts[0] || null;
}

// The package.json and the stylesheets of the package whose real folder is `real`, under `as` (a path from the
// root), outside its own node_modules; then the packages its sheets import, nested under `as`.
function copy(real, as, depth) {
  if (seen.has(as) || depth > 8) return;
  seen.add(as);
  const sheets = [];
  const walk = (dir, rel) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.name === "node_modules") continue;
      const full = path.join(dir, entry.name), sub = rel ? `${rel}/${entry.name}` : entry.name;
      if (entry.isDirectory()) walk(full, sub);
      else if (entry.isFile() && (SHEETS.test(entry.name) || sub === "package.json")) {
        const text = fs.readFileSync(full, "utf8");
        size += text.length;
        if (size > LIMIT) throw new Error(`the packages' sheets pass ${LIMIT >> 20} MB`);
        files[`${as}/${sub}`] = text;
        if (sub !== "package.json") sheets.push(text);
      }
    }
  };
  walk(real, "");
  const names = new Set();
  for (const text of sheets) for (const [, spec] of text.matchAll(IMPORTS)) names.add(named(spec));
  for (const name of names) {
    const found = name && located(real, name);  // Node's walk up, from the package's real folder
    if (found) copy(fs.realpathSync(found), `${as}/node_modules/${name}`, depth + 1);
  }
}

let error = null;
try {
  for (const [folder, name] of cfg.packages || []) {
    const found = located(path.resolve(root, folder), name);
    if (!found) {
      missing.push([folder, name]);
      continue;
    }
    const real = fs.realpathSync(found);
    if (!real.split(path.sep).includes("node_modules")) {
      workspace.push([folder, name]);
      continue;
    }
    copy(real, path.relative(root, found).split(path.sep).join("/"), 0);
  }
} catch (err) {
  error = String(err.message || err).split(/\r?\n/)[0];
}
fs.writeFileSync(outPath, JSON.stringify({ files, missing, workspace, error }));
