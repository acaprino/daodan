// a resource route: no default export, so no component, only the data functions
export async function loader() {
  return Response.json({ ok: true });
}

export async function action({ request }: { request: Request }) {
  const body = await request.json();
  return Response.json({ paid: Boolean(body) });
}
