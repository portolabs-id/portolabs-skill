---
name: capcut-webinar-edit
description: Use when cutting a long recorded webinar, live class or Zoom session (often 1–2 hours) into several lesson videos, one topic each, with the Portolabs intro and outro, as CapCut drafts for a classmate, e.g. "potong webinar ini jadi beberapa materi", "edit rekaman kelas jadi video classmate", "pecah zoom per materi", or a long .mp4 or Drive link of a webinar recording.
---

# CapCut webinar lessons

## Overview

One long webinar recording becomes one CapCut draft per lesson, at 1920x1080 and 30 fps: the Portolabs logo sting (8 s), the lesson, the sting again. **Only the material stays.** Chat, polls, waiting, QnA, promos and the closing are cut. Each lesson covers one topic, usually 2–20 minutes. The exported videos are what `classmate-import` turns into a classmate.

Work split:
- `capcut-auto-edit/scripts/transcribe.py` writes every word with its time, and the silences from the audio. It transcribes each stretch of speech on its own: one whisper run over a whole hour hallucinates for minutes ("Sampai Sampai Sampai…").
- `capcut-asmr-edit/scripts/scan.py` makes contact sheets, so you see where the slides, the screen-share practice and the QnA are.
- **You** map the recording, propose the lessons, wait for the user's OK, and write `plan.json` by word index.
- `scripts/build_webinar.py` checks the plan and writes one draft per lesson. It cuts on the real audio, so no word is clipped, and shrinks pauses over 3 s to 1 s.

Requirements: macOS with CapCut, `ffmpeg` and `mlx_whisper` (`uv tool install mlx-whisper`). `capcut-auto-edit` and `capcut-asmr-edit` must sit next to this skill; they ship together in this plugin. Below, `<skills>` is the folder that holds all three.

## Workflow

Keep working files in a scratch folder (`<work>`), never inside the CapCut drafts folder.

1. **Get the recording.** A local path is used as it is. For a Drive link, take the file id and check that it is shared and how big it is:
   ```bash
   curl -s -r 0-0 --max-time 30 -D - -o /dev/null "https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t" | grep -iE '^content-(disposition|range)'
   ```
   No lines back (check twice; Drive is sometimes slow): ask the user to share it as "Anyone with the link". Then download it with `run_in_background`:
   ```bash
   caffeinate -is curl -sSL -C - --retry 5 --retry-all-errors --speed-limit 10000 --speed-time 60 -o "<work>/webinar.mp4" "https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t"
   ```
2. **Transcribe** with `run_in_background`. An hour of audio takes about 20–25 minutes:
   ```bash
   caffeinate -is python3 <skills>/capcut-auto-edit/scripts/transcribe.py "<video>" "<work>" > "<work>/transcript.txt"
   ```
   It writes `words.json` and `audio.json`. `transcript.txt` has one line per stretch of speech: its start in seconds, then `[index]word`, then `‖` and the pause after it.
3. **While it runs**, scan the video and read every sheet:
   ```bash
   python3 <skills>/capcut-asmr-edit/scripts/scan.py "<video>" "<work>/scan"
   ```
   Write down where the slides run, where the speaker shares the screen to practise, and where the QnA, people on camera, and the closing start. In the same message, ask the user which number the first lesson gets: lessons are numbered across a whole series, so day 2 continues after day 1's last number. Default 1.
4. **Read the whole transcript** in chunks, start to end. Map every part as either a lesson topic or something to drop (next sections), each with its word range and times.
5. **Write `<work>/plan.json`** with the lessons you will propose, as described below.
6. **Dry-run:**
   ```bash
   python3 <skills>/capcut-webinar-edit/scripts/build_webinar.py "<work>/plan.json" --dry-run
   ```
   For each lesson it prints the minutes of material and, for each kept range, its first and last words. Fix the plan and dry-run again until:
   - every range starts at the beginning of a sentence and ends at the end of one. Whisper's punctuation is unreliable, so read the words on both sides of each edge in the transcript, and move the edge if the thought runs on;
   - every `WARNING` has a reason you can give the user (a lesson outside 2–20 min, the same words kept in two lessons);
   - every stretch in the `Not used` list (10 s or longer) is one you meant to drop. Material there means a range ends too early or starts too late.
