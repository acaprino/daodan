export default async function Order({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <h1>Ordine {id}</h1>;
}
