import { Form } from "react-router";

export async function loader() {
  return { cart: [] };
}

export async function action({ request }: { request: Request }) {
  const form = await request.formData();
  return { paid: form.get("card") !== null };
}

export default function Checkout() {
  return (
    <Form method="post">
      <button type="submit">Pay</button>
    </Form>
  );
}
