// The project's own Tailwind says which class tokens are its utilities: a context built from the project's
// config, asked `getClassOrder` (null for a token Tailwind does not generate). Tailwind 3 only.
// usage: node css_tailwind.js CONFIG.json OUT.json; CONFIG: {"tailwind": package folder, "config": path|null, "tokens": [...]}
"use strict";
const fs = require("fs");
const path = require("path");

const [configPath, outPath] = process.argv.slice(2);
const begun = Date.now();
const cfg = JSON.parse(fs.readFileSync(configPath, "utf8"));
const version = require(path.join(cfg.tailwind, "package.json")).version;
let result = { version, valid: null, error: null };
if (!version.startsWith("3.")) {
  result.error = `Tailwind ${version}: only Tailwind 3 is read`;
} else {
  const resolveConfig = require(path.join(cfg.tailwind, "resolveConfig"));
  const loadConfig = require(path.join(cfg.tailwind, "loadConfig"));
  const { createContext } = require(path.join(cfg.tailwind, "lib/lib/setupContextUtils"));
  // The config is the project's code: loading it runs it.
  const context = createContext(resolveConfig(cfg.config ? loadConfig(cfg.config) : {}));
  result.valid = context.getClassOrder(cfg.tokens).filter(([, order]) => order !== null).map(([token]) => token);
}
result.seconds = (Date.now() - begun) / 1000;
fs.writeFileSync(outPath, JSON.stringify(result));
