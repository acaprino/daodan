// The ground truth of the A/B for `var()`: every use of a custom property in a stylesheet, from the tokenizer of the
// pinned fork alone (no parser, no tree): a `var(` function token followed by an identifier that starts with `--`, its
// line and its fallback (the tokens after the first comma, up to the parenthesis that closes the `var(`).
// Comments, strings and unquoted urls are tokens of their own, so what sits inside them is not a use.
// usage: node var_tokens.mjs IN.json OUT.json   IN: {"engines": folder, "root": folder, "files": [relative paths]}
// OUT: {file: ["--name@line|fallback", ...]}; lines count LF only, after CRLF and CR became LF (the snapshot's); a
// fallback has its comments dropped and its whitespace collapsed to one space, as the engine writes it.
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const [inPath, outPath] = process.argv.slice(2);
const cfg = JSON.parse(fs.readFileSync(inPath, "utf8"));
const cs = createRequire(path.join(cfg.engines, "package.json"))("@eslint/css-tree");
const T = cs.tokenTypes;

function collapse(text) {
  let out = "", gap = false;
  cs.tokenize(text, (type, start, end) => {
    if (type === T.WhiteSpace || type === T.Comment) { gap = out.length > 0; return; }
    if (gap) out += " ";
    gap = false;
    out += text.slice(start, end);
  });
  return out;
}

const out = {};
for (const rel of cfg.files) {
  const text = fs.readFileSync(path.join(cfg.root, rel), "utf8").split("\r\n").join("\n").split("\r").join("\n");
  const uses = [], frames = [];  // a frame per open parenthesis or function; a `var(` frame holds its use
  let line = 1, at = 0;
  const extend = (start, end) => {  // a token inside the fallback of every open `var(` that has reached its comma
    for (const frame of frames) {
      if (frame.use && frame.use.comma) { if (frame.use.from === null) frame.use.from = start; frame.use.to = end; }
    }
  };
  cs.tokenize(text, (type, start, end) => {
    for (; at < start; at++) if (text.charCodeAt(at) === 10) line++;
    if (type === T.WhiteSpace || type === T.Comment) return;
    if (type === T.RightParenthesis) {
      const frame = frames.pop();
      if (frame && frame.use && frame.use.name) {
        const use = frame.use;
        uses.push(`${use.name}@${use.line}|${use.from === null ? "" : collapse(text.slice(use.from, use.to))}`);
      }
      extend(start, end);  // the parenthesis is part of the fallback of each `var(` still open
      return;
    }
    extend(start, end);
    const top = frames[frames.length - 1];
    if (type === T.Function) {
      frames.push({ use: text.slice(start, end).toLowerCase() === "var(" ? { line, name: null, comma: false, from: null, to: 0 } : null });
    } else if (type === T.LeftParenthesis) {
      frames.push({ use: null });
    } else if (top && top.use && !top.use.name && type === T.Ident && text.slice(start, end).startsWith("--")) {
      top.use.name = text.slice(start, end);
    } else if (top && top.use && top.use.name && !top.use.comma && type === T.Comma) {
      top.use.comma = true;
    }
  });
  out[rel] = uses;
}
fs.writeFileSync(outPath, JSON.stringify(out));
