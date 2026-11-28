const http = require('node:http');
const { listBooks, findBook } = require('./src/books');

const PORT = 3000;
const escape = text => String(text).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const page = (title, body) =>
  `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${escape(title)}</title></head><body><main>${body}</main></body></html>`;

async function answer(path) {
  const url = process.env.DATABASE_URL;
  if (path.startsWith('/books/')) {
    const book = await findBook(url, Number(path.slice('/books/'.length)));
    return book ? [200, page(book.title, `<h1>${escape(book.title)}</h1><p>${escape(book.author)}</p><a href="/">Back</a>`)]
      : [404, page('Not found', '<a href="/">Back</a>')];
  }
  const books = await listBooks(url);
  return [200, page('Shelf', `<h1>Shelf</h1><ul>${books.map(book =>
    `<li><a href="/books/${book.id}">${escape(book.title)}</a></li>`).join('')}</ul>`)];
}

http.createServer(async (request, response) => {
  if (request.url === '/favicon.ico') return response.writeHead(404).end();
  let status, html;
  try {
    [status, html] = await answer(request.url);
  } catch (error) {
    [status, html] = [500, page('Shelf', `<p>The shelf cannot read its database: ${escape(error.message)}</p>`)];
  }
  response.writeHead(status, { 'content-type': 'text/html; charset=utf-8' }).end(html);
}).listen(PORT, () => console.log(`Shelf on http://localhost:${PORT}/`));
