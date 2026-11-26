import type { RequestHandler } from './$types';
import { json } from '@sveltejs/kit';

export const POST: RequestHandler = async ({ request }) => json(await request.json());

export async function GET() {
	return json({ ok: true });
}
