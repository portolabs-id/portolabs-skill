# Style: the clean grid explainer

The look every reel shares. The template (`assets/template/index.html`) already draws the ground, the
captions, the rail and the scene transitions. You write only the scenes, one per beat.

## The look

| Element | Value |
|---|---|
| Canvas | 1080x1920, rendered at 60 fps |
| Ground | `#FDFDFD` with a 72 px grid in `--grid` |
| Accent | blue `#3170E8` (`--main`), one accent and no other colour of our own |
| Ink | `#16181D` (`--ink`); spoken-past words `--muted`, small labels `--label` |
| Type | Manrope 500/700/800 for everything; Instrument Serif italic only for `em` words |
| Cards | `.card`: ground colour, 28 px radius, a soft shadow and a 2 px grid-coloured ring |

Colour comes from brands, not from us: logos and screenshots keep their own colours. Never tint,
recolour, mask or invert a logo, and never put a coloured logo on a blue tile.

## Layout zones

| Zone | y (px) | Holds |
|---|---|---|
| Reels UI, top | 0–250 | nothing that must be read |
| Caption | 290–460 | one or two lines, centred |
| Rail chip | 520–700 | the beat's chip, beside the mascot (moves down slowly) |
| Stage | 720–1480 | the scene; centre x 540, keep x 140–940 |
| Reels UI, bottom | 1500–1920 | nothing that must be read |

Type never below 28 px (`hyperframes check` enforces it). Headline numbers use `.big`.

## Captions (automatic)

Pages of up to 4 words, broken after punctuation. Each word blurs in as it is spoken; the spoken
word is ink, earlier words go grey. Per beat in `script.json`:

- `sel`: the one word of the beat that names the thing on screen (a tool, a number). It gets the
  blue selection box. At most one per caption page.
- `em`: the word the sentence lands on, usually its last. It turns into serif italic.

## Writing a scene

`scene(el, beat, tl, kit)` builds into `el` and puts its motion on `tl` at absolute times. Time
everything from the words: `kit.at(i)` is when word `i` is spoken, `kit.end(i)` when it ends.
`beat.from_word` / `beat.to_word` bound the beat; `beat.sel` / `beat.em` list its styled words.

| Helper | Does |
|---|---|
| `kit.h(html)` | one element from markup |
| `kit.place(el, node, x, y)` | puts `node` in the scene centred on (x, y) |
| `kit.logo(name, size)` | the logo from the manifest on a plain tile; a monogram if none was found |
| `kit.shot(name, width)` | a screenshot in a plain browser frame |
| `kit.pop(node, t)` | entrance at `t`: fades and springs up, slightly before the word |
| `kit.float(node, from)` | a slow bob from `from` to the end, so a held thing never freezes |
| `kit.zoom(shot, t, {x, y, scale})` | pushes into a screenshot at `t`, centred on x%, y% of it |

The engine fades each scene in at its beat and out before the next. Inside a scene:

- **The thing that moves is the thing being said.** Each element enters on the word that names it.
- **Nothing static for more than about 2 s:** `kit.float`, a slow zoom, a counter.
- **Transforms only:** animate `x`, `y`, `scale`, `opacity`, `rotation`. Never `top`, `left`,
  `width` or `height`; they stutter in the frame-by-frame render.
- **One idea per beat.** Up to 5 cards; more, and it is two beats.
- Screenshots: push in (`kit.zoom`, scale 1.6 to 2.2) to the part being talked about. A whole page
  is unreadable on a phone.

## Scene patterns

Pick the pattern that says what the beat says.

**List that builds** (tools, steps, reasons): one row per item, entering on its word.

```js
tools(el, beat, tl, kit) {
  const rows = [["claude", "Claude", "nulis naskah", 8], ["ffmpeg", "FFmpeg", "render video", 11]];
  rows.forEach(([asset, name, job, word], k) => {
    const row = kit.h(`<div class="card" style="display:flex;align-items:center;gap:24px;padding:24px 30px;width:660px"><div><span class="label">${name}</span><div class="note">${job}</div></div></div>`);
    row.prepend(kit.logo(asset, 88));
    kit.place(el, row, 540, 860 + k * 180);
    kit.pop(row, kit.at(word));
    kit.float(row.firstElementChild, kit.at(word) + 0.5, 4);
  });
},
```

**Hub that fills** (a set that completes): a centre card counts `0/5`, items attach around it
on their words, a ring fills. Count with `tl.set(counter, {textContent: "3/5"}, t)`.

**Grid of steps** (a number said aloud): 2x2 numbered cards pop with a 0.12 s stagger on the number word.

**Screenshot focus** (show a real page): `kit.shot`, `kit.pop` on the beat's first word, `kit.zoom`
on the word that names the detail.

```js
contoh(el, beat, tl, kit) {
  const shot = kit.place(el, kit.shot("ffmpeg-site", 880), 540, 1040);
  kit.pop(shot, kit.at(beat.from_word));
  kit.zoom(shot, kit.at(22), { x: 52, y: 78, scale: 2.1 });
},
```

**Big number** (a statistic): `.big` number counting up from half its value, its label under it.

**End card** (CTA): one large icon or the brand's logo, held: `end_hold` keeps it 2 s after the
last word. One action only (follow, save, comment a keyword).

## Checks before render

1. `npx -y hyperframes@0.9.14 check --at <built> --no-collapse-static` passes, with the times
   `new_composition.py` printed. Expected warnings: `negative_z_index` (the selection box sits inside
   its word) and `film_silent` (the sound is added in CapCut). A line drawn through a word on purpose
   carries `data-layout-allow-occlusion` on the line itself, or `check` reports the word as hidden.
2. **No text runs out of its box.** `text_box_overflow` ✗ names the text and by how many pixels:
   widen the card (up to 800 px), shorten the words, or lower the font size. A number or a short
   label that must stay on one line gets `white-space:nowrap` and a size that fits.
3. `snapshot --at <built>`; read the contact sheet. Look for text past a card's edge, a line that
   wrapped where it should not ("PMK 49/" over "2026"), overlaps, and a logo that is wrong or blurry.
