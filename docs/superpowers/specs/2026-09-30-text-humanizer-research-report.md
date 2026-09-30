# text-humanizer September 2026 refresh: the research reports

Committed as evidence of the 2026-09-30 refresh, per the retention rule in the
`custom-plugin-refresh` skill. The three researcher reports verbatim, as returned. They were
transcribed from the task notifications, because the runs' transcript files were empty on
disk; the only change is that HTML entities introduced by that transport (`&amp;`, `&gt;`)
were decoded back to the characters the researchers wrote. Which of these claims entered a
shipped body, and how each was checked, is in `2026-09-30-text-humanizer-source-verification.md`.

sha256 of the body below: `5809197da5c0e7ee824df7cb9506f8979f2d74c3a2174265c6a60387aa27bfb6`

---

# Run 1: Wikipedia:Signs of AI writing

## Researcher report: Current content of Wikipedia:Signs of AI writing (WP:AISIGNS) as of 2026-09-30, and what changed since early 2026
Exit reason: saturated
Rounds: 3, searches: 0, pages read: 12 (2 more fetches failed), backend: websearch (auto mode, no serper key). No searches were run: every read went through Wikipedia's raw and API endpoints.

### Claims
**Page state**
1. The current revision is 1377577399 (2026-09-30 01:51 UTC, 222,070 bytes). It has carried an `{{update|the most recent models}}` banner since 2026-08-07 and is semi-protected. Protection was added on 2026-07-28 after two blankings and again on 2026-09-12. The page had 971 edits after 2026-01-01. Its size went from 131 KB on 2026-01-01 to 142 KB on 2026-03-31 and 238 KB on 2026-06-30, then fell when the comment signs were split out on 2026-07-01. [S1][S2][S7]

**(1) Current structure and every sign**
2. Caveats: AI detection tools; Your detection ability. [S1]
3. Content: Undue emphasis on significance, legacy, and broader trends; Canned emphasis on notability, attribution, and media coverage; Superficial analyses; Promotional and advertisement-like language (subtypes: cultural-heritage reminders, press-release tone); Vague expression of connection or association; Vague attributions and overgeneralization of opinions; Outline-like conclusions about challenges and future prospects; "Awards and recognition" section. [S1]
4. Language and grammar: High density of "AI vocabulary" words; Avoidance of basic copulatives; Negative parallelisms (Not just X, but also Y; Not X, but Y; Y rather than X); Leads treating lists or broad titles as proper nouns; Rule of three. [S1]
5. Style: Title heading; Title case; Headings only containing other headings; Overuse of boldface; Inline-header vertical lists; Overuse of em dashes; Emoji as formatting; Unusual use of tables; Curly quotation marks and apostrophes; Skipping heading levels; Overuse of level 1 headings; Thematic breaks between sections. [S1]
6. Communication intended for the user: Collaborative communication; Disclaimers about knowledge cutoffs, source availability, or recommended usage; Phrasal templates and placeholder text (covers `2025-XX-XX` dates, fields like `INSERT_SOURCE_URL_30`, and "Add if available" infobox comments). [S1]
7. Markup: Use of Markdown; Broken wikitext; Internal formatting and reference markup bugs (subsections for ChatGPT, Gemini, Grok, DeepSeek, Perplexity and Unclassified); Non-existent or out-of-place categories; Non-existent templates. [S1]
8. Citations: Broken external links; Invalid DOI and ISBNs; DOIs that lead to unrelated articles; Book citations without page numbers or URLs; Incorrect or unconventional use of references (includes `↩` footnote marks); `utm_source=`; Named references declared but unused. [S1]
9. Comment-specific indicators is now only a summary that points to WP:AITALKSIGNS. It lists: misquoted policies and made-up shortcuts, transcluded maintenance banners, comments divided into titled sections, claims of effort or policy adherence, requests for critics' input, dismissing concerns as speculation, and urging a focus on content. [S1]
10. Edit summaries: General examples; Canned assurance of adherence to policies and guidelines; "preserved/retained/avoided" procedural statements; Overemphasis on presence or reliability of citations; Overemphasis on parameter and template names; Reference to AfC review. [S1]
11. Miscellaneous: Pronounced shift in writing style (includes English-variety mismatch); "Submission statements" in AfC drafts; Pre-placed maintenance templates; Canned user pages; Permissions gaming; Differences between LLMs; Biases in content (Pro-authoritarian bias). [S1]
12. Signs of human writing: Age of text relative to the ChatGPT launch; Ability to explain one's own editorial choices; Syntax. Historical indicators: Didactic disclaimers (November 2022–2024); Section summaries; Prompt refusal; Abrupt cut offs; Outdated access-date parameters; Lexical diversity/elegant variation. [S1]

**(2) Changes since 2026-01-01**
13. Added by the end of March:
    - Avoidance of basic copulatives (2026-01-08)
    - DOI and book-citation subsections (2026-01-11)
    - Caveats section (January, present by 2026-01-22)
    - Skipping heading levels (by 2026-02-18)
    - Vocabulary era timeline (2026-02-27)
    - Thematic breaks (2026-03-23)
    - Non-existent shortcuts (2026-03-26)

    Removed in the same period:
    - False ranges (2026-03-03, "much more common in human writing than in AI writing")
    - Vague see also sections (2026-03-22, "a weak tell")

    Outdated access-dates moved to Historical indicators on 2026-03-17. [S2][S4]
14. Added April to June:
    - Permissions gaming (2026-04-04)
    - Differences between LLMs (2026-04-16)
    - "robust" in the vocabulary box (April, no citation)
    - Grok `grok_render_citation_card_json` and DeepSeek `【N†Lx-y】` markup (2026-05-12)
    - Human-detection studies in the Caveats (2026-05-28)
    - Syntax under Signs of human writing (2026-06-06)
    - `:::writing` markup (2026-06-13)
    - Gemini `[cite: N]` (about 2026-06-17)
    - The Y rather than X parallelism (2026-06-22)
    - Note that AI em dashes are usually spaced (2026-06-26)

    [S2][S4][S7]
15. Added July to September:
    - Emoji restored to Style (2026-07-04)
    - Detector scores are not valid for G15 deletion (2026-07-05)
    - Canned user pages (2026-07-13)
    - Markup bugs split per vendor, plus Gemini `[span_N](start_span)` (2026-07-17)
    - Edit summaries section (from 2026-07-19)
    - Perplexity `ppl-ai-file-upload` (by 2026-07-30)
    - Pangram named as a detector (2026-08-02)
    - "deep dive" and the Economist study (2026-08-08)
    - "Awards and recognition" (2026-08-11)
    - Title heading, headings-only headings and level-1 headings (2026-08-14)
    - Vague connection/association (2026-08-19)
    - Pro-authoritarian bias (2026-08-20)
    - Clarification that the attribution sign (AIATTR) is "narrow and distinct" from press releases (2026-08-27)
    - Note on moving em dashes to Historical (2026-09-02)
    - Markdown tables inside wikitables (2026-09-07)
    - Category markup that drops words (2026-09-21)
    - "was identified by" (2026-09-24)
    - Disclaimers of the form "[claim] should be treated as... rather than..." (2026-09-28)

    [S1][S2][S4][S10]
