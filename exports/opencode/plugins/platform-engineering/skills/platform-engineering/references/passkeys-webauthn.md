<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Passkeys and WebAuthn

Passkeys (WebAuthn-based credentials) are the default recommendation for new authentication flows in 2025-2026. They replace passwords + TOTP entirely for supported users and mitigate credential phishing at the protocol level.

## MUST

- **Use passkeys as the primary auth factor for new consumer apps.** Apple, Google, and Microsoft all support passkey sync via their respective platform credential managers. Consumer apps that require only a password + TOTP in 2026 should treat that as technical debt.
- **Verify `userVerification: 'required'`** on both registration and authentication for high-value operations (payments, admin actions). `'preferred'` is acceptable for low-risk sign-in.
- **Store credential metadata server-side, not secrets.** The server stores: `credentialId`, `publicKey`, `signCount`, `transports`, `userHandle` (opaque user identifier). Never the private key -- that lives in the authenticator.
- **Validate the `clientDataJSON.origin` matches your RP ID.** Prevents relay attacks. The `rpId` should be the registrable domain (`example.com`, not `www.example.com`) to allow passkey sharing across subdomains.
- **Use `attestation: 'none'` for consumer apps.** Only enterprise or regulated contexts need `'direct'` or `'enterprise'` attestation (and they add significant complexity for marginal value).
- **Rotate `signCount`** server-side -- if a new assertion has a `signCount` lower than what you have stored, treat it as a cloned authenticator and revoke the credential.

## DO

- Use `@simplewebauthn/server` (Node) or `py_webauthn` (Python) or `webauthn4j` (Java). Do NOT hand-roll WebAuthn parsing -- CBOR decoding and attestation verification are historically error-prone.
- Support multiple passkeys per user (one per device is common). Show the user a list with `friendlyName`, last-used timestamp, and let them revoke.
- Offer passkey enrollment as an upgrade path from password + TOTP. Don't force migration; users add passkeys voluntarily and you retire passwords once adoption is sufficient.
- Allow cross-device authentication via QR code (hybrid transport) for users whose primary device doesn't have the credential.
- Instrument passkey success vs fallback rates; if fallback (password) rate is high, your UX is broken.

## DON'T

- Treat `userVerification: 'discouraged'` as acceptable -- it bypasses biometric / PIN verification and defeats the point of passkeys.
- Accept a passkey registration without calling `verifyRegistrationResponse` (or equivalent) on the server. The client-returned `PublicKeyCredential` is attacker-controllable in a compromised browser.
- Use passwordless SMS or email magic links as "passkeys". Those are still phishable; real passkeys are public-key credentials tied to a specific origin.
- Block browsers that don't support WebAuthn (very few remain in 2026). Fall back to a second-best option, don't reject the user.
- Use the same `userHandle` value as the user's email or username. `userHandle` should be an opaque random identifier so that leaking a credential doesn't leak PII.

## Sample server-side verification (Node)

```typescript
import {
  verifyRegistrationResponse,
  verifyAuthenticationResponse,
} from '@simplewebauthn/server';

// Registration
const verification = await verifyRegistrationResponse({
  response: body,
  expectedChallenge: session.challenge,
  expectedOrigin: 'https://example.com',
  expectedRPID: 'example.com',
  requireUserVerification: true,
});

if (!verification.verified) throw new Error('Registration failed');

await db.credentials.insert({
  userId: session.userId,
  credentialId: verification.registrationInfo!.credentialID,
  publicKey: verification.registrationInfo!.credentialPublicKey,
  signCount: verification.registrationInfo!.counter,
  transports: body.response.transports ?? [],
  createdAt: new Date(),
});

// Authentication
const stored = await db.credentials.findByCredentialId(body.id);
if (!stored) throw new Error('Unknown credential');

const auth = await verifyAuthenticationResponse({
  response: body,
  expectedChallenge: session.challenge,
  expectedOrigin: 'https://example.com',
  expectedRPID: 'example.com',
  authenticator: {
    credentialID: stored.credentialId,
    credentialPublicKey: stored.publicKey,
    counter: stored.signCount,
    transports: stored.transports,
  },
  requireUserVerification: true,
});

if (!auth.verified) throw new Error('Authentication failed');

// Detect cloned authenticator
if (auth.authenticationInfo.newCounter <= stored.signCount && stored.signCount !== 0) {
  await db.credentials.revoke(stored.credentialId);
  throw new Error('Cloned authenticator detected');
}

await db.credentials.updateSignCount(stored.credentialId, auth.authenticationInfo.newCounter);
```

## Platform notes

| Platform | Passkey support | Notes |
|----------|-----------------|-------|
| iOS 16+ | Native (iCloud Keychain) | Syncs across Apple devices with same Apple ID |
| Android 9+ | Native (Google Password Manager, Chrome) | Android 14+ adds improved Credential Manager API |
| macOS 13+ | Native (iCloud Keychain) | Can authenticate Android/Windows sites via QR |
| Windows 10/11 | Native (Windows Hello) | Enterprise: Azure AD passkey policies |
| Chrome | All platforms | Credential Manager API |
| Safari | iOS / macOS only | Keychain-backed |
| Firefox | All platforms | Uses OS credential store |
| Edge | Windows / macOS / mobile | Inherits Chrome behavior |

## References
- [WebAuthn Level 3 (2024)](https://www.w3.org/TR/webauthn-3/)
- [FIDO Alliance Passkey Dev Resources](https://fidoalliance.org/passkeys/)
- [SimpleWebAuthn (Node)](https://simplewebauthn.dev/)
- [py_webauthn (Python)](https://github.com/duo-labs/py_webauthn)
- [webauthn4j (Java)](https://github.com/webauthn4j/webauthn4j)
- [passkeys.dev](https://passkeys.dev/)