7. **Propose and wait.** Show the lessons as a table: `#`, title, each kept range as start–end in the recording (mark an added QnA answer "+ QnA"), minutes of material from the dry-run, and what it covers. Then list everything you drop, with its times and the reason. Ask: "Pembagian materi dan bagian yang dibuang ini sudah benar?" Build nothing until the user approves. Apply their edits to the plan and dry-run again.
8. **Build.** Run the same command without `--dry-run`. Each lesson becomes a new draft named `#<n> <title>`; an existing draft is never overwritten (a number is added). CapCut picks new drafts up by itself; if one does not appear, the user restarts CapCut.
9. **Report** each draft's name and length, and what was dropped. Tell the user: export each draft in CapCut at 1080p, put the MP4s in one Drive folder, and run `classmate-import` on it. The export file name is the draft name.

## What stays, what goes

Keep the speaker teaching: explanations, slides, demos, assignments given to the participants, and feedback on participants' work when the speaker teaches through it (what works, what to fix). The overview of the session ("hari ini kita akan belajar…") and the speaker's own introduction (name, role, Instagram) make the first lesson, "Perkenalan Materi & Speaker", even when it is short. A line from the host or a participant stays only when the speaker's next words make no sense without it.

Drop:

| Drop | You recognize it by |
|---|---|
| Opening small talk and housekeeping | waiting for people to join, the host introducing the speaker, "nanti dibantu baca chat ya Kak…" |
| Chat and polls | "boleh tulis di chat", "kasih emot api kalau…", reading out participants' names or answers |
| Waiting and hands-on time | "2 menit ya", participants editing a shared design together, silence while everyone works |
| Failed or repeated demos | "kok nggak berubah", "kita ulangi lagi", fixing the screen, camera or mic. Keep a demo up to its last result that worked; a demo that never shows a working result goes entirely. |
| QnA | "sesi QnA", raise hand, participants on camera asking |
| Promo and event business | giveaways (Portolabs Premium), certificate requirements, "share di sosmed", other programs, sponsors, registration links |
| Closing | kesan-pesan, foto bersama, thanks and goodbye |

A QnA answer that teaches something about one of the lessons may be added to the end of that lesson. Propose it in the table; do not add it silently. Start it where the speaker starts answering; keep the question only when the answer makes no sense without it.

Whisper fills silence with phrases nobody said: "Terima kasih.", "Selamat menikmati", "Sampai jumpa", "Jangan lupa like, share dan subscribe", "hai, hai, hai", or one word repeated for minutes. Read them as silence: never a reason to keep a stretch, and never the first or last word of a range. Inside a range, leave them; the builder shrinks long silences anyway.

## Splitting into lessons

- **One topic per lesson.** A new topic starts where the slide title changes or the speaker moves on ("selanjutnya…", "nah sekarang kita…", "oke kita lanjut").
- **2–20 minutes of material.** A part that stands on its own may be shorter: the introduction, or the assignment given at the end. Merge any other short topic into the neighbour it belongs with. Two short neighbours that fit together share one lesson whose title names both ("Kegunaan & Hak Cipta Canva"). Split a topic over 20 minutes at a sub-topic.
- **Follow the recording's order,** for the lessons and for the ranges inside each lesson. The one exception is a QnA answer added at the end. A task the speaker explains mid-session stays where it was said, in whichever neighbouring lesson it belongs with (a task for the practice that follows opens that practice lesson). A lesson may skip a short aside inside it (a chat question in the middle): use several ranges.
- **Cut between sentences,** never in the middle of a thought.
- **Titles:** short Indonesian, product names as they are ("Prinsip Desain", "Canva Legal vs Ilegal"), no "Part 1".

## plan.json

Relative paths resolve from the plan's folder. `keep` ranges are word indices from the transcript, both ends included.

```json
{
  "video": "/Users/me/Downloads/Canva Mini Class Day 1.mp4",
  "words": "words.json",
  "first_number": 1,
  "lessons": [
    {"title": "Perkenalan Materi & Speaker", "keep": [[48, 132], [175, 236]]},
    {"title": "Mengenal Canva", "keep": [[262, 610], [771, 1450]]}
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `video` | yes | The webinar recording. |
| `words` | no | `words.json` from `transcribe.py` (default `words.json`); `audio.json` must sit next to it. |
| `first_number` | no | Number of the first lesson (default 1). |
| `lessons[].title` | yes | Lesson title; the draft is named `#<n> <title>`. |
| `lessons[].keep` | yes | `[[first word, last word], …]` in the order they play. |
| `intro`, `outro` | no | Another video instead of the Portolabs sting in `assets/`. |

## Notes

- The recording is linked by its path, not copied. Tell the user not to move or delete it until every lesson is exported. The stings are copied into each draft folder.
- Cuts are plain cuts. There are no subtitles, texts or music.
- The tuning constants (longest pause, kept pause, lesson length, canvas) sit at the top of `build_webinar.py`. Change them there, not per webinar.