16. Moved out or demoted after March:
    - Comment signs, including Subject lines and Non-existent shortcuts, moved to WP:AITALKSIGNS (2026-07-01).
    - The "Letter-like writing" ineffective indicator moved there as well (2026-07-19).
    - Elegant variation moved to Historical indicators (2026-08-19), because modern models no longer use a repetition penalty.
    - "as of [date]" was dropped from the cutoff word box.
    - "Gemini 3.0 even uses profanity at times" was dropped from Prompt refusal.

    [S2][S3][S4][S1]
17. Renames:
    - "Undue emphasis on notability..." became "Canned emphasis..." (May).
    - "Sudden shift" became "Pronounced shift" (April).
    - The knowledge-cutoff heading was renamed in September.
    - The lead's description of G15 changed from "LLM-generated pages without human review" to "Unambiguously LLM-generated pages" (2026-09-14).

    [S2][S3][S4][S1]
18. A 2026-01-22 addition calling the page "one big BEANS", made after Wired covered a humanizer plugin built on it, was reverted as itself BEANS. BEANS is Wikipedia shorthand for "don't give people bad ideas". On 2026-04-17 an editor removed a Claude detail as "maybe too BEANS". The page's scope note began as a subsection on 2026-01-23. [S2][S5][S9]

**(3) Caveats**
19. The lead says:
    - The list is "descriptive, not prescriptive".
    - The signs are "only potential signs of a problem, not the problem itself".
    - In bold since 2026-07-04: "Please do not merely treat these signs as the problems to be fixed; that could just make detection harder."
    - LLMs learn from human writing, so these traits also appear in editorials, blogs and fan fiction.
    - The guide is less useful for writing that is not informational.
    - Signs outside G15 are "not sufficient on their own" for speedy deletion.

    [S1][S2]
20. Detectors (GPTZero, Pangram) do better than chance but have "non-trivial error rates". Paraphrasing, markup and spacing changes, or models they were not trained on, can defeat them. [S1]
21. On human detection, the page says "Humans are notoriously bad" at telling LLM text from human text:
    - One 2025 study found people no better than chance.
    - A study of German theses found 57% recognition of AI texts and 64% of human texts.
    - Heavy LLM users are right about 90% of the time, roughly one false positive in ten tags. Light users are near chance.
    - Human writing is converging with LLM style.
    - Writers may adapt their style to avoid accusations.

    [S1]
22. Ineffective indicators: perfect grammar; mixed casual and formal registers; "bland" or "robotic" prose; fancy, academic or formal prose; transition words in isolation; unsourced content; bizarre wikitext; correct wikitext. The section warns that false accusations drive away new editors. [S1]
23. Signs of human writing:
    - Text written before 2022-11-30 cannot be AI (Who Wrote That? or WikiBlame show when text was added).
    - The editor can explain the edit.
    - Human syntax: simple is/has phrases; plain verbs (wrote rather than authored, used rather than utilized, died rather than passed away); superlatives; hedges and intensifiers; wordy constructions such as "in order to" and "the fact that".

    [S1]
24. The page also warns where humans share specific habits:
    - Negative parallelism is common in human "myths busted" listicles.
    - Curly quotes come from Word, macOS and iOS smart quotes, Chicago Manual of Style typesetting, and the Citer tool.
    - Markdown alone is weak evidence, since developers and users of Reddit, Discord, Slack and Google Docs write it.
    - Broken categories are common human mistakes.
    - Low-number PMID citations came from a VisualEditor bug between 2018 and 2023.
    - Not all promotional writing is AI.
    - Edit summaries that break the rigid formula or use abbreviations such as "ce" are unlikely to be AI.
    - Permissions gaming only counts as a sign in one direction.

    [S1]

**(4) Word lists**
25. The AI-vocabulary box lists: Additionally (sentence-initial), align with, boasts (meaning "has"), bolstered, crucial, deep dive, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate/intricacies, key (adjective, marked citation needed), landscape (abstract), meticulous/meticulously, pivotal, robust, showcase, tapestry (abstract), testament, underscore (verb), valuable, vibrant. Only "deep dive" and "robust" are new since March. [S1][S3]
26. The era split has been unchanged since 2026-02-27:
    - 2023 to mid-2024 (GPT-4): Additionally, boasts, bolstered, crucial, delve, emphasizing, enduring, garner, intricate, interplay, key, landscape, meticulous, pivotal, underscore, tapestry, testament, valuable, vibrant.
    - Mid-2024 to mid-2025 (GPT-4o): align with, bolstered, crucial, emphasizing, enhance, enduring, fostering, highlighting, pivotal, showcasing, underscore, vibrant.
    - Mid-2025 onward (GPT-5): emphasizing, enhance, highlighting, showcasing, plus notability and attribution phrasing.

    [S1][S2][S3]
27. Vendor notes and reading rules:
    - Grok overuses causal, empirical and correlate, and still overuses underscore in 2026 (added 2026-06-22).
    - Take the list literally: an overused word does not mean its synonyms are overused.
    - One or two hits may be coincidence; many hits in a post-2022 edit are "one of the strongest tells".
    - A word goes in the box only if a reliable, non-pop-science source corroborates it and it is common on Wikipedia.

    [S1][S2]
28. Other words-to-watch boxes changed since March:
    - Attribution: adds trade publications, cited/featured in, was identified by.
    - Superficial analyses: adds enhancing.
    - Copulatives: adds functions as, operates as, maintains, refers to.
    - Knowledge cutoff: adds "should be treated as... rather than...".
    - New boxes for connection/association and for three edit-summary signs.

    [S1][S3]

**(5) Specific formatting**
29. Em dashes:
    - LLMs use more em dashes than non-professional human writers, in places where people would use commas, parentheses or colons.
    - AI em dashes are usually spaced.
    - The sign works best combined with others and is more common on talk pages than in articles.
    - GPT-5.1 suppresses em dashes.
    - A July 2026 Economist study found that only Claude uses more em dashes than professional writers, and ChatGPT uses fewer.
    - A September 2026 note says the sign should move to Historical indicators unless recent examples turn up.

    [S1]
