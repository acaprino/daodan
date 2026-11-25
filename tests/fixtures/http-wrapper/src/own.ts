// What is named like the client and is not it.

export function fetch(url: string): string {
  return url;
}

export function useOwn(url: string) {
  return fetch(url);
}

export function injected(fetch: (url: string) => Promise<Response>, url: string) {
  return fetch(url);
}
