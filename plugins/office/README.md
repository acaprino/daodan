# Office

Editable DOCX, PPTX and XLSX methods for the Daodan hosts. The neutral kernel is
the source; packages under `exports/` are compiler output. Command entries live
in `daodan`. See [the user guide](../../docs/plugins/office.md).

## Shared decisions and native composition

`intake` resolves the request once. `content` owns the source/claim ledger,
transformations and requested-format projections in `CONTENT.md`. `design`
uses required Taste v2 art-direction knowledge through one bounded
[input/output contract](skills/design/references/art-direction.md). It authors
complete visual proposals for the settled brief. Existing format designers,
native producers and reviewers prove representative real content before the
HTML gallery and explicit choice in `DESIGN.md`. DOCX and PPTX own their
independent `structure.md` and `layout-patterns.md` references, native construction
and saved-file review. The existing five roles retain their production boundaries.

Palette extraction/generation, font checks, inspectors and native template tools
remain available. Direction catalogs supply ideas and seeds; each new brief
gets its own visual identity. Separate DOTX/POTX files are optional unless the
request calls for reusable templates. XLSX retains its existing method.

## Sources, pins and licenses

Office is MIT. The repository [LICENSE](../../LICENSE) does not replace the
licenses of adaptations listed below. Full third-party terms remain under the
owning skill's shipped references, so the generated host packages carry them.

| Contribution | Local scope and pinned source | Terms and adaptation |
|---|---|---|
| Taste v2 art direction | Required `taste-skill@taste-skill`, skill `design-taste-frontend`; [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) 2.1.5 inspected at `12af471f627f866411b4bd785b19646d3672784c` | [Upstream MIT terms](https://github.com/Leonxlnx/taste-skill/blob/12af471f627f866411b4bd785b19646d3672784c/LICENSE). Separately installed knowledge, no upstream source copied. Office owns intake, content, selection, geometry and review; the bridge bounds direction and critique. Verify installed identity/version and actual bytes; the upstream plugin catalog uses a mutable ref. |
| Agentit editorial/typography | [editorial-design.md](skills/design/references/editorial-design.md), [typography.md](skills/design/references/typography.md); [marcmarti9/agentit](https://github.com/marcmarti9/agentit) at `fc38111622ac459ccf843234863bd0b8fcb6ebfd` | Apache-2.0 plus retained RampStack and Peter Bamuhigire MIT notices. [Exact notices, source hashes and local modifications](skills/design/references/agentit-upstream.md). Guidance is assimilated into Office ownership, not a second harness. |
| Theme Factory seed palettes | Directions Q–T in [directions.md](skills/design/references/directions.md); [anthropics/skills](https://github.com/anthropics/skills) at `dbd4588f9e1033efb41dad4bef2f7947c8993d44` | Apache-2.0. [Retirement/provenance](skills/design/references/theme-factory-upstream.md) and [full terms](skills/design/references/LICENSE-theme-factory-APACHE-2.0.txt). The former preset skill/showcase is not shipped. |
| PPT Visual region sketches | [PPTX layout-patterns.md](skills/pptx/references/layout-patterns.md); [claude-office-skills/skills](https://github.com/claude-office-skills/skills) at `9c4c7d5cd2813a8936bf2c9fdb174ea883b85a11` | [MIT terms](skills/pptx/references/LICENSE-ppt-visual-MIT.txt). Only adapted sketches and specification handoffs; native object constraints and shared visual ownership remain local. |
| Word composition inspiration | [DOCX layout-patterns.md](skills/docx/references/layout-patterns.md); [tivojn/Office](https://github.com/tivojn/Office) at `303e55d42a71aca4bc1dffdb49f6c1f090889899` | Original local guidance. The inspected source lacked complete license terms; no source blocks, assets or fonts were copied. This is not a copied-source sync target. |

DeckCraft, WordCraft and GridCraft are separately supplied runtimes, not bundled
engines or copied-source dependencies. Their skills link the actual runtime
contracts and require capability/version evidence before dependent production.
Installed fonts retain their own licenses and embedding permissions.

PPT Design remains a candidate for an observed gap after the paired native
proof. Future upstream contributions
must enter the existing owner with retained provenance and measurable benefit;
avoid parallel style authorities or repeated instructions.

## Verification boundary

Record validation proves structural bindings. HTML previews demonstrate proposed
visual treatment. Native inspectors, actual saved-file renders and independent
review provide separate evidence. Compiler parity across five hosts does not
prove installed-host execution or Microsoft application fidelity. Token or cost
savings require actual telemetry, not estimates from text length.
