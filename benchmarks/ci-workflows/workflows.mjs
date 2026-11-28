// Each GitHub workflow given, read by GitHub's own parser (@actions/workflow-parser, MIT): one JSON line per file,
// `{file, errors, template}`: the schema's errors (`parseWorkflow`) and the converted model
// (`convertWorkflowTemplate`), or `{file, failed}` when the parser throws.
//
// The package imports its schema (`workflow-v1.0.min.json`) with no import attribute, which Node 24 refuses
// (ERR_IMPORT_ATTRIBUTE_MISSING): the load hook adds `type: "json"` to that one kind of file, nothing else.
import fs from "node:fs";
import { registerHooks } from "node:module";

registerHooks({
  load(url, context, nextLoad) {
    return nextLoad(url, url.endsWith(".json") ? { ...context, importAttributes: { type: "json" } } : context);
  },
});
const { parseWorkflow, convertWorkflowTemplate, NoOperationTraceWriter } = await import("@actions/workflow-parser");

for (const file of process.argv.slice(2)) {
  try {
    const content = fs.readFileSync(file, "utf8");
    const parsed = parseWorkflow({ name: file, content }, new NoOperationTraceWriter());
    const errors = parsed.context.errors.getErrors().map((error) => error.message);
    const template = parsed.value ? await convertWorkflowTemplate(parsed.context, parsed.value) : null;
    process.stdout.write(JSON.stringify({ file, errors, template }) + "\n");
  } catch (error) {
    process.stdout.write(JSON.stringify({ file, failed: String(error) }) + "\n");
  }
}
