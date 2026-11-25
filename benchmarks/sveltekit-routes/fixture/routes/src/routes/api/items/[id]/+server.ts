import type { RequestHandler } from './$types';
import { find } from '$lib/server/db';
import { json } from '@sveltejs/kit';

export const GET: RequestHandler = ({ params }) => json(find(params.id));
export const PUT: RequestHandler = async ({ params, request }) => json({ id: params.id, body: await request.text() });
export const DELETE: RequestHandler = ({ params }) => json({ deleted: params.id });
export const fallback: RequestHandler = ({ request }) => new Response(request.method);
