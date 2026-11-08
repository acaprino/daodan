// Keeps the bearer token in memory for the lifetime of the page.
let token: string | null = null;

const TOKEN = /^[A-Za-z0-9]+\.\d+\.[A-Za-z0-9_-]+$/;

export function setToken(value: string): void {
  if (!TOKEN.test(value)) {
    throw new Error("unexpected token format");
  }
  token = value;
}

export function clearToken(): void {
  token = null;
}

export function authHeaders(): Record<string, string> {
  if (token === null) {
    throw new Error("not signed in");
  }
  return { Authorization: `Bearer ${token}` };
}
