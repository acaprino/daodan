export interface Button {
  label: string;
  onPress: () => void;
}

export function button(label: string, onPress: () => void): Button {
  return { label, onPress };
}
