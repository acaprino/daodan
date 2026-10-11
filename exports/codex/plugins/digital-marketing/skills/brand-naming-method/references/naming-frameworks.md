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

# Naming Frameworks Reference

## CO.ME.OR.GO (Pennamontata)

Five criteria for an effective name:
1. **COrto** - Short, ideally 1-3 syllables
2. **MEmorabile** - Sticks after a single exposure
3. **ORiginale** - Stands out from competitors
4. **Gradevole** - Pleasant to hear and say
5. **Orecchiabile** - Catchy, phonetically engaging

## Spellbrand Evaluation Tests

- **Phone Test**: Say the name once over the phone. At least 70% of listeners should remember it correctly.
- **Spelling Test**: Say the name aloud. At least 80% should be able to spell it correctly.
- **Google Test**: Search the exact name. Avoid names with saturated SERPs of unrelated content.
- **T-shirt Test**: Would someone proudly wear this on a shirt? Tests likability and brand pride.
- **Radio Test**: Could a radio listener find the brand online after hearing it once?

## NameRobot Weighted Scoring

Source material only. The weights this skill applies are the Step 7 table in SKILL.md, which adds Market Saturation, SEO Potential, Domain Availability and Trademark Risk as separate criteria and rebalances the rest to make room; where the two disagree, Step 7 governs. NameRobot's published distribution, for reference:
- Simplicity/Memorability: 20%
- Uniqueness: 20%
- Relevance: 15%
- Pronunciation: 15%
- Cultural adaptability: 10%
- Availability: 10%
- Evocativeness: 10%

## Mock The Agency - Brand Element Criteria

Key properties of a strong brand name:
- **Memorability** - recognition and recall
- **Protectability** - legal trademark strength
- **Likability** - aesthetic and emotional appeal
- **Transferability** - works across categories and markets
- **Adaptability** - evolves with the brand over time

## Name Archetypes

| Archetype | Definition | Pros | Cons | Example |
|-----------|-----------|------|------|---------|
| Brandable Names | Coined/invented words with no prior meaning | Highly distinctive, easy to trademark | No inherent meaning, requires brand-building investment | Google, Rolex, Kodak, Noom |
| Evocative | Real-word combinations that suggest energy or emotion | Emotional resonance, storytelling, aspiration | Subjective interpretation, may feel forced | RedBull, Forever21, Nike, Lululemon |
| Short Phrase | 2-3 word descriptive phrases | Instant clarity, SEO-friendly, self-explanatory | Hard to trademark, long, limiting | Dollar Shave Club, MyFitnessPal, WeTransfer |
| Compound Words | Two real words merged into one | Balanced clarity and distinctiveness, memorable | Can feel generic if words are common | FedEx, Microsoft, YouTube, Snapchat |
| Alternate Spelling | Intentionally misspelled real words | Distinctive, registrable, recognizable | Spelling confusion, looks unprofessional if overdone | Lyft, Fiverr, Tumblr, Flickr, Reddit |
| Non-English Words | Words from other languages with relevant meaning | Cultural depth, unique, good brand story | May be mispronounced, meaning not obvious | Toyota, Audi, Volvo, Samsung, Lego |
| Real Words | Existing English words repurposed as brand names | Maximum memorability, immediate recognition | Hardest to trademark and get domains | Apple, Amazon, Slack, Stripe, Notion |

## Phonosymbolism

Research (Kohler 1929, Ramachandran 2001 - Bouba/Kiki effect) shows sounds carry meaning:

**Vowels**
- `a`, `o` - open, warm, large, approachable (e.g., Amazon, Oura)
- `i`, `e` - small, precise, light, quick (e.g., Wii, Etsy)
- `u` - deep, powerful, serious (e.g., Uber, Ubuntu)

**Consonants**
- `b`, `m`, `l` - soft, round, nurturing (e.g., Bumble, Mellow)
- `k`, `t`, `p` - sharp, strong, energetic (e.g., Kickstart, Tesla)
- `s`, `f`, `v` - flowing, smooth, elegant (e.g., Spotify, Visa)
- `r`, `g` - rugged, powerful, dynamic (e.g., Grit, Reebok)

## Case Studies

**Noom** - Abstract, symmetric, recalls "moon" reversed. No intrinsic meaning - built through marketing focused on behavioral psychology. Easy to register, globally pronounceable.

**Oura** - Originally "Jouzen" (from Finnish joutsen "swan" + zen). Simplified for global markets. Lesson: local names may need adaptation for international launch.

**Strava** - From Swedish "strava" (to strive). Short, evocative of athletic effort. Minor orthographic change (a instead of a-umlaut) for international readability.

**MyFitnessPal** - Descriptive/conversational. Immediate clarity about function. Strong SEO but weak trademark protection due to common words.

**Stripe** - Neutral, short, boring-on-purpose. Simplicity signals reliability for developers. Lesson: sometimes an unexciting name lets the product speak.

## Morphological Generation Techniques (legacy, evaluation only)

