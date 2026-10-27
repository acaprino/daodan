# Neutral project specifications

## Intent and authorization

The user requested project-owned specifications in `docs/specs/`, with no plugin
brand in their path, and authorized implementing the proposed Daodan flow:
brainstorming, specification, approval, then planning from that document.
This changes the existing delivery owner; no parallel planning plugin is added.

## Contract

1. Design requests route to Daodan brainstorming without requiring an explicit
   command. Once an approach is settled, the coordinator drafts the specification
   automatically. It distinguishes user decisions, assumptions and open questions.
2. New specifications default to `docs/specs/YYYY-MM-DD-<slug>-design.md`.
   Explicit destinations override that default. Existing specifications remain
   inputs at their present paths; migration is a separate authorized action.
3. Specification review and approval apply with or without ADRs. The run links
   the exact path, SHA-256 and approval question. A request to build before the
   document exists cannot approve unseen text. Existing valid approval is reused.
4. Planning, workers, continuation and final review consume the same binding.
   Changed bytes invalidate approval and dependent plans. Worktree handoffs carry
   identical approved bytes without overwriting unrelated work.
5. ADRs retain separate technical decisions; FRDs retain evidence-bound
   requirements. Neither becomes a duplicate project specification.

## Boundaries and acceptance

- Existing code is read before questions; answered questions are not repeated.
- Source-less projects can design before scaffolding; documents and run records
  do not make a project an initialized application. First-use choices survive
  the later creation of the repository and source.
- Specification approval is distinct from implementation, commit and publication
  authorization. Keeping a design starts no implementation.
- The brainstorming entry declares all workers used by specification review and
  its authorized continuation into the delivery method on all five hosts.
- Historical documents remain in place. Existing repair/refactor and legacy runs
  preserve their applicable contracts instead of retroactively inventing specs.

## Verification and limits

Render the five host packages and verify entry, shared reference, dispatch,
approval, handoff, continuation and durable-routing contracts. Run compiler,
registration, dependency, bundled-path and vocabulary checks; account for the
new reference in context budgets without raising existing caps. Preserve unrelated
preexisting changes and baseline failures. Static contract tests establish shipped
instructions, not proof of autonomous selection or execution on installed hosts.
