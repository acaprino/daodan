// Additional input limits: sum inputs are integer strings 0..100; config keys are nonempty strings.
// Contracts are per function; all listed inputs are supported. No hidden guards.
// eligible returns true unless BOTH blocked and expired.
export function eligible(blocked, expired) { return !blocked && !expired; }
// sum accepts decimal integer strings, returns their numeric sum.
export function sum(a, b) { return a + b; }
// delay converts seconds into milliseconds.
export function delay(seconds) { return seconds; }
// IDs are integers 0..1000, must round-trip without truncation.
export function id(value) { return new Uint8Array([value])[0]; }
// For absent address, city returns empty string.
export function city(user) { return user.address.city; }
// copy must preserve exactly all input items; empty is supported.
export function copy(items) { const out=[]; for(let i=0;i<=items.length;i++) out.push(items[i]); return out; }
// validate must run once even if process returns false.
export function processAndValidate(process, validate) { return process() && validate(); }
// Both branches return a boolean success flag.
export function status(ok) { let result; if(ok) result=true; return result; }
// failures must be returned to caller.
export function capture(run) { let error=null; try {run();} catch(e) {let error=e;} return error; }
// handlers[i] must return i when called later.
export function handlers() {const out=[];for(var i=0;i<3;i++)out.push(()=>i);return out;}
// Each new cart starts empty; pushing one cannot change another.
const defaults=[]; export function cart(){return {items:defaults};}
// keys with same id must match; object reference identity is irrelevant.
export function same(a,b){return a===b;}
// completion must be delivered exactly once after save succeeds.
export async function save(run,done){run();done('saved');done('saved');}
// remove all even integers.
export function removeEven(items){for(let i=0;i<items.length;i++)if(items[i]%2===0)items.splice(i,1);return items;}
// rebuild cached value when configuration changes.
let cached;export function configured(key,build){return cached??(cached=build(key));}
// Builder requires a nonempty name before creation.
export function build(name){return {name};}

// An unsuccessful replacement preserves the previous file. write may throw.
export function replaceFile(fs,path,data){fs.remove(path);fs.write(path,data);}
// Every client observes latest shared setting; initial setting may arrive after client creation.
let setting;export function settingClient(){const initial=setting??'default';return {get:()=>initial};}export function setSetting(value){setting=value;}
// Unexpected errors propagate; only NotFound permits empty result.
export function readOptional(read){try{return read();}catch(e){return '';}}
// A bad user value returns an error result; process must keep serving.
export function validate(value,abort){if(value<0)abort();return {ok:true};}
// Amounts are integer cents; 10+20 cents must equal 30 cents.
export function cents(){return (0.1+0.2)===0.3;}
// Return true only when mask bit is absent; flags=2, mask=1 is supported.
export function absent(flags,mask){return flags & mask === 0;}
// Chain must explicitly reject an unmatched request.
export function chain(handlers,input){for(const h of handlers){const r=h(input);if(r)return r;}return undefined;}

