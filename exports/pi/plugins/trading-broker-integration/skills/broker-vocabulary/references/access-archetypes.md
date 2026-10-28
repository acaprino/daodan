<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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

# Access Archetypes

Programmatic broker access comes in the five archetypes below, and which one you are integrating
decides more about the system you will build than the broker's name does. Two brokers that share an
archetype share their operational problems almost exactly. Two paths to the *same* broker under
different archetypes share almost nothing.

So name the archetype first. It fixes what has to be running, what dies with what, what you are on the
hook to keep alive, and which recovery stories are even available to you. Every later decision in this
skill depends on that answer.

## The five archetypes

| Archetype | Meaning |
|---|---|
| `direct-api` | A cloud API reached over the network. No vendor component runs on your machine |
| `local-terminal` | A vendor application must run locally, holds session state, and may perform order handling itself rather than relaying it |
| `vendor-gateway` | A vendor-operated gateway or protocol engine you connect to, usually behind onboarding or conformance certification |
| `bridge` | Third-party software sitting between a platform and a broker, operated by neither of them |
| `in-platform` | Code that runs inside the vendor's own application rather than beside it |

A vendor is not an archetype. One broker can publish a cloud API for one product and require a local
application for another, and its answers differ between the two. State the archetype of the path you
are on, not the name on the account.

## What changes per archetype

Four questions separate them, and the answers are the deployment rather than the code.

| Archetype | Where session state lives | What dies with what | You run and keep alive |
|---|---|---|---|
| `direct-api` | On the vendor's servers, keyed to a credential you hold. Your process holds a token, not a session | Your process dies and the broker does not notice. Working orders keep working | Your own code, plus credential rotation |
| `local-terminal` | Inside the vendor application on your machine. Your process holds a socket to that application, not to the broker | The application dies and every attached client's session dies with it, along with anything it was holding rather than relaying. Your process dies and the application usually keeps the session, so a restart reconnects instead of re-authenticating | The vendor application: its login, its restart schedule, its version, and the desktop session it expects |
| `vendor-gateway` | In a negotiated session on the gateway, sequenced by numbers both sides count | The session drops and the sequence state is what is at risk, not the resting orders. Recovery is a resend and gap-fill protocol, not a fresh query | Your side of the protocol engine, and its sequence store, which must survive a process restart on disk |
| `bridge` | Split in two. The bridge holds one session to the broker and one to you, and neither vendor knows it exists | The bridge dies and both vendors look healthy while nothing works | The bridge, its version, its mapping tables, and their correspondence to both sides after either one upgrades |
| `in-platform` | The platform's, and your code is inside it. There is no connection to lose | The platform dies and takes your strategy with it. Your code cannot outlive it, restart it, or alert from outside it | The platform, plus whatever step installs your code into it |

**The failure surface each one adds**, on top of what they all share (credential expiry, rate limits,
partial network failure, a broker that is simply down):

- `direct-api` adds nothing. It is the baseline the other four are this-plus-a-component versions of,
  which is why an integration that can choose `direct-api` usually should.
- `local-terminal` adds configuration you cannot read from your repository. The application carries
  settings that veto or silently mutate orders, it was built for a person to log into, and it is a
  second process that must outlive the strategy on a machine you maintain.
- `vendor-gateway` adds state that must outlive the process. Lose the sequence numbers and you cannot
  resume the session, only start a new one and reconcile. It also adds a certification or onboarding
  gate, which means you cannot answer a question by trying it until someone approves you.
- `bridge` adds a component with no support relationship. Translation loss is its signature failure:
  an attribute you set never reaches the broker and nothing reports it, because the bridge is the only
  party that saw both sides. Either vendor can break it in a routine release.
- `in-platform` adds the platform's language, scheduler and lifecycle as constraints on your code.
  There is no external supervisor, the library set is whatever the platform ships, and testing means
  running the platform.

Three consequences follow, and they are the reason this file is first:

- **Recovery means a different operation per archetype.** Refreshing a token, reopening a socket to a
  local component, resuming a sequenced session from a persisted counter, and restarting a process you
  do not own are four different designs. A recovery layer copied across archetypes is wrong before it
  is written.
