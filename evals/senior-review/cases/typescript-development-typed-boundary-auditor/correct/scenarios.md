# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## queue-storage-env

Queue user.id and stored profile.name must be strings; PORT must be a finite integer 1..65535. Invalid input is rejected before service use.

```ts
function field(raw:string,key:string){try{const value:unknown=JSON.parse(raw);if(typeof value==="object"&&value!==null&&typeof (value as Record<string,unknown>)[key]==="string")return (value as Record<string,string>)[key];}catch{}return null;}
export function queue(raw:string){return field(raw,"id")?.toLowerCase() ?? "invalid";}
export function stored(raw:string){return field(raw,"name")?.toUpperCase() ?? "invalid";}
export function port(env:Record<string,string|undefined>){const p=Number(env.PORT);return Number.isInteger(p)&&p>=1&&p<=65535?p:null;}
```

## trusted-adapter

Adapter is the only caller; it validates the complete payload before invoking handle. All code below belongs to one atomic deployment.

```ts
type User={name:string};
export function receive(raw:unknown){if(typeof raw!=="object"||raw===null||!("name" in raw)||typeof raw.name!=="string")return "invalid";return handle({name:raw.name});}
function handle(user:User){return user.name.toUpperCase();}
```
