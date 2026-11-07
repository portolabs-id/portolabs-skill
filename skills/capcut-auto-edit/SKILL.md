---
name: capcut-auto-edit
description: Use when turning a raw talking-head video into a ready CapCut draft with jump cuts and no dead air, in one of two styles - "della" (default, the Portolabs "0827" promo look - yellow subtitles, B-roll, info cards, poster, partner logos) or "minimal" (dark moody grade, kinetic captions with a big lime keyword, red strike, alert cards, REC frame, glitch transitions), e.g. "edit video ini", "bikinin editan capcut", "edit kayak 0827", "edit gaya minimal", "/portolabs:capcut-auto-edit minimal", "potong jeda terus kasih subtitle", or a path to a .MOV/.mp4 that should become a short vertical video.
---

# CapCut auto-edit

## Overview

One A-roll (a person talking to camera, retakes included) plus optional assets becomes a new CapCut draft at 1080x1920, 60 fps, in one of two styles. CapCut opens it with every layer editable. The length follows the content (usually 30–90 s), and the number of cuts follows the pauses.

**The pace never breaks while someone talks.** Every pause and retake is removed. The speech audio runs on one track with no gaps. B-roll and overlays cover the picture while the voice keeps going. Every other rule gives way to this one.

Work split:
- `scripts/transcribe.py` transcribes each stretch of speech separately with word timestamps, and maps silences from the audio itself. Whisper alone drifts across pauses and merges repeated takes.
- **You** read the transcript, choose the takes, and decide where each visual goes, by word index, in a `plan.json`.
- `scripts/build_draft.py` turns the plan into the draft. It cuts pauses from the real audio, alternates zoom on jump cuts, blurs the picture under overlays, places SFX on visual events, and clones every layer from `assets/template/`. That keeps fonts, effect IDs and grading identical to the reference project.

## Styles

The first word of the arguments names the style: `/portolabs:capcut-auto-edit minimal <video>`. No style word, or `della`, means della. In conversation, "gaya minimal" / "kayak reels clean minimal" means minimal and "kayak 0827" / "kayak della" means della. Put the style in `plan.json` as `"style"`.

| | della (default) | minimal |
|---|---|---|
| Look | Yellow 2–3 word captions, hook title, ART PAPER cards, poster, partner logos, CTA box, credit | Dark moody grade and vignette, kinetic captions (small white lead-in, big lime keyword with glow, small tail), red strike, stacked alert cards, REC frame, glowing ring, glitch transitions, fade to black |
| Placement rules | [references/style-della.md](references/style-della.md) | [references/style-minimal.md](references/style-minimal.md) |
| Plan fields | [references/plan.md](references/plan.md) | the same, plus "Minimal fields" there |

Requirements: macOS with CapCut, `ffmpeg`, and `mlx_whisper` (`uv tool install mlx-whisper`; the first run downloads about 1.6 GB). Check with `command -v ffmpeg mlx_whisper`. Minimal also needs `npx` (Node) and internet during the build: it renders its captions with HyperFrames, which loads the Inter font and GSAP from the web.

## Workflow

Keep working files in a scratch folder (`<work>`), never inside the CapCut drafts folder.

1. **Get the A-roll path and start transcribing at once** with `run_in_background`:
   ```bash
   python3 <skill>/scripts/transcribe.py "<aroll>" "<work>"
   ```
   A 7-minute file takes about a minute. It prints `[index]word` lines; `‖2.4s` marks a pause.
2. **Ask for assets while it runs.** Ask in one message, and say which ones are optional:
   - B-roll clips (any number, any orientation)
   - della only: hook text (two short lines plus a punchy highlight such as "Gw saksinya!"; offer to write it from the transcript), poster of the program, partner logos (green-screen `#00d800` animations or plain images), key info texts (benefit, requirements), the CTA text or link, the creator's name for the credit watermark.
   - minimal only: nothing more, but press for footage: screen recordings of the product or the result carry this style. You choose the highlights, strike, behind-the-head words, flying icons, alert texts, REC, ring and glitch spots from the transcript.
   Missing assets are fine: that element is left out. Use only the footage and files the user gives for this video; never take clips from other drafts, folders or the web on your own.
3. **Look at the whole A-roll, then at each B-roll** before you place anything. The A-roll file often carries its own footage after the talking (or between takes): screen recordings, the product, the result, with no narration or only background noise. Make a contact sheet of the whole file and read it:
   ```bash
   ffmpeg -loglevel error -i "<aroll>" -vf "fps=1/6,scale=120:-1,drawtext=text='%{pts\:hms}':x=2:y=2:fontsize=11:fontcolor=yellow:box=1:boxcolor=black,tile=11x6" -frames:v 1 "<work>/aroll-sheet.jpg"
   ```
   For a file longer than about 6.5 minutes, raise the interval (`fps=1/10`). Use those moments as B-roll: a `broll` item whose `file` is the A-roll itself, with `src_start` at the moment (zoom in with a second, denser sheet of that stretch to pick it). Footage of the A-roll file counts as the user's footage; prefer it to nothing. For each separate B-roll clip, grab a frame and read it:
   ```bash
   ffmpeg -loglevel error -ss 1 -i "<clip>" -frames:v 1 -vf scale=360:-1 "<work>/thumb-<n>.jpg"
   ```
