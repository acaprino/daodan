import type { APIRoute } from 'astro';

export const prerender = false;

export const GET: APIRoute = () => new Response(JSON.stringify(['a', 'b']));

export const POST: APIRoute = async ({ request }) => new Response(await request.text(), { status: 201 });
