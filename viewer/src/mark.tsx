// What a thing is, before its name: its logo where it has one (`markAddress`), else its icon, which is also there while the logo
// loads and where it fails.
import { Icon, Logo } from '@acaprino/sigrid/primitives';
import type { NodeIcon } from './icons.ts';

export function Mark({ image, icon }: { image?: string; icon: NodeIcon }) {
  return image ? <Logo src={image} icon={icon || undefined} decorative /> : <Icon name={icon} />;
}
