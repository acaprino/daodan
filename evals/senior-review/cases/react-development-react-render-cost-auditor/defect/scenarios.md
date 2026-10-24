# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## external-snapshot

useSyncExternalStore requires repeated snapshots to remain identical while the store is unchanged. React Compiler is enabled; store.items is immutable between changes.

```jsx
function List({store}) {
 const snapshot=useSyncExternalStore(store.subscribe,()=>({items:store.items}));
 return <span>{snapshot.items.length}</span>;
}
```

## item-identity

Editable rows retain their draft on reordering. items may reorder; Row owns input state initialized from item.

```jsx
function Table({items}) {return items.map((item,index)=><Row key={index} item={item}/>);}
```

## hydration-and-zero

The server has no window/localStorage; initial client markup must match server. Zero results must show no badge.

```jsx
function Badge({count}) {const theme=localStorage.getItem("theme");return <div className={theme}>{count && <b>{count}</b>}</div>;}
```

## hot-loop-and-layout

10,000 rows match 10,000 IDs. The accepted comparison-work budget is 300,000 key comparisons; DOM widths must be sampled before writes. Scrolling handler never cancels default.

```js
function labels(rows,ids){return ids.map(id=>rows.find(row=>row.id===id).label);}
function size(nodes){for(const node of nodes){node.style.width=(node.offsetWidth+1)+"px";}}
window.addEventListener("wheel",()=>recordScroll(),{passive:false});
```
A supplied trace shows one forced layout per node and scroll waiting for recordScroll (30ms).

## repeated-render-work

Input typing must not repeat an invariant expensive initial calculation. The pure initializer costs 40ms in the supplied trace; React Compiler is disabled for this component.

```jsx
function Search({loadInitial,items}) {
 const [saved]=useState(loadInitial());
 const [query,setQuery]=useState("");
 return <input value={query} onChange={e=>setQuery(e.target.value)}/>;
}
```
The trace attributes 40ms on every keystroke to loadInitial; items/saved are unused in this reduced view.
