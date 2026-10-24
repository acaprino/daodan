# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## revoked-permission-and-return

Permission can be revoked between launches. Native readFile throws PermissionDenied then; the app must show recovery instead of crash. OAuth return must resume the saved pending transaction.

```python
def resume(native, saved):
    if saved["permission_granted"]:
        return native.readFile(saved["path"])
    return "request permission"
def oauth_return(saved, callback):
    return complete(callback, transaction=None)
```

## native-capability-and-background

Host kills ordinary tasks on suspension; required upload continuation uses registered native scheduling. Biometric API may be unavailable and must fall back to system credentials.

```js
export function begin(host){setTimeout(()=>host.upload(),60000);return host.biometric.unlock();}
```
No native task is scheduled; biometric is undefined on a supported device.
