// The test data the CI writes before the tests: the table and its two books.
const { query } = require('../src/books');

const url = process.env.DATABASE_URL;
(async () => {
  await query(url, 'DROP TABLE IF EXISTS books');
  await query(url, 'CREATE TABLE books (id serial PRIMARY KEY, title text NOT NULL, author text NOT NULL)');
  await query(url, "INSERT INTO books (title, author) VALUES ('Dune', 'Frank Herbert'), ('Solaris', 'Stanislaw Lem')");
  console.log('seeded 2 books');
})().catch(error => {
  console.error(error);
  process.exit(1);
});
