export function startCheckout(plan) {
  return fetch('/api/checkout', { method: 'POST', body: plan });
}
export const priceFor = (plan) => (plan === 'pro' ? 10 : 0);
export function runWith(callback, value) {
  return callback(value);
}
