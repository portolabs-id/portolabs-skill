---
name: classmate-import
description: Use when inserting a Portolabs classmate (kelas/course) from a Google Drive folder of videos through Chrome, e.g. "insert data classmate", "masukin video kelas dari drive", "import materi classmate", or a drive.google.com/drive/folders link meant for a kelas.
---

# Portolabs classmate import from Google Drive

## Overview

One Drive folder of MP4s becomes one Classmate with ordered lessons grouped into modules, each with a one-paragraph summary of its video in `content` under `## Rangkuman`. File names are often random, so **you** decide the order and the modules, show them with the summaries, and write nothing to Strapi until the user approves it.

The Strapi admin at `https://api.portolabs.id/admin` is **production**. Save everything as a draft. Publish only when the user says so in this conversation.

Data model (`src/api/classmate*/content-types/*/schema.json` in the brief-service repo, `portolabs-id/portolabs-admin`):
- **Classmate**: `title`, `description`, `difficulty` (beginner/intermediate/advanced), `accessType` (required: free/premium/price/premium_or_price), `price`; `slug` fills itself.
- **Classmate Lesson**: `title`, `order`, `moduleTitle`, `moduleOrder`, `isFree`, `classmate` relation, `video_id` (the r2-video field).
- The site sorts lessons **and tests** of a classmate by one shared `order`, and groups them by `moduleOrder`/`moduleTitle`. So `order` runs 1..N across the whole course, not per module.

## Workflow

Use the Claude in Chrome tools (`mcp__claude-in-chrome__*`); the user is signed in to Google and Strapi there. Never type a password: on a sign-in page, ask the user to sign in.

1. **List the files.** Open the folder link as the user gave it (keep its `/u/<n>/` account index) and read the rows with `javascript_tool`:
   ```js
   [...new Map([...document.querySelectorAll('[data-id]')]
     .filter((e) => /^[\w-]{20,}$/.test(e.dataset.id))
     .map((e) => [e.dataset.id, (e.getAttribute('aria-label') || e.innerText).replace(/\s+/g, ' ').trim()]))]
     .map(([id, name]) => `${name} | ${id.match(/.{1,3}/g).join(' ')}`)
   ```
   The browser tool replaces strings that look like base64 with `[BLOCKED: Base64 encoded data]`, and Drive ids do. So the snippet returns each id in groups of 3 characters: remove the spaces before you use it. The first row is the folder itself. Drive renders only the rows on screen, so in a long folder scroll to the end and run it again. Keep `.mp4` files. List every other file (PDF, PPT, MOV) as skipped, and also any file whose name says not to use it (`[DO NOT UPLOAD]`, `jangan dipakai`).
2. **Check sharing.** The server downloads without a Google login, so every file must be "Anyone with the link". Put `<order> <id>` lines in a scratchpad file and run:
   ```bash
   while read -r n id; do echo "$n $(curl -s -r 0-0 --max-time 30 -D - -o /dev/null "https://drive.usercontent.google.com/download?id=$id&export=download&confirm=t" | grep -iE '^content-(disposition|range)' | tr -d '\r' | tr '\n' ' ')"; done < ids.txt
   ```
   Drive sometimes answers slowly and the line comes back empty. Check every empty line once more before you call the file private. Still empty: ask the user to share the folder as "Anyone with the link", then check again. `Content-Range` ends with the file size: a file near 1 GB takes about 5 minutes to import.
3. **Transcribe.** Needs `mlx_whisper` (`command -v mlx_whisper`). If it is missing, ask the user to run `uv tool install mlx-whisper`. Its first run downloads the model (about 1.6 GB, around 10 minutes). In the scratchpad, start this with `run_in_background` and carry on while it runs:
   ```bash
   caffeinate -is zsh -c 'mkdir -p transcripts && while read -r n id; do
     curl -sSL -C - --retry 5 --retry-all-errors --speed-limit 10000 --speed-time 60 -o "transcripts/$n.mp4" "https://drive.usercontent.google.com/download?id=$id&export=download&confirm=t" &&
     ffmpeg -nostdin -loglevel error -y -i "transcripts/$n.mp4" -vn -ac 1 -ar 16000 -c:a libmp3lame -b:a 32k "transcripts/$n.mp3" &&
     rm "transcripts/$n.mp4" &&
     mlx_whisper "transcripts/$n.mp3" --model mlx-community/whisper-large-v3-turbo --language id --output-format txt --output-dir transcripts --verbose False < /dev/null || echo "GAGAL $n"
   done < ids.txt'
   ```
   `caffeinate -is` keeps the Mac awake while the loop runs. Without it, an idle Mac sleeps and freezes the downloads for hours. It cannot keep a closed lid awake on battery, so ask the user to leave the lid open or the Mac on power. `curl` gives up on a download stuck under 10 KB/s for 60 s and resumes it (`-C -`). Do not point `ffmpeg` at the Drive URL: it has no timeout. Only one MP4 is on disk at a time. Whisper does an hour of audio in about 3 minutes. Run `GAGAL` lines again, alone.
