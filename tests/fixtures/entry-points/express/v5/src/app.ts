import express, { Router } from 'express';
import { orders } from './orders';
import * as files from './files';

const app = express();
const admin = Router();

admin.delete('/cache', (req, res) => {
  res.end();
});
admin.use('/orders', orders);
app.use('/admin', admin);
app.get('/files/{*path}', files.download);

export default app;
