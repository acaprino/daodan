import { useStore } from "./store.ts";

export function renderBadge(orderId: string): string {
  const status = useStore((s) => s.payment[orderId]);
  return status === "captured" ? "Pagato" : "Da pagare";
}
