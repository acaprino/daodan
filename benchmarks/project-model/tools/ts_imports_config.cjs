// What the compiler holds in each tsconfig: node ts_imports_config.cjs <typescript module> <project root> <tsconfig>...
// prints {typescript, configs: [{file, errors, codes} | {file, paths, baseUrl, pathsBasePath, references, stops, fileNames}]}
// (`native_tsc_config.cjs` of F1, with the list of files in place of their number, for `modal_ts_imports.py`).
// `fileNames` is the official list of the files the config keeps, relative to the project root; `references` are the
// config files the project references name (`resolveProjectReferencePath`, absolute); `stops` carries the two options
// that end tsserver's search for a config (`disableReferencedProjectLoad`, `disableSolutionSearching`).
// An error (an `extends` into a node_modules that is not there, no input found) is the config's whole answer, as for
// `tsc --showConfig`. Reads JSON only: no project code runs.
"use strict";
const path = require("path");
const ts = require(process.argv[2]);
const root = process.argv[3];
const folderOf = (file) => path.dirname(file);
const text = (diagnostic, file) => ts.formatDiagnostic(diagnostic, {
  getCurrentDirectory: () => folderOf(file), getCanonicalFileName: (name) => name, getNewLine: () => "\n",
}).trim();

const configs = process.argv.slice(4).map((file) => {
  try {
    const unrecoverable = [];
    const parsed = ts.getParsedCommandLineOfConfigFile(file, {}, {
      ...ts.sys,
      onUnRecoverableConfigFileDiagnostic: (diagnostic) => unrecoverable.push(diagnostic),
    });
    const diagnostics = unrecoverable.concat(parsed ? parsed.errors : []);
    if (diagnostics.length) {
      return { file, errors: diagnostics.map((diagnostic) => text(diagnostic, file)), codes: diagnostics.map((diagnostic) => diagnostic.code) };
    }
    const { paths, baseUrl, pathsBasePath, disableReferencedProjectLoad, disableSolutionSearching } = parsed.options;
    return {
      file, paths, baseUrl, pathsBasePath,
      references: (parsed.projectReferences || []).map((reference) => ts.resolveProjectReferencePath(reference)),
      stops: { references: !!disableReferencedProjectLoad, ancestors: !!disableSolutionSearching },
      fileNames: parsed.fileNames.map((name) => path.relative(root, name).split(path.sep).join("/")),
    };
  } catch (error) {
    return { file, errors: [String(error)] };
  }
});
console.log(JSON.stringify({ typescript: ts.version, configs }));
