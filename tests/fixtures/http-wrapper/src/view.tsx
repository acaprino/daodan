// Elements the reader walks: an attribute's value may be one, or a fragment, and hold a write.

declare const A: any;

export function jsxAttr<T>(url: string): T {
  void <A b=<A c={(url = '/evil')} /> />;
  return fetch(url) as any;
}

export function jsxAttrPlain(url: string) {
  void <A b=<A c={(url = '/evil')} /> />;
  return fetch(url);
}

export function jsxFragment(url: string) {
  void <A b=<>{(url = '/evil')}</> />;
  return fetch(url);
}

export function jsxChild(url: string) {
  void <A>{(url = '/evil')}</A>;
  return fetch(url);
}

export function jsxClean(url: string) {
  void <A b="plain" c={url.length} />;
  return fetch(url, { method: 'PUT' });
}
