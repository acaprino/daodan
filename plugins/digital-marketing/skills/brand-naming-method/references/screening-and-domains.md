# Domain Gate, Trademark Registers, and Market Saturation Procedure

On-demand reference for `digital-marketing:brand-naming-method` (Steps 3b, 3c, 4, 5, and 6).

## 1. Domain Checker Script (Step 3b and Step 4)

Use the domain checker script in `domain-hunter` for the Step 3b registration table, passing every candidate in one invocation:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/domain-hunter/scripts/domain_checker.py" name1 name2 --tlds .com,.io
```

- **Protocol**: Checks availability via RDAP across concurrent workers (`--workers`, default 8) using the Python standard library. Defaults to `.com`, `.app`, `.io`, `.co`, or the user's `--tlds` list.
- **Statuses**: `AVAILABLE`, `TAKEN`, or `UNKNOWN`. `UNKNOWN` means the lookup failed (never treat it as free).
- **Non-RDAP TLDs (`.it`, `.eu`, `.io`)**: The script queries the registry's port-43 whois first (paced at 1 req/s per host) and labels results `(via whois.nic.it)`, `(via whois.eu)`, or `(via whois.nic.io)`.
- **Registrar fallback (`.co` or unreadable whois)**: Checked on Gandi's search page via headless Patchright (`(Gandi page, headless Patchright)`). Requires `pip install patchright && patchright install chromium`. If Patchright is missing, the script prints `UNKNOWN (no RDAP service for .co; patchright not installed ...)`; do not retry, report the missing install.
- **Blocking rule**: A candidate is blocked only when every requested TLD with a readable answer is `TAKEN`. For a blocked name, run one web search (`"name" app` or `"name" company`): if an established business holds it, drop the name and generate a replacement; if parked/dormant, carry it forward with a note for Step 6a. Never open the user's visible browser (`open`/`start`).

## 2. Refinement Toolkit (Step 3c)

For polishing promising-but-rough survivors (never for generating coined words from scratch):
- **Phonosymbolism**: Vowels `a`/`o` (open, warm), `i`/`e` (small, precise), `u` (deep, serious). Consonants `b`/`m`/`l` (soft, round), `k`/`t`/`p` (sharp, energetic), `s`/`f`/`v` (flowing, elegant), `r`/`g` (rugged, dynamic).
- **Morphological refinement**: Suffix shifts (`-ia`/`-a` warm, `-ix`/`-ik` sharp, `-os`/`-io` international, `-eo`/`-ova` modern), vowel swaps, consonant softening, clipping (`Tumbler` -> `Tumblr`), and cross-linguistic blending (`Auralux` from Latin `aura` + `lux`).

## 3. Trademark Pre-screening Procedure (Step 5)

Trademark risk is graded for three territories: **Reference country** (from Step 1), **Europe**, and **World**. Search engines do not index trademark registers; a web search never substitutes for a register query.

| Territory | Registers that must answer |
|---|---|
| Reference country | Italy: UIBM banca dati. US: USPTO Trademark Search. Other country: that national office's official trademark database (if unreachable, mark `NS`). |
| Europe | EUIPO TMview, or EUIPO eSearch plus (`https://euipo.europa.eu/eSearch/`, EU trade marks only) when TMview does not answer. |
| World | WIPO Global Brand Database and USPTO Trademark Search. |

### Browser Query Rules (Playwright MCP, Headless)

Query registers through the `playwright` plugin's MCP tools in headless mode:
1. Open the register's home page, type the exact name in its search box, and inspect the result list for exact and confusingly similar marks in the product's Nice classes. Never hand-construct deep results URLs.
2. **Pace queries**: One register and one name at a time, waiting several seconds between requests. Never run parallel queries against the same register.
3. **Search spaced variants**: Also search the spaced form of compound names (`"new orbit"` for `NewOrbit`).
4. **Verify register response**: Confirm the page shows a result list or explicit zero-results message. WAF blocks ("Problem detected", "Access denied", CAPTCHAs, `tmdn.org/error/revise.html`) are recorded as `NOT SCREENED: <register>` with the page title and reference number.
   - **UIBM quirk**: Reload the search page before every name (the input field disappears after a zero-results page).
   - **WIPO quirk**: Valid only when the header restates the query (`contains the word <name>` or `sounds like <name>`); a generic multi-million-row list means the query did not run (`NOT SCREENED`). Run WIPO's phonetic ("sounds like") search on finalists as well.
   - **TMview truncation**: "Contains" searches cap at 30 rows; note truncation if full and do not claim class A from a truncated list.

### Missing Playwright MCP Recovery

If Playwright MCP tools are unavailable, stop Step 5 and output:

```
Missing required dependency: Playwright MCP (Microsoft, @playwright/mcp)

Install Microsoft's Playwright MCP server for your active host, then re-run:
  Claude Code  claude plugin install playwright@claude-plugins-official
  Codex        codex mcp add playwright npx "@playwright/mcp@latest"
  VS Code      code --add-mcp '{"name":"playwright","command":"npx","args":["@playwright/mcp@latest"]}'
  Copilot CLI  /mcp add  (name playwright, command npx @playwright/mcp@latest)
  Pi           pi install npm:pi-mcp-adapter, then add "playwright" in ~/.config/mcp/mcp.json
  OpenCode     opencode mcp add playwright --global -- npx @playwright/mcp@latest
```

### Risk Classes (A to D, plus NS)

- **A**: No identical or similar mark found (requires every register for the territory to have answered).
- **B**: Similar marks only in unrelated Nice classes.
- **C**: Similar mark in the product's class, or identical mark in a related class.
- **D**: Identical or near-identical mark (registered or pending) in the product's class. A **D in the reference country** eliminates the name at Step 5; a D in Europe or World lowers the Step 7 score and is listed in "Before you commit".
- **NS** (not screened): A required register did not answer. Never treat `NS` as `A`.

## 4. Market Saturation Gate Details (Step 6)

When web search is unavailable or blocked by a challenge, mark affected checks `not checked` (valid status words: `in use`, `free`, `not checked`), keep the iTunes Search API app lookup (`https://itunes.apple.com/search?term=<name>&country=<cc>&entity=software`), and list skipped checks in "Before you commit".

Run fail-fast in order:
- **6a. Domain activity (GATE)**: Inspect `TAKEN` domains from Step 3b (`ACTIVE BUSINESS` in same sector -> discard immediately and replace; `PARKED` -> moderate risk; `AVAILABLE` -> clear).
- **6b. App stores**: Search Google Play and Apple App Store (`SATURATED` 3+ same-category matches / `MODERATE` 1-2 / `CLEAR` 0).
- **6c. SERP saturation (Google Test)**: Search `"exactname"` (`DOMINATED` / `COMPETITIVE` / `OPEN`).
- **6d. Social media**: Check Instagram, X/Twitter, TikTok, LinkedIn (`TAKEN BY BRAND` / `INACTIVE/PERSONAL` / `AVAILABLE`).
- **6e. Industry saturation**: Search `"name" + industry keywords`, Product Hunt, Crunchbase (`LOW` / `MEDIUM` / `HIGH` / `BLOCKED`).
- **6f. SEO potential**: Rate `HIGH` / `MEDIUM` / `LOW` from keyword relevance and SERP competition.
