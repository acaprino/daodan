// Additional input limits: sum inputs are integer strings 0..100; config keys are nonempty strings.
// Contracts are per function; all listed inputs are supported. No hidden guards.
// eligible returns true unless BOTH blocked and expired.
// sum accepts decimal integer strings, returns their numeric sum.
// delay converts seconds into milliseconds.
// IDs are integers 0..1000, must round-trip without truncation.
// For absent address, city returns empty string.
// copy must preserve exactly all input items; empty is supported.
// validate must run once even if process returns false.
// Both branches return a boolean success flag.
// failures must be returned to caller.
// handlers[i] must return i when called later.
// Each new cart starts empty; pushing one cannot change another.
// keys with same id must match; object reference identity is irrelevant.
// completion must be delivered exactly once after save succeeds.
// remove all even integers.
// rebuild cached value when configuration changes.
// Builder requires a nonempty name before creation.
// Contracts match the defective target; explicit guards are complete.
export function eligible(blocked, expired) { return !(blocked && expired); }
export function sum(a, b) { return Number(a) + Number(b); }
export function delay(seconds) { return seconds * 1000; }
export function id(value) { return value; }
export function city(user) { return user.address?.city ?? ''; }
export function copy(items) { return [...items]; }
export function processAndValidate(process, validate) { const ok=process(); const valid=validate(); return ok && valid; }
export function status(ok) { return Boolean(ok); }
export function capture(run) { let error=null; try {run();} catch(e) {error=e;} return error; }
export function handlers() {const out=[];for(let i=0;i<3;i++)out.push(()=>i);return out;}
export function cart(){return {items:[]};}
export function same(a,b){return a.id===b.id;}
export async function save(run,done){await run();done('saved');}
export function removeEven(items){return items.filter(x=>x%2!==0);}
let cacheKey, cached;export function configured(key,build){if(key!==cacheKey){cached=build(key);cacheKey=key;}return cached;}
export function build(name){if(!name)throw new Error('name required');return {name};}

// Unsuccessful replacement preserves prior file; atomicReplace preserves old bytes on throw.
export function replaceFile(fs,path,data){fs.atomicReplace(path,data);}
// Every client observes latest shared setting, including one arriving after construction.
let setting;export function settingClient(){return {get:()=>setting??'default'};}export function setSetting(value){setting=value;}
// Only NotFound permits empty result; unexpected errors propagate.
export function readOptional(read){try{return read();}catch(e){if(e.name==='NotFound')return '';throw e;}}
// Bad user values return error without terminating the service.
export function validate(value,abort){if(value<0)return {ok:false};return {ok:true};}
// Integer cents preserve the declared unit.
export function cents(){return (10+20)===30;}
// Mask absent predicate for every supported bit pattern.
export function absent(flags,mask){return (flags & mask) === 0;}
// Unmatched requests receive explicit rejection.
export function chain(handlers,input){for(const h of handlers){const r=h(input);if(r)return r;}return {error:'unsupported'};}

