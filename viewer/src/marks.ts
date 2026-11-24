// The address of a logo: the server of a page answers, on a route of its own, the mark of an entry of its registry, to whoever has
// the page's token where there is one: an image sends no header. An address that answers nothing (a static export, an entry with no
// mark) leaves the icon in its place.
export const markAddress = (route: string, mark: string | null | undefined, token: string): string | undefined =>
  (mark ? `${route}?${new URLSearchParams({ id: mark, ...(token && { token }) })}` : undefined);