4. **Summarize.** When the transcripts are done, give one subagent (`model: "sonnet"`) the `transcripts/` folder and this brief: for each `<n>.txt`, write one paragraph of 3–5 sentences in Indonesian about what the video teaches, using only what the transcript says. Fix names whisper mishears (it writes "portalabs" for Portolabs). State the content directly: no "teman-teman", no "di video ini". A transcript under 30 words (music, silence) gets no summary. Write `summaries.md` with a `## <n>` heading per file. Read only `summaries.md`, so the transcripts stay out of your context.
5. **Order and group** (see the next section) and show the table, then the summaries by `order`. Stop until the user approves or edits both.
6. **Target classmate.** Ask: new Classmate, or add to an existing one? Ask this while the transcription runs.
   - New: ask `accessType` (and `price` for price types), `difficulty` and an optional description. Create it at `/admin/content-manager/collection-types/api::classmate.classmate/create`, title from the approved table, then **Save** (not Publish).
   - Existing: open it, read its lessons and tests, and continue after the highest `order` and `moduleOrder`. Reuse an existing `moduleTitle` only when the user's table says so.
7. **One lesson at a time, in table order**, at `/admin/content-manager/collection-types/api::classmate-lesson.classmate-lesson/create`. Ask once which lessons are free previews (`isFree`, default off). Use `browser_batch` so one lesson takes a few calls.
   1. **Text fields and Drive links** with `javascript_tool`. Fill in `f`: the same Drive link goes in both the 720p and the 480p box, `videoId` is `<classmate-slug>-<NN>` (`NN` = `order`, two digits), and `content` is the approved summary as `'## Rangkuman\n\n<paragraph>'` (escape quotes; leave `content` out for a lesson with no summary).
      ```js
      const f = { title: '…', order: 1, moduleTitle: '…', moduleOrder: 1, content: '## Rangkuman\n\n…', link: 'https://drive.google.com/file/d/<id>/view', videoId: '<classmate-slug>-01' };
      const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
      const q = (name) => document.querySelector(`[name="${name}"]`);
      const driveInputs = () => [...document.querySelectorAll('input[placeholder*="drive.google.com/file"]')];
      for (let i = 0; i < 30 && !(q('title') && driveInputs().length === 2); i++) await sleep(500);
      await sleep(1000);
      // The prototype's setter, so React sees the change; `content` is a textarea, the rest are inputs.
      const set = (el, v) => { el.focus(); Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value').set.call(el, String(v)); el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); el.blur(); };
      set(q('title'), f.title); set(q('order'), f.order); set(q('moduleTitle'), f.moduleTitle); set(q('moduleOrder'), f.moduleOrder);
      if (f.content) set(q('content'), f.content);
      driveInputs().forEach((el) => set(el, f.link));
      await sleep(500);
      // Typing a link makes the field propose "video-<6 chars>" in the "video_id baru" box.
      const draftId = [...document.querySelectorAll('input')].find((el) => /^video-[a-z0-9]{6}$/.test(el.value));
      if (!draftId) throw new Error('form not ready');
      set(draftId, f.videoId);
      ```
   2. **Classmate relation**: click the `classmate` box, type the classmate title, wait 2 s, and click the option with `computer` (find it with `find` the first time, then reuse its coordinates). A JavaScript `click()` on the option does not select it. Check that the field label now reads `classmate (1)`.
   3. **isFree**: for a free preview, click **TRUE** with `computer`.
   4. **Import**: click **Import dari Drive** (a JavaScript `click()` works here). The box shows "Server menyalin dari Google Drive…" until "Selesai. Klik Save untuk menyimpan.". Every `javascript_tool` call times out after 45 s, so check the status in short calls, about every 30 s:
      ```js
      [...document.querySelectorAll('p,span')].map((e) => e.innerText).find((t) => /Selesai|menyalin|gagal|tidak|bukan|sudah ada|lebih dari/i.test(t))
      ```
      Do not leave the page while it runs. The server imports one video at a time.
   5. **Save**, then wait until the URL no longer ends in `/create`. Click **Generate Thumbnail** in the side panel and wait about 12 s. The admin shows the thumbnail as a plain file icon (blog thumbnails look the same), so check that the field has a `lesson-thumbnail-<n>.webp` file, not a preview.
   6. After the first two lessons, reload one and check that every field was saved, including the ones set by JavaScript.
