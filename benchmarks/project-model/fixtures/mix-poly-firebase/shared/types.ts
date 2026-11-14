export interface Order {
  id: string;
  uid: string;
  status: "open" | "paid";
}
