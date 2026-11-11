import { apiPost } from "./api.ts";
import { PAYMENTS } from "./routes.ts";
import { setState, useStore } from "./store.ts";
import { button, type Button } from "./ui.ts";

interface PaymentReply {
  orderId: string;
  status: string;
}

export async function submitPayment(orderId: string): Promise<void> {
  const reply = (await apiPost(PAYMENTS, { orderId })) as PaymentReply;
  const payment = useStore((s) => s.payment);
  setState({ payment: { ...payment, [reply.orderId]: reply.status } });
}

export function onPayClick(orderId: string): void {
  void submitPayment(orderId);
}

export function renderCheckout(orderId: string): Button[] {
  return [button("Paga", () => onPayClick(orderId))];
}
