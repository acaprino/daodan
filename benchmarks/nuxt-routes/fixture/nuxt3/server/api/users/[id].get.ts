export default defineEventHandler((event) => ({ id: getRouterParam(event, 'id') }))
