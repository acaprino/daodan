const { Client } = require('pg');

async function query(url, text, values = []) {
  const client = new Client({ connectionString: url });
  await client.connect();
  try {
    return (await client.query(text, values)).rows;
  } finally {
    await client.end();
  }
}

const listBooks = url => query(url, 'SELECT id, title FROM books ORDER BY id');
const findBook = async (url, id) => (await query(url, 'SELECT title, author FROM books WHERE id = $1', [id]))[0];

module.exports = { query, listBooks, findBook };
