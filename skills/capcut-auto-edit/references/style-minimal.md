# Minimal style: where things go

The reference is a "clean & minimal" reels-editing reel: a dark, moody talking head where the words do the work. One phrase at a time sits on the chest: a small white lead-in, one big lime keyword with a glow, a small white tail. Graphics are few and each one means something. These rules describe *when* each element appears. The builder handles how it looks.

## What the builder does on its own

- Same pace as della: takes, pause cuts, zooms on jump cuts, B-roll covers.
- Captions only around the highlighted words (`emphasis`, plus every `strike` and `behind` word), with no text between them: up to two small words before the big keyword and up to three after, never across a sentence. The keyword holds at least 1.6 s from its word (2.8 s behind the head) and the phrase ends a breath before the next one, an alert or a glitch.
- Small words blur in as they are spoken; the keyword blurs and settles in on its word; the phrase blurs out at its end. Captions and alert cards are one transparent video rendered with HyperFrames (Inter, lime glow), so they are not editable in CapCut: change the plan and build again.
- Moody grade (darker shadows and blacks) with a vignette, an opening woosh, and a fade to black over the last 0.8 s.

## Pace

Shorter and tighter than della: 20–60 s. One idea per phrase. Drop any sentence that does not move the point forward.

## Highlights (`emphasis`)

Only the important words get a caption; the rest of the speech has none, so the big words breathe.

- One highlight every 3–5 s: about 8–10 in a 40 s video. The dry-run prints a `FIX:` for two closer than 2 s.
- A highlight is the word that carries the point: a noun, a strong verb or a number ("portfolio", "khawatir", "website", "otomatis"). Never a glue word.
- Leave the gaps empty on purpose: under an alert, over B-roll that already shows the point, and on the line right after a big word.
- The dry-run prints each caption as `start-end  lead [KEYWORD] tail`. Read it: each line should read as a phrase on its own.
- Without any `emphasis`, the builder picks the longest non-glue words about 3.5 s apart. Always choose them yourself.

## Strike (`strike`)

A red line across the keyword: the thing the speaker rejects or says is over ("~~download~~ ulang", "~~desain~~ yang heboh"). At most two per video; it loses its punch when repeated.

## Alerts (`alerts`)

Dark red cards with an icon, stacked when they overlap: the doubts or pains the viewer has ("nunggu mood dulu?", "harus punya laptop?").

- Use them in the problem part, usually near the start. Two or three in a row that stack read best.
- Card text is short: a question or a fragment, under about 25 characters.
- Captions hide while a card shows, so a card should say what the speech says, in fewer words.
- `icon` changes the emoji (default ⚠️; ✖️ for a "no", ✅ for a fix).

## Behind the head (`behind`)

The keyword sits behind the speaker, the head covering part of it: the most important word of the hook or the turn ("gimana caranya bikin ~portfolio~"). One or two per video.

- Read a frame of the A-roll and set `head_y` (−1…1) so the keyword overlaps the top of the head and the hair, not the eyes. For a speaker framed from the chest up that is about 0.4–0.5.
- The phrase moves to `head_y`, and the shots under it lose their zoom: the matte is cut from the plain frame.
- Never over B-roll: the speaker must be on screen to hide the word. The dry-run prints a `FIX:` when it is.

## Flying icons (`icons`)

A small lime icon flies in from below right and settles beside the tail (or the keyword), then bobs: the paper plane of the reference ("to Understand ✈ your value"). `plane` for sending or sharing ("kasih link", "kirim"), `sparkle` for a result or something new ("otomatis", "langsung jadi"), `arrow` for direction or growth. One every 8–10 s at most, on a phrase that stays at least a second.

## REC frame (`rec`)

A camera viewfinder over the picture while the speaker talks about recording, filming or "showing you now" ("gue bakal kasih lihat gimana caranya"). One span per video.

## Ring (`rings`)

A glowing circle around the face for a personal, emotional beat ("gue juga pernah stres di depan kamera"). Look at a frame first and set `x`, `y` (the face centre, −1…1) and `size` (the circle's width as a share of the frame). Captions move to the top of the frame while a ring shows.

## Glitch (`glitch`)

A Signal Glitch 2 transition with a swish on the first word of a new part: problem → solution, solution → proof, proof → CTA. Two to four per video.

## B-roll

Use only the footage the user gives or imported for this video, the footage inside the A-roll file included (screen recordings after the talking). Never pull clips from anywhere else (other drafts, Downloads, stock, the web): ask instead. Put a clip wherever the speaker names something it shows (the website, the editor, the result), for the whole sentence about it. A landscape screen recording goes in `posters` (floating over the blurred A-roll, as in della); vertical footage goes in `broll`. Keep the face on screen for the hook, a caption behind the head and the CTA.

## Not used

Hook title, cards, partner logos, CTA box, credit watermark (della elements; the build stops if the plan sets one), background music.
