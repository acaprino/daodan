import createClient from "openapi-fetch";
import type { paths } from "./api/schema";

const client = createClient<paths>({ baseUrl: "http://localhost:8000" });

export async function listOrders() {
  const { data, error } = await client.GET("/orders");
  if (error) throw new Error("cannot list orders");
  return data;
}

export async function createOrder(total: number) {
  const { data } = await client.POST("/orders", { body: { total } });
  return data;
}
