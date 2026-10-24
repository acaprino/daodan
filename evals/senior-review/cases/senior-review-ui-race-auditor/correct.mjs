// Requirement: The latest search must own displayed results. fetchResults(query) returns a promise; requests can resolve out of order. render replaces the displayed result, and no external cancellation or ordering guard exists.

let generation = 0;
export async function search(query, fetchResults, render) {
  const current = ++generation;
  const result = await fetchResults(query);
  if (current === generation) render(result);
}
