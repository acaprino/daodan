// a resource route: no default export
export async function action({ request }: { request: Request }) {
  const body = await request.json();
  return Response.json({ paid: Boolean(body) });
}
