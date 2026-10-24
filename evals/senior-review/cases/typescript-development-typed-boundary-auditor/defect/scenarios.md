# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## queue-storage-env

Queue user.id and stored profile.name must be strings; PORT must be a finite integer 1..65535. Invalid input is rejected before service use.

```ts
export function queue(raw:string){const user=JSON.parse(raw) as {id:string};return user.id.toLowerCase();}
export function stored(raw:string){return (JSON.parse(raw) as {name:string}).name.toUpperCase();}
export function port(env:Record<string,string|undefined>){return Number(env.PORT!);}
```

## trusted-adapter

Adapter is the only caller; it validates the complete payload before invoking handle. All code below belongs to one atomic deployment.

```ts
type User={name:string};
export function receive(raw:unknown){return handle(raw as User);}
function handle(user:User){return user.name.toUpperCase();}
```
