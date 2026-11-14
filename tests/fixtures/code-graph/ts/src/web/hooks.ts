import { useCallback } from 'react';
function open(): number {
  return 1;
}
export function useModal() {
  const close = useCallback(() => 0, []);
  return { open, close };
}
