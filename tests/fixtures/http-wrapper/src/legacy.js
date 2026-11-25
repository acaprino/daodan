// A script, not a module (no import, no export): sloppy mode, where `arguments` aliases the parameters and `with` exists.

function argsAliasJs(url) {
  arguments[0] = '/x';
  return fetch(url);
}

function withSloppy(url, scope) {
  with (scope) {
    url = '/x';
  }
  return fetch(url);
}

function parenEvalJs(url) {
  (eval)("url = '/x'");
  return fetch(url);
}
