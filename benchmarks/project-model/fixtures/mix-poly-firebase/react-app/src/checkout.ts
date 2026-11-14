import { httpsCallable } from "firebase/functions";
import { collection, onSnapshot } from "firebase/firestore";
import { invoke } from "@tauri-apps/api/core";
import { loadStripe } from "@stripe/stripe-js";
import { ORDERS } from "@shared/collections";
import type { Order } from "@shared/types";
import { db, functions } from "./firebase";

export const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);

export async function startCheckout(price: string): Promise<string> {
  const create = httpsCallable<{ price: string; return_url: string }, { url: string }>(
    functions,
    "create_checkout_session",
  );
  const { data } = await create({ price, return_url: window.location.href });
  return data.url;
}

export function watchOrders(onChange: (orders: Order[]) => void): () => void {
  return onSnapshot(collection(db, ORDERS), (snap) =>
    onChange(snap.docs.map((d) => ({ id: d.id, ...d.data() }) as Order)),
  );
}

export function saveReceipt(orderId: string): Promise<string> {
  return invoke<string>("save_receipt", { orderId });
}
