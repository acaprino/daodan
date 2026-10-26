# Skill metadata

Place SKILL.toml beside a registered or host/project-discoverable SKILL.md:

```toml
schema = "daodan/skill-metadata/v1"
kind = "knowledge"
operations = ["review", "develop", "test", "document"]
languages = ["kotlin"]
frameworks = []
topics = []
dimensions = ["correctness", "resource-lifecycle"]
```

Kinds: knowledge, method, workflow, unknown. Operations and selector/dimension
labels are open, nonempty single-line strings; the caller derives matching labels
from verified candidate evidence. A knowledge entry needs at least one operation.
Within a selector group values are OR; nonempty groups combine with AND. Empty
groups impose no filter; at least one selector group must match for auto-selection.
Use framework constraints for framework-specific knowledge, and topics for narrow
questions such as async, packaging or authentication. Keep general language
knowledge broad. The metadata contains no prompt, command or role binding.

A new skill needs its own metadata, not a change to senior-review. An external skill
without metadata remains searchable as unknown. Classification is a reviewed owner
change; do not annotate foreign installed files as a side effect of reviewing code.
Qualified exact IDs resolve collisions. Duplicate IDs fail inventory normalization.
Provider metadata version and installed roots are supplied by the host binding;
the same-version generated declaration must match installed sidecar content with
line endings normalized to LF. Per-run metadata and body fingerprints still pin
exact installed bytes; a change after preparation invalidates that input.
