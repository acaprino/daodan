---
name: instagram-grab
description: 'Download all full-resolution photos, videos, carousels and reels from an Instagram profile into an incremental local archive. TRIGGER WHEN: downloading, archiving, mirroring or backing up media from an Instagram profile. DO NOT TRIGGER WHEN: building a custom scraper for another site (use grabber-development).'
argument-hint: '<username> [--out DIR] [--limit N] [--since YYYY-MM-DD] [--no-videos] [--metadata]'
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.
> Arguments: `<username> [--out DIR] [--limit N] [--since YYYY-MM-DD] [--no-videos] [--metadata]`. Wherever `<arguments>` appears below, substitute the text the user typed after the prompt name.

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

<!-- Generated by the Daodan compiler for copilot. Edit the kernel, never this file. -->

# Instagram profile grab

Archive the media of one Instagram profile using the bundled grabber. The script
does the work; this workflow exists to get the arguments right, to handle the two
screens that need a human, and to report honestly on what came back.

## Requirements

<arguments>

## What this actually does

The collection strategy is capture-and-replay, and it matters that it stays that
way. The script drives a real logged-in browser to the profile, keeps one genuine
`PolarisProfilePostsTabContentQuery_connection` request the page issues on its
own, then walks the whole timeline by re-posting that request with only the
cursor changed. No `doc_id`, `fb_dtsg` or `lsd` value is ever reconstructed, so
Meta rotating them breaks nothing.

The background and every field name are in
`${PLUGIN_ROOT}/skills/grabber-development/references/instagram-media.md`.
Read it before changing the script, and especially before "simplifying" the collector
into a passive network listener: the newest 24 posts never appear in that query,
so a listener silently returns a truncated archive.

## Step 1: Settle the target and the destination

Resolve the username from the request, stripping any `@` or profile URL wrapper.

Pick a destination that will not be published by accident. A media dump belongs
outside anything a static host serves and outside anything git tracks. If the
repository has an established place for untracked source assets, use it and say
so; otherwise default to `ig-<username>` in the working directory and tell the
user where it landed.

State the plan in one line before running anything: profile, destination, and
whether videos are included.

## Step 2: Check the session

The grabber keeps a browser storage state at `~/.instagram-grabber/session.json`.
If it exists, the run is unattended. If it does not, the run needs a person at
the keyboard, so say that before starting rather than leaving a browser window
waiting in silence.

Anonymous access is not an option and is not worth attempting. Both
`web_profile_info` endpoints answer `401 require_login`, and a logged-out browser
is redirected to the login page before a single post reaches the DOM.

Credentials, when the user supplies them, go in the `IG_USER` and `IG_PASS`
environment variables of that one command. Never write them to a file, a script,
a manifest or a commit, and never type a password inline on a command line: a
shell records command lines to a history file on disk. Read it into the variable
instead. Say plainly that a password pasted into a conversation stays in that
conversation's log.

The stored session is itself a live credential. Until it is revoked it grants the
account without a password and without a second factor, so keep it outside the
repository and outside backups, never point `--session` at a path inside a
working tree, and revoke it from Instagram's active-sessions page once a grab
campaign is over.

## Step 3: Dry run first

```
python "${PLUGIN_ROOT}/skills/grabber-development/scripts/instagram_grab.py" \
  <username> --out <dir> --dry-run
```

The dry run collects the whole timeline and prints the counts plus the first 20
planned files, without spending bandwidth. Check three things in its output before continuing:

1. The post count looks like the profile, not a fraction of it.
2. The newest listed file matches the profile's most recent post. If the top of
   the list is years old, the collector fell back to passive sniffing and the
   archive would be truncated.
3. Photos and videos are both present when both were asked for.

## Step 4: Two screens may need a human

Both appear in the browser window the script opens, and both are one-time:

- **The Meta cookie dialog** renders over the login form and swallows clicks
  underneath it. The script dismisses it, but a new variant may need a manual
  click.
- **The EU pay-or-consent flow**, `/consent/?flow=ad_free_subscription`, blocks
  every navigation until answered. This is a decision about advertising and
  payment on the user's own account, so never answer it on their behalf. The
  script parks and waits; tell the user to answer it in the window. Once
  answered, it is stored in the session and does not return.

If the run reports it could not reach the profile grid, one of these two is
almost always the reason.

## Step 5: Run it

Drop `--dry-run` and add the flags the request implies:

| Flag | Use |
|---|---|
| `--limit N` | the newest N posts only |
| `--since YYYY-MM-DD` | keep only posts newer than this date, though the whole timeline is still walked |
| `--no-videos` / `--no-photos` | narrow the media kinds |
| `--covers` | also keep each video's cover frame |
| `--metadata` | record captions, permalinks and alt text in the manifest |
| `--concurrency N` | parallel downloads, default 5 |

The run is resumable and idempotent. Files that already exist are skipped, so a
second run picks up only new posts, and an interrupted run continues where it
stopped. Downloads land through a `.part` file and are renamed only once
complete, so a killed run leaves no truncated media behind.

## Step 6: Report

Give the user the counts the script printed: downloaded, already present,
failed, total size, destination. If any file failed, name it and say why rather
than rounding the number down to a success.

Two things are worth flagging without being asked:

- The manifest at `_manifest.json` records what was actually fetched: post codes,
  dates, media types, and with `--metadata` the captions and permalinks.
  Incrementality comes from the files already on disk, not from the manifest, but
  the metadata it carries exists nowhere else, so do not delete it to "clean up".
- CDN signatures expire. A plan produced by a dry run hours earlier should be
  regenerated rather than reused.
