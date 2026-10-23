<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# Instagram profile media: the observed surface

Everything here was captured from a live session on 2026-09-10, not inferred.
Where a value is known to rotate, the text says so and names what the tooling
reads instead of hardcoding it.

## Anonymous access is closed

Three probes, three refusals:

| Probe | Result |
|---|---|
| `GET /api/v1/users/web_profile_info/?username=<u>` on `www.instagram.com` | `401` `{"require_login": true, "igweb_rollout": true}` |
| the same path on `i.instagram.com` | identical `401` |
| `GET /<username>/?__a=1&__d=dis` | `201` with an empty body |

A logged-out browser loading a profile renders `PolarisLoggedOutDesktopWWWProfile`
for a moment and then navigates to
`/accounts/login/?source=desktop_dynamic_landing_dialog`. No post link ever
reaches the DOM, and the only `api/graphql` bodies are 125 to 231 byte telemetry
payloads. Adding an `x-ig-app-id` header does not change any of this.

Conclusion: a profile grab needs a session. Plan for the login, do not plan
around it.

## The login form changed

`input[name="username"]` and `input[name="password"]` no longer exist. The form
carries:

| Control | Selector |
|---|---|
| account | `input[name="email"]` with `autocomplete="username webauthn"` |
| password | `input[name="pass"]` |
| submit | a `div` with `role=button` labelled `Accedi` or `Log in`, not a `button[type=submit]` |

The Meta cookie dialog renders on top of the form and its container swallows
every click underneath, so Playwright reports `subtree intercepts pointer
events` on the submit control until the dialog is answered. Dismiss it first
(`Consenti tutti i cookie`, `Allow all cookies`, or either refusal variant),
then fill the form.

## The EU pay-or-consent wall

Inside the EU a freshly logged-in account is redirected to

```
/consent/?flow=ad_free_subscription&source=ad_free_subscription_blocking_flow
```

and every navigation lands on the home feed until that flow is answered. The
symptom is misleading: a `goto` to the profile appears to succeed, but the
captured queries are `PolarisFeedRootPaginationCachedQuery`, the home feed,
rather than the profile grid.

This is a decision about advertising and payment on someone's account, so
automation should park on it and let a human answer, then persist the resulting
storage state so it is answered once rather than every run.

## The profile grid query

```
POST https://www.instagram.com/graphql/query
content-type: application/x-www-form-urlencoded
fb_api_req_friendly_name = PolarisProfilePostsTabContentQuery_connection
doc_id = 39535953862670189            (observed 2026-09-10, rotates)
```

The body also carries `fb_dtsg`, `lsd`, `jazoest`, `__csr`, `__hs`, `__rev` and
a dozen more session-scoped values. **Do not reconstruct them.** Capture one
genuine request the page issues on its own, keep it as a template, and re-post
it with only `variables.after` swapped. That keeps the `doc_id` rotation and the
token scheme out of the tooling entirely.

`variables` of interest:

```json
{"after": "<cursor>", "before": null, "first": 12, "last": null,
 "username": "<profile>", "include_multi_captions": true,
 "data": {"count": 12, "include_relationship_info": true}}
```

The cursor is `<media_pk>_<user_id>`, for example
`3374869699831538610_3041758876`. Passing `after: null` returns page one.

Response shape:

```
data.xdt_api__v1__feed__user_timeline_graphql_connection
  edges[].node        96 fields
  page_info           {end_cursor, has_next_page, has_previous_page, start_cursor}
```

## The newest 24 posts are not in that query

This is the trap worth remembering. Instagram delivers the first 24 posts inside
the initial page payload, and the first `_connection` request the client issues
**already carries a deep cursor**. A collector that only listens to network
traffic therefore captures the timeline from post 25 onward and silently misses
the most recent ones. Observed directly: with 24 post links already in the DOM,
the first sniffed page returned posts dated 2024-05-20 to 2024-02-19 on a
profile whose newest post was 2026-07-02.

The fix is to stop listening passively. Use the captured template to walk the
timeline from `after: null`, which asks the same genuine endpoint for page one.

## Node fields that matter

| Field | Meaning |
|---|---|
| `code` | shortcode, the `/p/<code>/` permalink and a stable file key |
| `pk`, `id` | numeric media ids, `pk` is the cursor's left half |
| `taken_at` | unix seconds |
| `media_type` | `1` image, `2` video, `8` carousel |
| `product_type` | `feed`, `clips` (a reel), `carousel_container` |
| `image_versions2.candidates` | several sizes of the same still, ordering not guaranteed |
| `video_versions` | several entries, often one resolution under type ids `101`, `102`, `103` |
| `carousel_media` | child nodes, each with its own `image_versions2` and `video_versions` |
| `caption.text`, `accessibility_caption` | copy, useful for alt text |
| `original_width`, `original_height` | the uploaded dimensions |

Select the largest candidate by `width * height` rather than trusting index `0`,
and treat a child with a non-empty `video_versions` as a video whatever its
declared `media_type` says.

Real distribution on a 180 post profile: 160 images, 12 reels, 8 carousels,
expanding to 193 files. Largest candidate observed was 3072x4096, so the grab is
full resolution and not a thumbnail scrape.

## Downloading

Media sit on `instagram.<edge>.fna.fbcdn.net` behind a signed URL that needs no
cookie and no auth header. A browser `User-Agent` plus
`Referer: https://www.instagram.com/` is enough, and the signature expires, so
download soon after collecting. `curl_cffi` with `impersonate="chrome"` is the
comfortable path; plain `urllib` also works.

## The script

`${CLAUDE_PLUGIN_ROOT}/skills/grabber-development/scripts/instagram_grab.py`
implements all of the above: session reuse, the login and consent parking, the
capture-and-replay pagination, largest-candidate selection, carousel expansion,
concurrent resumable downloads and a manifest. Run it with `--dry-run` first to
see the plan without spending bandwidth.
