<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# Secrets Management

## MUST

- **Never store API keys, database credentials, private keys, or any secret in frontend code, client-side bundles, or mobile app binaries.** They will be extracted.
  - GitHub detected over 39 million leaked secrets across its platform in 2024.
  - GitGuardian found 12.8 million secrets in public repositories in 2023 alone, a 28% year-over-year increase.
  - A Wiz study found 65% of Forbes AI 50 companies had leaked verified secrets on GitHub, including Hugging Face tokens that could have exposed approximately 1,000 private AI models.

- **Never commit secrets to version control.** Use `.gitignore` for `.env` files and implement pre-commit hooks with tools like detect-secrets, GitLeaks, or TruffleHog. Enable GitHub's push protection and secret scanning.

- **Use environment variables or dedicated secret management services** (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, GCP Secret Manager) for server-side secrets. For third-party API calls requiring keys, proxy through your backend -- never call external APIs with secrets directly from the client.

## DON'T

- Store secrets in `.env` files that get bundled into client builds. Variables prefixed with `REACT_APP_`, `VITE_`, or `NEXT_PUBLIC_` are embedded in the production JavaScript bundle and are visible to anyone who opens DevTools.
- Hardcode secrets in mobile binaries -- reverse-engineering tools extract them in minutes.
- Store secrets in Electron ASAR archives, which are extractable with `asar extract app.asar`.

## Official docs

- OWASP Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- AWS Secrets Manager: https://aws.amazon.com/secrets-manager/
- HashiCorp Vault: https://www.vaultproject.io/
- Azure Key Vault: https://azure.microsoft.com/en-us/products/key-vault
- GCP Secret Manager: https://cloud.google.com/security/products/secret-manager
- GitHub secret scanning + push protection: https://docs.github.com/en/code-security/secret-scanning
- detect-secrets: https://github.com/Yelp/detect-secrets
- GitLeaks: https://github.com/gitleaks/gitleaks
- TruffleHog: https://github.com/trufflesecurity/trufflehog
