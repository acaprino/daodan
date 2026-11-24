// The token comes in the address the MCP server returned; a static export has none and needs none.
export const TOKEN = new URLSearchParams(window.location.search).get('token') ?? '';
