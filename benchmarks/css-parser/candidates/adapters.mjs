// Every candidate behind the same shape, so ONE comparator reads them all.
// adapt(src) -> { threw: string|null, errors: number, rules: [{sel, line, col, endLine}], decls: [{property, value, important, line}],
//                 atrules: [{name, prelude, hasBlock, line, col, endLine}], comments: [{text, line, column}], pos: [...] }
// sel / value / prelude: an array of candidate source texts (the comparator accepts any), or null when the tool gives none
// (a null prelude is "no prelude"; undefined is "the tool does not give the text"); line / endLine / col: 1-based or null.
import * as csstreeMod from 'css-tree';
import * as eslintMod from 'css-tree-eslint';
import postcss from 'postcss';
import safe from 'postcss-safe-parser';
import { transform } from 'lightningcss';

const collapse = (s) => s.replace(/\s+/g, ' ').trim();
const empty = () => ({ threw: null, errors: 0, rules: [], decls: [], atrules: [], comments: [], pos: [] });

// ---------------------------------------------------------------------------------------------------- css-tree and its fork
function csstreeAdapt(cs, src) {
  const out = empty();
  const comments = [];
  let ast;
  try {
    ast = cs.parse(src, {
      positions: true,
      onParseError: () => { out.errors++; },
      onComment: (value, loc) => comments.push({ text: value.trim(), line: loc.start.line, column: loc.start.column }),
    });
  } catch (e) { out.threw = `${e.name}: ${e.message}`; return out; }
  out.comments = comments;
  const kids = (n) => (n && n.children ? n.children.toArray() : []);
  const slice = (loc) => (loc ? src.slice(loc.start.offset, loc.end.offset) : '');
  const visit = (node) => {
    for (const ch of kids(node)) {
      if (ch.type === 'Rule') {
        const p = ch.prelude;
        out.rules.push({ sel: [collapse(slice(p.loc)), cs.generate(p)], line: ch.loc.start.line, col: ch.loc.start.column, endLine: ch.loc.end.line });
        out.pos.push({ kind: 'rule', line: ch.loc.start.line, col: ch.loc.start.column, offset: ch.loc.start.offset, endOffset: ch.loc.end.offset, text: collapse(slice(p.loc)).slice(0, 3) });
        visit(ch.block);
      } else if (ch.type === 'Atrule') {
        const p = ch.prelude;
        out.atrules.push({ name: ch.name, prelude: p ? [collapse(slice(p.loc)), cs.generate(p)] : null, hasBlock: !!ch.block, line: ch.loc.start.line, col: ch.loc.start.column, endLine: ch.loc.end.line });
        out.pos.push({ kind: 'atrule', line: ch.loc.start.line, col: ch.loc.start.column, offset: ch.loc.start.offset, endOffset: ch.loc.end.offset, text: '@' + ch.name.slice(0, 3) });
        if (ch.block) visit(ch.block);
      } else if (ch.type === 'Declaration') {
        const v = ch.value;
        out.decls.push({ property: ch.property, value: [collapse(slice(v.loc)), cs.generate(v)], important: !!ch.important, line: ch.loc.start.line });
        out.pos.push({ kind: 'decl', line: ch.loc.start.line, col: ch.loc.start.column, offset: ch.loc.start.offset, endOffset: ch.loc.end.offset, text: ch.property.slice(0, 3) });
      }
    }
  };
  visit(ast);
  return out;
}

