<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
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

# Mobile Authentication

Deep-link OAuth callback plumbing, hosted callback HTML, Apple Sign-In, and the full React AuthContext with deep-link listener cleanup. The OAuth/PKCE security architecture lives in `authentication.md` -- this file is the mobile-specific wiring.

## When to use

Wiring OAuth sign-in for an Android/iOS Tauri 2 app: deep-link config, hosted callback page, Apple Sign-In flow, AuthContext shape. For desktop/general OAuth security patterns, see `authentication.md`.

## Deep-link config (the parts that matter)

```json
// tauri.conf.json
"plugins": {
  "deep-link": {
    "mobile": [{ "scheme": ["myapp"], "appLink": false }]
  }
}
```

```json
// capabilities/default.json
"permissions": ["deep-link:default", "opener:default", "store:default"]
```

## Gotchas

- **`shell:open` does NOT work for URLs on Android.** It throws `Scoped shell IO error: No such file or directory (os error 2)`. **Use the `opener` plugin** (v2.3.0+) -- it opens Chrome Custom Tabs on Android and Safari on iOS.
- **The system browser cannot directly redirect to `myapp://...`** in the OAuth flow. You need a hosted callback page (Firebase Hosting or similar) that receives the OAuth fragment, parses tokens, and bounces via `window.location.href = "myapp://..."`. Pattern below.
- **Apple Sign-In returns user info ONLY on first sign-in.** The `user` parameter (containing name + email) is NOT returned on subsequent sign-ins. Persist it on first auth -- you cannot fetch it later.
- **Apple `nonce` MUST be passed as `rawNonce` to Firebase**, not the SHA-256-hashed version. Firebase's `OAuthProvider('apple.com').credential({ idToken, rawNonce: nonce })` expects the original random nonce. Hashing breaks signature verification.
- **Deep-link listener cleanup is async.** `onOpenUrl()` returns `Promise<UnlistenFn>` -- store the returned unlisten in state and call it on unmount/unload, otherwise you leak a listener every re-render.
- **`response_type=token id_token` is implicit flow.** For production prefer PKCE (`response_type=code`) -- see `authentication.md`. The hosted callback page has different behavior for each.
- **Callback page CORS**: must be served from the same domain as the OAuth `redirect_uri`. Mismatched origin = silent failure.
- **Cache-Control: no-store on the callback page.** Otherwise mobile browsers may serve a stale page that bounces to a stale state.

## Hosted callback page (the bridge between OAuth and deep link)

