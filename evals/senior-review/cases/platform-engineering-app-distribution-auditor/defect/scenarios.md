# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## artifact-target-and-inclusion

Ship Windows arm64 and include helper.exe under resources/bin. The loader uses that exact path.

Package manifest declares only x64; artifact inventory contains resources/helper.exe. The Windows arm64 target and resources/bin/helper.exe are absent.

## verified-update-channel

Stable distribution may install only signed stable artifacts; updater.verify is the host-provided required verification hook.

```js
export async function update(updater){const asset=await updater.download("nightly");return updater.install(asset);}
```
