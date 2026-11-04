# 0827 style: where things go

The style comes from the CapCut project "0827 (1)", a promo for a scholarship program. These rules describe *when* each element appears. The builder handles how it looks. Treat the numbers as feel, not targets.

## Story shape

Most videos follow this order. Each part takes as long as the speaker needs.

1. **Hook**: one strong statement. Hook title on screen, fast B-roll, woosh.
2. **Story / context**: a personal experience. Mostly A-roll, with B-roll whenever something showable is mentioned.
3. **The offer**: benefit card, then the poster when the program is named, then partner logos at "kolaborasi antara…".
4. **What you get**: a spoken list, with a click on each item.
5. **Who can join**: an overlay card with the requirements.
6. **CTA**: a punch-in on "daftar…" and the CTA box until the end.

## Pace

- Keep only fluent takes. A shorter video that never stalls beats a longer one with hesitations.
- Take the hook from the strongest sentence, even if it was recorded later. `keep` order is video order.
- The builder removes pauses longer than 0.3 s. Do not leave filler words ("eee", "jadi gini") in `keep`.

## B-roll

- About a quarter of the video, **concentrated in the hook**: the first few seconds should be mostly B-roll.
- Put a clip where the narration names something visible (a place, an activity, an object, a moment). Do not use a clip just to fill time.
- One clip per phrase. Two or three words is enough for a cutaway.
- Do not cover the face during punchlines, numbers that matter, or the CTA: the viewer should see the person say them.

## Cards, poster, logos

- **Fullscreen card**: the single biggest benefit ("100% full beasiswa"). Use one per video, at most two.
- **Overlay card**: requirements or conditions ("terbuka untuk umum… 18 tahun").
- **Poster**: when the program name is spoken.
- **Logos**: when partners are named. The title is the phrase that introduces them.
- Each one lasts as long as the phrase that talks about it, and ends when the topic changes.
- Card text is short: two lines, under about 40 characters, no full sentences copied from speech.

## SFX (most are added automatically)

| Event | SFX | Who adds it |
|---|---|---|
| Video start | Deep woosh | builder (with `hook`) |
| End of hook, punch-in | Swish | builder |
| Card or CTA appears | pop! | builder |
| Poster or logo appears | Mouse click | builder |
| Spoken list item | Mouse click | you, via `clicks` |

## Not used

Background music, speed ramps, audio fades, stickers, more than one transition.
