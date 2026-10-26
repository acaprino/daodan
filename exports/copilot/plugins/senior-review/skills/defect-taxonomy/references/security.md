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

# Security Vulnerabilities

Reference for defect taxonomy category 6.

---

## Category 6: Security Vulnerabilities

### 6.1 SQL Injection
- **CWE**: 89 | **OWASP**: A03:2021
- **Pattern**: User input concatenated into SQL string
- **Detection**: Taint analysis, regex for `execute(.*\+`, CodeQL `sql-injection`, Semgrep
- **Fix**: Parameterized queries / prepared statements, ORM query builders, stored procedures
- **Difficulty**: Low
- **Signature**: `"SELECT * FROM users WHERE id=" + userId`, `f"SELECT ... {input}"`

### 6.2 Cross-Site Scripting (XSS)
- **CWE**: 79 | **OWASP**: A03:2021
- **Types**:
  - Reflected -- input echoed in response
  - Stored -- persisted in DB, rendered to other users
  - DOM-based -- client-side JS writes to DOM
- **Detection**: Data flow to `innerHTML`, `dangerouslySetInnerHTML`, `document.write`, `|safe` (Django), `v-html` (Vue)
- **Fix**: Context-aware output encoding, CSP headers, React auto-escaping (avoid `dangerouslySetInnerHTML`)
- **Difficulty**: Medium
- **Signature**: `element.innerHTML = userInput`, `{{ data|safe }}`, `v-html="userContent"`

### 6.3 Command Injection
- **CWE**: 78 | **OWASP**: A03:2021
- **Pattern**: User input passed to shell commands
- **Detection**: Taint to `os.system()`, `shell=True`, `Runtime.exec()`, backticks, `child_process.exec`
- **Fix**: `subprocess.run([cmd, arg], shell=False)`, allowlists for commands, parameterized exec
- **Difficulty**: Low-Medium
- **Signature**: `os.system("ping " + host)`, `exec("ls " + dir)`

