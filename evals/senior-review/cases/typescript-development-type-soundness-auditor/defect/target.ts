// TypeScript strict. Requirement: greet accepts any unknown value, rejecting non-User data without throwing.
type User = {id: string; name: string};
function isUser(v: unknown): v is User {
  return typeof v === "object" && v !== null && typeof (v as Record<string, unknown>).id === "string";
}
export function greet(v: unknown) { return isUser(v) ? v.name.toUpperCase() : "invalid"; }
