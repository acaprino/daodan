import { setState, useStore } from "./store.ts";
import { button, type Button } from "./ui.ts";

export function addToCart(item: string): void {
  const cart = useStore((s) => s.cart);
  setState({ cart: [...cart, item] });
}

export function toggleTheme(): void {
  const theme = useStore((s) => s.theme);
  setState({ theme: theme === "light" ? "dark" : "light" });
}

export function renderCart(): { lines: string[]; actions: Button[] } {
  const cart = useStore((s) => s.cart);
  return {
    lines: cart.map((item, index) => `${index + 1}. ${item}`),
    actions: [button("Tema", toggleTheme)],
  };
}