- **Every archetype except `direct-api` adds a process you must keep alive**, and that process is where
  the operating cost of the integration actually lives. Budget for it as a component, with its own
  supervision, its own upgrade path and its own alerts.
- **The archetype decides whether "can this run unattended" is a setting or an open question.** Under
  `direct-api` it is a setting. Under the other four it is a question, and the honest answer comes from
  a measurement on your platform and version rather than from a vendor page.

## The second axis: one broker or many

The archetype answers how software reaches a counterparty. It says nothing about how many
counterparties sit behind that software, and the two questions are independent.

| Scope | Meaning |
|---|---|
| `single-broker` | The subject is one broker, together with any connection tooling that broker publishes itself. Facts established about it hold for every user of that broker, subject to entity and entitlement |
| `multi-broker-platform` | The subject is software or a back end that many independent brokers sit behind. Facts established against one of them may be false for the next, because each configures its own instruments, execution rules and trading hours |

On a `multi-broker-platform`, a measurement carries the broker it was taken against, and a fact
that varies per broker is a **runtime detection problem** rather than a documentation problem: no
amount of writing down the right answer for one broker makes it the right answer for the next
one, so the code has to ask. MetaTrader 4 and 5, cTrader, DXtrade, Match-Trader and TradeLocker
are all this shape, one piece of platform software with hundreds of independently configured
brokers behind it, which is the pattern to recognise wherever it recurs.

## Where the two integrated brokers sit

Interactive Brokers (through the TWS API and IB Gateway) is `local-terminal` and `single-broker`:
the terminal is IBKR's own, and a fact established about it holds for every IBKR account, subject
to entity and entitlement. MetaTrader 5 is `local-terminal` and `multi-broker-platform`: the
terminal is the same software regardless of which broker issued the login, but the broker behind
that login decides the instruments, fill modes, margin mode and trading hours a given account
actually sees.

Sharing the archetype is what makes their operational problems the same problems: connection
lifecycle, terminal restarts and session exclusivity all transfer, which is why an operational
lesson learned on one usually transfers while a trading-vocabulary lesson usually does not.
Sharing the archetype does not make a fact about one true of the other. For MetaTrader 5 it does
not even make a fact about one broker's instance true of the next broker on the same platform.

| Shared consequence | What it means in practice |
|---|---|
| Order handling happens locally rather than being relayed | The local application can hold, stage, mutate or veto an order before the broker ever sees it. "The broker rejected it" is a conclusion you have to earn, not the default reading of a refusal |
| Unattended operation is an open question, not a setting | Whether the application starts without an interactive desktop, and stays up, is measured per operating system and per version. Both are desktop applications first |
| Authentication is the terminal's, and it was designed for a person sitting at it | Your process never authenticates to the broker; it attaches to a component that already holds a session. Interactive Brokers puts a GUI login and a second factor in that path, so unattended operation needs a login-automation layer. MetaTrader 5 accepts credentials on the initialize call, but the desktop application still has to be there to receive them |
| A session is an exclusive resource, and a second attachment contends for it | With Interactive Brokers the contention is at the credential: a second login on the same username can take the session, so an operator opening the vendor's app on the bot's credential evicts the bot and the symptom reads as a network fault. With MetaTrader 5 the contention is at the terminal: one process to one terminal, and a second process attaching to the same instance degrades or errors. Either way, sharing is a decision to make explicitly rather than discover |
| The terminal restarts on the vendor's clock | Interactive Brokers' terminal has a mandatory daily reset window and a periodic forced re-login. MetaTrader 5 has no daily reset but has weekend closure and an auto-updater that will restart the application mid-session unless disabled. Under both, reconnection is a routine scheduled event rather than an exceptional one |
| State dies with the terminal | Whatever the application was holding rather than relaying is gone when it dies. After any terminal death your process must rebuild ground truth by asking the broker, never by trusting what it remembers |

The archetype is a property of the path, not of the broker, and Interactive Brokers is its own
counterexample: it also publishes a Web API, and whether a given deployment of that is `direct-api` or
`local-terminal` depends on whether a local session component sits in the path. Answer that per
deployment before carrying any conclusion over from the terminal path.
