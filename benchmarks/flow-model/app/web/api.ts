const BASE = "/api/shop";

export async function apiGet(path: string): Promise<unknown> {
  const response = await fetch(BASE + path);
  if (!response.ok) {
    throw new Error(`GET ${path}: ${response.status}`);
  }
  return response.json();
}

export async function apiPost(path: string, body: unknown): Promise<unknown> {
  const response = await fetch(BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST ${path}: ${response.status}`);
  }
  return response.json();
}
