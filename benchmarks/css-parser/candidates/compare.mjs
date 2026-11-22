// node compare.mjs : one comparator over every tool's norm_*.json in $OUT (the expectations were written before any tool ran).
// Writes $OUT/summary.json, $OUT/per-input.tsv and $OUT/candidates-per-input.json.
// failed     = the tool threw, or lost something the expectations require (fewer rules / declarations / at-rules than expected);
// difference = nothing lost but something extra, a value / line / prelude / flag that differs, a comment missing, or an error on valid CSS;
// as expected otherwise. A capability a tool does not have (no source text, no lines, no comments) is not compared and is listed as "not given".
import fs from 'node:fs';
import path from 'node:path';

const HERE = import.meta.dirname;
const OUT = process.env.OUT || path.join(HERE, 'out');
const inputs = JSON.parse(fs.readFileSync(path.join(HERE, 'inputs.json'), 'utf8'));
const byId = Object.fromEntries(inputs.map((i) => [i.id, i]));
const TOOLS = ['current', 'css-tree', 'css-tree-eslint', 'postcss', 'postcss-safe', 'lightning', 'lightning-recovery', 'tinycss2'];
const strip = (s) => s.replace(/\s+/g, '');
const match = (expected, cands) => (cands || []).some((c) => c !== null && c !== undefined && strip(expected) === strip(c));
// Inputs that are invalid CSS by design (a browser drops or repairs them): an error on them is not spurious.
const INVALID = new Set(['g3-nesting-amp-suffix', 'g3-vue-svelte-modes', 'g4-url-forms', 'g4-ie-hacks', 'g5-unclosed-block-eof', 'g5-unclosed-nested-eof', 'g5-unclosed-string', 'g5-unclosed-string-eof',
  'g5-stray-close-brace', 'g5-stray-close-brace-end', 'g5-extra-close-in-block', 'g5-semicolon-stray-top', 'g5-slash-slash', 'g5-slash-slash-selector', 'g5-nul-and-control', 'g5-missing-semicolon-then-prop',
  'g5-decl-without-colon', 'g5-bad-selector-rule', 'g5-comment-unclosed', 'c09-amp-suffix-sass-leftover', 't05-theme-inline', 's21-import-in-media', 'n20-top-level-amp']);
const INVALID_BY_DESIGN_FOR_THROW = [...INVALID].filter((id) => id.startsWith('g5-'));

