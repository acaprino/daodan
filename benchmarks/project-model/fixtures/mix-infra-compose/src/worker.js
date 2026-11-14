import pg from 'pg';
import amqp from 'amqplib';

const db = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const channel = await (await amqp.connect(process.env.AMQP_URL)).createChannel();
await channel.assertQueue('orders');

channel.consume('orders', async (message) => {
  const order = JSON.parse(message.content.toString());
  await db.query('UPDATE orders SET receipt_sent = true WHERE id = $1', [order.id]);
  channel.ack(message);
});
