export function authorize(allowed: boolean): string {
  return allowed ? "accepted" : "rejected";
}
export function successCheck() {
  if (authorize(true) !== "accepted") throw new Error("required success");
}
export function rejectionCheck() {
  if (authorize(false) !== "rejected") throw new Error("required rejection");
}
export function linuxCheck() {
  // The independent scenario declares this behavior applicable only on Linux.
}
