import { useModal } from './hooks';
export function tag() {
  const { open: openTag, close: closeTag } = useModal();
  openTag();
  closeTag();
}
