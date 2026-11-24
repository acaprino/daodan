// What a thing is, before its name: its logo where it has one, else its icon, which is also there while the logo loads and where
// it fails.
import { Icon, Logo } from '@acaprino/sigrid/primitives';
import type { NodeIcon } from './icons.ts';
import { markAddress } from './marks.ts';
import { TOKEN } from './token.ts';

export function Mark({ mark, icon }: { mark?: string; icon: NodeIcon }) {
  const address = markAddress(mark, TOKEN);
  return address ? <Logo src={address} icon={icon || undefined} decorative /> : <Icon name={icon} />;
}