8. **Check and report.** Open `/admin/content-manager/collection-types/api::classmate-lesson.classmate-lesson?sort=order:ASC&filters[$and][0][classmate][title][$eq]=<classmate title>` and confirm the lesson count. Then report the final table with each lesson's `video_id`, the classmate admin link, skipped files, and any failure. Say that everything is still a draft.

## Ordering and grouping

Clean each name first: drop the extension, leading numbers, and noise such as `720p`, `final`, `fix`, `rev`, `v2`, `copy of`, `(1)`, `_`.

Decide the order from the strongest signal you have:
1. **Numbers in the name**: `01`, `1.2`, `M2-03`, `Part 3`, `Eps 4`, `Sesi 2`, `Day 5`. `1.2` means module 1, lesson 2.
2. **Topic logic**: intro/pengenalan/overview first, then setup/instalasi, basics before advanced, studi kasus/project/latihan near the end, penutup/kesimpulan/outro last.
3. **Unreadable names** (`IMG_1234`, `video (3)`, `Rekaman 2026-…`): read how the video opens (`head -c 600 transcripts/<n>.txt`) and its summary. Still unclear: open the folder in Grid view and `zoom` into each thumbnail to read its title card. Then use the dates in the Drive list as a tiebreaker.

Group into modules by shared topic, usually 3–7 lessons each. Under 6 videos with one topic: one module. Give modules short Indonesian titles ("Pengenalan Figma", not "Module 1"). Clean lesson titles into readable Indonesian, keeping product names as they are.

Duplicates (same lesson as `v1` and `v2`, or `_720` and `_480`): keep the newest or the 720 one, and list the other as skipped.

Show the plan in this shape, and mark every row you guessed with `?` in **Alasan**:

| moduleOrder | Modul | order | Judul lesson | File asli | Alasan |
|---|---|---|---|---|---|
| 1 | Pengenalan Figma | 1 | Apa itu Figma | `rec_final2.mp4` | judul "intro" |
| 1 | Pengenalan Figma | 2 | Instalasi dan akun | `IMG_4410.mp4` | ? title card "Install" |

Then list the summaries as `**<order>. <Judul lesson>**` followed by its paragraph, list skipped files with the reason, and ask: "Urutan, modul, dan rangkuman ini sudah benar?"

## Errors

| Message | Do |
|---|---|
| "Video … sudah ada di R2. Pakai video_id lain." | Add `-2` to the video_id and import again. |
| "… tidak bisa didownload. Pastikan sharing-nya \"Anyone with the link\"." | Ask the user to fix sharing, then import again. |
| "… bukan MP4." / "… lebih dari 5 GB." | Skip the lesson and report it. |
| "File video belum ada di R2 …" on Save | The import is not finished. Wait for "Selesai", then Save. |
| `CDP sendCommand "Runtime.evaluate" timed out after 45000ms` | Only the tool call stopped; the import keeps running. Check the status again in short calls. |
| "form not ready" from the fill snippet | The page was still loading. Run the snippet again. |

## Red flags

| Thought | Do instead |
|---|---|
| "Urutannya sudah jelas, langsung input saja" | Show the table and wait for the user's approval. |
| "Order mulai dari 1 lagi tiap modul" | `order` is one sequence across the course, after any existing lessons and tests. |
| "Publish biar langsung kelihatan" | Save as draft. Publish only when the user asks. |
| "Upload videonya lewat browser" | Use **Import dari Drive**. The server copies the file. |
| "Rangkumannya tulis dari judul saja, transkripnya lama" | Write a summary only from its transcript. No transcript, no summary: say so in the report. |
| "Strapi minta login, isi saja passwordnya" | Ask the user to sign in. |
