import type { Request, Response } from 'express';

export function download(req: Request, res: Response) {
  res.end();
}
