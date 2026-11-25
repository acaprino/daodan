const canvasOf = (name: string) => document.querySelector(`[role="group"][aria-label="${name}"]`);

// Whether things of the canvas are in sight, by their ids. A workaround: the canvas moves its view (`focus`) and does not say what is
// in it, and a view that is moved where all is in sight already loses the person. So the things are read from the page, where Sigrid
// writes the id of each (`data-node-id`). What is out of the view is not drawn.
export function inSight(canvasName: string, ids: readonly string[]): boolean {
  const canvas = canvasOf(canvasName);
  if (!canvas) return false;
  const room = canvas.getBoundingClientRect();
  const seen = new Set<string | undefined>();
  for (const thing of canvas.querySelectorAll<HTMLElement>('[data-node-id]')) {
    const { left, right, top, bottom } = thing.getBoundingClientRect();
    if (left >= room.left && right <= room.right && top >= room.top && bottom <= room.bottom) seen.add(thing.dataset.nodeId);
  }
  return ids.every(id => seen.has(id));
}

const STILL = 3;  // frames with one width: what slides has stopped

// After what is drawn now is on the page and the canvas has its width (an inspector that opens slides in beside it); ended by what
// it returns.
export function onceDrawn(canvasName: string, run: () => void): () => void {
  const widthNow = () => canvasOf(canvasName)?.getBoundingClientRect().width;
  let width = widthNow(), same = 0;
  const next = () => {
    const now = widthNow();
    same = now === width ? same + 1 : 0;
    width = now;
    if (same < STILL) frame = requestAnimationFrame(next);
    else run();
  };
  let frame = requestAnimationFrame(next);
  return () => cancelAnimationFrame(frame);
}