30. Curly quotes: ChatGPT and DeepSeek typically use curly quotes and apostrophes, sometimes mixed with straight ones. Gemini and Claude typically do not. Curly quotes alone do not prove LLM use. [S1]
31. Title case wording is unchanged: in headings, chatbots "strongly tend to capitalize all main words". Boldface wording is also unchanged, and adds that Markdown bold attempts on user pages are "typically the strongest giveaway". Emoji is now in the past tense ("have used emoji in the past"), mostly on talk pages and in edit summaries, and "more rare now". [S1][S3]
32. Citation-token artifacts by vendor:
    - ChatGPT: `:contentReference[oaicite:N]{index=N}`, `oai_citation`, `Source+N`, PUA-wrapped `citeturn0search0` (first seen February 2025) with image, news and file variants, and `({"attribution":{"attributableIndex":"X-Y"}})`.
    - Gemini: `[cite: N]` and `[span_N](start_span)`.
    - Grok: `grok-card` and `grok_render_citation_card_json`.
    - DeepSeek: `【N†Lx-y】`.
    - Perplexity: `[attached_file:1]`, `[web:1]` and `ppl-ai-file-upload`.
    - Unclassified: `:::writing{variant="document" id=NNNNN}`.

    [S1]
33. Tracking parameters: `utm_source=openai` or `utm_source=chatgpt.com` (ChatGPT), `utm_source=copilot.com` (Copilot), `referrer=grok.com` (Grok); Gemini and Claude add them less often. The page now says these "near-definitively" prove ChatGPT was involved, but not that it wrote the text. [S1]

**(6) Non-English text**
34. There is no non-English section. Scattered guidance:
    - LLMs default to American English, so a variety mismatch can be a sign, but non-native speakers also mix varieties.
    - Non-native writers also avoid repetition; the page gives Italian schooling as an example (added 2026-05-29).
    - Chinese-language responses are more authoritarian than English-language ones.
    - The `:::writing` markup can appear localized, e.g. French `:::écriture{variante=...}`.
    - Stray tags from the Content Translation tool are not an AI sign.

    [S1][S2]
35. On 2026-09-25 a French Wikipedia editor reported on the talk page that trivial facts are increasingly given in-text attribution. A core editor replied that LLM text is "surprisingly similar across languages" and cited arXiv 2502.15603. [S5]
36. Talk context, not page text:
    - One editor's dataset uses model cutoffs of 2024-05-13 (GPT-4o), 2024-12-05 (o1), 2025-08-07 (GPT-5) and 2025-11-02 (GPT-5.1).
    - The signs most typical of newer AI text are itemized coverage, edit-summary templates, and the absence of human syntax markers.
    - "delve" is now "basically unheard of".

    [S6][S8]

### Sources read
| id | title | site | date carried | URL | rank |
|---|---|---|---|---|---|
| S1 | Wikipedia:Signs of AI writing, raw wikitext, rev 1377577399 | en.wikipedia.org | 2026-09-30 | https://en.wikipedia.org/w/index.php?title=Wikipedia:Signs_of_AI_writing&action=raw | 1 |
| S2 | Revision history with summaries, 971 revisions (API) | en.wikipedia.org | 2026-01-01 to 2026-09-30 | https://en.wikipedia.org/w/index.php?title=Wikipedia:Signs_of_AI_writing&action=history | 1 |
| S3 | March baseline, rev 1346411633 | en.wikipedia.org | 2026-03-31 | https://en.wikipedia.org/w/index.php?oldid=1346411633 | 1 |
| S4 | Month-end revisions 1330599492, 1340855780, 1351749990, 1357064563, 1361923325, 1366900465, 1372013638 | en.wikipedia.org | 2026-01-01 to 2026-08-29 | https://en.wikipedia.org/w/api.php?action=query&prop=revisions&revids=1330599492%7C1372013638 | 1 |
| S5 | Wikipedia talk:Signs of AI writing | en.wikipedia.org | 2026-08-23 to 2026-09-30 | https://en.wikipedia.org/wiki/Wikipedia_talk:Signs_of_AI_writing | 3 |
| S6 | Talk Archive 6 | en.wikipedia.org | 2026-02-18 to 2026-06-06 | https://en.wikipedia.org/wiki/Wikipedia_talk:Signs_of_AI_writing/Archive_6 | 3 |
| S7 | Talk Archive 7 | en.wikipedia.org | 2026-06 to 2026-07 | https://en.wikipedia.org/wiki/Wikipedia_talk:Signs_of_AI_writing/Archive_7 | 3 |
| S8 | Talk Archive 8 | en.wikipedia.org | 2026-07-17 to 2026-08-23 | https://en.wikipedia.org/wiki/Wikipedia_talk:Signs_of_AI_writing/Archive_8 | 3 |
| S9 | Diff of the Caveats edits | en.wikipedia.org | 2026-01-23 | https://en.wikipedia.org/w/index.php?diff=1334415726&oldid=1334264798 | 1 |
| S10 | Diff adding "Awards and recognition" | en.wikipedia.org | 2026-08-11 | https://en.wikipedia.org/w/index.php?diff=1368836971&oldid=1368757327 | 1 |

All ten sources are one site by design, so independent agreement does not apply. Confidence rests on primary wikitext compared across revisions.

### Contradictions seen
- The page keeps em dashes as a current sign [S1]. On the talk page, some cleanup editors say they no longer look for them, while another says they are "still noticeably overrepresented" [S8]. Unresolved; the September 2026 note on the page reflects this.
- utm_source: March said it "does definitively prove" ChatGPT's involvement [S3]; the current page says "near-definitively" [S1]. The later wording wins.
- Copulatives: March said the sign does not apply to leads [S3]. The current page reports a decline on Wikipedia even when leads are excluded, and adds "refers to" as a lead sign [S1]. The later wording wins.
- An April 2026 talk critique proposed cutting the vocabulary, rule of three, elegant variation and historical sections [S6]. All were kept; elegant variation was demoted for a different reason [S1][S2].

### Open threads
- WP:AITALKSIGNS (Wikipedia:Signs of AI use in comments) was not read because it is outside the boundary. It now holds Subject lines, Non-existent shortcuts and the letter-like writing indicator.
- Talk proposals not on the page as of 2026-09-30 [S5][S7][S8]:
  - inanimate subjects doing the action with no human actor named
  - "process narration" (text describing how it was researched)
  - summary-shaped headings
  - codes used as if they were names
  - "while maintaining/preserving" constructions
  - Unicode thin and zero-width spaces
  - pasted line breaks
  - citation style consistent within each article but different across one user's articles
  - "Major/comprehensive X:" edit-summary preambles
- Talk archives 1 to 5 (before February 2026) were not read.
- Local copies for a mechanical diff:
  - C:/Users/alfio/AppData/Local/Temp/claude/D--Projects-daodan/f04ae3f0-3990-49d0-9b7c-ddfd40b5e3bc/scratchpad/current.wikitext
  - C:/Users/alfio/AppData/Local/Temp/claude/D--Projects-daodan/f04ae3f0-3990-49d0-9b7c-ddfd40b5e3bc/scratchpad/march31.wikitext
  - C:/Users/alfio/AppData/Local/Temp/claude/D--Projects-daodan/f04ae3f0-3990-49d0-9b7c-ddfd40b5e3bc/scratchpad/matrix.txt (headings present in each month)
  - C:/Users/alfio/AppData/Local/Temp/claude/D--Projects-daodan/f04ae3f0-3990-49d0-9b7c-ddfd40b5e3bc/scratchpad/wtw.txt (word boxes, March vs current)
  - C:/Users/alfio/AppData/Local/Temp/claude/D--Projects-daodan/f04ae3f0-3990-49d0-9b7c-ddfd40b5e3bc/scratchpad/allsummaries.txt (all edit summaries)

