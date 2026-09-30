# text-humanizer September 2026 refresh: source verification

Committed as evidence of the 2026-09-30 refresh, per the retention rule in the
`custom-plugin-refresh` skill. One row per claim that ships in a text-humanizer body,
with where it was checked and the verdict. The local texts are the primary copies the
researchers saved: the Wikipedia wikitext of revision 1377577399 with its edit
summaries, and pdftotext extractions of Antonelli, Juzek and the Crusca norms. The
three arXiv numbers were re-read in their raw HTML rather than through a summarizing
fetch. No claim failed, so no `*(verify)*` mark ships.

sha256 of the body below: `3d9d4f0ce5a19f67d948ab9a78d32bd7bff7503392bcb2241ac754a288585cbc`

---

| # | Claim | Ships in | Source | Checked against | Verdict |
|---|---|---|---|---|---|
| 1 | Page revision 1377577399 is the one read, and the head on 2026-09-30 | SKILL.md attribution comment, Reference | Wikipedia API | `action=query&prop=revisions`: revid 1377577399, 2026-09-30T01:51:09Z | confirmed |
| 2 | Signs are "only potential signs of a problem, not the problem itself"; do not merely treat them as problems to fix | SKILL.md intro, Reference | Wikipedia rev 1377577399 | local wikitext line 10 | confirmed |
| 3 | LLM output "tends toward the most statistically likely result that applies to the widest variety of cases" | SKILL.md Reference | Wikipedia rev 1377577399 | local wikitext line 34 | confirmed (the quote is now exact; 1.1.0 carried a paraphrase in quotation marks) |
| 4 | Humans are poor judges, often near chance | SKILL.md When not to act | Wikipedia rev 1377577399 | local wikitext line 23 ("Humans are notoriously bad") and researcher report R1 claim 21 | confirmed |
| 5 | Ineffective indicators: perfect grammar, formal prose, mixed register, bland prose, isolated transitions, unsourced content | SKILL.md When not to act | Wikipedia rev 1377577399 | local wikitext lines 1817-1825 | confirmed |
| 6 | "in order to" and "the fact that" are signs of human writing | SKILL.md When not to act, pattern 22 | Wikipedia rev 1377577399 | local wikitext line 1814 | confirmed |
| 7 | Text written before 30 November 2022 cannot be AI | SKILL.md When not to act | Wikipedia rev 1377577399 | researcher report R1 claim 23 | confirmed by the researcher on the page; not re-read line by line |
| 8 | False ranges removed in March 2026 as more common in human writing | SKILL.md pattern 12 | Wikipedia history | edit summary 2026-03-03T02:12, rev 1341406870 | confirmed |
| 9 | Elegant variation moved to historical indicators in August 2026 because models no longer need a repetition penalty | SKILL.md pattern 11 | Wikipedia history and page | edit summaries 2026-08-18 and 2026-08-19, revs 1370067129 and 1370086238; wikitext line 1896 | confirmed |
| 10 | Italian schools teach writers to avoid repetition | SKILL.md pattern 11, italiano.md | Wikipedia rev 1377577399 | local wikitext line 1914 | confirmed |
| 11 | Curly quotes: ChatGPT and DeepSeek use them, Gemini and Claude typically do not; Word smart quotes and Chicago typesetting produce them | SKILL.md pattern 18 | Wikipedia rev 1377577399 | local wikitext lines 846-852 | confirmed |
| 12 | Emoji are rarer in current AI output | SKILL.md pattern 17 | Wikipedia rev 1377577399 | local wikitext line 710 ("they are more rare now") | confirmed |
| 13 | AI em dashes are usually surrounded by spaces | SKILL.md pattern 13 | Wikipedia rev 1377577399 | local wikitext line 675 | confirmed |
| 14 | AI vocabulary additions (deep dive, robust, meticulous, bolstered, boasts) and the era split | SKILL.md pattern 7 | Wikipedia rev 1377577399 | local wikitext lines 354-362 | confirmed |
| 15 | Copula additions: functions as, operates as, maintains, refers to | SKILL.md pattern 8 | Wikipedia rev 1377577399 | local wikitext lines 402 and 408 | confirmed |
| 16 | Vague connection words: in connection with, connected with/to, in association with, associated with | SKILL.md pattern 5 | Wikipedia rev 1377577399 | local wikitext line 224 | confirmed |
| 17 | "Y rather than X"; thematic breaks; headings containing only headings | SKILL.md patterns 9 and 16 | Wikipedia rev 1377577399 | local wikitext lines 485, 887, 553 | confirmed |
| 18 | Citation tokens per vendor and the tracking parameters utm_source=openai, utm_source=chatgpt.com, utm_source=copilot.com, referrer=grok.com | SKILL.md pattern 19 | Wikipedia rev 1377577399 | local wikitext lines 1217-1300 and 1528-1542; token list as in researcher report R1 claim 32 | confirmed |
| 19 | Placeholders 2025-XX-XX, INSERT_SOURCE_URL, "Add if available" | SKILL.md pattern 19 | Wikipedia rev 1377577399 | local wikitext lines 1119-1158 | confirmed |
| 20 | Disclaimer "should be treated as... rather than..." | SKILL.md pattern 20 | Wikipedia rev 1377577399 | local wikitext lines 1041-1048 | confirmed |
| 21 | Canned attribution words: trade publications, cited/featured in, was identified by | SKILL.md pattern 2 | Wikipedia rev 1377577399 | researcher report R1 claim 28 | confirmed by the researcher; not re-read line by line |
| 22 | Em dashes per 1,000 words: GPT-5.4 1.43, Gemini 2.5 Pro 3.53, GPT-4o 4.12, Claude Opus 4.6 9.09, GPT-4.1 10.62; human mean 3.23 | SKILL.md pattern 13 | Freeburg, arXiv 2603.27006 | arxiv.org/html/2603.27006 fetched raw and searched: every value found | confirmed |
| 23 | GPT-4o uses present participial clauses at 5.3 times the human rate | SKILL.md pattern 3 | Reinhart et al., PNAS 2025 (arXiv 2410.16107v2) | arxiv.org/html/2410.16107v2 fetched raw: "GPT-4o uses present participial clauses at 5.3 times the rate of humans" | confirmed |
| 24 | Excess 2024 vocabulary is mostly verbs (66%) and adjectives (14%) | SKILL.md pattern 7 | Kobak et al., Science Advances 2025 (arXiv 2406.07016v5) | arxiv.org/html/2406.07016v5 fetched raw: "66% were verbs and 14% were adjectives" | confirmed |
| 25 | Italian: impattare, valido for corretto, vi for ci, coloro che | italiano.md | Antonelli 2025, LCdM 9(1) | local pdftotext lines 326 and 809 | confirmed |
| 26 | Italian: riveste un ruolo fondamentale as a raised register, è cruciale che, entità dinamiche in continua evoluzione, In conclusione | italiano.md | Antonelli 2025 | local pdftotext lines 811, 825, 838, 842, 770 | confirmed |
| 27 | Italian: bold key terms; one emoji per line and five or more hashtags, at least one in English | italiano.md, SKILL.md pattern 17 | Antonelli 2025 | local pdftotext lines 1277-1279 | confirmed |
| 28 | Italian: symmetric non solo X, ma anche Y in model fiction; keyword loops; restating the question; "Certamente, ecco" openers | italiano.md | Antonelli 2025 | local pdftotext lines 2137-2148, 287, 574, 2257, 898, 980 | confirmed |
| 29 | Italian: interference from English largely gone by mid-2025 | italiano.md | Antonelli 2025 | researcher report R3 claim 24 | confirmed by the researcher; not re-read line by line |
| 30 | Italian: sottolineare and evidenziare (emphasis verbs, overused in 24 of 34 languages); importanza, innovativo, mirato | italiano.md | Juzek 2026, arXiv 2605.25358 | local pdftotext lines 23, 340, 372-390, 1063-1109 | confirmed |
| 31 | Crusca norms: short quotations in “…”, nested « “…” », meanings in ‘…’, full stop after the closing mark, ? and ! of the quotation inside it | italiano.md | Accademia della Crusca, Norme editoriali | local pdftotext lines 19-51 | confirmed |
| 32 | blader/humanizer is MIT, "Copyright (c) 2025 Siqi Chen"; current version 3.1.0 | SKILL.md attribution comment | GitHub | `gh api` on LICENSE and CHANGELOG.md | confirmed |

Not shipped, recorded for completeness: the Economist em dash study the Wikipedia page cites could not be fetched by the researcher and is cited in no body. The Italian calques in `italiano.md` ("fare senso", "giocare un ruolo", "realizzare") are stated as house style preferences, not as sourced claims, and the Italian surface forms listed without a citation under "The catalog in Italian" are translations of the English patterns, as that section says.
