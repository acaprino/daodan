export function norm(value: string): string;
export function norm(value: number): number;
export function norm(value: string | number): string | number {
  return value;
}
export function useNorm(): number {
  return norm(1);
}