### Searched and not found
- The Economist, "How to spot AI writing" (2026-07-30), the page's only source for em-dash rates by model: WebFetch refused the domain and webfetch.py returned "failed to fetch URL". The claim is unverified beyond the page's own citation.

# Run 2: blader/humanizer, forks and peers

## Researcher report: blader/humanizer and its forks and peers, as of September 2026
Exit reason: budget-exhausted (14 of 14 pages, 4 of 4 rounds)
Rounds: 4, searches: 11 (1 WebSearch, 10 GitHub repo searches), pages read: 14 (I counted each GitHub API batch as one page per repository or issue set), backend: websearch, with the `gh` CLI used for GitHub reads

### Claims
**(1) License**
1. The repo is MIT. Its LICENSE reads "MIT License" and "Copyright (c) 2025 Siqi Chen", and the SKILL.md frontmatter declares `license: MIT` [S2][S5].
2. The repo launched without a LICENSE file. mvanhorn contributed one on 2026-03-11 and it was merged on 2026-03-20 (PR #58), resolving issue #7 from 2026-01-22. The repo itself was created on 2026-01-18 [S4][S7][S1].
3. Derivatives handle that line differently. humanizer-de's LICENSE keeps "Copyright (c) 2025 Siqi Chen (portions derived from blader/humanizer)" [S12]. Humanizer-zh's LICENSE names only "Copyright (c) 2026 歸藏", although its README credits blader/humanizer v3.0.0 [S11].
4. The German and Italian derivatives put their pattern catalogs under CC BY-SA 4.0 because Wikipedia's source page is CC BY-SA. blader/humanizer ships under MIT only [S12][S13][S2].

**(2) Version and changes since March 2026.** The CHANGELOG has no dates. I mapped each version to a date by matching it to commit titles.
5. The current version is 3.1.0 (`metadata.version`, and the top CHANGELOG entry). The last commit is 225a6f3 on 2026-09-28. On 2026-09-30 the repo had 52,968 stars and 4,224 forks [S5][S3][S4][S1].
6. The "24 patterns" description is out of date. The pattern count went: 24 (January), 25 (2026-03-20, v2.3.0, hyphenated pairs), 28-29 (2026-04-01, v2.5.x), 30 (2026-05-27, v2.7.0), 33 (2026-06-07, v2.8.0), 35 (2026-08-17, v2.10.0), 25 (2026-09-06, v3.0.0), 26 (2026-09-28, v3.1.0) [S3][S4].
7. The current catalog has 26 patterns in six sections [S5]:
   - **A. Staging instead of stating:** 1 Not X but Y; 2 One-line closers and dramatic fragments; 3 Sayings that sound deep; 4 Staged run-up before the point; 5 Arguing with no one
   - **B. Rhythm by rule:** 6 Forced triads; 7 Repeated sentence openings; 8 Dashes as the universal connector; 9 Stacked qualifiers; 10 Hyphenated pairs everywhere; 11 Passive voice and missing subjects
   - **C. Inflation and borrowed authority:** 12 Overused AI words; 13 Inflated significance; 14 Vague connection or association; 15 Shallow -ing riders; 16 Sales language; 17 Borrowed authority; 18 Avoiding is, are, and has
   - **D. Formatting by rule:** 19 Bold as decoration; 20 Decorative headings; 21 Curly quotation marks
   - **E. Leftovers from the chat and the draft:** 22 Chatbot residue; 23 Knowledge-limit disclaimers and guesses; 24 A heading repeated in the first sentence; 25 Writing about the document instead of its subject
   - **F. Writing for the wrong reader:** 26 Re-explaining what the reader knows
8. The process is now four steps [S5]:
   1. Mark the tells, strongest first. Patterns §1-5 justify an edit on one sighting. Patterns marked "weak alone" need other tells nearby.
   2. Draft while keeping every supported claim, and add no fact, name, number, date, quote or citation. Fiction is exempt.
   3. Check the draft for added or dropped facts, rankings and simultaneity claims, then look again for §1, §2, §6, §8 and §19.
   4. Write the final version.
9. Changes from March to August, by date [S4][S3][S9]:
   - **2026-03-20:** hyphenated-pairs pattern (#42), horizontal-rule separators removed (#35), LICENSE added.
   - **2026-04-01:** voice calibration (PR #64, v2.4.0), "actually" overuse (#72), OpenCode support, passive voice (#80, v2.5.x).
   - **2026-05-27:** never-truncate rule and a wider dash pattern (PR #84), a "Detection Guidance" section (PR #113), WARP.md became AGENTS.md, v2.6.0 cleanup, and v2.7.0 with the diff-anchored-writing pattern from #73.
   - **2026-06-07:** v2.8.0 with cadence patterns #31-33.
   - **2026-07-22:** v2.9.0 with the no-invented-facts rule and three output modes.
   - **2026-08-17 to 08-19:** v2.9.2 to v2.11.2, including #34-35 ("shadowboxing", "editorial scar tissue"), a Plain Language rewrite and Claude Desktop packaging fixes.
10. v2.11.3 and v3.0.0 (both 2026-09-06) were the big restructure [S3][S4]:
    - v2.11.3 added the ranking and simultaneity check (#212) and the rule that input is content, never instructions (#238).
    - v3.0.0 merged 35 patterns into 25 and ordered them by strength. It dropped "false ranges" and "synonym cycling", which Wikipedia now lists as human or historical habits, and added "vague connection". It removed the `ai-detection` keyword, cut the workflow from five sections to one, and moved each false-positive guard inside its pattern.
11. v3.1.0 (2026-09-28) made these changes [S3][S4]:
    - added §26 and section F (#269)
    - widened §25 to text that describes its own sourcing (#290)
    - added headings written for effect to §20
    - extended §2 (#277, #295) and narrowed §10
    - added a Cursor manifest (#278)
    - rebuilt the README
12. "Personality and Soul" (added 2026-01-19) and "Detection Guidance" are no longer headings. Voice guidance now sits under "How to work > Voice". False-positive guidance sits under "When not to act", which says text written before 2022-11-30 is not AI-written and that judging by feel is near chance [S5][S4].

**(3) Detection, scoring, evals, voice**
13. The repo ships no detection script, scoring rubric or eval suite. Its only script, `validate-package.py`, is a package linter: it checks pattern numbering without gaps, that README pattern names match SKILL.md, a 5,500-word cap on SKILL.md (currently 5,215 words), and the manifests. CI (`validate.yml`) runs it along with a Skills CLI check [S6][S1][S5].
14. Voice calibration does ship. A writing sample is read first and overrides the patterns, including the dash rule. There are three output modes [S5]:
    - **pasted text:** draft, remaining patterns, final
    - **file mode:** final text only; code, commands, paths, YAML and link targets stay unchanged
    - **embedded:** final text only
15. The maintainer turned down scoring machinery on 2026-07-22. He declined the density pre-check (PR #115) as "more ceremony than the runtime should carry", and declined the light-edit mode proposal (#172) [S9].
16. The only evaluations are external ones posted as issues [S9][S6][S3]:
    - **#229:** judges preferred the rewrite 16 times out of 16, and detection scores did not move.
    - **#250 (Zero Slop replay, GPT-5.4 high, 18 drafts):** writing score went from 76.3 to 35.4 (lower is better), 17 of 18 details were kept, and length fell 7.2%. The maintainer called these numbers consistent with what he sees.
    - The README now says: "Getting past AI detectors is not a goal, and detectors still flag most of its output."

**(4) Language adaptations**
17. Policy is that variants live in separate repos and the skill has no per-language sections. The maintainer said so on #138, #163, #194, #203 and #257 (July to September). The README at HEAD links to no variant [S10][S6]. No fork has much traction: the most-starred one, jooray/humanizer, has 51 stars [S8].
18. **Chinese, op7418/Humanizer-zh** (18,753 stars, MIT) [S11]:
    - After the January translation, its only later commit (2026-09-23) rewrote the rules to keep facts, stance and genre, and stopped changing every parallelism, dash and connective by default.
    - It has 31 checkpoints: sections A-E mirror v3.0.0, and F is Chinese-specific (long attributive modifiers, 进行+verb, stacked 被 passives, four-character parallelism, all-purpose background, boilerplate closers).
    - By default it returns only the final text, with no draft, hit list or self-score.
    - It ships 18 test cases and a structure-check script, and says it guarantees nothing against detectors.
19. **Other Chinese variants, described in issues** [S10]:
    - zh-CN (jiji262) reverses the curly-quote rule, because “” is the GB/T 15834-2011 standard, and checks for mixed full-width and half-width punctuation instead. It also softens the dash ban, since —— is correct punctuation.
    - zh-TW (nagameTW) keeps full-width punctuation and uses the 「」『』 quotation marks.
20. **French, ferr079/humanizer-fr** (33 patterns adapted, not translated) [S10]:
    - Reverses the quote tell: « » with non-breaking spaces is normal, so straight or curly quotes become the tell.
    - Redefines Title Case as capitalizing every word of a heading.
    - Adds French tells: "Il est important de noter que", "À l'ère de…", overuse of notamment, par ailleurs and en effet, calques such as "adresser un problème", and "N'hésitez pas à…".
21. **German, marmbiz/humanizer-de** (Martin Moeller) began as a blader fork and is now independent at v5.28.0 (2026-09-24) [S12]:
    - 72 patterns, based on German Wikipedia's "Anzeichen für KI-generierte Inhalte" as well as the English page. Local scripts check 19 of them deterministically.
    - Targets mechanical connectors such as "Darüber hinaus", Nominalstil and anglicism verbs.
    - Three modes (Locker, Sachlich, Formal), voice calibration and optional LanguageTool. Explicitly not a detector-bypass tool.
22. **Italian:** I found no blader fork. hypnosdesign/claude-skill-scrittura-italiana (v2.19.2, 2026-09-25, CC BY-SA) is an editorial skill with a humanize action, and its README does not mention blader/humanizer [S13]:
    - Targets perifrasi, gerundite, triads, -mente adverbs, long dashes, antilingua and empty closers.
    - Its typography rules (caporali vs straight quotes, trattino vs lineetta) are relaxed for informal text.
    - Ships a 66-case eval (60 development cases, 6 held out) and 48 deterministic tests.
23. **Spanish** [S10][S14]:
    - The adelaidasofia fork (#92) adds Spanish connectors ("cabe destacar"), openers ("En la era de"), promotional words, copula avoidance ("se erige como") and protection for code-switching. It was never merged upstream.
    - Hainrixz/humanizalo is an independent skill: MIT, 40 patterns, no commits since 2026-03-22. Its Spanish side is a translated README. It self-audits up to 3 times and scores six qualities, with a 42/60 threshold.

**(5) Criticisms**
24. The most frequent complaint is that it does not beat AI detectors: GPTZero (#2), Turnitin (#252), Pangram (#263), and #82, which argues prompts cannot beat perplexity-based detectors. The maintainer's answer is that detector scores are not a success criterion [S9][S7].
25. On invented details: #187 (2026-07-21) showed the skill's own examples inventing facts, including an NYT interview, a 2019 CAS survey and Lisbon trip details. v2.9.0 (2026-07-22) added the no-invention rule [S9][S3].
26. That fix is incomplete. #306 (2026-09-29) lists three 3.1.0 examples that still add or change facts:
    - §12 adds "considered a delicacy" and "especially in the south".
    - §18 turns "over 3,000" into "totaling 3,000".
    - §25 invents "Two vendors publish nothing".

    The issue's author closed it the same day as "not planned", with no fix, and all three examples are still in SKILL.md at HEAD [S9][S5][S4].
27. On lost information: truncation (#78) led to PR #84. #212, filed on a technical recommendation document, showed triad and hedging edits dropping rankings; 3.0.0 fixed it [S9].
28. On over-correction: #93, #172 and #146 say it strips voice from human text and produces clipped fragments in transactional emails. All three were declined on 2026-07-22 [S9].
29. On technical documentation: #73 (diff-anchored docs) became pattern #30, now §25. SKILL.md keeps technical text "neutral and plain", allows technical uses of "gate", and leaves inline code out of the dash rule. #238 (file mode writing without guards) was addressed in v2.11.3 [S9][S5][S3][S7].

### Sources read
| id | title | site | date carried | URL | rank |
|---|---|---|---|---|---|
| S1 | Repo metadata and root tree (API) | github.com | pushed 2026-09-28 | https://github.com/blader/humanizer | 1 |
| S2 | LICENSE | github.com | undated | https://github.com/blader/humanizer/blob/main/LICENSE | 1 |
| S3 | CHANGELOG.md | github.com | undated (to 3.1.0) | https://github.com/blader/humanizer/blob/main/CHANGELOG.md | 1 |
| S4 | Commit history | github.com | 2026-01-18 to 2026-09-28 | https://github.com/blader/humanizer/commits/main | 1 |
| S5 | SKILL.md at HEAD 225a6f3 | github.com | v3.1.0 | https://github.com/blader/humanizer/blob/main/SKILL.md | 1 |
| S6 | README, validate-package.py, validate.yml, openai.yaml | github.com | HEAD 2026-09-28 | https://github.com/blader/humanizer/blob/main/README.md | 1 |
| S7 | Issue list, all states | github.com | 2026-01-19 to 2026-09-29 | https://github.com/blader/humanizer/issues?q=is%3Aissue | 3 |
| S8 | Forks sorted by stars (API) | github.com | 2026-09-30 | https://github.com/blader/humanizer/forks | 3 |
| S9 | Issues #2, 73, 78, 82, 93, 146, 172, 187, 212, 229, 250, 263, 306 | github.com | per issue | https://github.com/blader/humanizer/issues/306 | 3 |
| S10 | Issues #92, 138, 163, 194, 203, 257 | github.com | 2026-04-13 to 2026-09-06 | https://github.com/blader/humanizer/issues/163 | 3 |
| S11 | op7418/Humanizer-zh README, LICENSE, commits | github.com | 2026-09-23 | https://github.com/op7418/Humanizer-zh | 1 |
| S12 | marmbiz/humanizer-de README, LICENSE, commits | github.com | 2026-09-24 | https://github.com/marmbiz/humanizer-de | 1 |
| S13 | hypnosdesign/claude-skill-scrittura-italiana README, LICENSE | github.com | 2026-09-25 | https://github.com/hypnosdesign/claude-skill-scrittura-italiana | 1 |
| S14 | Hainrixz/humanizalo README, LICENSE | github.com | 2026-03-22 | https://github.com/Hainrixz/humanizalo | 1 |

### Contradictions seen
- The LICENSE says "Copyright (c) 2025" [S2], but the repo was created on 2026-01-18 [S1] and the file was added by a contributor on 2026-03-11 [S4]. This is unresolved; the 2025 date may reflect when the skill was written, before it was published.
- CHANGELOG 2.9.0 says it "updated every example" [S3], but #306 shows three examples that still add facts [S9]. I checked HEAD and #306 is right [S5].
- In #194 and #203 (2026-08-17) the maintainer said he was "not maintaining a one-off adaptation directory in the core README". In #257 (2026-09-06) he said "the README can link to it" [S10]. The README at HEAD links nothing [S6], so the later, softer position has not been acted on.

### Open threads
- The Wikipedia source is CC BY-SA 4.0 and blader/humanizer is MIT. I did not look into whether that is compatible; it is a legal question outside this scope.
- Repos I found but did not read, with GitHub search metadata only:
  - Korean: epoko77-ai/im-not-ai (5,797 stars)
  - Traditional Chinese: Raymondhou0917/speak-human-tw (1,011)
  - Russian: ilyautov/humanizer-ru (398)
  - Other languages: Japanese makotofalcon/humanizer-ja; Portuguese waldyrfelix/humanizer-pt_BR; Polish pielas-activy/humanizer-pl; Hungarian Dexxter182/humanizer-hu; multilingual devswha/patina
  - French: alxbd/boileau and L4inLov3r/malherbe (84 patterns)
  - Peers: Nanako0129/sepia (2,916), AIScientists-Dev/academic-humanizer (1,741), Aboudjem/humanizer-skill (0-100 score), seyedehsanhadi/sloptrim, hardikpandya/stop-slop, manavmishra/ZeroSlop
- The French and Spanish fork contents come from their authors' issue posts; I did not read the repos themselves. I also did not read #260 (the measurement protocol) or check the tags and releases.

### Searched and not found
- An Italian fork of blader/humanizer: "humanizer italiano" and "humanizer-it" found only the independent hypnosdesign skill, and "umanizzare testo AI skill" returned nothing.
- "humanizer deutsch", "humanizer español" and "humanizer français" all returned nothing.
- The WebSearch results were aggregator and SEO pages (nevercodealone.de, agentpedia.codes, agentskill.work). I did not read them.

# Run 3: non-English tells and corpus evidence

## Researcher report: markers of LLM-generated prose beyond the English Wikipedia list (A: tells and typography to preserve in IT, FR, DE and ES; B: corpus studies 2024-2026 and false positives)
Exit reason: budget-exhausted
Rounds: 4, searches: 18, pages read: 16, backend: websearch (no serper key; `--check-key` exited 2)

How the numbers were checked: numbers taken from HTML pages (S1, S2, S4, S5, S6, S10, S12, S14) come from WebFetch's extraction model. Every PDF claim (S3, S7, S8, S9, S13) and S11 was checked against text I extracted myself. I did that because WebFetch invented a summary for S9 (see Contradictions).

### Claims

**Part B: corpus studies**
1. Kobak et al. studied 15.1M English PubMed abstracts from 2010 to 2024. They put a lower bound of 13.5% on 2024 abstracts processed with LLMs. That bound reaches Δ≈0.41 for computation papers from China and ≈0.34 for South Korea in *Sensors* [S1].
2. The strongest excess style words in 2024 were "delves" (frequency ratio 28.0), "underscores" (13.8) and "showcasing" (10.7). Among common words, the excess frequency gap was 0.052 for "potential", 0.041 for "findings" and 0.037 for "crucial" [S1].
3. In 2024, 66% of the excess words were verbs and 14% were adjectives. Earlier excess vocabulary, from the Covid period, was 79.2% nouns. So the LLM signal is in style words, not topic words [S1].
4. On a separate corpus (medRxiv abstracts, 2020-2025), Kobak's eight strongest style words all rose after ChatGPT: delve, groundbreaking, underscore, intricate, meticulously, garner, showcase, leverage. Odds ratios ran from 2.33 ("leverage") to 14.17 ("delve"), with a composite OR of 4.05 [S3][S1].
5. That study's pre-registered marker list had been drafted with LLM help, and 2 of its 8 words ("boast", "underpinning") were not on Kobak's list. A human check against the source caught the error [S3].
6. "Delve" and similar words fell in arXiv abstracts soon after they were publicized in early 2024, while "significant" kept rising [S6].
7. Kobak's method cannot tell direct LLM use apart from humans adopting LLM-preferred words, and it misses abstracts that contain no marker words [S1].
8. **Em dash.** A pre-registered study covered 69,632 medRxiv preprints. The share of Discussion sections containing at least one U+2014 rose from 4.23% before 30 Nov 2022 to 11.58% after (+7.35 pp; OR 2.96). By year it was about 4% through 2023, 8.03% in 2024 and 20.30% in 2025. It reached 23.5% in Q3 2025 and 20.89% in January to April 2026 [S3].
9. The increase was a delayed acceleration, not a jump at ChatGPT's release. Placebo sections hardly moved (Acknowledgments went from 0.22% to 0.46%). In 2025, preprints that declared AI use had em dashes in 32.1% of Discussions, against 19.9% for the rest [S3].
10. PubMed normalizes typography: typographic punctuation survives in only about 0.6% of its abstracts. Em-dash counts therefore need sources that keep the author's original characters [S3].
11. Twelve models were measured in March 2026, in em dashes per 1,000 words. The range ran from 0.00 (Llama 3.1 8B and 3.3 70B) to 10.62 (GPT-4.1). Claude Opus 4.6 scored 9.09, DeepSeek V3 6.95, GPT-4o 4.12, Gemini 2.5 Pro 3.53 and GPT-5.4 1.43. The human mean was 3.23 (range 0.33 to 17.12), taken from 8 essays totalling 57,232 words [S2].
12. When told to avoid markdown, every model dropped headers, bullets and bold. Em dashes persisted in some models (GPT-4.1 at 9.10/1K, DeepSeek V3 at 5.41/1K) and nearly vanished in others (Claude Opus 4.6 at 0.19, Gemini 2.5 Pro at 0.00). Even an explicit "do not use em dashes" left GPT-4.1 at 3.86/1K in long-form output [S2].
13. **Structure.** Reinhart et al. used parallel human and LLM corpora (HAP-E, 8,290 texts in six genres; CAP, 9,615 texts). Compared with human text, GPT-4o used:
    - present participial clauses at 5.3 times the rate
    - nominalizations at 2.1 times
    - "that" clauses as subjects at 2.6 times
    - phrasal coordination at 1.9 times
    - agentless passives at about half the rate [S5]
14. Instruction tuning made output less human-like. Llama 3 base models used these features at human rates, while GPT-4o and instruction-tuned Llama drifted away. The two model families also moved in opposite directions on clausal coordination and on downtoners [S5]. Em-dash rates likewise follow the fine-tuning procedure [S2].
15. Antislop (Oct 2025) profiles each model's repetitive phrasing against human baselines. It reports patterns that appear more than 1,000 times as often in LLM output as in human text, and its sampler suppresses over 8,000 patterns [S4].
16. **Negative parallelism.** Italian fiction written by four LLMs (June 2025) was full of symmetric "non X, ma Y" and "non solo X, ma anche Y" structures, such as «non solo muri e pavimenti, ma anche possibilità». The stories also repeated keywords in a loop from opening to close [S8]. I found no quantitative academic measurement of this construction.
17. **False positives.** An em dash "decides nothing about any single manuscript." In 2025, the 57 papers that explicitly declared no AI use had em dashes in 24.6% of Discussions, no lower than the roughly 20% baseline [S3]. Human writers also vary 50-fold in how often they use the em dash [S2].
18. **Non-native writers.** Kobak's lower bound for LLM use was about 0.20 for authors from China, South Korea and Taiwan, against 0.05 for the UK and Australia. The authors suggest native speakers are better at spotting and deleting unnatural style words, which would hide their own use [S1][S7].
19. One line on detectors: GPT detectors consistently misclassified non-native English writing as AI-generated while classifying native samples correctly. The authors say this penalizes "constrained linguistic expressions" [S14].
20. A German university writing centre says AI use in a text generally cannot be proven. It recommends grading the text's quality instead of trying to establish where it came from [S9].

**Part A: tells in other languages**
21. A 34-language study compared GPT-4.1-mini news continuations with human news text. Emphasize-type verbs were AI-overused in 24 of the 34 languages [S7]:
    - German: betonen, hervorheben
    - Spanish: enfatizar, destacar, subrayar, realzar
    - French: insister, marquer
    - Italian: sottolineare, evidenziare
22. Two more concept groups converged across languages, and the study also tracked care and rigour adjectives [S7]:
    - Importance nouns (20 of 34): German Bedeutung, Notwendigkeit, Dringlichkeit; Spanish importancia; French importance, nécessité; Italian importanza.
    - Innovation adjectives (18 of 34): German innovativ, modern; Spanish innovador; French innovant; Italian innovativo.
    - Care and rigour adjectives tracked: German sorgfältig and präzise, Spanish impecable, Italian mirato.
23. Each language's top-20 AI words rose in 26 of 34 languages between 2020-21 and 2023-24. The mean change was +15.1%, against −4.5% for matched baseline words; German rose 70.8%. The effects are smaller than in scientific English, and the rise started before ChatGPT [S7].
24. Italian tests of ChatGPT, Copilot, Gemini and Claude ran from Nov 2023 to Jun 2025. By the end, grammatical slips and interference from English had largely disappeared [S8].
25. Italian tells documented in those tests [S8]:
    - the fashionable anglicizing verb "impattare"
    - "valido" used for "corretto"
    - an inflated register: "vi" for "ci", "coloro che", "riveste un ruolo fondamentale", "entità dinamiche in continua evoluzione"
    - "È cruciale che"
    - a closing "In conclusione"
    - key terms in bold
    - restating the key elements of the question
26. When asked to write an Italian social-media post, ChatGPT, Copilot and Claude used roughly one emoji per line. They ended with at least five hashtags, at least one of them in English [S8].
27. German academic prose (Konstanz, Aug 2024) shows these signs [S9]:
    - adjectives that are unusual in kind and number for academic text
    - switching between present and preterite tense
    - doubled sentence structures
    - a paragraph that seems to close the text, followed by a new idea
    - exaggeration and subjective claims
    - arguments listed without weighting, often numbered ("erstens, zweitens")
    - the same idea coming back several times
28. The same guide says AI-drafted German papers cite few sources. Those sources are open access, come from many disciplines and are often translated from English [S9].

**Part A: typography a rewriter must keep**
29. French, as set by the OQLF in Québec (2024) [S10]:
    - a non-breaking space before the colon and before %
    - a non-breaking space inside guillemets, after « and before »
    - no space before ; ! ? (the OQLF's choice), though a thin space is also accepted
30. For the French parenthetical dash (tiret), the OQLF puts a normal space before the opening dash and a non-breaking space after it. The closing dash takes a non-breaking space before it [S10].
31. Spanish, per the RAE's DPD [S11]:
    - the raya is a different sign from the hyphen and the minus sign
    - paired rayas around an aside sit tight against the enclosed words, with spaces outside them
    - the closing raya stays even at the end of a sentence
32. In Spanish dialogue, a raya opens each speaker's turn with no space after it. Rayas frame the narrator's comments, and punctuation goes after the closing raya. A raya followed by a space also introduces list items [S11].
33. German, per Duden rules D 9 to D 12 [S12]:
    - quotation marks are „…", and other forms such as »…« are common in print
    - nested quotes use half marks
    - the comma always follows the closing quote mark
    - ? and ! go inside the quote only when they belong to it

    The German guide in S9 sets its own asides with spaced en dashes: "generative KI – auch unerlaubt – für" [S9].
34. The Accademia della Crusca's own journal norms [S13]:
    - short quotations go in “…”
    - nested quotes take the form « “…” »
    - meanings go in ‘…’
    - the full stop always comes after the closing quote mark

### Sources read
| id | title | site | date carried | URL | rank |
|---|---|---|---|---|---|
| S1 | Kobak et al., Delving into LLM-assisted writing… excess vocabulary (Sci. Adv. 11(27)) | arxiv.org | 2025-07-03 (v5) | https://arxiv.org/html/2406.07016v5 | 1 |
| S2 | Freeburg, The Last Fingerprint: How Markdown Training Shapes LLM Prose | arxiv.org | 2026-03 | https://arxiv.org/html/2603.27006 | 2 |
| S3 | Czuma, Em-ergence of the em-dash… medRxiv preprints | arxiv.org | 2026-06 (corpus pulled 2026-05-26) | https://arxiv.org/pdf/2606.29540 | 2 |
| S4 | Paech et al., Antislop | arxiv.org | 2025-10-16 | https://arxiv.org/abs/2510.15061 | 2 |
| S5 | Reinhart et al., Do LLMs write like humans? (PNAS 122; abstract page also read) | arxiv.org | 2025-08-21 (v2) | https://arxiv.org/html/2410.16107v2 | 1 |
| S6 | Geng & Trotta, Human-LLM Coevolution: Evidence from Academic Writing | arxiv.org | 2025-02-13 | https://arxiv.org/abs/2502.09606 | 2 |
| S7 | Juzek, AI-Associated Lexical Shifts Across 34 Languages | arxiv.org | 2026-05-25 | https://arxiv.org/pdf/2605.25358 | 2 |
| S8 | Antonelli, Storia brevissima (ma molto intensa) dell'IA-taliano, LCdM 9(1) | riviste.unimi.it | 2025-07-31 | https://riviste.unimi.it/index.php/LCdM/article/download/29341/24571/85920 | 1 |
| S9 | Everke Buchanan, Typische Schwächen KI-generierter Texte (Schreibzentrum Konstanz) | academicintegrity.eu | 2024-08 | https://academicintegrity.eu/materials/public/uploads/361/Typische_Schwaechen_KI_Texte.pdf | 3 |
| S10 | OQLF, Espacement avant et après les signes de ponctuation | vitrinelinguistique.oqlf.gouv.qc.ca | 2024 | https://vitrinelinguistique.oqlf.gouv.qc.ca/22039/la-typographie/espacement/espacement-avant-et-apres-les-signes-de-ponctuation-et-les-symboles | 1 |
| S11 | RAE, DPD 2.ª ed., raya | rae.es | undated | https://www.rae.es/dpd/raya | 1 |
| S12 | Duden, Anführungszeichen | duden.de | undated | https://www.duden.de/sprachwissen/rechtschreibregeln/anfuehrungszeichen | 1 |
| S13 | Accademia della Crusca, Italiano digitale: Norme editoriali | accademiadellacrusca.it | 2017 | https://accademiadellacrusca.it/sites/www.accademiadellacrusca.it/files/page/2017/08/10/norme_editoriali_italiano_digitale.pdf | 1 |
| S14 | Liang et al., GPT detectors are biased against non-native English writers (Patterns) | arxiv.org | 2023-07-10 | https://arxiv.org/abs/2304.02819 | 1 |

Ranks: 1 means an official language-authority norm or a peer-reviewed primary study, 2 an arXiv preprint primary study, 3 an institutional handout. The arXiv papers come from independent author groups, and I treated them as independent sources.

### Contradictions seen
- **WebFetch's summary of S9 vs the text of S9.** The summary credited S9 with the connectors "allerdings", "insbesondere" and "darüber hinaus", frequent Gedankenstriche, and "Content" as an anglicism. None of these appear in the two-page document. The text wins, so those German tells have no source in this report.
- **Why models overuse the em dash: S2 vs S3.** S2 blames markdown in the training data, amplified by fine-tuning. S3 suggests edited professional prose in training and rewards for setting ideas apart. This is unresolved. S2 has model-level data showing that fine-tuning sets the rate.
- **Human baseline: S2 vs S3.** S2's 8 essayists average 3.23 em dashes per 1,000 words. In S3, only about 4% of scientific Discussion sections from before 2023 contain any em dash at all. The baseline depends heavily on genre, and S3's sample is far larger.
- **Human uptake: S6 vs S7.** S6 finds that publicized markers decline, while S7 finds AI words amplifying trends that were already under way. The two fit together: writers consciously avoid only the words that have been flagged.

### Open threads
- **Quantitative "not X but Y".** The Atlantic (Will Oremus, July 2026, "The Most Famous AI Writing Tic Is Also the Most Mysterious") reportedly cites two counts. Barron's found the construction in Fortune 500 filings rising from 50 in 2023 to more than 200 in 2025. A Washington Post dataset showed it in about 6% of July messages. I saw these only through the aiweekly.co aggregator and a scraped mirror, and found no primary URL.
- **French and Spanish phrase calques** ("plonger dans", "il est important de noter", "captivant"; "adentrarse", "explorar") appear only in press snippets (journaldunet.com, lebigdata.fr, enter.co, latercera.com). I found no corpus study.
- **German phrase list** from t3n.de ("Tauchen wir ein", "In der heutigen Zeit", "integraler Bestandteil", "nicht nur…, sondern auch") is unread.
- **Sentence-case titles.** The Spanish rule (capitalize only the first word of a work's title) surfaced on UDEP's "Castellano actual" and on the UCM Ediciones Complutense site; neither was read. I did not search the Italian or French equivalents.
- **French practice in France** (a thin non-breaking space before ; ! ?, per the Imprimerie nationale's Lexique) is unread; the Lexique is print-only. **RAE DPD "comillas"** and **Duden "Gedankenstrich"** are also unread.
- **Surfaced but unread:**
  - Juzek & Ward, COLING 2025, "Why Does ChatGPT 'Delve' So Much?", which attributes overuse to preference tuning (arxiv.org/html/2412.11385v1)
  - Puccetti et al. 2024 on Italian news
  - Yakura et al. 2024 on spoken "delve"
  - arXiv 2609.07447 on Korean
  - arXiv 2512.01560 on prevalence estimates
  - Czuma 2026 on Unicode fidelity in APIs (arXiv 2606.24897)
- **Non-English Wikipedia AI-tell pages** (fr, de, es, it): one search found only press coverage.
- **Liang's TOEFL misclassification percentage** is in the body of the paper, not in the abstract I read.

### Searched and not found
- The arXiv HTML for 2606.29540 returned 404, so I read the PDF instead.
- rae.es returned 403 to WebFetch; I read it with webfetch.py.
- WebFetch could not parse four PDFs (S3, S7, S8, S13). I extracted their text locally with pdftotext; the files are in `C:\Users\alfio\AppData\Local\Temp\claude\D--Projects-daodan\f04ae3f0-3990-49d0-9b7c-ddfd40b5e3bc\scratchpad\`.
- The RILEX article (García Fernández, doi 10.17561/rilex.7.3.9111) was read but is off-target: it covers ChatGPT vocabulary for Spanish B1/B2 teaching, not AI tells.
- Two searches found no academic corpus measurement of "not X but Y".
- I found no Crusca consultation on virgolette basse vs alte, only its editorial norms.
