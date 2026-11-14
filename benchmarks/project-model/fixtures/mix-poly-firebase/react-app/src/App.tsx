import { useEffect, useState } from "react";
import type { Order } from "@shared/types";
import { saveReceipt, startCheckout, watchOrders } from "./checkout";

export default function App() {
  const [orders, setOrders] = useState<Order[]>([]);
  useEffect(() => watchOrders(setOrders), []);

  return (
    <main>
      <button onClick={async () => window.location.assign(await startCheckout("price_basic"))}>Buy</button>
      {orders.map((order) => (
        <button key={order.id} onClick={() => saveReceipt(order.id)}>
          Receipt {order.id}
        </button>
      ))}
    </main>
  );
}
