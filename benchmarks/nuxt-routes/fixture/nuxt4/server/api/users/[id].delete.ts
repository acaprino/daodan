export default defineEventHandler((event) => ({ removed: getRouterParam(event, 'id') }))
