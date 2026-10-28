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

# Font pairings

Eighteen heading/body pairings from Google Fonts for Office documents and decks.
Every face is OFL-1.1 and permits installation and document embedding; each was
downloaded and verified with `scripts/font_fetch.py` when this catalog was written.
Use these pairings as optional resources when authoring the DESIGN typography
roles. Brand/template constraints and the assigned candidate remain authoritative.
A numbered pairing in `directions.md` is a seed, not a required font choice.

The `Spec` column is the exact argument for `font_fetch.py`: it requests only the
weights listed in that example. Verify the actual selected families, weights,
glyphs, licenses and recipient fallbacks for the current file, including fonts
outside this catalog. The table's Office fallbacks are starting points to check.

## Where the contrast comes from

A pairing works because its two faces differ in one deliberate way. Decide which
before choosing names; a pairing without a source of contrast is two fonts that
happen to be installed.

| Source | Mechanism | Risk |
|---|---|---|
| Form | Serif display with sans body, or the reverse | The x-heights must sit close, or the body looks a size smaller than the headings on the same line |
| Family | One superfamily for both roles (Inter, Nunito, Plex, Noto) | Safe and even, with little expression; carry the hierarchy with size and weight |
| Era | A face from one century against a face from another, at least two centuries apart | Fifty years apart looks like an accident; a low x-height old face needs about 8% more size when mixed with a modern sans on one line |

The `Contrast` column names the source for each pairing.

| # | Pairing | Tone and use | Contrast | Headings | Body | Spec | Office fallback (headings / body) |
|---|---|---|---|---|---|---|---|
| 1 | Inter | Corporate, consulting, SaaS: neutral and very legible on screen | Family | Inter 600/700 | Inter 400, italic | `Inter:ital,wght@0,400;0,600;0,700;1,400` | Arial / Calibri |
| 2 | Source Serif 4 + Source Sans 3 | Board, finance, strategy: classic authority | Family | Source Serif 4 600 | Source Sans 3 400/700, italic | `Source Serif 4:wght@600` `Source Sans 3:ital,wght@0,400;0,700;1,400` | Cambria / Calibri |
| 3 | Playfair Display + Lato | Brand story, culture, magazine-style decks | Form | Playfair Display 700 | Lato 400/700, italic | `Playfair Display:wght@700` `Lato:ital,wght@0,400;0,700;1,400` | Georgia / Calibri |
| 4 | Libre Baskerville + Libre Franklin | Long reports, publications, policy papers | Form | Libre Baskerville 700 | Libre Franklin 400/600, italic | `Libre Baskerville:wght@700` `Libre Franklin:ital,wght@0,400;0,600;1,400` | Georgia / Arial |
| 5 | IBM Plex Sans + IBM Plex Mono | Engineering, IT, data and architecture | Family | IBM Plex Sans 600 | IBM Plex Sans 400, italic; Plex Mono 400 for code | `IBM Plex Sans:ital,wght@0,400;0,600;1,400` `IBM Plex Mono:wght@400` | Arial / Calibri, Consolas |
| 6 | Montserrat + Open Sans | Marketing, product launch, events | Form | Montserrat 600/700 | Open Sans 400/600, italic | `Montserrat:wght@600;700` `Open Sans:ital,wght@0,400;0,600;1,400` | Arial / Calibri |
| 7 | Cormorant Garamond + Montserrat | Luxury, hospitality, fashion: elegant and airy | Form | Cormorant Garamond 600 | Montserrat 400 | `Cormorant Garamond:wght@600` `Montserrat:wght@400` | Garamond / Arial |
| 8 | Nunito | Education, onboarding, HR: friendly and rounded | Family | Nunito 700 | Nunito 400, italic | `Nunito:ital,wght@0,400;0,700;1,400` | Calibri / Calibri |
| 9 | Barlow Semi Condensed + Barlow | Dashboards, KPIs, operations: dense data | Family | Barlow Semi Condensed 600 | Barlow 400/500, italic | `Barlow Semi Condensed:wght@600` `Barlow:ital,wght@0,400;0,500;1,400` | Arial Narrow / Arial |
| 10 | Space Grotesk + Inter | Startup pitch, tech product: contemporary | Form | Space Grotesk 700 | Inter 400, italic | `Space Grotesk:wght@700` `Inter:ital,wght@0,400;1,400` | Arial / Calibri |
| 11 | DM Serif Display + DM Sans | Non-profit, wellness, food, culture: warm | Form | DM Serif Display 400 | DM Sans 400/700, italic | `DM Serif Display:wght@400` `DM Sans:ital,wght@0,400;0,700;1,400` | Georgia / Calibri |
| 12 | Noto Serif + Noto Sans | Compliance, public sector, multilingual content | Family | Noto Serif 700 | Noto Sans 400/700, italic | `Noto Serif:wght@700` `Noto Sans:ital,wght@0,400;0,700;1,400` | Cambria / Arial |
| 13 | Newsreader + Geist | Research briefings, reports, quiet editorial decks: a screen-tuned transitional serif over a plain sans | Form | Newsreader 500 | Geist 400/600, italic | `Newsreader:wght@500` `Geist:ital,wght@0,400;0,600;1,400` | Georgia / Arial |
| 14 | EB Garamond + IBM Plex Sans | Humanities, culture, long papers: a 16th-century serif against a rational modern sans | Era | EB Garamond 500, set about 8% larger than Plex on a shared line | IBM Plex Sans 400, italic | `EB Garamond:wght@500` `IBM Plex Sans:ital,wght@0,400;1,400` | Garamond / Arial |
| 15 | Lora + Hanken Grotesk | Services, wellness, mid-length reports: a calligraphic serif over a neutral grotesque | Form | Lora 600 | Hanken Grotesk 400/600, italic | `Lora:wght@600` `Hanken Grotesk:ital,wght@0,400;0,600;1,400` | Georgia / Calibri |
| 16 | Schibsted Grotesk + Source Serif 4 | News, media, analyst notes: a newspaper grotesque as display, serif body for sustained reading | Form, reversed | Schibsted Grotesk 700 | Source Serif 4 400, italic | `Schibsted Grotesk:wght@700` `Source Serif 4:ital,wght@0,400;1,400` | Arial / Cambria |
| 17 | Archivo + Inter | Campaigns, keynotes, big-number pages: a wide heavy grotesque with Inter kept to body sizes | Form | Archivo 800 | Inter 400, italic | `Archivo:wght@800` `Inter:ital,wght@0,400;1,400` | Arial Black / Calibri |
| 18 | Bricolage Grotesque + Newsreader | Creative agencies, culture, bold editorial decks: ink-trap display over a calm serif body | Form | Bricolage Grotesque 700 | Newsreader 400, italic | `Bricolage Grotesque:wght@700` `Newsreader:ital,wght@0,400;1,400` | Arial / Georgia |

