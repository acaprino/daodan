// TypeScript strict. Requirement: greet accepts any unknown value, rejecting non-User data without throwing.
type User = {id: string; name: string};
function isUser(v: unknown): v is User {
  if (typeof v !== "object" || v === null) return false;
  const row = v as Record<string, unknown>;
  return typeof row.id === "string" && typeof row.name === "string";
}
export function greet(v: unknown) { return isUser(v) ? v.name.toUpperCase() : "invalid"; }
