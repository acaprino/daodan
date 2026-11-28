import { Hono } from 'hono'

export const users = new Hono()

function list(c) {
  return c.json([])
}

users.get('/', list)
users.all('/:id', (c) => c.json({}))
