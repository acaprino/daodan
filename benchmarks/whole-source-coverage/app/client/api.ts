import { authHeaders } from "./session.ts";

export interface Note {
  name: string;
  text: string;
}

const NAME = /^[a-z0-9][a-z0-9_-]{0,63}$/;

function noteUrl(base: string, name: string): string {
  if (!NAME.test(name)) {
    throw new Error("invalid note name");
  }
  return `${base}/notes/${encodeURIComponent(name)}`;
}

export async function getNote(base: string, name: string): Promise<Note> {
  const response = await fetch(noteUrl(base, name), { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(`get failed: ${response.status}`);
  }
  const body: unknown = await response.json();
  if (typeof body !== "object" || body === null || typeof (body as Note).text !== "string") {
    throw new Error("unexpected response");
  }
  return body as Note;
}

export async function putNote(base: string, name: string, text: string): Promise<void> {
  const response = await fetch(noteUrl(base, name), {
    method: "PUT",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    throw new Error(`put failed: ${response.status}`);
  }
}
