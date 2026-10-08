# claude skill inventory binding

The generated catalog is not installation evidence. Use the session's available Skill inventory and installed plugin manifests. Resolve an entry from the path supplied when its skill is loaded; commands and agent definitions are not knowledge entries.

For each actual available skill, normalize its exact ID, provider, actual version,
absolute provider root, provider-relative SKILL.md path and origin. Keep the source
of this availability evidence in the caller's run record. Use only explicit resolved
roots; never crawl a home, cache parent or unselected package tree. If a root/version
is unavailable, record an inventory-resolution gap rather than synthesizing a path.
External/project skills use their own SKILL.toml; unannotated matches stay unknown.

This is an adapted inventory procedure using the host context and read tools.
No new enumeration API, runtime enforcement or installed-host probe is claimed.
The stdlib helper consumes the normalized inventory and reads metadata at those
locations. It never scans other skill bodies or executes their workflows.