4. **Choose the takes.** Read the whole transcript. For each sentence keep the **last complete, fluent take**. Drop false starts, stutters, "eh ulang", and anything after the script ends (chatter, other recordings in the same file). The order of `keep` is the order of the video, so you may move a sentence. Fix misheard names and brands in `word_fixes` (whisper writes "decoding" for Dicoding).
5. **Place the visuals** with the rules of the style ([della](references/style-della.md), [minimal](references/style-minimal.md)). Write `<work>/plan.json` as described in [references/plan.md](references/plan.md). For a ring or `behind` in minimal, read a frame of the A-roll to find the face centre and the top of the head.
6. **Dry-run and check the pace:**
   ```bash
   python3 <skill>/scripts/build_draft.py "<work>/plan.json" --dry-run
   ```
   It prints the duration, the speech pieces and every shot. Fix the plan if:
   - the video is outside 30–90 s without a reason,
   - a shot runs longer than about 3.5 s with nothing moving,
   - the B-roll is not concentrated in the hook (della),
   - an overlay sits on the wrong words,
   - (minimal) a line under `Captions` highlights the wrong word, or the highlights come thicker than one every 3 s: fix `emphasis`.
7. **Fix the transcript check.** The dry-run also prints `Transcript check:` with one `FIX:` line per spot that will sound wrong. Clear every line, then dry-run again until it says `nothing to fix`:
   - `said twice`: a phrase repeats back to back in what you kept ("bisa banget, bisa banget daftar…"). Take the earlier copy out of `keep`, so only the later take remains.
   - `spans … across a pause`: one word stretches over a pause, so whisper probably hid a repeat or false start inside it. Use another take of that sentence. If there is none, tell the user the time in the source video to check by ear.
8. **Fix the layout check.** Captions and texts must never sit on each other or hide each other. The dry-run estimates every text's box on screen (calibrated on CapCut's own rendering) and prints `Layout check:`.
   - It moves captions clear of the hook, cards, logo title and CTA by itself, and moves the credit watermark to a free spot. These show up as `moved …` lines; nothing to do.
   - A `FIX:` line means two texts placed by the plan (hook, card, logo title, CTA) overlap. Give one of them a different `"y"` in the plan (−1 bottom … 1 top), or shorten its text or time. Dry-run again until it says `nothing to fix`.
9. **Recheck the tail of every cut.** People reading a script glance down at it as a line ends, and a glance just before a jump cut looks like a mistake. The dry-run writes `<work>/tails/sheet-N.jpg` and lists what each row is: one row per cut the viewer sees, with the frames 0.3 / 0.2 / 0.1 / 0 s before the cut. Read every sheet. For each row where the eyes leave the camera (down at the script, sideways, closed) or the head turns away:
   - Only the last frame is off: add `"trim_tail": {"<word index>": 0.04}` for the word the row ends on.
   - Off from 0.1 s or earlier: the glance starts while the word is still sounding, so trimming would clip the word (the dry-run prints a `WARNING` when a trim does). Cover the end of that phrase with B-roll instead. Another moment of a clip you already used is fine.
   Dry-run and read the sheets again until every tail looks at the camera.
10. **Build.** Run the same command without `--dry-run`. It writes a new draft folder (never overwrites one) named after `plan.name`, with a cover frame. CapCut finds new folders in its projects folder by itself, even while it is open. If the draft does not appear, the user restarts CapCut.
   **Minimal: check the contrast** before you report. The build measures the picture behind every caption (lime keyword ≥ 3:1, white words ≥ 4.5:1) and puts a soft dark backdrop behind those that fall short; the summary lists each under `Contrast check`. Then read `<work>/minimal/contrast-sheet.jpg`, every caption over its picture. A caption that still does not read at a glance (busy text behind it, a face covered): move its highlight to another word, move the B-roll off that phrase, or let the face show there, and build again.
11. **Report** the draft name, its duration, which takes you used, and which assets were missing and so left out. Offer changes ("hook lebih pendek", "B-roll ini taruh di kalimat X"): edit the plan and build again under a new name.

## Notes

- Media is linked by absolute path, not copied. Tell the user not to move or delete the source files until the video is exported.
- Fonts, text effects, filter and transitions point at CapCut's effect cache of the machine that made the template. On another Mac, CapCut may have to download them once. Minimal's glitch transition and fade come from `assets/minimal/prototypes.json`, the same way.
- Minimal's captions, strike and alert cards are one transparent video (`assets/minimal/captions.html`, rendered with HyperFrames; a build of 40 s takes a few minutes). Words behind the head are cut out with an Apple Vision person matte (`scripts/person_matte.js`, run by `osascript`). Its ring, REC frame, vignette and black are PNGs from `scripts/overlays.py`. All of it is copied into the draft folder. The captions are not editable in CapCut: change the plan and build again.
- The tuning constants (pause length, pads, zoom amounts, shot lengths) sit at the top of `build_draft.py`. Change them there, not per video.
