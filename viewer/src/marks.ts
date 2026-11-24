// The address of a logo: the server of the page answers the mark of an entry of its registry, to whoever has the page's token
// where there is one. An address that answers nothing (a static export, an entry with no mark) leaves the icon in its place.
export const markAddress = (mark: string | undefined, token: string): string | undefined =>
  (mark ? `./api/mark?id=${encodeURIComponent(mark)}${token && `&token=${encodeURIComponent(token)}`}` : undefined);
