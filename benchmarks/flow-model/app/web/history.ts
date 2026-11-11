import { apiGet } from "./api.ts";
import { ORDERS } from "./routes.ts";

export async function loadHistory(): Promise<string[]> {
  const rows = (await apiGet(ORDERS)) as Array<{ id: string; paid: boolean }>;
  return rows.map((row) => `${row.id}: ${row.paid ? "pagato" : "aperto"}`);
}
