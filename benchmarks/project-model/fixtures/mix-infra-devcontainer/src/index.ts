import pg from 'pg';

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });

export async function countInvoices(): Promise<number> {
  const { rows } = await pool.query<{ n: string }>('SELECT count(*) AS n FROM invoices');
  return Number(rows[0].n);
}
