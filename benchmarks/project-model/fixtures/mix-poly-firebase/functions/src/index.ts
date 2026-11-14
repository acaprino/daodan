import { onDocumentUpdated } from "firebase-functions/v2/firestore";
import { initializeApp } from "firebase-admin/app";
import Stripe from "stripe";
import { ORDERS } from "../../shared/collections";
import type { Order } from "../../shared/types";

initializeApp();
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY ?? "");

export const onOrderPaid = onDocumentUpdated(`${ORDERS}/{orderId}`, async (event) => {
  const after = event.data?.after.data() as Order | undefined;
  if (after?.status === "paid") {
    await stripe.invoices.list({ limit: 1 });
  }
});
