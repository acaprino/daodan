import { pool } from "@/lib/db";

export async function GET() {
  await pool.query("select 1");
  return Response.json({ ok: true });
}
