# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## dependency-cycle

Each component instance loads once on mount. load always resolves and each object result is distinct.

```jsx
function Panel({load}) {
  const [data, setData] = useState({});
  const refresh = useCallback(async () => setData(await load()), [data, load]);
  useEffect(() => { refresh(); }, [refresh]);
  return null;
}
```

## lifetime-and-action

Each click sends exactly one order; changing theme must not resend. Removing the component must remove its timer. React 19.

```jsx
function Buy({theme, send}) {
 const [submitted,setSubmitted]=useState(false);
 useEffect(()=>{if(submitted) send();},[submitted,theme,send]);
 useEffect(()=>{setInterval(()=>console.log("tick"),1000);},[]);
 return <button onClick={()=>setSubmitted(true)}>Buy</button>;
}
```

## state-ownership

Props are caller-owned; sorted view must not mutate them. Two queued increments must add two. Derived sum must immediately reflect current items.

```jsx
function Totals({items}) {
 const [count,setCount]=useState(0);
 const [sum,setSum]=useState(0);
 useEffect(()=>setSum(items.reduce((a,b)=>a+b,0)),[]);
 items.sort((a,b)=>a-b);
 return <button onClick={()=>{setCount(count+1);setCount(count+1);}}>{sum}:{count}</button>;
}
```

## effect-event-contract

React version supports useEffectEvent with current documented effect-only semantics. room changes reconnect; theme changes only change notification appearance.

```jsx
function Room({room,theme,connect,notify}) {
 const onConnected=useEffectEvent(()=>notify(theme));
 useEffect(()=>{const c=connect(room);c.on("connected",onConnected);return()=>c.close();},[room,onConnected]);
 return null;
}
```
connect/notify are stable for the component lifetime.
