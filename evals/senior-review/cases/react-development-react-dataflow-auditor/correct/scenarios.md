# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## dependency-waterfall

loadA and loadB are independent read-only operations, each taking 400ms in supplied measurements. Required response budget is 600ms excluding negligible render. Auth has already completed.

```js
export async function page(loadA,loadB){const [a,b]=await Promise.all([loadA(),loadB()]);return {a,b};}
```

## freshness-and-storage

Account switching must never reuse another account’s balance. Old stored profile version 1 lacks name; current version 2 requires name:string. Query fetches are externally supplied.

```js
export const balanceQuery=(account)=>({queryKey:["balance",account],queryFn:()=>fetchBalance(account),staleTime:300000});
export function storedName(storage){try{const p=JSON.parse(storage.getItem("profile"));return p?.version===2 && typeof p.name==="string" ? p.name.toUpperCase() : "unknown";}catch{return "unknown";}}
```

## serialization-and-lifetime

Client receives only displayName; the request-specific access token must stay server-side. Framework serializes every enumerable field of the passed plain object. Completion logging must survive response cleanup via supplied after().

```js
export function props(user){return {displayName:user.displayName};}
export function finish(log,after){after(log);return "ok";}
```
after registers request-lifetime completion in this supplied host contract.
