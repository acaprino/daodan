export function slug(text) {
  return text.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-');
}
