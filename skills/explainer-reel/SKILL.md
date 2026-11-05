---
name: explainer-reel
description: Use when making a vertical explainer reel from a topic in the clean grid style (word-by-word captions with blue selection boxes, a progress rail, UI cards, real logos and screenshots), voiced with ElevenLabs and delivered as a CapCut draft, e.g. "bikin reel explainer", "bikin konten reel tentang X", "riset terus bikin script, motion, dubbing", "reel kayak mrcreates", or a topic plus reference reel links.
---

# Explainer reel

## Overview

A topic becomes a 60–90 s vertical reel in four steps. Each step ends with something the user
sees before the next one starts:

1. **Research** → `research.md`: the angle, hook options, facts with their sources.
2. **Script** → `script.json`, approved by the user. Nothing is voiced before that: voice costs credits.
3. **Produce** → ElevenLabs voice, word timing, logos and screenshots, motion rendered with HyperFrames.
4. **Assemble** → a CapCut draft (motion, voice, SFX) and `preview.mp4`. The user adds music, exports, posts.

The look and how to write scenes: [references/style.md](references/style.md). How the reference
reel was analysed, and why HyperFrames: [references/reference-analysis.md](references/reference-analysis.md).

**Say so when a step needs something this skill cannot do:**

| Cannot | Instead |
|---|---|
| Instagram insights, trending audio | the user checks them in the app |
| Pages behind a login or a bot check (Cloudflare): no screenshot | a public page, or the user's own screenshot in the brand kit |
| A logo whose site gives only a blurry icon and Simple Icons lacks | the official file in the brand kit |
| Licensed music | the user picks it from CapCut's library |
| Stock photos | the user's own images, or leave them out |
| Creating the ElevenLabs account or key | the user does it and sets the environment variables |
| Exporting from CapCut, posting | the user |

## Requirements

- `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` set in the user's shell profile. Never ask them to
  paste the key in chat. `python3 scripts/tts.py --list-voices` lists the voices in their account
  (add an Indonesian voice from ElevenLabs' Voice Library first).
- macOS with CapCut, `ffmpeg`, `uv`, Node ≥ 22, Google Chrome. The `capcut-auto-edit` skill next to this one.
- Prefix every `npx hyperframes` call with `DO_NOT_TRACK=1`.

Work in `~/Movies/explainer-reel/<slug>/` (`<work>`). CapCut links media by path, so never work in a
temporary folder. `<skill>` is this skill's folder; `<capcut>` is `capcut-auto-edit`'s.

## 1. Research

1. Settle the topic and who it is for with the user, in one question if it is unclear.
2. Facts: WebSearch and WebFetch, primary sources first. Every number or claim gets its source.
3. Reference reels, when the user gives links. Downloading reads their browser's login cookies, so
   ask first, and say macOS will ask for keychain access:
   ```bash
   uv run <skill>/scripts/download_reference.py "<url>" <work>/refs --browser chrome
   ```
   Dia and Arc: `--chromium-dir "~/Library/Application Support/Dia/User Data" --keyring Dia`.
   Then study it as in `reference-analysis.md`: transcript (`mlx_whisper`), a 1 fps contact sheet, cuts, loudness.
4. Write `<work>/research.md`: the angle, three hook options, 5–8 facts with sources, notes from the references.

## 2. Script

Structure: **hook** (a problem, a number, a promise of time) → **numbered beats**, one action and one
visual each → **recap** → **one thesis line** → **CTA** (one action). About 200–300 words for 60–90 s.
Spoken Indonesian; names spelt as they should appear on screen (the words on screen are the script's).

```json
{"title": "Lima tool buat edit reel",
 "beats": [
  {"id": "hook", "chip": "Hook", "vo": "Kamu cuma butuh lima tool.", "sel": ["lima"], "em": ["tool."], "assets": []},
  {"id": "tools", "chip": "Lima tool", "vo": "Claude yang bikin motion-nya.", "sel": ["Claude"], "em": ["motion-nya."],
   "assets": [{"name": "claude", "domain": "claude.ai", "logo": "claude"}]}
 ]}
```

- `id`: lowercase letters, digits, `-`. `chip`: 1–3 words for the rail.
- `sel` and `em` are words of that beat's `vo`, spelt exactly as there, punctuation included (style.md, Captions).
- `assets`: what the beat shows, in `fetch_assets.py`'s format: a logo by `domain` and Simple Icons
  slug `logo`, or a `screenshot` URL.

Show the user the script as plain text, beat by beat, with the visual idea of each beat and the
estimated length. **Wait for their approval.** Save it as `<work>/script.json`.

## 3. Produce

1. **Voice:**
   ```bash
   python3 <skill>/scripts/tts.py <work>/script.json <work>
   ```
   Writes `voice.mp3`, `voice.mp4`, `words.json`, `audio.json`, `beats.json` and a starting `plan.json`.
   Tell the user `voice.mp3` is ready to listen to; a wrong pronunciation is fixed by respelling the
   word in `vo` and voicing again.
2. **Timing:** pauses over 0.3 s are cut, so the motion is timed from the edit, not from the voice:
   ```bash
   python3 <capcut>/scripts/build_draft.py <work>/plan.json --timeline
   ```
3. **Assets:** collect every beat's `assets` into `<work>/assets.json`, then:
   ```bash
   uv run <skill>/scripts/fetch_assets.py <work>/assets.json <work>/assets [--brand-dir <dir>]
   ```
   **Look at every logo and screenshot** (read the image files) before using them: a wrong or old
   mark, a blurry icon, a cookie wall. Fix with a `url` to the right file or a file in the brand kit,
   and run it again. Logos are never recoloured.
4. **Motion:**
   ```bash
   python3 <skill>/scripts/new_composition.py <work>
   ```
   Write the `SCENES` block of `<work>/motion/index.html`, one scene per beat (style.md). Then, in `<work>/motion`:
   ```bash
   DO_NOT_TRACK=1 npx -y hyperframes@0.9.14 check
   DO_NOT_TRACK=1 npx -y hyperframes@0.9.14 snapshot --at <start of each beat>,<last second>
   DO_NOT_TRACK=1 npx -y hyperframes@0.9.14 render -f 60 -o ../motion.mp4
   ```
   Fix every ✗ from `check`, and read the snapshot contact sheet before rendering.

After the voice changes, run steps 1, 2 and `new_composition.py` again (it keeps the scenes
written), and check the scenes still fit their words. Never change `keep`, `word_fixes` or
`end_hold` in `plan.json` after the render: the motion would fall out of sync.

## 4. Assemble

```bash
python3 <capcut>/scripts/build_draft.py <work>/plan.json
python3 <skill>/scripts/preview_draft.py "<draft dir it printed>" <work>/motion.mp4 <work>/preview.mp4
```

Send the user `preview.mp4` (motion with the voice exactly as the draft cuts it). Then tell them:
open the draft in CapCut, add music from CapCut's library about 12 dB under the voice, export
1080x1920, post.
