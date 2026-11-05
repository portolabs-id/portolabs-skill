# Storytelling: from research to an approved brief

Pre-production ends with `brief.md`, which the user approves. Nothing is voiced, fetched or
rendered before that. This page is how the story is built; work through it in order.

## 1. One idea, one shift

Before any line, write three sentences at the top of the brief:

- **Penonton:** who, and what they feel or believe right now, in their words
  ("Udah coba ChatGPT, tapi hasilnya ngawur").
- **Pergeseran:** what they should believe after watching ("Masalahnya di perintah, bukan di AI").
- **Aksi:** the one thing they do next.

If the shift does not fit in one sentence, it is two reels.

## 2. Length: 30–90 s

ElevenLabs reads about 150 words a minute once pauses over 0.3 s are cut (measured on a test
reel): 30 s ≈ 75 words, 60 s ≈ 150, 90 s ≈ 225. Pick the length from the idea, and go shorter
when the idea fits:

| Idea | Length |
|---|---|
| One tip, one fact, one tool | 30–45 s |
| A list of 3–5 | 45–70 s |
| A full how-to, start to finish | 70–90 s |

## 3. Structure

Pick the one that fits the shift, and name it in the brief with one line on why.

| Structure | Use when | Beats |
|---|---|---|
| Masalah → gejolak → solusi | the viewer already feels the pain | name the pain; what it costs them; the fix, step by step; the result |
| Before → after → bridge | the change is easy to show | before; after (show it early); how to get there |
| Mitos vs fakta | a common belief is wrong | the myth, as they would say it; why it feels true; the fact, with proof; what to do instead |
| Hasil dulu | the result is impressive on its own | the result in the first 3 s; the steps; a one-line recap |
| Cerita → pelajaran | there is a real story (a participant, a client, a number) | the moment of trouble; the turn; what changed; the lesson in one line |
| Daftar yang naik | 3–5 tips or tools | the promise of the list; the items, best last; a one-line recap |

Link beats with conflict or consequence, "tapi" and "jadi", never with "terus" or "lalu": a
sequence of "and then" is a list nobody finishes.

## 4. Hook: the first sentence, the first 1–3 s

Write five options, each from a different pattern, and mark the one you would pick:

| Pattern | Example |
|---|---|
| Problem + time promise | "Edit reel sejam? Kasih aku 60 detik." |
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

## 5. Body: tension and payoff

- **Open a loop** in the hook or the first beat and close it in the last third
  ("...dan langkah ketiga yang paling sering dilewatin").
- **First payoff by 5–8 s:** a fact, a result, the first step.
- **Specific beats generic:** a number, a name, a real task ("rekap pesanan", not "pekerjaan").
- **One pattern break** in the middle: a surprising number, a before and after, a reversal.
- **Every beat answers "terus kenapa?"** for the viewer. A beat that does not is cut.
- Each beat is one action with one visual, 1–2 sentences (about 25 words at most).
- Over 60 s: a one-line recap before the CTA.

## 6. Voice

Portolabs default, until the user gives their own:

- Spoken Indonesian with "kamu" (and "aku" when the speaker talks about themself). Casual words
  are fine: udah, nggak, bikin, pakai.
- Sentences of 12 words or fewer, one idea each.
- No filler or intro phrases: "halo guys", "di video kali ini", "jadi gini", "nah".
- No hype: "rahasia sukses", "dijamin", "100% berhasil".
- English tech words as people say them: prompt, tools, caption, coding.
- Names written as they should appear on screen. If the voice says one wrong, respell it
  phonetically in `vo` for the voice pass only.

## 7. Proof and real stories

- Every number and claim has its source in `research.md`. A claim without a source is cut.
- Say how small a study is when it is small ("UMKM yang disurvei"), and show the source on screen.
- A real story beats an invented example. For "Cerita → pelajaran", ask the user for one. Never
  invent a person, a quote, a testimonial or a result.

## 8. CTA

One action: comment a keyword (only if someone will answer the DMs), save, or follow for part 2.
The end card holds 2 s after the last word.

## 9. Check before showing the brief

Fix whatever fails, then show it:

- [ ] The shift fits in one sentence.
- [ ] The hook is 10 words or fewer, about the viewer, with no greeting.
- [ ] The reel pays the hook's promise.
- [ ] The first payoff lands by 8 s.
- [ ] Beats are linked by "tapi" or "jadi", and each has its visual.
- [ ] Every claim has a source; no invented people, quotes or results.
- [ ] One CTA.
- [ ] The word count fits the length (about 150 a minute).

## 10. The brief

Write `<work>/brief.md` and show it in chat as plain text, not JSON:

```markdown
# <working title>
Untuk: <who>. Durasi: ±<n> detik (<words> kata). Struktur: <structure>, karena <one line>.

Penonton: <what they feel now>
Pergeseran: <what they believe after>
Aksi: <the one thing they do>

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
