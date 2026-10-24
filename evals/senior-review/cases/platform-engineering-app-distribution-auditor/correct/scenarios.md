# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## artifact-target-and-inclusion

Ship Windows arm64 and include helper.exe under resources/bin. The loader uses that exact path.

Package manifest and supplied artifact inventory contain arm64 and resources/bin/helper.exe; the manifest binds their hashes to the candidate. No installation was performed.

## verified-update-channel

Stable distribution may install only signed stable artifacts; updater.verify is the host-provided required verification hook.

```js
export async function update(updater){const asset=await updater.download("stable");if(!await updater.verify(asset))throw new Error("invalid update");return updater.install(asset);}
```
