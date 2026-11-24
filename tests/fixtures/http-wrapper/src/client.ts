// Functions that wrap the HTTP client: the URL is a parameter, passed on as it is.

export async function plain(url: string, body: unknown): Promise<Response> {
  return fetch(url, { method: 'POST', body: JSON.stringify(body) });
}

export async function generic<T>(url: string, decode: (raw: unknown) => T): Promise<T> {
  const response = await fetch(url, { method: 'PUT' });
  return decode(await response.json());
}

export const arrow = (url: string) => fetch(url);

export class Api {
  remove(url: string) {
    return fetch(url, { method: 'DELETE' });
  }
}

export function second(first: string, url: string) {
  return fetch(url, { method: 'PATCH', headers: { 'x-first': first } });
}

export function viaWindow(url: string) {
  return window.fetch(url);
}

export function remote(url: string) {
  return fetch(url, { method: 'GET' });
}

export function agreeing(url: string, flag: boolean) {
  if (flag) {
    return fetch(url, { method: 'POST' });
  }
  return fetch(url, { method: 'POST', headers: {} });
}

export function overloadedFunction(url: string): Promise<Response>;
export function overloadedFunction(url: string, extra: string): Promise<Response>;
export function overloadedFunction(url: string, extra?: string) {
  return fetch(url, { headers: { extra: extra ?? '' } });
}

export class Overloaded {
  get(url: string): Promise<Response>;
  get(url: string, extra: string): Promise<Response>;
  get(url: string, extra?: string) {
    return fetch(url, { headers: { extra: extra ?? '' } });
  }
}

export function withThis(this: Window, url: string) {
  return fetch(url);
}

export async function genericDefault<T>(url: string, retries = 1): Promise<T> {
  return (await fetch(url, { method: 'PUT' })).json();
}

// The shape of a wrapper a real project has: generic, five parameters (two optional), a nested arrow, a `try`, nested spread.
type Decoder<T> = (raw: unknown) => T;
declare const auth: { currentUser: { getIdToken(): Promise<string> } | null };

export async function adminFetch<T>(
  url: string,
  body: object,
  decode: Decoder<T>,
  signal?: AbortSignal,
  extraHeaders?: Record<string, string>,
): Promise<T> {
  const user = auth.currentUser;
  if (!user) throw new Error('Not authenticated');
  const assertCurrent = () => {
    if (signal?.aborted || auth.currentUser !== user) {
      throw new DOMException('Request cancelled', 'AbortError');
    }
  };
  try {
    assertCurrent();
    const token = await user.getIdToken();
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...extraHeaders },
      body: JSON.stringify(body),
      signal,
    });
    assertCurrent();
    return decode(await response.json());
  } catch (error) {
    assertCurrent();
    throw error;
  }
}

export function quotedKey(url: string) {
  return fetch(url, { 'method': 'POST' });
}

// An indirect eval runs in the global scope: it cannot write the parameter.
export function indirectEval(url: string) {
  (0, eval)("url = '/x'");
  return fetch(url, { method: 'PUT' });
}
