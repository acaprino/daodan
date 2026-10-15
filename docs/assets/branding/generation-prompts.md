# Daodan logo generation

Generated with the built-in `image_gen` tool. PNG files preserve the generated alpha channel.

Final assets:

- `daodan-logo-oni.png`: DAODAN wordmark.
- `daodan-icon-oni.png`: matching square D icon.

Visual reference: [Oni logo on SteamGridDB](https://www.steamgriddb.com/game/5245774/logos). The original reference image is retained only in the local run directory, `.daodan/runs/2026-10-14-daodan-logo/references/oni-logo.png`.

The earlier `daodan-icon.png` is a discarded concept; the user requested a closer Oni reference.

## Wordmark prompt

```text
Use case: logo-brand.
Create a logo for DAODAN using the supplied ORIGINAL ONI GAME LOGO as the direct visual reference. The user specifically rejected a previous curvy fantasy/esports/chrome-flame D logo because it did not resemble Oni. Ignore any previous generated identities. Study this reference carefully and use its actual typographic design language.
Required text, exactly once: "DAODAN", spelled D A O D A N. Make the entire artwork a single custom wordmark. Do not add a separate emblem next to the wordmark.
What must carry over from the reference: the distinctive early-2000s Oni logo's slightly forward leaning geometric letterforms; mostly very DARK MIDNIGHT NAVY faces with a subtle blue lower-face texture; a relatively THIN silver/ice-blue beveled outline on both inner and outer edges; sharp angular clipped corners and little stepped notches; an almost calligraphic silhouette constructed from straight edges and precise circles, industrial and Japanese sci-fi rather than smooth organic fantasy. The dark face dominates, about 80 percent of each stroke. The silver border is restrained. Avoid making the letter faces silver or chrome. Avoid generic wide squared-off sci-fi fonts. Preserve the Oni reference's unusual character.
Design the first D with a big almost circular bowl and a distinctive squared angular interruption/step in the upper-left junction, referencing the iconic interrupted circular O of Oni. Construct the A, O, D, A, N as a harmonious custom family with tall clearly legible angular counters, slight forward lean, pointed step details comparable to the reference N, controlled width, and optical kerning. Keep the word compact and cohesive. A long thin sharp blue-and-silver underline beneath the last five letters echoes the original mark's underline. Spell DAODAN correctly and do not duplicate the first D.
Add the requested Daodan aura very subtly: a soft ethereal cobalt/blue-violet bioplasmic glow rising a little behind the letter silhouette and along its upper contour, a few diffuse ghost-like light veils, naturally soft, no literal flames, no thick cyan neon tubing, no lightning. The typography remains crisp and dominant.
Deliver one centered wide horizontal finished logo, transparent background with actual alpha, with enough clear margin around all tips, underline and aura. No characters, no horns, no blades, no organic ribbons, no shield, no 3D mockup, no scene, no poster, no caption, no trademark symbol, no other text. The reference is a style and construction source; replace its lettering with the exact new name DAODAN.
```

## First-letter correction

```text
Use case: precise-object-edit.
Edit this DAODAN wordmark with one precise correction: the FIRST character currently looks like an O/power symbol. Change ONLY that first character into an unmistakable capital D, with a clearly STRAIGHT upright left spine and a rounded right bowl, leaning forward slightly like the fourth letter D. Keep its overall large size and give its upper-left spine a small angular stepped corner to fit the Oni style, but DO NOT use a circle or power-button silhouette. It must unambiguously read D.
The full exact text must read DAODAN, D A O D A N. Six letters.
Preserve the other five letters AODAN exactly, the dark midnight blue faces, thin blue/silver beveled outlines, optical alignment, long underline, and diffuse blue-violet Daodan aura. Maintain the horizontal layout and generous outer margin. Preserve actual background transparency. Add nothing else.
```

## Matching icon prompt

```text
Use case: logo-brand.
Create a square repository icon extracted from the supplied DAODAN wordmark identity. Show ONLY the FIRST capital D from the supplied reference, faithfully preserving its construction: straight slightly forward leaning left spine, generous rounded right bowl, distinctive small angular stepped notch near the upper-left corner, dark navy/near-black front faces, a restrained relatively thin silver/ice-blue bevel along inside and outside edges, subtle cobalt-blue texture at the lower part of the face. This D must look like it belongs to Bungie's original Oni logo's visual family. No organic curving blades, no flames, no esports aesthetic. It must read unmistakably as capital D.
Keep the same soft cobalt-blue and blue-violet bioplasmic Daodan aura diffused close behind the glyph, slightly higher at its upper contour, elegant translucent wisps. The D stays crisp and dominant. Large open transparent center. No additional symbol, no underline, no other letters, no wordmark.
Composition: one centered glyph only, square canvas, use about 72 percent of canvas height for the solid glyph and contain the ENTIRE aura well within an approximately 12 percent safe margin. Balanced optically, readable as a small GitHub avatar. Actual transparent background with alpha around the glyph and inside its counter. Preserve all the restrained dark-blue-and-silver Oni-style material from the reference; no shiny all-silver face, no background tile, no mockup.
```
