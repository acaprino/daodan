// Whether things of the canvas are in sight, by their ids. A workaround: the canvas moves its view (`focus`) and does not say what is
// in it, and a view that is moved where all is in sight already loses the person. So the things are read from the page, where Sigrid
// writes the id of each (`data-node-id`). What is out of the view is not drawn.
export function inSight(canvasName: string, ids: readonly string[]): boolean {
  const canvas = document.querySelector(`[role="group"][aria-label="${canvasName}"]`);
  if (!canvas) return false;
  const room = canvas.getBoundingClientRect();
  const seen = new Set<string | undefined>();
  for (const thing of canvas.querySelectorAll<HTMLElement>('[data-node-id]')) {
    const { left, right, top, bottom } = thing.getBoundingClientRect();
    if (left >= room.left && right <= room.right && top >= room.top && bottom <= room.bottom) seen.add(thing.dataset.nodeId);
  }
  return ids.every(id => seen.has(id));
}

// After what is drawn now is on the page, and the page has its new sizes (an inspector that opens); ended by what it returns.
export function onceDrawn(run: () => void): () => void {
  let frame = requestAnimationFrame(() => { frame = requestAnimationFrame(run); });
  return () => cancelAnimationFrame(frame);
}
