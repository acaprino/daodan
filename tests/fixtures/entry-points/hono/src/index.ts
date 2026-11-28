import { writeFileSync } from 'node:fs'
import { Hono } from 'hono'
import { health } from './handlers'
import { users } from './users'
import { other } from './other'

writeFileSync('ran.txt', 'the app ran')  // never: the fixture is read, not run

const app = new Hono()
const api = new Hono().basePath('/api')

app.get('/health', health)
app.post('/login', (c) => c.text('ok')).get('/me', (c) => c.json({}))
app.use('*', async (c, next) => {
  await next()
})
api.route('/users', users)
api.delete('/cache', (c) => c.body(null))
app.route('/', api)
const where = '/x' + process.env.PREFIX
app.route(where, other)

export default app
