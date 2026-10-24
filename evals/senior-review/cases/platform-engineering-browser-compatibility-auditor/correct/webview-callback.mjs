/* Supported product target: WebViewBridge 4 on the supplied mobile engine.
   Effective native contract: registerCallback(name, fn) registers a case-sensitive
   named callback and returns its unsubscribe function. externalAuth(requestId)
   eventually emits exactly one {requestId, status:'ok'|'cancel'} to 'oauthResult'.
   No DOM event or other callback is emitted. Native callback delivery is queued
   after externalAuth returns; this view stays mounted until delivery and calls
   the returned unsubscribe on teardown. complete(result) is the sole transition
   out of waiting and handles either status. Native results are already verified
   by the host; only the current request may complete this view. This source is
   a supplied synthetic binding, not an observed browser/native execution. */

export function mount(host, requestId, complete) {
  const unsubscribe = host.registerCallback('oauthResult', result => {
    if (result.requestId === requestId) complete(result);
  });
  host.externalAuth(requestId);
  return unsubscribe;
}