**Do NOT generate names from this section.** SKILL.md Step 2 bans exactly what these techniques produce: coined words, algorithmic letter-mashing, and cheap suffixes (-io, -ly, -fy). These patterns are kept here to describe and evaluate names that already exist, such as a competitor's brand or a name the user arrived at elsewhere. For generation, use the 4 Strategic Directions in Step 2. For polishing a promising candidate, use the Refinement Toolkit in SKILL.md.

Advanced techniques for creating registrable, distinctive brand names that go beyond simple portmanteau.

### Technique A: Clipping & Suffixing

Extract a root morpheme from a relevant word and attach a non-standard suffix.

**Suffix Inventory:**
| Suffix | Feel | Examples |
|--------|------|----------|
| -io | tech, modern | Nutrio, Cardio, Clasp.io |
| -ia | place, community | Luminia, Experia, Trivia |
| -ly | friendly, approachable | Grammarly, Bitly, Orderly |
| -fy | action, transformation | Spotify, Shopify, Testify |
| -os | global, pluralistic | Chronos, Helios, Kairos |
| -ix | precision, tech | Graphix, Nutrix, Automatix |
| -ara | warmth, organic | Solara, Zephara, Lunara |
| -ova | innovation, fresh | Innova, Genova, Vitanova |
| -ium | premium, scientific | Titanium, Radium, Palladium |
| -eo | modern, video-era | Vimeo, Cameo, Stereo |
| -ika | distinctive, global | Botanika, Dynamika, Logika |

**Process:**
1. Identify 5-10 keywords relevant to the brand
2. Extract root morphemes (first 3-5 letters)
3. Combine each root with 3-4 suffixes from the inventory
4. Filter for pronounceability and distinctiveness

### Technique B: Vowel Dropping / Consonant Shifting

Alter the spelling of a known word to make it unique and registrable.

**Rules:**
- Drop interior vowels (Tumbler -> Tumblr, Flicker -> Flickr)
- Swap consonants for phonetic neighbors (ph->f, c->k, s->z)
- Double a consonant for emphasis (Trello from trail)
- Add/remove a trailing vowel (Figment -> Figma)
- Swap vowel sounds (a->o, e->i) to create near-words

**Phonetic Neighbor Map:**
| Original | Alternatives |
|----------|-------------|
| c/k | k, q, ck |
| s/z | z, x, ss |
| f/ph | f, ph, v |
| t/d | t, d, th |
| b/p | b, p |
| g/j | g, j, gh |

**Process:**
1. Start with a meaningful word (even a banned one)
2. Apply 1-2 alterations (not more - must remain pronounceable)
3. Verify the result doesn't accidentally spell something in another language
4. Check the altered form is not already taken

### Technique C: V-C-V-C-V Phonotactic Structures

Generate words using alternating Vowel-Consonant patterns. These are universally pronounceable across languages.

**Target Structures:**
| Pattern | Syllables | Examples |
|---------|-----------|---------|
| V-CV | 2 | Umi, Eko, Alo |
| CV-CV | 2 | Nova, Melo, Suki |
| V-CV-CV | 3 | Oralo, Avion, Eluma |
| CV-CV-CV | 3 | Talora, Merino, Kasumi |
| V-CV-CV-CV | 4 | Ivori, Akirano |

**Process:**
1. Select consonants from the phonosymbolic palette matching brand emotions
2. Select vowels for the desired warmth/precision balance
3. Arrange in V-C-V-C-V or CV-CV-CV patterns
4. Filter: must "feel like a word" without being one
5. Cross-check against major languages for unintended meanings

**Vowel-Emotion Guide:**
- Front vowels (i, e) - precision, lightness, technology
- Back vowels (a, o, u) - warmth, depth, trust

### Technique D: Cross-linguistic Blending

Fuse morphemes from different languages where both parts carry relevant meaning.

**Productive Language Pairs:**
| Pair | Why it works | Example |
|------|-------------|---------|
| Latin + Japanese | Authority + minimalism | Auralux (aura + lux), Zenkai (zen + kai) |
| Greek + Nordic | Science + strength | Chronvald (chronos + vald) |
| Sanskrit + Italian | Wisdom + elegance | Pranagio (prana + viaggio) |
| Arabic + French | Richness + refinement | Qamarelle (qamar + belle) |
| Finnish + Spanish | Uniqueness + energy | Suviluz (suvi + luz) |

**Process:**
1. List relevant concepts in 3-4 source languages
2. Extract morphemes (2-4 letters each)
3. Test combinations for flow and pronounceability
4. Verify neither morpheme has negative connotations in common languages
5. Prefer combinations where the blend creates a new phonetic identity (not obviously two words stapled together)

**Quality Check:**
- The blend should sound like a single word, not a compound
- Native speakers of the source languages should not find it awkward
- The etymology should be discoverable (good brand story) but not obvious (not a dictionary lookup)

## Trademark Resources

- **EUIPO TMview**: https://www.tmdn.org/tmview/
- **USPTO Trademark Search**: https://tmsearch.uspto.gov/ (replaced TESS, retired 2023-11-30; old TESS links redirect here)
- **WIPO Global Brand Database**: https://branddb.wipo.int/
- **Nice Classification**: 45 classes of goods/services for trademark registration

All three registers are JavaScript applications. A search engine does not index their records, so they are queried in a browser, never through a web search for the name.
