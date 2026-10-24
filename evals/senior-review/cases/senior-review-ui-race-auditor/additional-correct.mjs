// Initial dialog: token=0, visible=true; callers invoke open on that current dialog.
// Contract: after user closes dialog, delayed open must not steal focus; node references can be replaced.
// Width changes between registration and callback; measured layout must use current width.
// New images can change height after initial commit; sticky bottom must update on content-size changes unless user scrolls away.
// Two mounted components must display the same online state after either updates it.
// IPC may arrive after destroy; required contract prohibits access to a destroyed view.
// Same contracts; ready may finish after close. Node instance owns the generation.
export async function open(dialog, ready){const token=++dialog.token;await ready;if(dialog.visible&&token===dialog.token)dialog.focus();}
export function close(dialog){dialog.visible=false;dialog.token++;}
// Width read at callback execution.
export function resize(node,subscribe,render){subscribe(()=>render(node.width));}
// userAtBottom records intentional user scroll separately from programmatic layout.
export function sticky(view,onSize){const update=()=>{if(view.userAtBottom)view.scrollTop=view.height;};update();onSize(update);}
// Shared owner and explicit subscriptions drive all mounted displays.
let online=false;const listeners=new Set();export function connection(){return {read:()=>online,subscribe:fn=>listeners.add(fn),set:value=>{online=value;for(const fn of listeners)fn(value);}};}
// Late callbacks are allowed but ignored after lifetime ends.
export function bind(view,ipc){let alive=true;ipc.subscribe(value=>{if(alive)view.render(value);});return ()=>{alive=false;view.destroy();};}

