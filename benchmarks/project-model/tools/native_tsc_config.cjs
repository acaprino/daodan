// The compiler's own reading of tsconfig files: node native_tsc_config.cjs <typescript module> <tsconfig>...
// prints {typescript, configs: [{file, errors} | {file, paths, baseUrl, pathsBasePath, references, files}]}.
// It calls the public API `tsc --showConfig` is built on (`getParsedCommandLineOfConfigFile`, and the same test of
// `errors`), which gives the options that tsc's own show leaves out. `pathsBasePath` is the folder of the file that
// declares `paths`: the compiler resolves `paths` against `baseUrl ?? pathsBasePath` (TypeScript 6.0.3,
// src/compiler/utilities.ts:6611 `getPathsBasePath`; it is set at src/compiler/commandLineParser.ts:3432, kept by the
// `extends` merge at 3451 and 3481, and declared `@internal` at src/compiler/types.ts:7512, so not in typescript.d.ts).
// Reads JSON only: no project code runs (tsc's `plugins` are for the language service).
"use strict";
const path = require("path");
const ts = require(process.argv[2]);
// file names in a message are relative to the folder of the tsconfig read, as when `tsc -p` runs in that folder
const text = (diagnostic, folder) => ts.formatDiagnostic(diagnostic, {
  getCurrentDirectory: () => folder, getCanonicalFileName: (name) => name, getNewLine: () => "\n",
}).trim();

const configs = process.argv.slice(3).map((file) => {
  try {
    const unrecoverable = [];
    const parsed = ts.getParsedCommandLineOfConfigFile(file, {}, {
      ...ts.sys,
      onUnRecoverableConfigFileDiagnostic: (diagnostic) => unrecoverable.push(diagnostic),
    });
    const diagnostics = unrecoverable.concat(parsed ? parsed.errors : []);
    if (diagnostics.length) return { file, errors: diagnostics.map((diagnostic) => text(diagnostic, path.dirname(file))) };
    const { paths, baseUrl, pathsBasePath } = parsed.options;
    return {
      file, paths, baseUrl, pathsBasePath,
      references: (parsed.projectReferences || []).map(ts.resolveProjectReferencePath),
      files: parsed.fileNames.length,
    };
  } catch (error) {
    return { file, errors: [String(error)] };
  }
});
console.log(JSON.stringify({ typescript: ts.version, configs }));
