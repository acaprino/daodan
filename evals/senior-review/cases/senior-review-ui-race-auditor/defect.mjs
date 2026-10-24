// Requirement: The latest search must own displayed results. fetchResults(query) returns a promise; requests can resolve out of order. render replaces the displayed result, and no external cancellation or ordering guard exists.

export async function search(query, fetchResults, render) {
  const result = await fetchResults(query);
  render(result);
}
