---
name: reel-caption
description: Use when writing the Instagram caption for a finished @dibalikharga explainer reel (Di Balik Harga), e.g. "bikin caption", "caption IG buat reel ini", "tulis caption sama hashtag", or a ~/Movies/explainer-reel/<slug> folder that has preview.mp4 but no caption.txt.
---

# Reel caption (@dibalikharga)

## Overview

One finished explainer reel gets one Instagram caption, `<work>/caption.txt`, plain text the user pastes when posting.
`<work>` is the reel's folder, `~/Movies/explainer-reel/<slug>/`, made by `explainer-reel`.

The shape comes from the reels that got the most views in Indonesian explainer and economy accounts (November 2026).
Their captions are short, open with a tension, say what it means for the viewer's money, and end with a question the viewer can answer.
The low performers retell the video, shout in capitals, and stack hashtags.

## Read these five files, nothing else

| File | Gives |
|---|---|
| `brief.md` | the hook, Pergeseran (the shift), the chosen CTA, notes on fairness and names |
| `script.json` | the words as voiced; `title` is the hook as used |
| `research.md` | the facts, each with its source, and the limits of the reel's claims |
| `credits.md` | the photo block to copy |
| `trends.md` | the words people search, for the hashtags |

## The caption, in this order

1. **Opening, 1–2 short lines:** the reel's tension as a contrast or a question, with its key number.
   This is all Instagram shows before "lebih banyak". It takes the hook further instead of repeating the on-screen words.
2. **Answer:** the brief's Pergeseran in one or two short sentences.
3. **What it means for you:** one or two sentences that tie the topic to the viewer's money (a price, the rupiah, a bill), using only facts from `research.md`.
4. **Facts:** 2 to 4 lines that start with `• `, each with a number or a date the voice skipped or rounded.
5. **Fairness lines**, only when `brief.md` or `research.md` names a limit: numbers still changing, a verdict not yet given, or a cause the reel does not claim.
   One sentence per limit, two at most, each with the date its numbers hold for.
6. **Question:** one question about the viewer's own money or experience ("Harga apa yang paling kerasa naik buat kamu?").
   On a political topic, the question is still about the viewer's money, never about a politician or a party.
7. **CTA:** the brief's chosen CTA with `@dibalikharga`, one line.
   When that CTA asks for a comment, join it to the question in part 6 as one line that keeps `@dibalikharga`.
8. **Sources:** one line, `Sumber: <source> via <outlet> (d/m/yyyy), ...` (just `<source> (d/m/yyyy)` when it is not a news report), naming the source of every fact the voice or the caption states.
   The date is the one `research.md` or `brief.md` gives for it; a source with none goes in without a date. No URLs here: Instagram does not link them.
9. **Photos:** the `Foto` block of `credits.md` as it stands, photographers' names and licence links included (the licences require them), without its source list.
10. **Hashtags:** 3 to 5 on the last line, short topic words from the searches in `trends.md` or the facts in `research.md`, not catch-alls like #ekonomi or #viral.
    `#dibalikharga` goes last. Instagram allows 5 at most.

Leave a blank line between parts. Parts 1–7 (everything above `Sumber:`) are at most 700 characters, and the whole caption is under Instagram's 2,200.
Count them with:

```bash
python3 -c "import sys; t = open(sys.argv[1], encoding='utf-8').read(); print('all', len(t), '| above Sumber', len(t.split('\nSumber:')[0].strip()), '| hashtags', sum(w.startswith('#') for w in t.split()))" caption.txt
```

When parts 1–7 run over, cut fact lines down to two, then shorten sentences. The opening, the fairness lines, the question and the CTA stay.

## Voice

The script's voice: casual Indonesian with "kamu", short sentences, one idea each, no hype words and no capitals for shouting. At most two emoji.
Name only the person the reel is about. Officials, analysts and academics are named by their role ("Menteri Perdagangan", "analis Bank Woori Saudara"), even where the video shows a name.

## Finish

Write `<work>/caption.txt`; when one already exists, show it and ask before replacing it.
Show the caption in chat as plain text with the counts.
When `brief.md` says numbers may still change, tell the user to re-check them before posting.

## Example

From the `tiket-pesawat-nataru` reel, where the brief's CTA asks for a comment:

```
PPN tiket pesawat Nataru ditanggung 100%. Tapi tiket Rp1,1 juta cuma turun sekitar Rp160 ribu.

Yang dihapus cuma pajaknya. Tarif dasar dan avtur, 80% tiket, nggak didiskon.

Bagasi ekstra dan pilih kursi? PPN-nya tetap kamu bayar.

• PPN-nya persis Rp100.276, 11% dari tarif dasar + avtur.
• Beli 20 Okt 2026–10 Jan 2027, terbang 22 Des 2026–10 Jan 2027.

Rp160 ribu itu contoh DDTC. Proyeksi Kemenhub 28/10/2026: rata-rata turun 11–12%.

Harga apa yang paling kerasa di dompetmu? Tulis di komentar, nanti @dibalikharga bongkar.

Sumber: PMK 77/2026 dan DDTC News (21/10/2026), Kemenhub via Fortune IDN (28/10/2026), KM 83/2026 via The Star (15/4/2026), KM 1041/2026 via Katadata (15/5/2026), Kemenhub via Katadata, Kemenhub via Kontan (2/11/2026).

Foto: Wikimedia Commons
- Pesawat di Bandara Soekarno-Hatta: "PK-GNL (Soekarno-Hatta Airport, 29 December 2017).jpg" oleh Sabung.hamster, CC BY-SA 4.0
- Terminal 3 Soekarno-Hatta: "Pelaporan Masuk Penumpang Terminal 3 Bandara Soekarno Hatta (Januari 2025).jpg" oleh Medelam, CC BY-SA 4.0
- Pesawat di Bandara Juanda malam hari: "Pelita Air Airbus A320 PK-PWF Surabaya 2025 (01).jpg" oleh Bahnfrend, CC BY-SA 4.0
- Gedung Kementerian Perhubungan: "Gedung Perhubungan, Jakarta.jpg" oleh Denny Rachmat Ghaffari, CC BY-SA 3.0
- Gedung Kementerian Keuangan: "Gedung Kementerian Keuangan Republik Indonesia.jpg" oleh Seeharee, CC0

Lisensi: https://creativecommons.org/licenses/by-sa/4.0/, https://creativecommons.org/licenses/by-sa/3.0/
Foto dipotong (crop) dan diperbesar perlahan di dalam video.

#tiketpesawat #nataru #ppntiketpesawat #dibalikharga
```
