// the loader is a variable holding an arrow function
export const loader = async ({ params }: { params: { id: string } }) => {
  return { id: params.id };
};

export default function Order() {
  return <h1>Order</h1>;
}