### 6.4 LDAP Injection
- **CWE**: 90
- **Pattern**: Special characters in LDAP queries (`*`, `(`, `)`, `\`, NUL)
- **Detection**: Taint analysis to LDAP search filters
- **Fix**: Escape per RFC 4515, parameterized LDAP queries, input validation
- **Difficulty**: Medium

### 6.5 Template Injection / SSTI
- **CWE**: 1336
- **Pattern**: User input used as template source, not template data
- **Detection**: `Template(user_input)`, `render_template_string(user_input)`, `eval` in template engines
- **Fix**: Never pass user input as template -- always as data/context, sandbox template engines
- **Difficulty**: Medium-High
- **Signature**: `Template(request.args['name']).render()`, Jinja2/Twig/Freemarker with user-controlled template

### 6.6 Authentication / Authorization Flaws
- **CWE**: 862 (missing authz), 863 (incorrect authz) | **OWASP**: A01:2021, A07:2021
- **Patterns**:
  - Missing auth middleware on routes
  - JWT `alg: none` accepted
  - IDOR -- direct object reference without ownership check
  - Privilege escalation -- user modifies role field
  - Session fixation -- session ID not rotated after login
- **Detection**: Route handlers without `@login_required`/`@PreAuthorize`, JWT library config audit
- **Fix**: Framework-level auth enforcement, server-side JWT validation (reject `none`), RBAC/ABAC, ownership checks
- **Difficulty**: High
- **Signature**: `@GetMapping("/admin/users")` without `@PreAuthorize`, `/api/orders/{id}` without ownership check

### 6.7 Cryptographic Misuse
- **CWE**: 327 (broken algo), 330 (weak PRNG), 321 (hardcoded key) | **OWASP**: A02:2021
- **Weak algorithms**: MD5, SHA1 (for security), DES, 3DES, RC4, ECB mode, PKCS1v1.5
- **Weak PRNGs**: `Math.random()`, `random.random()`, `rand()`, `java.util.Random`
- **Detection**: Flag calls to weak algorithm constructors, hardcoded key patterns
- **Fix**:
  - Encryption: AES-256-GCM, ChaCha20-Poly1305
  - Hashing: SHA-256+, BLAKE3
  - Passwords: bcrypt, Argon2id, scrypt
  - PRNG: `SecureRandom`, `crypto.getRandomValues()`, `secrets` module
- **Difficulty**: Low
- **Signature**: `MessageDigest.getInstance("MD5")`, `new Random()` for tokens, `key = "hardcoded123"`

### 6.8 Insecure Deserialization
- **CWE**: 502 | **OWASP**: A08:2021
- **Pattern**: Deserializing untrusted data into arbitrary objects -- RCE risk
- **Dangerous APIs**:
  - Python: `pickle.loads()`, `yaml.load()` (without `SafeLoader`)
  - Java: `ObjectInputStream.readObject()`
  - Ruby: `Marshal.load()`
  - .NET: `BinaryFormatter.Deserialize()`
- **Fix**: Safe formats (JSON, Protobuf), `ObjectInputFilter` (Java 9+), `yaml.safe_load()`, type allowlists
- **Difficulty**: Low-Medium
- **Signature**: `pickle.loads(request.data)`, `new ObjectInputStream(untrustedStream)`

### 6.9 Path Traversal
- **CWE**: 22 | **OWASP**: A01:2021
- **Pattern**: `../` sequences in file paths allowing directory escape
- **Detection**: Taint analysis to `open()`, `File()`, `fs.readFile()`, `Path.resolve()`
- **Fix**: `os.path.realpath()` then validate starts with base dir, `Path.normalize()`, reject `..` in input
- **Difficulty**: Low-Medium
- **Signature**: `open("/uploads/" + filename)` where filename = `../../etc/passwd`

### 6.10 Server-Side Request Forgery (SSRF)
- **CWE**: 918 | **OWASP**: A10:2021
- **Pattern**: Server fetches user-supplied URL -- access to internal services, cloud metadata
- **Detection**: Taint to `requests.get()`, `axios.get()`, `HttpClient`, `fetch()` on server
- **Fix**: URL allowlist, block private/reserved IP ranges (10.x, 172.16-31.x, 192.168.x, 169.254.169.254), DNS rebinding protection
- **Difficulty**: Medium
- **Signature**: `requests.get(user_url)`, accessing `http://169.254.169.254/latest/meta-data/`

### 6.11 Timing Attacks
- **CWE**: 208
- **Pattern**: Non-constant-time comparison of secrets -- byte-by-byte timing leaks
- **Detection**: Code review for `==` on tokens/hashes/keys, timing analysis
- **Fix**:
  - Python: `hmac.compare_digest()`
  - Node.js: `crypto.timingSafeEqual()`
  - Java: `MessageDigest.isEqual()`
- **Difficulty**: High
- **Signature**: `if (token == storedToken)`, `password.equals(dbPassword)`

### 6.12 Secrets in Source Code
- **CWE**: 798 (hardcoded credentials), 259 (hardcoded password)
- **Detection regex patterns**:
  - AWS: `AKIA[0-9A-Z]{16}`
  - GitHub: `ghp_[a-zA-Z0-9]{36}`
  - OpenAI: `sk-[a-zA-Z0-9]{48}`
  - Private keys: `BEGIN.*PRIVATE KEY`
  - Generic: `(secret|key|password|token)\s*[:=]`
- **Tools**: TruffleHog, GitLeaks, git-secrets, pre-commit hooks
- **Fix**: Environment variables, vault systems (HashiCorp Vault, AWS Secrets Manager), `.gitignore` for `.env`
- **Difficulty**: Low-Medium
- **Signature**: `API_KEY = "sk-abc123..."`, `password = "admin123"` in config files

### 6.13 CORS Misconfiguration
- **CWE**: 942
- **Patterns**:
  - `Access-Control-Allow-Origin: *` with credentials
  - Reflecting `Origin` header without validation
  - Overly permissive allowed methods/headers
- **Detection**: Response header analysis, CORS config review
- **Fix**: Explicit origin allowlist, never reflect arbitrary origins with credentials, restrict methods
- **Difficulty**: Low-Medium

### 6.14 Missing Input Validation
- **CWE**: 20
- **Patterns**:
  - No server-side validation (relying on client only)
  - ReDoS from nested quantifiers `(a+)+$`
  - Missing length limits, type checks, range validation
- **Detection**: CodeQL, Semgrep rules, regex complexity analysis
- **Fix**: Server-side validation always, RE2 engine (no backtracking), Joi/Zod/Pydantic schemas, input length limits
- **Difficulty**: Medium-High
- **Signature**: `new RegExp(userPattern)`, no validation between HTTP handler and business logic

### 6.11 Regex Denial-of-Service (ReDoS)
- **CWE**: 1333 | **OWASP**: related to A04:2021 (Insecure Design)
- **Pattern**: Catastrophic-backtracking regex applied to attacker-controlled input. Nested quantifiers (`(a+)+`), overlapping alternations (`(a|a)*`), exponential blowup on unanchored patterns.
- **Detection**: Scan for regex literals with `+*` or `**`; Python `re.match` without `re.DOTALL`/`re.ASCII` flags on user input; `validators` / email-regex libraries older than a year; Semgrep rule `python.lang.security.audit.dangerous-regex`.
- **Fix**: Use `re2` (linear-time engine), `regex` library with timeout, rewrite pattern to eliminate nested quantifiers, validate length before matching, anchor patterns (`^...$`).
- **Difficulty**: Medium
- **Signature**: `re.match(r"^(a+)+$", user_input)`, `re.fullmatch(r"(\w+\s?)+", ...)`, unanchored email validators on untrusted input

### 6.12 Server-Side Request Forgery (SSRF)
- **CWE**: 918 | **OWASP**: A10:2021
- **Patterns**:
  - Fetching a URL from user input without allowlist (`requests.get(url)`)
  - Following redirects to cloud metadata (`169.254.169.254`, `metadata.google.internal`, `fd00:ec2::254`)
  - DNS rebinding (resolve-check vs resolve-at-use race)
  - Blind SSRF via Webhooks, PDF renderers, image proxies
- **Detection**: Taint from HTTP inputs into outbound HTTP calls; scan for `requests.get(url)`/`httpx.get(url)` where `url` is user-controlled; check redirect policies.
- **Fix**: Allowlist of allowed hosts/schemes; disable redirects (`allow_redirects=False`) or validate each hop; block `169.254.0.0/16`, `127.0.0.0/8`, `::1`, RFC1918, link-local; use a dedicated SSRF-proof library (e.g., `ssrfmap`-aware fetchers); pin DNS resolution with `getaddrinfo` + revalidate on connect.
- **Difficulty**: Medium-High
- **Signature**: `requests.get(user_url)` with no validation; webhook endpoints that fetch arbitrary URLs; PDF/image renderers that resolve remote resources

### 6.13 Monetary Precision / Floating-Point Money (CWE-681 family)
- **CWE**: 681 (Incorrect Conversion between Numeric Types), 682 (Incorrect Calculation)
- **Pattern**: Financial calculations using IEEE-754 binary float (`float` in Python, `Number` in JS) instead of decimal / integer cents. Accumulated rounding errors, sum-not-equal-to-parts, fee miscalculations.
- **Detection**: Grep for `* 0.01`, `price: float`, `amount: Number`; check model schemas for `float`/`double` columns on money fields; scan for `round(...)` on totals (hides underlying drift).
- **Fix**: Use `decimal.Decimal` with explicit precision + rounding mode; store as integer minor units (cents / satoshi); use libraries like `moneyed` (Python) or `dinero.js` (TS); enforce via Pydantic `Decimal` / `condecimal`.
- **Difficulty**: Low to detect, medium to fix (schema migration)
- **Signature**: `total = sum(p * 0.01 for p in prices)`, `amount: float` in API payloads, SQLAlchemy `Float` column on a `price_usd` field

---

## Quick Reference: Security Detection Priorities

| Priority | Vulnerability | CWE | Automated Detection Feasibility |
|----------|--------------|-----|-------------------------------|
| Critical | SQL Injection | 89 | High -- taint analysis |
| Critical | Command Injection | 78 | High -- taint analysis |
| Critical | Deserialization | 502 | High -- API pattern matching |
| High | XSS | 79 | Medium -- data flow analysis |
| High | Auth flaws | 862/863 | Medium -- route analysis |
| High | Path Traversal | 22 | High -- taint analysis |
| High | Secrets in code | 798 | High -- regex patterns |
| Medium | SSRF | 918 | Medium -- taint analysis, allowlist check |
| Medium | Template Injection | 1336 | Medium -- API pattern matching |
| Medium | ReDoS | 1333 | Medium -- regex AST analysis, quantifier heuristics |
| Medium | Monetary Precision | 681 / 682 | High -- schema scan for `float` on money fields |
| Lower | Timing attacks | 208 | Low -- requires context understanding |
