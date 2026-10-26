<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

# Authentication Token Storage and OAuth Flows

Token storage is where most authentication implementations fail. The correct approach differs significantly by platform.

## MUST

- **Never store JWTs in localStorage or sessionStorage on web platforms (SPA/PWA).** Any XSS vulnerability enables `localStorage.getItem('token')` to exfiltrate every user's session. Store access tokens in JavaScript memory (variables, React context, closures) and refresh tokens in httpOnly + Secure + SameSite=Strict cookies.
  - Privasec red team: a stored XSS vulnerability on a site using localStorage JWTs allowed the attacker to steal every visiting user's token and hijack their sessions. HttpOnly cookies would have blocked JavaScript access entirely.

- **Use short-lived access tokens (5-15 minutes) with rotating refresh tokens.** Issue a new refresh token with each access-token renewal and invalidate the old one. Limits blast radius of token theft.

- **Use the correct OAuth 2.0 flow per platform:**

| Platform | OAuth Flow |
|----------|-----------|
| **SPA/PWA** | Authorization Code + PKCE (implicit flow deprecated by OAuth 2.1) |
| **Mobile** | System browser + PKCE -- never use embedded WebViews for OAuth login (credential interception risk). Use ASWebAuthenticationSession (iOS), Custom Tabs (Android) |
| **Desktop** | Standard PKCE |

- **Store tokens in platform-native secure storage on mobile and desktop:**

| Platform | Secure Storage |
|----------|---------------|
| **iOS** | Keychain with `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` |
| **Android** | Keystore with EncryptedSharedPreferences |
| **macOS** | Keychain |
| **Windows** | Credential Manager |
| **Linux** | libsecret |

- Never use SharedPreferences, NSUserDefaults, or plain-text files.

## DO

- Use RS256 (asymmetric) for JWTs verified by multiple services; HS256 only when a single service both signs and verifies.
- Add MFA for sensitive operations.
- Implement token revocation and blacklisting server-side.

## DON'T

- Use the JWT `none` algorithm -- always validate the `alg` header server-side.
- Embed sensitive user data in JWT payloads (they're base64-encoded, not encrypted).
- Store credentials in Android SharedPreferences or iOS NSUserDefaults without hardware-backed encryption.

## Official docs

- OAuth 2.1 (consolidating BCPs): https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1
- OAuth 2.0 for Native Apps (RFC 8252) -- system browser + PKCE: https://www.rfc-editor.org/rfc/rfc8252
- PKCE (RFC 7636): https://www.rfc-editor.org/rfc/rfc7636
- OWASP JWT Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- iOS Keychain: https://developer.apple.com/documentation/security/keychain_services
- Android EncryptedSharedPreferences: https://developer.android.com/reference/androidx/security/crypto/EncryptedSharedPreferences
- Android Custom Tabs: https://developer.chrome.com/docs/android/custom-tabs
- iOS ASWebAuthenticationSession: https://developer.apple.com/documentation/authenticationservices/aswebauthenticationsession
- Windows Credential Manager: https://learn.microsoft.com/en-us/windows/win32/api/wincred/
- libsecret (Linux): https://wiki.gnome.org/Projects/Libsecret
