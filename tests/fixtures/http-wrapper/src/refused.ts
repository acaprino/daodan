// Functions around the HTTP client that are no wrapper the proof may name, each for its own cause.

declare function prefix(path: string): string;

export function reassigned(url: string) {
  url = url + '/x';
  return fetch(url);
}

export function augmented(url: string) {
  url += '/x';
  return fetch(url);
}

export function counted(url: any) {
  url++;
  return fetch(url);
}

export function destructured(url: string, others: string[]) {
  [url] = others;
  return fetch(url);
}

export function iterated(url: string, many: string[]) {
  for (url of many) {
    void url;
  }
  return fetch(url);
}

export function shadowed(url: string) {
  {
    const url = '/inner';
    return fetch(url);
  }
}

export function templated(path: string) {
  return fetch(`/api${path}`);
}

export function concatenated(path: string) {
  return fetch('/api' + path);
}

export function called(path: string) {
  return fetch(prefix(path));
}

export function methodParameter(url: string, method: string) {
  return fetch(url, { method });
}

export function optionsPassed(url: string, options: RequestInit) {
  return fetch(url, options);
}

export function spreadOptions(url: string, options: RequestInit) {
  return fetch(url, { ...options, method: 'POST' });
}

export function computedMethod(url: string) {
  return fetch(url, { method: ['GET', 'POST'][0] });
}

export function conflicting(url: string, other: string) {
  fetch(url, { method: 'POST' });
  return fetch(other, { method: 'PUT' });
}

export function fixed() {
  const url = '/api/fixed';
  return fetch(url);
}

export function parenthesized(url: string) {
  (url as any) = '/x';
  return fetch(url);
}

export function nonNull(url: string) {
  url! = '/x';
  return fetch(url);
}

export function objectPattern(url: string, other: { url: string }) {
  ({ url } = other);
  return fetch(url);
}

export function closure(url: string) {
  const change = () => {
    url = '/changed';
  };
  change();
  return fetch(url);
}

export function noArgument() {
  return fetch();
}

export function arrayParen(url: string, xs: string[]) {
  [(url as any)] = xs;
  return fetch(url);
}

export function forParen(url: string, xs: string[]) {
  for ((url as any) of xs) {}
  return fetch(url);
}

export function pairParen(url: string, o: any) {
  ({ a: (url as any) } = o);
  return fetch(url);
}

export function arrayNonNull(url: string, xs: string[]) {
  [url!] = xs;
  return fetch(url);
}

export function evaluated(url: string) {
  eval("url = '/x'");
  return fetch(url);
}

export function argsAlias(url: string) {
  arguments[0] = '/x';
  return fetch(url);
}

export async function genericArrayParen<T>(url: string, xs: string[]): Promise<T> {
  [(url as any)] = xs;
  return (await fetch(url, { method: 'PUT' })).json();
}

export async function genericEval<T>(url: string): Promise<T> {
  eval("url = '/x'");
  return (await fetch(url, { method: 'PUT' })).json();
}

export async function genericDefaultArrayParen<T>(url: string, xs: string[], retries = 1): Promise<T> {
  [(url as any)] = xs;
  return (await fetch(url, { method: 'PUT' })).json();
}

export function destructuredParameter({ url }: { url: string }) {
  return fetch(url);
}

export function restParameter(...url: string[]) {
  return fetch(url as any);
}

export function outer(url: string) {
  function inner() {
    return fetch(url);
  }
  return inner;
}

export function nestedGeneric(url: string, xs: string[]) {
  [(url as any)] = xs;
  function later<T>(value: T) {
    return value;
  }
  later(1);
  return fetch(url);
}

export async function genericBlock<T>(url: string, flag: boolean): Promise<T> {
  if (flag) {
    (url as any) = '/x';
  }
  return (await fetch(url, { method: 'PUT' })).json();
}

export function unreadBlock(url: string, xs: string[]) {
  if (xs.length) {
    [(url as any)] = xs;
  }
  return fetch(url);
}

export function parenEval(url: string) {
  (eval)("url = '/x'");
  return fetch(url);
}

export function asEval(url: string) {
  (eval as any)("url = '/x'");
  return fetch(url);
}

export function nonNullEval(url: string) {
  (eval!)("url = '/x'");
  return fetch(url);
}

export async function genericParenEval<T>(url: string): Promise<T> {
  (eval)("url = '/x'");
  return (await fetch(url, { method: 'PUT' })).json();
}

export function computedKey(url: string) {
  return fetch(url, { ['method']: 'POST' });
}

export function computedOther(url: string, key: string) {
  return fetch(url, { [key]: 'x', method: 'POST' });
}

export function protoMethod(url: string) {
  return fetch(url, { __proto__: { method: 'POST' } } as any);
}

