// Initial dialog: token=0, visible=true; callers invoke open on that current dialog.
// Contract: after user closes dialog, delayed open must not steal focus; node references can be replaced.
export async function open(dialog, ready) { await ready; dialog.focus(); }
export function close(dialog){dialog.visible=false;}
// Width changes between registration and callback; measured layout must use current width.
export function resize(node, subscribe, render){const width=node.width;subscribe(()=>render(width));}
// New images can change height after initial commit; sticky bottom must update on content-size changes unless user scrolls away.
export function sticky(view, onSize){view.scrollTop=view.height;}
// Two mounted components must display the same online state after either updates it.
export function connection(){let online=false;return {read:()=>online,set:value=>{online=value;}};}
// IPC may arrive after destroy; required contract prohibits access to a destroyed view.
export function bind(view,ipc){ipc.subscribe(value=>view.render(value));return ()=>view.destroy();}

