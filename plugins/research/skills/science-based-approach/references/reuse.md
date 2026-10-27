# Reuse before creation

Run this check after Science Mode permits an automatic operation, or when the
user explicitly requests research. It applies before new research files are
created and when a conversation returns to a known topic.

1. Resolve any research already cited in this conversation. Inspect the global
   index and relevant owner dossiers. Enumerate/search existing Markdown under
   `docs/research/` and the project's plugin/domain research directories,
   including unindexed legacy files. The runtime's registered list is not an
   inventory of all existing research. Group revisions/checks by their parent
   identity; templates and indexes are not separate studies.
2. Search semantic neighbours: question, concept synonyms, constraints,
   technology and supported decision. Read the plausible current documents;
   filename equality is insufficient. Record searched locations, candidates
   and the reuse decision briefly in the caller's run.
3. If one document already owns the question, use it. A conversational follow-up,
   new source, updated technology or narrower detail normally extends that same
   document and identity. Reuse without new evidence creates no Markdown or
   check receipt and does not claim a new online verification.
4. When new evidence changes the answer, update that current file in place.
   Preserve creation metadata, change research/update timestamps honestly,
   strike through the specific superseded statements visibly (`~~old claim~~`),
   and explain replacement evidence, date and reason beside them. Keep the
   current synthesis coherent and append a descriptive changelog. Preserve
   immutable historical snapshots separately; do not create another current
   document named after the date, conversation or run.
5. Create a new current document only for a genuinely distinct question/owner
   that cannot sensibly extend existing research. State that distinction.
   If multiple documents overlap and ownership or merge disposition is unclear,
   ask which should remain canonical before creating, merging, moving or
   deleting them. Do not silently fork a duplicate to avoid that question.

Legacy Markdown retains its exact path. On its first substantive update the
runtime binds that file as current and preserves its original bytes in history;
it does not produce a parallel current README. Follow the project owner's
write/synchronization rules and explicit grants. A forbidden documentation root
never becomes writable merely because a related document was found there.

The agent judges relevance; a mechanical identity/path collision check cannot
prove that two differently named documents cover different concepts.
