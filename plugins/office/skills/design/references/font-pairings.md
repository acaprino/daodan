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
