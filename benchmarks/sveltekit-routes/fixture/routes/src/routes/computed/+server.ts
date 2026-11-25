const make = (name: string) => () => new Response(name);

export const GET = make('get');
