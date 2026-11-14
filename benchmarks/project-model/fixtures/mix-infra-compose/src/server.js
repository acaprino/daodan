import express from 'express';
import pg from 'pg';
import Redis from 'ioredis';
import amqp from 'amqplib';

const db = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const cache = new Redis(process.env.REDIS_URL);
const channel = await (await amqp.connect(process.env.AMQP_URL)).createChannel();
await channel.assertQueue('orders');

const app = express();
app.use(express.json());

app.post('/orders', async (req, res) => {
  const { rows } = await db.query('INSERT INTO orders (total) VALUES ($1) RETURNING id', [req.body.total]);
  await cache.del('orders:recent');
  channel.sendToQueue('orders', Buffer.from(JSON.stringify(rows[0])));
  res.status(201).json(rows[0]);
});

app.listen(3000);
