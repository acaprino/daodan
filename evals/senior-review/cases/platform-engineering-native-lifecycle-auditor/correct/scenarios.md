# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## revoked-permission-and-return

Permission can be revoked between launches. Native readFile throws PermissionDenied then; the app must show recovery instead of crash. OAuth return must resume the saved pending transaction.

```python
def resume(native, saved):
    try: return native.readFile(saved["path"])
    except PermissionDenied: return "request permission"
def oauth_return(saved, callback):
    return complete(callback, transaction=saved["pending_transaction"])
```
complete validates callback binding to the supplied saved transaction.

## native-capability-and-background

Host kills ordinary tasks on suspension; required upload continuation uses registered native scheduling. Biometric API may be unavailable and must fall back to system credentials.

```js
export function begin(host){host.scheduleNativeUpload();return host.biometric ? host.biometric.unlock() : host.systemCredential();}
```
Both fallback operations are registered by the supplied native manifest.
