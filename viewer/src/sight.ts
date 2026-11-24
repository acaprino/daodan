// Whether things of the canvas are in sight. A workaround: the canvas moves its view (`focus`) and does not say what is in it, and a
// view that is moved where all is in sight already loses the person. What a person meets there is read instead: the things by their
// role and their name, which starts with their label. What is out of the view is not drawn.
export function inSight(canvasName: string, labels: readonly string[]): boolean {
  const canvas = document.querySelector(`[role="group"][aria-label="${canvasName}"]`);
  if (!canvas) return false;
  const room = canvas.getBoundingClientRect();
  const names = Array.from(canvas.querySelectorAll('[role="button"][aria-label]'), thing => {
    const { left, right, top, bottom } = thing.getBoundingClientRect();
    const whole = left >= room.left && right <= room.right && top >= room.top && bottom <= room.bottom;
    return whole ? thing.getAttribute('aria-label')! : '';
  });
  return labels.every(label => names.some(name => name === label || name.startsWith(`${label},`)));
}

// After what is drawn now is on the page, and the page has its new sizes (an inspector that opens); ended by what it returns.
export function onceDrawn(run: () => void): () => void {
  let frame = requestAnimationFrame(() => { frame = requestAnimationFrame(run); });
  return () => cancelAnimationFrame(frame);
}
