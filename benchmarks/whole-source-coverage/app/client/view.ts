import type { Note } from "./api.ts";

// Shows one note, or an error message, in the container.
export function renderNote(container: HTMLElement, note: Note): void {
  const title = document.createElement("h2");
  title.textContent = note.name;
  const body = document.createElement("pre");
  body.textContent = note.text;
  container.replaceChildren(title, body);
}

export function renderError(container: HTMLElement, message: string): void {
  const line = document.createElement("p");
  line.className = "error";
  line.textContent = message;
  container.replaceChildren(line);
}
