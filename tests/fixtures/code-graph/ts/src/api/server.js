const express = require('express');
const { CheckoutService, MemoryStore } = require('./service');
const app = express();
const service = new CheckoutService(new MemoryStore());
function checkout(req, res) {
  res.status(201).json(service.create(req.body));
}
const health = (req, res) => res.json({ ok: true });
app.post('/api/checkout', checkout);
app.get('/health', health);
app.listen(3000);