function compare(inp, n, caps) {
  const ex = inp.expect || {};
  const r = { cat: 'as expected', missing: [], extra: [], mismatch: [], notes: [] };
  if (n.threw) return { ...r, cat: 'failed', notes: [`threw: ${n.threw}`] };
  if (caps.errors && n.errors > 0 && !INVALID.has(inp.id)) r.mismatch.push(`${n.errors} error(s) on valid CSS`);
  const list = (name, exp, got) => {
    if (got.length < exp.length) { r.missing.push(`${name}: expected ${exp.length}, got ${got.length}`); return false; }
    if (got.length > exp.length) { r.extra.push(`${name}: expected ${exp.length}, got ${got.length}`); return false; }
    return true;
  };
  if (ex.rules) {
    if (list('rules', ex.rules, n.rules)) ex.rules.forEach((e, i) => {
      const g = n.rules[i];
      if (caps.ruleSel && g.sel && !match(e[0], g.sel)) r.mismatch.push(`rule ${i} selector ${JSON.stringify(e[0])}`);
      if (g.line != null && e[1] !== '*' && g.line !== e[1]) r.mismatch.push(`rule ${i} line ${e[1]} got ${g.line}`);
      if (caps.ruleEnd && g.endLine != null && e[2] !== '*' && g.endLine !== e[2]) r.mismatch.push(`rule ${i} endLine ${e[2]} got ${g.endLine}`);
    });
  }
  if (ex.decls) {
    if (caps.declOrder) {
      if (list('decls', ex.decls, n.decls)) ex.decls.forEach((e, i) => {
        const g = n.decls[i];
        if (g.property.toLowerCase() !== e[0].toLowerCase()) r.mismatch.push(`decl ${i} property ${e[0]} got ${g.property}`);
        if (caps.declValue && g.value && e[1] !== '*' && !match(e[1], g.value)) r.mismatch.push(`decl ${i} (${e[0]}) value ${JSON.stringify(e[1])}`);
        if (e[2] !== '*' && !!g.important !== !!e[2]) r.mismatch.push(`decl ${i} (${e[0]}) important ${e[2]}`);
        if (caps.declLine && g.line != null && e[3] !== '*' && g.line !== e[3]) r.mismatch.push(`decl ${i} (${e[0]}) line ${e[3]} got ${g.line}`);
      });
    } else if (list('decls', ex.decls, n.decls)) {
      // Order not given (important declarations apart, or a parent's declarations before its nested rules): compare as a set of what is given.
      const key = (p, imp, v, l) => `${p.toLowerCase()}|${imp ? 1 : 0}|${caps.declValue && v != null ? strip(v) : ''}|${caps.declLine && l != null ? l : ''}`;
      const want = ex.decls.map((e) => key(e[0], e[2] === '*' ? false : e[2], e[1] === '*' ? null : e[1], e[3] === '*' ? null : e[3])).sort();
      const got = n.decls.map((d) => key(d.property, d.important, d.value ? d.value[0] : null, d.line)).sort();
      if (JSON.stringify(want) !== JSON.stringify(got)) r.mismatch.push(`declarations differ as a set (${caps.declValue ? 'name, value, important, line' : 'name, important'})`);
    }
  }
  if (ex.atrules && caps.atrules) {
    if (list('atrules', ex.atrules, n.atrules)) ex.atrules.forEach((e, i) => {
      const g = n.atrules[i];
      if (g.name.toLowerCase() !== e[0].toLowerCase()) r.mismatch.push(`atrule ${i} name ${e[0]} got ${g.name}`);
      if (caps.atrulePrelude && g.prelude !== undefined) {
        if (e[1] === null) { if (g.prelude !== null) r.mismatch.push(`atrule ${i} prelude should be none`); }
        else if (g.prelude === null || !match(e[1], g.prelude)) r.mismatch.push(`atrule ${i} (${e[0]}) prelude ${JSON.stringify(e[1])}`);
      }
      if (g.hasBlock !== e[2]) r.mismatch.push(`atrule ${i} (${e[0]}) block ${e[2]}`);
      if (g.line != null && e[3] !== '*' && g.line !== e[3]) r.mismatch.push(`atrule ${i} line ${e[3]} got ${g.line}`);
      if (g.endLine != null && e[4] !== '*' && g.endLine !== e[4]) r.mismatch.push(`atrule ${i} endLine ${e[4]} got ${g.endLine}`);
    });
  }
  if (ex.comments) {
    if (!caps.comments) r.notes.push('comments not given');
    else if (n.comments.length < ex.comments.length) r.notes.push(`comments: expected ${ex.comments.length}, got ${n.comments.length}`);
    else if (n.comments.length > ex.comments.length) r.notes.push(`comments: expected ${ex.comments.length}, got ${n.comments.length}`);
    else ex.comments.forEach((e, i) => {
      const g = n.comments[i];
      if (g.text !== e[0] || g.line !== e[1] || g.column !== e[2]) r.notes.push(`comment ${i}: ${JSON.stringify(e)} got ${JSON.stringify([g.text, g.line, g.column])}`);
    });
  }
  const commentGap = r.notes.some((x) => x.startsWith('comment'));
  if (r.missing.length) r.cat = 'failed';
  else if (r.extra.length || r.mismatch.length || commentGap) r.cat = 'difference';
  return r;
}

const out = {};
for (const tool of TOOLS) {
  const f = path.join(OUT, `norm_${tool}.json`);
  if (!fs.existsSync(f)) continue;
  const data = JSON.parse(fs.readFileSync(f, 'utf8'));
  const per = {};
  for (const n of data.items) per[n.id] = { ...compare(byId[n.id], n, data.caps), threw: n.threw, errors: n.errors };
  out[tool] = { caps: data.caps, position: data.position, per, items: Object.fromEntries(data.items.map((i) => [i.id, i])) };
}

