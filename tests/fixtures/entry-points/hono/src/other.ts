import { Hono } from 'hono'

export const other = new Hono()

other.get('/o', (c) => c.text('o'))
