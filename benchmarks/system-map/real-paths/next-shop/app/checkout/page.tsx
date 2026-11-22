import { pay } from "./actions";

export default function Checkout() {
  return (
    <form action={pay}>
      <button type="submit">Paga</button>
    </form>
  );
}