Host at `/auth/callback/index.html` (Firebase Hosting or similar). Parses the OAuth fragment, builds the `myapp://` URL, redirects.

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Authenticating...</title>
  <style>
    body { font-family: system-ui, sans-serif; display: flex; flex-direction: column;
           justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }
    .spinner { width: 40px; height: 40px; border: 3px solid #ddd;
               border-top-color: #4285f4; border-radius: 50%; animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    p { color: #666; margin-top: 16px; }
    .error { color: #d32f2f; }
    .fallback a { color: #4285f4; text-decoration: none; }
  </style>
</head>
<body>
  <div class="spinner" id="spinner"></div>
  <p id="status">Redirecting to app...</p>
  <div id="fallback" style="display:none">
    <p>If the app doesn't open automatically:</p>
    <a id="manual-link" href="#">Open App Manually</a>
  </div>
  <script>
    (function() {
      const params = new URLSearchParams(window.location.hash.substring(1));
      const error = params.get('error');
      if (error) {
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('status').textContent =
          params.get('error_description') || 'Authentication failed';
        document.getElementById('status').className = 'error';
        return;
      }

      // Parse continue URI from state
      let continueUri = 'myapp://auth/callback';
      const state = params.get('state');
      if (state) {
        try {
          const stateObj = JSON.parse(decodeURIComponent(state));
          continueUri = stateObj.continueUri || continueUri;
        } catch {}
      }

      const deepLinkUrl = new URL(continueUri);
      const idToken = params.get('id_token');
      const accessToken = params.get('access_token');
      if (idToken)     deepLinkUrl.searchParams.set('id_token', idToken);
      if (accessToken) deepLinkUrl.searchParams.set('access_token', accessToken);
      if (state)       deepLinkUrl.searchParams.set('state', state);

      const finalUrl = deepLinkUrl.toString();
      document.getElementById('manual-link').href = finalUrl;
      window.location.href = finalUrl;
      setTimeout(() => { document.getElementById('fallback').style.display = 'block'; }, 2000);
    })();
  </script>
</body>
</html>
```

## Firebase Hosting config (for the callback page)

```json
{
  "hosting": {
    "rewrites": [{ "source": "/auth/callback", "destination": "/auth/callback/index.html" }],
    "headers": [{
      "source": "/auth/**",
      "headers": [
        { "key": "Cache-Control", "value": "no-store" },
        { "key": "X-Content-Type-Options", "value": "nosniff" }
      ]
    }]
  }
}
```

## Apple Sign-In

Apple Developer setup: register App ID with "Sign in with Apple" capability, create a Services ID for web auth, configure domains and redirect URLs.

```typescript
import { openUrl } from '@tauri-apps/plugin-opener';

export async function initiateAppleSignIn(): Promise<void> {
  const config = getAuthConfig();
  const nonce = crypto.randomUUID();
  await saveOAuthState({
    continueUri: `${config.appScheme}://auth/callback`,
    nonce, timestamp: Date.now(), provider: 'apple',
  });

  const authUrl = new URL('https://appleid.apple.com/auth/authorize');
  authUrl.searchParams.set('client_id', config.appleClientId);   // Your Services ID
  authUrl.searchParams.set('redirect_uri', config.callbackUrl);
  authUrl.searchParams.set('response_type', 'code id_token');
  authUrl.searchParams.set('scope', 'name email');
  authUrl.searchParams.set('response_mode', 'fragment');
  authUrl.searchParams.set('state', encodeURIComponent(JSON.stringify({nonce, ...})));
  authUrl.searchParams.set('nonce', nonce);

  await openUrl(authUrl.toString());
}
```

Firebase bridge for Apple credentials -- **`rawNonce` not hashed**:

```typescript
import { OAuthProvider, signInWithCredential } from 'firebase/auth';

export async function completeAppleSignIn(idToken: string, nonce: string) {
  const credential = new OAuthProvider('apple.com').credential({
    idToken,
    rawNonce: nonce,                                              // CRITICAL: raw, not hashed
  });
  await signInWithCredential(getAuth(), credential);
}
```

Apple-specific callback (persist user info on first sign-in only):

```typescript
function handleAppleCallback(params: OAuthCallbackParams): void {
  const userParam = params.user;
  if (userParam) {
    try {
      const userInfo = JSON.parse(decodeURIComponent(userParam));
      // Persist -- won't be returned on subsequent sign-ins
      localStorage.setItem('apple_user_info', JSON.stringify(userInfo));
    } catch {}
  }
}
```

## AuthContext with deep-link listener cleanup (React)

The full pattern that handles auth state, OAuth callbacks, and listener cleanup:

```tsx
import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { onOpenUrl } from '@tauri-apps/plugin-deep-link';
import { getAuth, onAuthStateChanged, signOut as firebaseSignOut, User } from 'firebase/auth';
import { initiateGoogleSignIn } from '../utils/oauth';
import { initiateAppleSignIn } from '../utils/oauth-apple';
import { handleOAuthCallback, OAuthError } from '../utils/oauth-callback';
import { clearOAuthState } from '../utils/oauth-state';

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const auth = getAuth();
  const clearError = useCallback(() => setError(null), []);

  const processCallback = useCallback(async (url: string) => {
    if (!url.includes('auth/callback')) return;
    setLoading(true); setError(null);
    try {
      await handleOAuthCallback(url);
    } catch (err) {
      setError(err instanceof OAuthError ? err.message : 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const unsubscribeAuth = onAuthStateChanged(auth, (u) => {
      setUser(u); setLoading(false);
    });

    let unsubscribeDeepLink: (() => void) | undefined;
    onOpenUrl((urls) => urls.forEach(processCallback))
      .then((unsub) => { unsubscribeDeepLink = unsub; });

    return () => {
      unsubscribeAuth();
      unsubscribeDeepLink?.();        // CRITICAL: clean up the deep-link listener
    };
  }, [auth, processCallback]);

  const signInWithGoogle = useCallback(async () => {
    setError(null); setLoading(true);
    try { await initiateGoogleSignIn(); }
    catch (err) {
      setLoading(false);
      setError(err instanceof OAuthError ? err.message : 'Failed to start sign-in.');
    }
  }, []);

  const signOut = useCallback(async () => {
    await clearOAuthState();
    await firebaseSignOut(auth);
  }, [auth]);

  return <AuthContext.Provider value={{ user, loading, error, signInWithGoogle, signOut, clearError }}>
    {children}
  </AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
```

## Mobile troubleshooting

| Problem | Solution |
|---------|----------|
| Shell plugin URL error on Android | Use `opener` plugin instead of `shell:open` |
| Deep link not received | Scheme in `tauri.conf.json` must match the URL scheme |
| Callback page not found | Firebase Hosting path must match `redirect_uri` |
| App not opening from browser | Verify `deep-link` plugin is initialized in `lib.rs` |
| Apple Sign-In fails | Verify Services ID + domain configuration |
| Token not in callback | Check `response_type` includes `token id_token` |
| CORS errors | Callback page must be on same domain as `redirect_uri` |
| Apple "rawNonce mismatch" | Pass the original nonce, not the SHA-256 hash |

## Official docs

- Tauri `deep-link` plugin: https://v2.tauri.app/plugin/deep-link/
- Tauri `opener` plugin: https://v2.tauri.app/plugin/opener/
- Apple Sign-In Services ID setup: https://developer.apple.com/help/account/configure-app-capabilities/configure-sign-in-with-apple-for-the-web
- Apple Sign-In JS reference: https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_js
- Firebase Apple OAuth integration: https://firebase.google.com/docs/auth/web/apple
- Android Custom Tabs: https://developer.chrome.com/docs/android/custom-tabs
- iOS ASWebAuthenticationSession (alternative to Custom Tabs): https://developer.apple.com/documentation/authenticationservices/aswebauthenticationsession

## Related

- `authentication.md` -- OAuth/PKCE security architecture, state validation, Firebase signInWithCredential
- `plugins-mobile.md` -- the `deep-link` plugin in the broader mobile context
- `frontend-patterns.md` -- React lifecycle hooks (the `useEffect` cleanup pattern this file uses)
