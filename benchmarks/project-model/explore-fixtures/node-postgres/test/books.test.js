const test = require('node:test');
const assert = require('node:assert/strict');
const { listBooks } = require('../src/books');

test('the shelf lists the books the seed wrote', async () => {
  const books = await listBooks(process.env.DATABASE_URL);
  assert.deepEqual(books.map(book => book.title), ['Dune', 'Solaris']);
});
