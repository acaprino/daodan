// TypeScript strict. Contract: parse an external JSON payload with id:string; otherwise return "invalid", including malformed JSON.
export function parse(raw: string): string {
  let value: unknown;
  try { value = JSON.parse(raw); } catch { return "invalid"; }
  if (typeof value !== "object" || value === null || !("id" in value) || typeof value.id !== "string") return "invalid";
  return value.id.toLowerCase();
}