// ---------------------------------------------------------------------------------------------------- PostCSS (core, and the safe parser)
function postcssAdapt(src, parse) {
  const out = empty();
  let root;
  try { root = parse(src); } catch (e) { out.threw = `${e.name}: ${e.reason || e.message}`; return out; }
  const at = (n) => ({ line: n.source.start.line, col: n.source.start.column, offset: n.source.start.offset, endLine: n.source.end ? n.source.end.line : null, endOffset: n.source.end ? n.source.end.offset : null });
  const walk = (nodes) => {
    for (const n of nodes) {
      const p = at(n);
      if (n.type === 'rule') {
        out.rules.push({ sel: [n.selector, n.raws.selector ? n.raws.selector.raw : n.selector], line: p.line, col: p.col, endLine: p.endLine });
        out.pos.push({ kind: 'rule', ...p, text: (n.raws.selector ? n.raws.selector.raw : n.selector).trimStart().slice(0, 3) });
        walk(n.nodes || []);
      } else if (n.type === 'atrule') {
        out.atrules.push({ name: n.name, prelude: n.params ? [n.params, n.raws.params ? n.raws.params.raw : n.params] : null, hasBlock: n.nodes !== undefined, line: p.line, col: p.col, endLine: p.endLine });
        out.pos.push({ kind: 'atrule', ...p, text: '@' + n.name.slice(0, 3) });
        if (n.nodes) walk(n.nodes);
      } else if (n.type === 'decl') {
        out.decls.push({ property: n.prop, value: [n.value, n.raws.value ? n.raws.value.raw : n.value], important: !!n.important, line: p.line });
        const hack = /[*_]$/.exec(n.raws.before || '');
        out.pos.push({ kind: 'decl', ...p, text: ((hack && !n.prop.startsWith(hack[0]) ? hack[0] : '') + n.prop).slice(0, 3) });
      } else if (n.type === 'comment') {
        out.comments.push({ text: n.text, line: p.line, column: p.col });
        out.pos.push({ kind: 'comment', ...p, text: '/*' });
      }
    }
  };
  walk(root.nodes);
  return out;
}

// ---------------------------------------------------------------------------------------------------- Lightning CSS
const AT_NAMES = {
  media: 'media', import: 'import', 'font-face': 'font-face', page: 'page', supports: 'supports', 'counter-style': 'counter-style', namespace: 'namespace',
  'layer-block': 'layer', 'layer-statement': 'layer', container: 'container', scope: 'scope', 'starting-style': 'starting-style', property: 'property',
  'custom-media': 'custom-media', nesting: 'nest', viewport: 'viewport', 'moz-document': 'document', 'view-transition': 'view-transition',
  'font-palette-values': 'font-palette-values', 'font-feature-values': 'font-feature-values', 'position-try': 'position-try',
};
const prefixed = (name, vp) => {
  const p = Array.isArray(vp) ? vp : vp ? [vp] : [];
  const pick = ['webkit', 'moz', 'ms', 'o'].find((x) => p.includes(x));
  return pick ? `-${pick}-${name}` : name;
};
function declName(d) {
  if (d.property === 'unparsed') return prefixed(d.value.propertyId.property, d.value.propertyId.vendorPrefix);
  if (d.property === 'custom') return d.value.name;
  return prefixed(d.property, d.vendorPrefix);
}
const FACE = { source: 'src' };
function lightningAdapt(src, errorRecovery) {
  const out = empty();
  let tree = null;
  try {
    const r = transform({ filename: 'in.css', code: Buffer.from(src), errorRecovery, visitor: { StyleSheet(s) { tree = JSON.parse(JSON.stringify(s)); } } });
    out.errors = r.warnings.length;
    out.errorMessages = r.warnings.map((x) => x.message);
  } catch (e) { out.threw = `${e.name || 'Error'}: ${String(e.message).slice(0, 100)}`; return out; }
  const line = (loc) => (loc ? loc.line + 1 : null);
  const col = (loc) => (loc ? loc.column : null);
  const addDecls = (block, important = false) => {
    if (!block) return;
    for (const d of block.declarations || []) out.decls.push({ property: declName(d), value: undefined, important: false, line: null });
    for (const d of block.importantDeclarations || []) out.decls.push({ property: declName(d), value: undefined, important: true, line: null });
  };
  const addRule = (r) => {
    const v = r.value;
    if (r.type === 'style') {
      out.rules.push({ sel: undefined, line: line(v.loc), col: col(v.loc), endLine: null });
      out.pos.push({ kind: 'rule', line: line(v.loc), col: col(v.loc) });
      addDecls(v.declarations);
      for (const x of v.rules || []) addRule(x);
    } else if (r.type === 'nested-declarations') {
      addDecls(v.declarations);
    } else if (r.type === 'keyframes') {
      out.atrules.push({ name: prefixed('keyframes', v.vendorPrefix), prelude: undefined, hasBlock: true, line: line(v.loc), col: col(v.loc), endLine: null });
      out.pos.push({ kind: 'atrule', line: line(v.loc), col: col(v.loc) });
      for (const k of v.keyframes || []) { out.rules.push({ sel: undefined, line: null, col: null, endLine: null }); addDecls(k.declarations); }
    } else if (r.type === 'unknown') {
      out.atrules.push({ name: v.name, prelude: undefined, hasBlock: v.block !== null, line: line(v.loc), col: col(v.loc), endLine: null });
      out.pos.push({ kind: 'atrule', line: line(v.loc), col: col(v.loc) });
    } else if (r.type === 'ignored') {
      // nothing
    } else {
      const name = AT_NAMES[r.type] || r.type;
      const hasBlock = r.type !== 'import' && r.type !== 'layer-statement' && r.type !== 'namespace' && r.type !== 'custom-media';
      out.atrules.push({ name, prelude: undefined, hasBlock, line: line(v.loc), col: col(v.loc), endLine: null });
      out.pos.push({ kind: 'atrule', line: line(v.loc), col: col(v.loc) });
      if (r.type === 'font-face') {
        for (const p of v.properties || []) out.decls.push({ property: p.type === 'custom' ? p.value.name : FACE[p.type] || p.type, value: undefined, important: false, line: null });
      } else if (r.type === 'property') {
        out.decls.push({ property: 'syntax', value: undefined, important: false, line: null }, { property: 'inherits', value: undefined, important: false, line: null });
        if (v.initialValue) out.decls.push({ property: 'initial-value', value: undefined, important: false, line: null });
      } else if (r.type === 'page' || r.type === 'counter-style' || r.type === 'font-palette-values' || r.type === 'viewport') {
        addDecls(v.declarations);
        for (const x of v.rules || []) addRule(x);
      }
      for (const x of v.rules || []) if (r.type !== 'page') addRule(x);
    }
  };
  for (const r of tree.rules) addRule(r);
  return out;
}