const cssIds = inputs.filter((i) => !i.id.startsWith('g6-')).map((i) => i.id);
const g6Ids = inputs.filter((i) => i.id.startsWith('g6-')).map((i) => i.id);
const met155 = inputs.filter((i) => ['css', 'tailwind'].includes(i.lang) && (i.expect.rules !== undefined || i.expect.decls !== undefined)).map((i) => i.id);
const nesting = inputs.filter((i) => /^n\d\d-/.test(i.id)).map((i) => i.id);
const daisy = ['c02-layer-in-rule-dotted', 'c03-layer-in-rule-spaced', 'c12-nested-two-levels-class'];
const unknownAt = ['g2-custom-media', 'g2-custom-selector', 'g2-value-define', 'g2-tw-apply-variant-important', 't09-apply-variants', 't10-apply-arbitrary', 't05-theme-inline', 't07-utility-wildcard',
  'g2-tw-source', 't06-source-inline-and-not', 'g2-tw-utility', 't01-custom-variant-short', 't12-import-layer-theme', 'm03-value-as-from', 'g2-unknown'];
const commentIds = inputs.filter((i) => i.expect.comments).map((i) => i.id);
const letter = { 'as expected': 'E', difference: 'D', failed: 'F' };

const summary = {};
for (const tool of Object.keys(out)) {
  const T = out[tool];
  const count = (ids) => { const c = { 'as expected': 0, difference: 0, failed: 0 }; for (const id of ids) c[T.per[id].cat]++; return c; };
  const rd = (id) => { const p = T.per[id]; return !p.threw && !p.missing.length && !p.extra.length && !p.mismatch.some((x) => /^(rule|decl)/.test(x)); };
  summary[tool] = {
    expectationsMet155: `${met155.filter(rd).length}/${met155.length}`,
    css189: count(cssIds),
    group6Threw: `${g6Ids.filter((id) => T.per[id].threw).length}/${g6Ids.length}`,
    nesting22: count(nesting),
    nestingCodes: nesting.map((id) => letter[T.per[id].cat]).join(''),
    daisyui: daisy.map((id) => `${id.split('-')[0]}:${letter[T.per[id].cat]}`).join(' '),
    unknownAtRules: unknownAt.map((id) => `${letter[T.per[id].cat]}`).join(''),
    invalidThrew: `${INVALID_BY_DESIGN_FOR_THROW.filter((id) => T.per[id].threw).length}/${INVALID_BY_DESIGN_FOR_THROW.length}`,
    commentsOk: `${commentIds.filter((id) => !T.per[id].notes.some((x) => x.startsWith('comment')) && !T.per[id].threw).length}/${commentIds.length}`,
    position: T.position,
  };
}
fs.writeFileSync(path.join(OUT, 'candidates-per-input.json'), JSON.stringify({ summary, per: Object.fromEntries(Object.entries(out).map(([t, T]) => [t, T.per])), unknownAt, nesting, daisy, met155: met155.length }, null, 1));
fs.writeFileSync(path.join(OUT, 'summary.json'), JSON.stringify(summary, (k, v) => (k === 'startMismatch' ? undefined : v), 1) + '\n');
// One row per input: E / D / F per tool (T: the tool threw), then what the fork and the current reader got wrong.
const tools = Object.keys(out);
const detail = (T, id) => { const p = T.per[id]; return p ? [...p.missing, ...p.extra, ...p.mismatch, ...p.notes].join('; ').slice(0, 300) : ''; };
const rows = ['id\tlang\t' + tools.join('\t') + '\tfork detail\tcurrent reader detail'];
for (const i of inputs) {
  const cell = (tool) => { const p = out[tool].per[i.id]; return p.threw ? 'T' : letter[p.cat]; };
  rows.push([i.id, i.lang, ...tools.map(cell), detail(out['css-tree-eslint'], i.id), detail(out.current, i.id)].join('\t'));
}
fs.writeFileSync(path.join(OUT, 'per-input.tsv'), rows.join('\n') + '\n');
console.log(JSON.stringify(summary, (k, v) => (k === 'startMismatch' ? undefined : v), 1));
