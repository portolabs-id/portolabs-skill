# Script: from research to an approved brief

Pre-production ends with `brief.md`, which the user approves. Nothing is voiced, fetched or
rendered before that.

## Length: 30–90 s

ElevenLabs reads about 150 words a minute once pauses over 0.3 s are cut (measured on a test
reel): 30 s ≈ 75 words, 60 s ≈ 150, 90 s ≈ 225. Pick the length from the idea, and go shorter
when the idea fits:

| Idea | Length |
|---|---|
| One tip, one fact, one tool | 30–45 s |
| A list of 3–5 | 45–70 s |
| A full how-to, start to finish | 70–90 s |

One idea per reel. A second idea is a second reel ("part 2" is also a good CTA).

## Hook: the first sentence, the first 1–3 s

Write five options, each from a different pattern, and mark the one you would pick:

| Pattern | Example |
|---|---|
| Problem + time promise | "Edit reel sejam? Kasih gue 60 detik." |
| Number | "Cuma butuh empat tool buat bikin reel kayak gini." |
| Enemy or contrast | "Orang bayar kursus 500 ribu buat ini. Padahal gratis." |
| Result first | "Reel ini dibikin tanpa buka editor sama sekali." |
| Mistake | "Stop nulis caption reel satu-satu." |
| Question that stings | "Kenapa reel kamu di-skip di detik kedua?" |
| Insider | "Ini yang nggak dikasih tahu tutorial editing." |

- Ten words or fewer. The first words are about the viewer's problem or the payoff.
- No greeting, no "halo guys", no channel intro. The template shows the first words at frame 0.
- The reel must pay the promise. A hook it cannot keep loses the viewer at the second beat.
- Borrow the angle of titles that are working in `trends.md`; never copy them.

## Body

- Numbered beats, each one action with one visual, 1–2 sentences (about 25 words at most).
- The first payoff lands by 5–8 s.
- Something new on screen every 3–5 s; the scene plan takes care of it, the script gives it material.
- One pattern break in the middle: a number, a surprising fact, a before and after.
- Over 60 s: a one-line recap before the CTA.
- Spoken Indonesian, short words. Write names as they should appear on screen; if the voice
  says one wrong, respell it phonetically in `vo` only for the voice pass.

## CTA

One action: comment a keyword (for a DM), save, or follow for part 2. The end card holds 2 s
after the last word.

## Facts

Every number and claim has its source in `research.md`. A claim without a source is cut.

## The brief

Write `<work>/brief.md` and show it in chat as plain text, not JSON:

```markdown
# <working title>
Untuk: <who>. Durasi: ±<n> detik (<words> kata).

## Kenapa sekarang
- <trend or finding, with its link>

## Hook (pilih satu)
1. <hook> ← rekomendasi
2. ...

## Naskah
| # | Chip | Voice over | Visual | Aset | ±detik |
|---|---|---|---|---|---|

## CTA
<one action>

## Sumber
- <link>
```

Ask which hook, and whether to change anything. Revise until the user says go ("jalan", "gas",
"oke produksi"). Then write `script.json` from the chosen hook and the table.