export const adapters = {
  'css-tree': (src) => csstreeAdapt(csstreeMod, src),
  'css-tree-eslint': (src) => csstreeAdapt(eslintMod, src),
  postcss: (src) => postcssAdapt(src, (s) => postcss.parse(s)),
  'postcss-safe': (src) => postcssAdapt(src, (s) => safe(s)),
  lightning: (src) => lightningAdapt(src, false),
  'lightning-recovery': (src) => lightningAdapt(src, true),
};

// What each tool gives; a false capability is not compared (and reported as "not given").
export const caps = {
  'css-tree': { ruleSel: true, ruleEnd: true, declLine: true, declValue: true, atrules: true, atrulePrelude: true, comments: true, declOrder: true, errors: true },
  'css-tree-eslint': { ruleSel: true, ruleEnd: true, declLine: true, declValue: true, atrules: true, atrulePrelude: true, comments: true, declOrder: true, errors: true },
  postcss: { ruleSel: true, ruleEnd: true, declLine: true, declValue: true, atrules: true, atrulePrelude: true, comments: true, declOrder: true, errors: false },
  'postcss-safe': { ruleSel: true, ruleEnd: true, declLine: true, declValue: true, atrules: true, atrulePrelude: true, comments: true, declOrder: true, errors: false },
  lightning: { ruleSel: false, ruleEnd: false, declLine: false, declValue: false, atrules: true, atrulePrelude: false, comments: false, declOrder: false, errors: false },
  'lightning-recovery': { ruleSel: false, ruleEnd: false, declLine: false, declValue: false, atrules: true, atrulePrelude: false, comments: false, declOrder: false, errors: true },
};
