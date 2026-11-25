// The address of a logo: the server of a page answers, on a route of its own, the mark of an entry of its registry, to whoever has
// the page's token where there is one: an image sends no header. An address that answers nothing (a static export, an entry with no
// mark) leaves the icon in its place.
export const markAddress = (route: string, mark: string | null | undefined, token: string): string | undefined =>
  (mark ? `${route}?${new URLSearchParams({ id: mark, ...(token && { token }) })}` : undefined);

// The logo of what a group of code is made with: of the one framework it declares. Where it declares several, none is more its own
// than the others: it has its icon, and its details list them all.
export function frameworkMark(technologies: readonly { category?: string; mark?: string }[]): string | undefined {
  const frameworks = technologies.filter(item => item.category === 'framework');
  return frameworks.length === 1 ? frameworks[0].mark : undefined;
}