## Overused faces

Some faces became the default answer of design tools and now read as
"generated" before the content is read. They remain legitimate when the brand
uses them or the role suits them; the substitute is for the case where the face
was reached for by habit.

| Face in its overused role | Why it reads as a default | Substitute in this catalog |
|---|---|---|
| Inter as a display face (pairings 1, 10) | Drawn for interface text; at display sizes it is even and expressionless | Archivo (17) or Schibsted Grotesk (16) for headings; keep Inter for body |
| Space Grotesk (pairing 10) | The reflex "tech" display of product pages | Schibsted Grotesk (16); Familjen Grotesk 700 is a verified alternative |
| Playfair Display (pairing 3) | The reflex "elegant" display; invitation-card feel | DM Serif Display (11) or Cormorant Garamond (7) |
| Fraunces, Instrument Serif as display | The reflex "tasteful" serif of generated layouts; Instrument Serif has one weight | Newsreader (13, 18) |

A warm paper ground with a high-contrast serif is a look family, not an overused
face. One proposal may use it; three proposals in that family are one proposal.

## Choosing

- Match the typography to the audience, content and assigned direction. A catalog
  suggestion cannot replace the candidate's typography roles. A material change
  follows the existing design revision and selection authority.
- Respect display thresholds. Cormorant Garamond holds only at 30 pt and above
  (its hairlines break smaller); Bricolage Grotesque and Archivo 800 are display
  faces, with body set in their partner. A low x-height serif on the same line
  as a modern sans (EB Garamond with Plex, Newsreader with Geist) needs about
  8% more size to look equal.
- Check script coverage for the content's languages. Noto covers Latin, Greek and
  Cyrillic; other scripts need the matching Noto family (for example Noto Sans JP
  or Noto Sans Arabic) fetched the same way.
- Use display faces where their shapes and size remain readable in the actual
  DOCX/PPTX context. Verify dense body and table text at the intended reading size.
- Fetch and verify every selected weight and italic face. Do not rely on
  synthesized styles or treat the table's example weights as an allowed set.

## Provenance

This catalog and the fetch and embed helpers are original Office guidance, not
part of the adapted upstream typography skill. Fonts are downloaded at run time
from Google Fonts and are not bundled; their licenses travel inside each file.
Pairings 13 to 18, the contrast-source column, the overused-face table and the
display thresholds adopt ideas from the typography reasoning of
[alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) (MIT),
read at commit `4fc7bfdbd5ec3fa2d43ce7a6433de60976a5e4b1`, rewritten for Office
point sizes and verified with `font_fetch.py` on 2026-10-27. No upstream text,
CSS or web sizing rule is copied.
