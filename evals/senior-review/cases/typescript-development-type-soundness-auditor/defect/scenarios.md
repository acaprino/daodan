# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## assertions-and-generics

Exported functions must handle every value admitted by their declared parameter types without a TypeError.

```ts
export function length<T=any>(value:T):number{return (value as any).length.toFixed();}
export function email(users:Map<string,{email:string}>,id:string){return users.get(id)!.email;}
```

## effective-config-and-exhaustiveness

All pending/paid/refunded states render a label. Child tsconfig extends a base with strict true; effective indexing remains unchecked. Declared runtime input can be an unknown key.

```ts
type State="pending"|"paid"|"refunded";
export function label(s:State){switch(s){case "pending":return "wait";case "paid":return "done";}}
export function lookup(values:Record<string,string>,key:string){return values[key].toLowerCase();}
```
First-party .d.ts says lookup never returns undefined; compiler lane skips that declaration.
