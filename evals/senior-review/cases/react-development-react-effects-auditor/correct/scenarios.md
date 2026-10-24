# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## dependency-cycle

Each component instance loads once on mount. load always resolves and each object result is distinct.

```jsx
function Panel({load}) {
  const [data, setData] = useState({});
  useEffect(() => { let active = true; load().then(value => { if(active) setData(value); }); return () => {active=false;}; }, [load]);
  return null;
}
```
The load prop is stable for this mounted instance.

## lifetime-and-action

Each click sends exactly one order; changing theme must not resend. Removing the component must remove its timer. React 19.

```jsx
function Buy({theme, send}) {
 useEffect(()=>{const id=setInterval(()=>console.log("tick"),1000);return()=>clearInterval(id);},[]);
 return <button onClick={()=>send()}>Buy</button>;
}
```

## state-ownership

Props are caller-owned; sorted view must not mutate them. Two queued increments must add two. Derived sum must immediately reflect current items.

```jsx
function Totals({items}) {
 const [count,setCount]=useState(0);
 const sorted=[...items].sort((a,b)=>a-b);
 const sum=sorted.reduce((a,b)=>a+b,0);
 return <button onClick={()=>{setCount(n=>n+1);setCount(n=>n+1);}}>{sum}:{count}</button>;
}
```

## effect-event-contract

React version supports useEffectEvent with current documented effect-only semantics. room changes reconnect; theme changes only change notification appearance.

```jsx
function Room({room,theme,connect,notify}) {
 const onConnected=useEffectEvent(()=>notify(theme));
 useEffect(()=>{const c=connect(room);c.on("connected",onConnected);return()=>c.close();},[room]);
 return null;
}
```
connect/notify are stable for the component lifetime.
