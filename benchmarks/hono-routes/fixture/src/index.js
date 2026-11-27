import { Hono } from 'hono'

import api from './api.js'

const app = new Hono()

async function timing(c, next) {
  await next()
  c.header('X-Fixture', '1')
}

function health(c) {
  return c.json({ ok: true })
}

app.use('*', timing)
app.get('/health', health)
app.get('/inline', (c) => c.text('inline'))
app.route('/api', api)

export default app
