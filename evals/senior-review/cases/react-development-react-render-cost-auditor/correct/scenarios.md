# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## external-snapshot

useSyncExternalStore requires repeated snapshots to remain identical while the store is unchanged. React Compiler is enabled; store.items is immutable between changes.

```jsx
function List({store}) {
 const items=useSyncExternalStore(store.subscribe,()=>store.items);
 return <span>{items.length}</span>;
}
```

## item-identity

Editable rows retain their draft on reordering. items may reorder; Row owns input state initialized from item.

```jsx
function Table({items}) {return items.map(item=><Row key={item.id} item={item}/>);}
```

## hydration-and-zero

The server has no window/localStorage; initial client markup must match server. Zero results must show no badge.

```jsx
function Badge({count,initialTheme}) {return <div className={initialTheme}>{count>0 ? <b>{count}</b> : null}</div>;}
```
The server serializes initialTheme and the client uses the same value.

## hot-loop-and-layout

10,000 rows match 10,000 IDs. The accepted comparison-work budget is 300,000 key comparisons; DOM widths must be sampled before writes. Scrolling handler never cancels default.

```js
function labels(rows,ids){const byId=new Map(rows.map(row=>[row.id,row]));return ids.map(id=>byId.get(id).label);}
function size(nodes){const widths=nodes.map(node=>node.offsetWidth);nodes.forEach((node,i)=>{node.style.width=(widths[i]+1)+"px";});}
window.addEventListener("wheel",()=>recordScroll(),{passive:true});
```
Every requested ID exists. Supplied trace shows a single initial layout.

## repeated-render-work

Input typing must not repeat an invariant expensive initial calculation. The pure initializer costs 40ms in the supplied trace; React Compiler is disabled for this component.

```jsx
function Search({loadInitial}) {
 const [saved]=useState(()=>loadInitial());
 const [query,setQuery]=useState("");
 return <input value={query} onChange={e=>setQuery(e.target.value)}/>;
}
```
The trace attributes loadInitial only to mounting.
