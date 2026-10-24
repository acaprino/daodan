# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## assertions-and-generics

Exported functions must handle every value admitted by their declared parameter types without a TypeError.

```ts
export function length<T extends {length:number}>(value:T):number{return value.length;}
export function email(users:Map<string,{email:string}>,id:string){const user=users.get(id);return user ? user.email : "unknown";}
```

## effective-config-and-exhaustiveness

All pending/paid/refunded states render a label. Child tsconfig extends a base with strict true; effective indexing remains unchecked. Declared runtime input can be an unknown key.

```ts
type State="pending"|"paid"|"refunded";
const labels:Record<State,string>={pending:"wait",paid:"done",refunded:"returned"};
export function label(s:State){return labels[s];}
export function lookup(values:Record<string,string>,key:string){return values[key]?.toLowerCase() ?? "unknown";}
```
Child tsconfig still inherits strict; the real boundary guard protects absent keys.
