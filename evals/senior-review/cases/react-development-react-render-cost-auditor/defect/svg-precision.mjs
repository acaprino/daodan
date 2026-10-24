/* The React export view emits this function's result as an SVG polyline points
   attribute on a critical initial artifact. Exactly 10,000 validated finite
   coordinate pairs have each component in [0, 1000]. ASCII bytes equal string
   length here. Required points-attribute budget is 200,000 bytes. Coordinates
   may differ from input by at most 0.001 viewBox units; no finer precision is
   needed for this display. The bundler does not rewrite the generated string.
   The separately requested scientific export must keep error below 1e-10 and
   has no size budget. It is intentionally not the initial artifact. JavaScript
   Number/toFixed semantics apply; no actual browser/serialization timing is
   supplied, and dependencies or geometry beyond these bounds are irrelevant. */

export function displayPoints(points) {
  return points.map(([x, y]) => `${x.toFixed(12)},${y.toFixed(12)}`).join(' ');
}

export function scientificPoints(points) {
  return points.map(([x, y]) => `${x.toFixed(12)},${y.toFixed(12)}`).join(' ');
}
