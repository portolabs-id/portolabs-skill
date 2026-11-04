---
name: capcut-auto-edit
description: Use when turning a raw talking-head video into a ready CapCut draft in the Portolabs "0827" promo style (jump cuts with no dead air, yellow subtitles, B-roll, info cards, poster, partner logos, SFX, 4K filter and colour grade), e.g. "edit video ini", "bikinin editan capcut", "edit kayak 0827", "potong jeda terus kasih subtitle", or a path to a .MOV/.mp4 that should become a short vertical video.
---

# CapCut auto-edit (0827 style)

## Overview

One A-roll (a person talking to camera, retakes included) plus optional assets becomes a new CapCut draft at 1080x1920, 60 fps. CapCut opens it with every layer editable. The length follows the content (usually 30–90 s), and the number of cuts follows the pauses.

**The pace never breaks while someone talks.** Every pause and retake is removed. The speech audio runs on one track with no gaps. B-roll and overlays cover the picture while the voice keeps going. Every other rule gives way to this one.

Work split:
- `scripts/transcribe.py` transcribes each stretch of speech separately with word timestamps, and maps silences from the audio itself. Whisper alone drifts across pauses and merges repeated takes.
- **You** read the transcript, choose the takes, and decide where each visual goes, by word index, in a `plan.json`.
- `scripts/build_draft.py` turns the plan into the draft. It cuts pauses from the real audio, alternates zoom on jump cuts, blurs the picture under overlays, places SFX on visual events, and clones every layer from `assets/template/`. That keeps fonts, effect IDs and grading identical to the reference project.

Requirements: macOS with CapCut, `ffmpeg`, and `mlx_whisper` (`uv tool install mlx-whisper`; the first run downloads about 1.6 GB). Check with `command -v ffmpeg mlx_whisper`.

## Workflow

Keep working files in a scratch folder (`<work>`), never inside the CapCut drafts folder.

1. **Get the A-roll path and start transcribing at once** with `run_in_background`:
   ```bash
   python3 <skill>/scripts/transcribe.py "<aroll>" "<work>"
   ```
   A 7-minute file takes about a minute. It prints `[index]word` lines; `‖2.4s` marks a pause.
2. **Ask for assets while it runs.** Ask in one message, and say which ones are optional:
   - B-roll clips (any number, any orientation)
   - Hook text: two short lines plus a punchy highlight such as "Gw saksinya!". Offer to write it from the transcript.
   - Poster of the program, partner logos (green-screen `#00d800` animations or plain images), key info texts (benefit, requirements), the CTA text or link, the creator's name for the credit watermark.
   Missing assets are fine: that element is left out.
3. **Look at each B-roll** before you place it. Grab a frame, then read the image:
   ```bash
   ffmpeg -loglevel error -ss 1 -i "<clip>" -frames:v 1 -vf scale=360:-1 "<work>/thumb-<n>.jpg"
   ```
4. **Choose the takes.** Read the whole transcript. For each sentence keep the **last complete, fluent take**. Drop false starts, stutters, "eh ulang", and anything after the script ends (chatter, other recordings in the same file). The order of `keep` is the order of the video, so you may move a sentence. Fix misheard names and brands in `word_fixes` (whisper writes "decoding" for Dicoding).
5. **Place the visuals** with the rules in [references/style.md](references/style.md). Write `<work>/plan.json` as described in [references/plan.md](references/plan.md).
6. **Dry-run and check the pace:**
   ```bash
   python3 <skill>/scripts/build_draft.py "<work>/plan.json" --dry-run
   ```
   It prints the duration, the speech pieces and every shot. Fix the plan if:
   - the video is outside 30–90 s without a reason,
   - a shot runs longer than about 3.5 s with nothing moving,
   - the B-roll is not concentrated in the hook,
   - an overlay sits on the wrong words.
7. **Build.** Run the same command without `--dry-run`. It writes a new draft folder (never overwrites one) named after `plan.name`, with a cover frame. CapCut finds new folders in its projects folder by itself, even while it is open. If the draft does not appear, the user restarts CapCut.
8. **Report** the draft name, its duration, which takes you used, and which assets were missing and so left out. Offer changes ("hook lebih pendek", "B-roll ini taruh di kalimat X"): edit the plan and build again under a new name.

## Notes

- Media is linked by absolute path, not copied. Tell the user not to move or delete the source files until the video is exported.
- Fonts, text effects, filter and transitions point at CapCut's effect cache of the machine that made the template. On another Mac, CapCut may have to download them once.
- The tuning constants (pause length, pads, zoom amounts, shot lengths) sit at the top of `build_draft.py`. Change them there, not per video.
