import { useCallback, useMemo } from 'react';
import { startCheckout, priceFor } from './billing';
export function useCheckout(plan) {
  const pay = useCallback(() => startCheckout(plan), [plan]);
  const price = useMemo(() => priceFor(plan), [plan]);
  return { pay, price };
}
