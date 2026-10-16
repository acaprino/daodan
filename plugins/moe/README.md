# moe: Ultra Nerd

Explicit multi-model problem solving for difficult tasks. Two configured models
propose independently, challenge one another, and return evidence for a coordinator
who verifies and delivers a single answer. Exposes its own MCP server with moe_models and moe_ask;
it does not duplicate credentials or certify its separate peer-review protocol.

Entry: `moe:ultra-nerd`. Defaults to two rounds and at most six transport invocations,
with per-request output and payload limits. Configure MOE_API_BASE and MOE_API_KEY
for an OpenAI-compatible endpoint. Tri-Tech integration must bind MOE_BRIDGE_URL and MOE_BRIDGE_TOKEN
to its native context broker, with no direct HTTP fallback. Payloads live under
MOE_RUN_ROOT inside the active project (default .moe). A third round is explicit. Warns about
increased token consumption before paid calls. Total billing limits and immediate
cancellation require runtime support.

This plugin supplies a portable method, not the Ultra Nerd chat button. Tri-Tech
must separately bind gateway profiles, approved output paths, accounting and UI.
No live model exchange is implied by compilation or registration.


The 24000-byte reciprocal payload reserves 6000 UTF-8 bytes for the brief, 8000
for each exact reply and 2000 for framing. Oversized briefs stop before spending.
The second proposal passes peer_model from the first returned model. Critiques
require phase="critique", expected_model and peer_model pinned to the initial
actual identities; collisions, missing identities or model changes stop the run.
Payloads are read using pinned nonlink directory/file handles, not a checked path
that is reopened without protection.
