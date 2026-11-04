---
name: capcut-asmr-edit
description: Use when turning a long raw process recording (laptop or PC service, cleaning, repair, restoration, often 30–60 min and often with no usable sound) into several short satisfying "ASMR" reels as CapCut drafts over a background song, e.g. "bikin reels ASMR dari video service ini", "potong jadi beberapa reels", "edit ASMR capcut", or a long .mp4 plus a song file.
---

# CapCut ASMR reels

## Overview

One long process video plus one song becomes several CapCut drafts at 1080x1920, 60 fps, each 15–60 s. Every draft holds the best moments of one part of the work, sped up where the action repeats. Each clip sits sharp in the middle over a blurred copy of itself, and a section of the song runs under it with a fade in and out. There is no text and no SFX: the picture and the song carry the reel.

Work split:
- `scripts/scan.py` makes contact sheets stamped with source times: a coarse pass over the whole video, then 1-second passes over the windows you pick.
- **You** read the sheets, map the stages of the work, propose the reels, pick each moment to the second, and write `plan.json`.
- `scripts/build_reels.py` checks the plan, renders preview sheets of exactly what each clip will show, and writes one draft per reel. It clones layers from the `capcut-auto-edit` template through that skill's draft writer, so both skills must sit side by side (they ship together in this plugin).

Requirements: macOS with CapCut, and `ffmpeg`. Check with `command -v ffmpeg`.

## Workflow

Keep working files in a scratch folder (`<work>`), never inside the CapCut drafts folder.

1. **Get the video and the song.** The song can be any audio file; a `.webm` downloaded from YouTube is fine. Tell the user once: popular songs are copyrighted, and Instagram often mutes them on business accounts when they are baked into the video. The safe route is to leave `music` out of the plan and pick the song from Instagram's own library when posting.
2. **Scan the whole video** with `run_in_background` (about 25 s for 33 minutes):
   ```bash
   python3 <skill>/scripts/scan.py "<video>" "<work>/scan"
   ```
   It prints each sheet and the time span it covers. Read every sheet. Write down the stages of the work with their time ranges, for example: unscrew the bottom case 0:50–2:30, lift the cover 3:45, take the heatsink off 6:48, wipe the old paste 7:15–8:10, brush the fans 11:40–16:40, new paste 18:40–19:40, reassemble 21:00–27:40, wipe and power on 28:00–30:10.
3. **Propose the reels and wait for an OK.** Recommend one full-journey reel (45–60 s) plus one reel per stage that has at least about 20 s of good footage (15–30 s each), at most 5 reels in all. Show each reel as a short list of moments with their source times. Take the user's changes.
4. **Fine-scan every moment you intend to use**, at one frame per second:
   ```bash
   python3 <skill>/scripts/scan.py "<video>" "<work>/fine-<start>" --start <start> --end <start+20> --every 1
   ```
   Pick the second the action starts. Several fine scans can run in parallel.
5. **Write `<work>/plan.json`** as described below, following the editing rules.
6. **Dry-run and read the previews:**
   ```bash
   python3 <skill>/scripts/build_reels.py "<work>/plan.json" --dry-run
   ```
   It prints every reel's clips (output time, source time, speed, zoom) with warnings, and writes `<work>/preview/reel-N-K.jpg`: one row per clip, showing its first, middle and last frame cropped to what will be sharp on screen. Read every sheet. Fix a clip when one of its frames shows:
   - the floor, feet, walking, or a blurred whip of the camera (move `at` or drop the clip),
   - empty hands, or hands leaving the frame (shorten `dur` or move `at`),
   - the subject cut off by the crop (set `focus`, or lower `zoom`),
   - nothing changing from first to last frame (raise `speed` or pick another moment).

   Dry-run again until every row looks right.
7. **Build.** Run the same command without `--dry-run`. Each reel becomes a new draft folder in CapCut's projects folder, named after the reel (a number is added if the name exists; nothing is overwritten). The song section is written into the draft folder as `bgm.m4a`. CapCut picks new drafts up by itself; if one does not appear, the user restarts CapCut.
8. **Report** each draft's name and length, and the stages each reel covers. Offer changes ("hook-nya ganti", "reel kipas lebih pendek"): edit the plan and build again.

## Editing rules

- **Hook first.** The first clip (1.5–2.5 s) is the most satisfying payoff of that reel: the keyboard backlight coming on, heatpipes revealed as the cover lifts, fresh paste spreading, a clean fan. Showing the result first is fine; the reel ends on it again.
- **Then the real order of the work.** Do not shuffle the steps after the hook.
- **One clip, one action that visibly progresses:** a screw comes out, a brush stroke clears dust, paste spreads. Start when the hands are already on it.
- **1.5–3 s on screen per clip.** Speed: repetitive actions (unscrewing, prying the case, brushing fins) ×2–3; delicate ones (paste, lifting the heatsink, lights coming on) ×1–1.5. Past ×3 the motion turns jerky.
- **End on the payoff,** held 2.5–3 s.
- **Skip** walking, the floor, feet, the head turned away, hunting for a tool, the phone, chatting with the customer. A head-mounted camera does these between almost every action, so expect most of the footage to be unusable.
- **Framing:** `zoom` 1.7 by default. Use 1.0–1.3 when the whole laptop matters (closing the case, the keyboard lighting up), and up to about 2.5 for small details with `focus` on them. A 720p source turns soft beyond 2.5. If the camera burns a date stamp into a top corner, 1.7 hides most of it and 2.0 hides all of it.

## plan.json

Times are seconds in the source video. Relative paths resolve from the plan's folder.

```json
{
  "video": "/Users/me/Downloads/service.mp4",
  "music": "/Users/me/Downloads/song.webm",
  "reels": [
    {"name": "ASMR Service - Repaste", "music_start": 0, "clips": [
      {"at": 1126, "dur": 2.0, "speed": 1.5},
      {"at": 409, "dur": 2.0},
      {"at": 437, "dur": 3.0, "speed": 2},
      {"at": 1340, "dur": 3.0, "speed": 3, "zoom": 1.2},
      {"at": 255, "dur": 2.5, "speed": 3, "focus": 0.65}
    ]}
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `video` | yes | The long source video. Its own sound is muted. |
| `music` | no | The song. Left out, the drafts have no audio track. |
| `reels[].name` | yes | Draft name in CapCut. |
| `reels[].music_start` | no | Where in the song the reel starts, in seconds (default 0, the intro). |
| `reels[].music_volume` | no | Song volume, 1.0 by default. |
| `clips[].at` | yes | Source time the clip starts at. |
| `clips[].dur` | yes | Seconds the clip lasts on screen. It uses `dur × speed` seconds of the source. |
| `clips[].speed` | no | Playback speed, 1 by default. |
| `clips[].zoom` | no | Size over the blurred background: 1 fits the width, 1.7 by default. |
| `clips[].focus` | no | Horizontal point to keep centred when zoomed, 0 left … 1 right (default 0.5). |

## Notes

- The video is linked by its path, not copied. Tell the user not to move or delete it until the reels are exported.
- Cuts are not timed to the song's beat.
- The tuning constants (default zoom, fades, reel length bounds) sit at the top of `build_reels.py`. Change them there, not per video.
