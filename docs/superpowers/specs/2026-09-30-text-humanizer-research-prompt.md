# text-humanizer September 2026 refresh: the research prompts

Committed as evidence of the 2026-09-30 refresh, per the retention rule in the
`custom-plugin-refresh` skill. These are the exact spawn blocks given to three parallel
`research:deep-researcher` agents, reproduced verbatim below, one per run. Each run's
`Boundaries` line is what kept it off its neighbours' ground, so a source absent from one
report was excluded by instruction, not missed.

sha256 of the body below: `653b9fb0ba33ce142223c36a28f73ab1c6228808570d76c58a948de1fd83fb8a`

---

# Run 1: Wikipedia:Signs of AI writing

Role: researcher
Objective: Establish the current content of the English Wikipedia project page "Wikipedia:Signs of AI writing" (WP:AISIGNS, maintained by WikiProject AI Cleanup) as of September 2026, so an existing 24-pattern humanizer knowledge base written from a March 2026 snapshot can be diffed against it. Report: (1) the page's current section structure and every catalogued sign with its section; (2) signs added or substantially changed since early 2026, with revision dates where visible; (3) the page's explicit caveats: signs it calls unreliable or not signs of AI, its warnings about false positives, about AI detectors, and about human writers who share these habits; (4) its current word lists, including any split of vocabulary by model era or vendor; (5) what it says about em dashes, curly quotation marks, title case, boldface, emoji, and markup artifacts (citation tokens such as oaicite or utm_source=chatgpt.com); (6) any guidance it gives on non-English text.
Boundaries: Only the Wikipedia page, its talk page, its revision history, and pages it cites as its own sources. Do not survey third-party humanizer tools or academic stylometry.
Source families: official/primary (the page itself fetched directly, plus its history and talk page), recency (revision history since 2026-01-01)
Domain hint: Wikipedia project-space guidance on detecting LLM-generated text
Backend: auto
Budget: 12 searches / 14 pages / 4 rounds
Return format: the researcher report

# Run 2: blader/humanizer, forks and peers

Role: researcher
Objective: Establish the current state of the open-source "humanizer" skill at github.com/blader/humanizer (a Claude Code skill listing 24 AI-writing patterns derived from Wikipedia:Signs of AI writing) and its notable forks and peers, as of September 2026. Report: (1) its license and the exact copyright line; (2) its current version and every pattern, section, or process step added, removed or changed since March 2026, with commit dates; (3) any detection script, scoring rubric, eval, or voice-calibration feature it now ships; (4) language adaptations such as op7418/humanizer-zh and any Italian, French, German or Spanish variant, with what each changes for its language; (5) known criticisms or issues filed against it (false positives, fabricated specifics in rewrites, register mismatch with technical documentation).
Boundaries: Open-source humanizer skills and prompts and their repositories. Do not survey commercial AI-detector or "AI humanizer" SaaS products beyond noting that they exist.
Source families: official/primary (the GitHub repositories, their commits, issues and license files), recency (commits and releases since 2026-03-01), community (issues, discussions)
Domain hint: GitHub repositories of Claude Code and agent skills for humanizing AI-generated prose
Backend: auto
Budget: 15 searches / 14 pages / 4 rounds
Return format: the researcher report

# Run 3: non-English tells and corpus evidence

Role: researcher
Objective: Find the best-evidenced markers of LLM-generated prose beyond the English Wikipedia list, in two parts. Part A, non-English: for Italian, French, German and Spanish, the documented lexical tells (overused words and calques of English AI vocabulary), structural tells, and the typographic conventions a rewriting tool must preserve rather than "fix" (native quotation marks such as guillemets and low-high quotes, dialogue dashes, spacing before punctuation in French, sentence-case headings). Part B, empirical studies from 2024 to 2026 that measured LLM stylistic markers in corpora: excess-vocabulary studies (such as Kobak et al. on "delve" in PubMed abstracts), em dash frequency, negative parallelism ("not X but Y"), and newer tells reported for 2025-2026 models; plus what those studies say about false positives on human writing, non-native English writers in particular.
Boundaries: Stylistic and lexical markers of machine-generated prose and how to edit them out. Do not cover watermarking, perplexity-based detector internals, or commercial detector accuracy benchmarks, beyond one line each.
Source families: academic (arXiv, ACL Anthology, journals), official/primary (style guides and language academies for typography: Accademia della Crusca, Duden, Imprimerie nationale, RAE), recency (2025-2026 publications), community (native-speaker editor discussions of AI tells in their language)
Domain hint: computational stylistics of LLM output; multilingual editing and typography
Backend: auto
Budget: 18 searches / 16 pages / 4 rounds
Return format: the researcher report
