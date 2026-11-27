import { Hono } from 'hono'

const api = new Hono().basePath('/v1')

export function listUsers(c) {
  return c.json([])
}

api.get('/users', listUsers)
api.post('/users/:id', async (c) => c.json({ id: c.req.param('id') }))

export default api
