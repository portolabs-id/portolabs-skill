---
name: explainer-reel
description: Use when making a vertical explainer reel (30–90 s) from a topic: trend research, hooks and script first, then, once the user approves, an ElevenLabs voice, real logos and screenshots and HyperFrames motion in the clean grid style, delivered as a CapCut draft. E.g. "bikin reel explainer", "bikin konten reel tentang X", "riset tren terus bikin hook dan script", "reel kayak mrcreates", or a topic plus reference reel links.
---

# Explainer reel

## Overview

A topic becomes a 30–90 s vertical reel in two stages:

**Pre-production** (talk and documents, nothing costs money):
1. **Research** → `trends.md` and `research.md`: what is trending, the angle, facts with sources.
2. **Script** → `brief.md`: hook options, the script beat by beat with its visuals and length.

**Gate: show the brief and wait.** Do not run anything from step 3 (no voice, no assets, no
render) until the user picks a hook and says go ("jalan", "gas", "oke produksi"). Revise the
brief as often as they ask.

**Production:**
3. **Produce** → ElevenLabs voice, word timing, logos and screenshots, motion rendered with HyperFrames.
4. **Assemble** → a CapCut draft (motion, voice, SFX) and `preview.mp4`. The user adds music, exports, posts.

Storytelling (structures, hooks, voice, the brief): [references/script.md](references/script.md). The look and how to
write scenes: [references/style.md](references/style.md). How the reference reel was analysed,
and why HyperFrames: [references/reference-analysis.md](references/reference-analysis.md).

**Say so when a step needs something this skill cannot do:**

| Cannot | Instead |
|---|---|
| Instagram and TikTok search, insights, trending audio (they need a login) | trends from Google Trends and YouTube, plus reels the user links |
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

1. Settle the topic, who it is for and what they should do after watching, in one question if
   any of it is unclear.
2. **Trends:** 2–4 keywords for the niche, in the words viewers search:
   ```bash
   uv run <skill>/scripts/trend_scan.py <work> "<keyword>" "<keyword>"
   ```
   `trends.md` lists today's Google Trends in Indonesia and, per keyword, the most viewed short
   videos uploaded this month. Read it for what is rising, which angles get views, and how the top
   titles hook. A Google trend that touches the topic is a reason to make the reel now.
3. **Facts:** WebSearch and WebFetch, primary sources first. Every number or claim gets its source.
4. **Reference reels**, when the user gives links. Downloading reads their browser's login cookies,
   so ask first, and say macOS will ask for keychain access:
   ```bash
   uv run <skill>/scripts/download_reference.py "<url>" <work>/refs --browser chrome
   ```
   Dia and Arc: `--chromium-dir "~/Library/Application Support/Dia/User Data" --keyring Dia`.
   Then study it as in `reference-analysis.md`: hook, transcript (`mlx_whisper`), a 1 fps contact
   sheet, pace, loudness.
5. Write `<work>/research.md`: the angle and why now, 5–8 facts with sources, what the references
   and the trending titles do in their first three seconds.

## 2. Script

Build the story with [references/script.md](references/script.md), in its order: the one idea
and the shift it makes, the length (30–90 s, about 150 words a minute), a structure that fits,
five hooks from different patterns, beats with tension and payoff, the voice, sources, one CTA.
Run its checklist and fix what fails. Write `<work>/brief.md`, show it in chat as plain text, and
ask which hook and what to change. **Stop here until the user says go.**

After the go, write `<work>/script.json` from the chosen hook and the brief's table:

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
- The words of `vo` are the brief's, unchanged: the user approved them.

## 3. Produce

1. **Voice:**
   ```bash
   python3 <skill>/scripts/tts.py <work>/script.json <work>
   ```
   Writes `voice_raw.mp3` (as ElevenLabs returned it), `voice.mp3`, `voice.mp4`, `words.json`,
   `audio.json`, `beats.json` and a starting `plan.json`. `voice.mp3` is already mastered to a warm
   podcast sound (high-pass, more body, less mud and harsh highs, de-essed, compressed, then
   -14 LUFS under -1.5 dBTP), and everything after it is measured from it: never
   master or replace the voice later, or the cuts drift from the motion.
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
   It prints the moment each scene is fully built (`<built>`). Write the `SCENES` block of
   `<work>/motion/index.html`, one scene per beat (style.md). Then, in `<work>/motion`:
   ```bash
   DO_NOT_TRACK=1 npx -y hyperframes@0.9.14 check --at <built> --no-collapse-static
   DO_NOT_TRACK=1 npx -y hyperframes@0.9.14 snapshot --at <built>
   DO_NOT_TRACK=1 npx -y hyperframes@0.9.14 render -f 60 -o ../motion.mp4
   ```
   Always pass both flags: a bare `check` samples 9 moments and can miss a whole scene, and without
   `--no-collapse-static` a problem seen at only one of those moments is dropped. Fix every ✗,
   `text_box_overflow` (text running out of its card) included, then read the snapshot contact sheet
   before rendering (style.md, Checks before render).

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

Write the Instagram caption with the `reel-caption` skill next to this one.
