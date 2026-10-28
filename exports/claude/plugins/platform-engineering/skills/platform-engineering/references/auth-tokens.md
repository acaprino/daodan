<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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
