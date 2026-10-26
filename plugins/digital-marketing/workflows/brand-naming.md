---
description: >
  Runs the whole workflow from a brief, with optional language and TLD constraints.
  TRIGGER WHEN: the user asks for brand, startup, product, or company names.
  DO NOT TRIGGER WHEN: renaming source code identifiers (use clean-code), or picking SEO keywords (use /digital-marketing:seo-audit).
argument-hint: "<brief description or industry> [--country <country>] [--languages <lang1,lang2>] [--tlds <.com,.app,.io>]"
---

# Brand Naming

## Invocation

Invoke the `brand-naming-method` skill and follow its full workflow.

## Arguments

- `<brief>`: Industry, target, values, and any constraints for the naming project
- `--country`: Reference country for the trademark check, graded first and weighted most; asked when neither the arguments nor the project name one
- `--languages`: Languages to check for cultural conflicts (default: en,it,es,fr,de,pt)
- `--tlds`: TLDs to check for domain availability (default: .com,.app,.io,.co)

## Examples

```
/digital-marketing:brand-naming Meal prep app for vegan athletes. Values: energy, nature, performance. Target: 20-35, international.
/digital-marketing:brand-naming SaaS project management tool for remote teams --languages en,es,pt
/digital-marketing:brand-naming Italian artisan coffee brand, premium positioning --tlds .com,.it,.coffee --country Italy
```

## What it does

1. Takes the brief from the arguments when they carry it, scans the current project only when the brief is thin or names the project, and asks for the reference country and any other field neither supplies
2. Generates 12-15 curated candidates across 4 Strategic Directions: Etymological Hijacking, Scientific Decontextualization, Metaphorical Shift, Phonetic Real-Word
3. Filters linguistically and culturally (pronunciation, negative meanings, phonosymbolism)
4. Checks domain registration once over the requested TLDs with the domain checker (RDAP, and a headless Patchright registrar page for TLDs with no RDAP), lists every dropped name with its reason, then checks social media handles
5. Analyzes market saturation: existing apps, websites, active businesses with same name (Google, Play Store, App Store, Crunchbase)
6. Pre-screens trademarks through a browser (the `playwright` plugin's MCP tools) in the national register of the reference country (UIBM for Italy), EUIPO TMview (falling back to EUIPO eSearch plus for EU trade marks when TMview refuses the browser), USPTO Trademark Search and the WIPO Global Brand Database, and grades the reference country, Europe and the world from class A (lowest risk) to D (highest); a register that did not answer makes its territory NS (not screened), never A
7. Scores the top 5 from 1 to 5 on weighted criteria (memorability, distinctiveness, market saturation, SEO, legal risk, etc.) and computes an overall score from 1.0 to 5.0, with the trademark score weighted to the reference country
8. Delivers the evaluation report from a fixed template: summary, scorecard of all 5 names, the top 3 with a description, a motivation for every score and a trademark class for each territory, the runners-up, the removed names, the checks still open and the evidence behind them
