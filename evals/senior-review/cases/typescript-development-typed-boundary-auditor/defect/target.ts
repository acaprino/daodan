// TypeScript strict. Contract: parse an external JSON payload with id:string; otherwise return "invalid", including malformed JSON.
export function parse(raw: string): string {
  let value: unknown;
  try { value = JSON.parse(raw); } catch { return "invalid"; }
  return (value as {id: string}).id.toLowerCase();
}
