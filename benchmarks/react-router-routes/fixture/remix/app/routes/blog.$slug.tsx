export async function loader({ params }: { params: { slug: string } }) {
  return { slug: params.slug };
}

export default function Post() {
  return <h1>Post</h1>;
}
