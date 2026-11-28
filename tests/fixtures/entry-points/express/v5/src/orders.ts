import { Router, type Request, type Response } from 'express';

export const orders = Router();

export function getOrder(req: Request, res: Response) {
  res.json({});
}

orders.get('/:id', getOrder);
orders.all('/:id/audit', getOrder);
