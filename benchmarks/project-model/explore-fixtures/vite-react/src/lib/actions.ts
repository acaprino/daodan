function validate(n: number): number {
  return Number.isFinite(n) ? n : 0;
}

export function save(n: number): number {
  return validate(n) + 1;
}

export function reset(): number {
  return 0;
}
