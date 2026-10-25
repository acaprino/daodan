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

# Font pairings

Twelve heading/body pairings from Google Fonts for Office documents and decks.
Every face is OFL-1.1 and permits installation and document embedding; each was
downloaded and verified with `scripts/font_fetch.py` when this catalog was written.
Choose one pairing for the whole file; a supplied brand or template font always
comes first. The direction in `directions.md` names its pairing by the number
below; this catalog supplies the type.

The `Spec` column is the exact argument for `font_fetch.py`: it requests only the
weights the pairing uses. The fallback is a font that ships with Microsoft Office,
for a recipient who has neither the font nor an embedded copy.

| # | Pairing | Tone and use | Headings | Body | Spec | Office fallback (headings / body) |
|---|---|---|---|---|---|---|
| 1 | Inter | Corporate, consulting, SaaS: neutral and very legible on screen | Inter 600/700 | Inter 400, italic | `Inter:ital,wght@0,400;0,600;0,700;1,400` | Arial / Calibri |
| 2 | Source Serif 4 + Source Sans 3 | Board, finance, strategy: classic authority | Source Serif 4 600 | Source Sans 3 400/700, italic | `Source Serif 4:wght@600` `Source Sans 3:ital,wght@0,400;0,700;1,400` | Cambria / Calibri |
| 3 | Playfair Display + Lato | Brand story, culture, magazine-style decks | Playfair Display 700 | Lato 400/700, italic | `Playfair Display:wght@700` `Lato:ital,wght@0,400;0,700;1,400` | Georgia / Calibri |
| 4 | Libre Baskerville + Libre Franklin | Long reports, publications, policy papers | Libre Baskerville 700 | Libre Franklin 400/600, italic | `Libre Baskerville:wght@700` `Libre Franklin:ital,wght@0,400;0,600;1,400` | Georgia / Arial |
| 5 | IBM Plex Sans + IBM Plex Mono | Engineering, IT, data and architecture | IBM Plex Sans 600 | IBM Plex Sans 400, italic; Plex Mono 400 for code | `IBM Plex Sans:ital,wght@0,400;0,600;1,400` `IBM Plex Mono:wght@400` | Arial / Calibri, Consolas |
| 6 | Montserrat + Open Sans | Marketing, product launch, events | Montserrat 600/700 | Open Sans 400/600, italic | `Montserrat:wght@600;700` `Open Sans:ital,wght@0,400;0,600;1,400` | Arial / Calibri |
| 7 | Cormorant Garamond + Montserrat | Luxury, hospitality, fashion: elegant and airy | Cormorant Garamond 600 | Montserrat 400 | `Cormorant Garamond:wght@600` `Montserrat:wght@400` | Garamond / Arial |
| 8 | Nunito | Education, onboarding, HR: friendly and rounded | Nunito 700 | Nunito 400, italic | `Nunito:ital,wght@0,400;0,700;1,400` | Calibri / Calibri |
| 9 | Barlow Semi Condensed + Barlow | Dashboards, KPIs, operations: dense data | Barlow Semi Condensed 600 | Barlow 400/500, italic | `Barlow Semi Condensed:wght@600` `Barlow:ital,wght@0,400;0,500;1,400` | Arial Narrow / Arial |
| 10 | Space Grotesk + Inter | Startup pitch, tech product: contemporary | Space Grotesk 700 | Inter 400, italic | `Space Grotesk:wght@700` `Inter:ital,wght@0,400;1,400` | Arial / Calibri |
| 11 | DM Serif Display + DM Sans | Non-profit, wellness, food, culture: warm | DM Serif Display 400 | DM Sans 400/700, italic | `DM Serif Display:wght@400` `DM Sans:ital,wght@0,400;0,700;1,400` | Georgia / Calibri |
| 12 | Noto Serif + Noto Sans | Compliance, public sector, multilingual content | Noto Serif 700 | Noto Sans 400/700, italic | `Noto Serif:wght@700` `Noto Sans:ital,wght@0,400;0,700;1,400` | Cambria / Arial |

## Choosing

- Match the tone to the audience and argument settled at intake, not to taste
  alone. A deck's visual direction may name Office fonts; a pairing replaces them
  only when the user accepts it.
- Check script coverage for the content's languages. Noto covers Latin, Greek and
  Cyrillic; other scripts need the matching Noto family (for example Noto Sans JP
  or Noto Sans Arabic) fetched the same way.
- Display faces (Playfair Display, Cormorant Garamond, DM Serif Display) are for
  headings at `24 pt` and above only; never set body text or table cells in them.
- Use only the listed weights. A bold or italic that was not fetched is
  synthesized by the application and renders worse.

## Provenance

This catalog and the fetch and embed helpers are original Office guidance, not
part of the adapted upstream typography skill. Fonts are downloaded at run time
from Google Fonts and are not bundled; their licenses travel inside each file.
