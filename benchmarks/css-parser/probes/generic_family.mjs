// The lexer's verdict on the system font keywords: `<generic-family>` or `<family-name>`.
// usage: modal_css_parser.py::probe_run --script benchmarks/css-parser/probes/generic_family.mjs (README.md, "fixed: not a family")
import { createRequire } from 'node:module';
const cs = createRequire('/engines/package.json')('@eslint/css-tree');
for (const w of ['-apple-system', 'BlinkMacSystemFont', 'system-ui', 'Roboto', 'sans-serif']) {
  const v = cs.parse(w, { context: 'value' });
  const g = cs.lexer.matchType('generic-family', v), f = cs.lexer.matchType('family-name', v);
  console.log(w, 'generic-family:', g.error ? 'no' : 'yes', ' family-name:', f.error ? 'no' : 'yes');
}
