---
name: classmate-import
description: Use when inserting a Portolabs classmate (kelas/course) from a Google Drive folder of videos through Chrome, e.g. "insert data classmate", "masukin video kelas dari drive", "import materi classmate", or a drive.google.com/drive/folders link meant for a kelas.
---

# Portolabs classmate import from Google Drive

## Overview

One Drive folder of MP4s becomes one Classmate with ordered lessons grouped into modules. File names are often random, so **you** decide the order and the modules, show them as a table, and write nothing to Strapi until the user approves it.

The Strapi admin at `https://api.portolabs.id/admin` is **production**. Save everything as a draft. Publish only when the user says so in this conversation.

Data model (`src/api/classmate*/content-types/*/schema.json` in the brief-service repo, `portolabs-id/portolabs-admin`):
- **Classmate**: `title`, `description`, `difficulty` (beginner/intermediate/advanced), `accessType` (required: free/premium/price/premium_or_price), `price`; `slug` fills itself.
- **Classmate Lesson**: `title`, `order`, `moduleTitle`, `moduleOrder`, `isFree`, `classmate` relation, `video_id` (the r2-video field).
- The site sorts lessons **and tests** of a classmate by one shared `order`, and groups them by `moduleOrder`/`moduleTitle`. So `order` runs 1..N across the whole course, not per module.

## Workflow

Use the Claude in Chrome tools (`mcp__claude-in-chrome__*`); the user is signed in to Google and Strapi there. Never type a password: on a sign-in page, ask the user to sign in.

1. **List the files.** Take the folder id from the link (`/folders/<id>`), open `https://drive.google.com/embeddedfolderview?id=<id>#list`, and read it with `javascript_tool`:
   ```js
   [...document.querySelectorAll('a[href*="/file/d/"]')].map((a) => ({
     id: a.href.match(/\/file\/d\/([\w-]+)/)[1],
     name: (a.querySelector('.flip-entry-title') ?? a).innerText.trim(),
   }))
   ```
   Empty result: open the folder itself in List view, scroll to the end, and read names and ids from the rows. Keep `.mp4` files; list every other file (PDF, PPT, MOV) as skipped.
2. **Check sharing.** The server downloads without a Google login, so every file must be "Anyone with the link". For each id:
   ```bash
   curl -s -r 0-0 --max-time 20 -D - -o /dev/null "https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t" | grep -i content-disposition
   ```
   No `Content-Disposition` line: the file is private. Ask the user to share the folder as "Anyone with the link", then check again.
3. **Order and group** (see the next section) and show the table. Stop until the user approves or edits it.
4. **Target classmate.** Ask: new Classmate, or add to an existing one?
   - New: ask `accessType` (and `price` for price types), `difficulty` and an optional description. Create it at `/admin/content-manager/collection-types/api::classmate.classmate/create`, title from the approved table, then **Save** (not Publish).
   - Existing: open it, read its lessons and tests, and continue after the highest `order` and `moduleOrder`. Reuse an existing `moduleTitle` only when the user's table says so.
5. **One lesson at a time, in table order**, at `/admin/content-manager/collection-types/api::classmate-lesson.classmate-lesson/create`:
   1. Fill `title`, `order`, `moduleTitle`, `moduleOrder`, `isFree` (ask once which lessons are free previews; default off) and pick the classmate in the `classmate` relation box.
   2. Under "Atau import dari Google Drive", put the same link `https://drive.google.com/file/d/<id>/view` in **Link Drive 720p** and **Link Drive 480p**. Replace "video_id baru" with `<classmate-slug>-<NN>` (`NN` = `order`, two digits).
   3. Click **Import dari Drive**. The box shows "Server menyalin dari Google Drive…". Check it about every 30 s with `find`/`read_page`; do not leave the page while it runs. The server imports one video at a time, so a long folder takes a while.
   4. On "Selesai. Klik Save untuk menyimpan.", click **Save**. Then click **Generate Thumbnail** in the side panel (it answers right away).
6. **Report**: the final table with each lesson's `video_id`, the classmate admin link, skipped files, and any failure. Say that everything is still a draft.

## Ordering and grouping

Clean each name first: drop the extension, leading numbers, and noise such as `720p`, `final`, `fix`, `rev`, `v2`, `copy of`, `(1)`, `_`.

Decide the order from the strongest signal you have:
1. **Numbers in the name**: `01`, `1.2`, `M2-03`, `Part 3`, `Eps 4`, `Sesi 2`, `Day 5`. `1.2` means module 1, lesson 2.
2. **Topic logic**: intro/pengenalan/overview first, then setup/instalasi, basics before advanced, studi kasus/project/latihan near the end, penutup/kesimpulan/outro last.
3. **Unreadable names** (`IMG_1234`, `video (3)`, `Rekaman 2026-…`): open the folder in Grid view and `zoom` into each thumbnail, or open the file's preview and screenshot the first frame, to read its title card. Then use the dates in the Drive list as a tiebreaker.

Group into modules by shared topic, usually 3–7 lessons each. Under 6 videos with one topic: one module. Give modules short Indonesian titles ("Pengenalan Figma", not "Module 1"). Clean lesson titles into readable Indonesian, keeping product names as they are.

Duplicates (same lesson as `v1` and `v2`, or `_720` and `_480`): keep the newest or the 720 one, and list the other as skipped.

Show the plan in this shape, and mark every row you guessed with `?` in **Alasan**:

| moduleOrder | Modul | order | Judul lesson | File asli | Alasan |
|---|---|---|---|---|---|
| 1 | Pengenalan Figma | 1 | Apa itu Figma | `rec_final2.mp4` | judul "intro" |
| 1 | Pengenalan Figma | 2 | Instalasi dan akun | `IMG_4410.mp4` | ? title card "Install" |

Then list skipped files with the reason, and ask: "Urutan dan modul ini sudah benar?"

## Errors

| Message | Do |
|---|---|
| "Video … sudah ada di R2. Pakai video_id lain." | Add `-2` to the video_id and import again. |
| "… tidak bisa didownload. Pastikan sharing-nya \"Anyone with the link\"." | Ask the user to fix sharing, then import again. |
| "… bukan MP4." / "… lebih dari 5 GB." | Skip the lesson and report it. |
| "File video belum ada di R2 …" on Save | The import is not finished. Wait for "Selesai", then Save. |

## Red flags

| Thought | Do instead |
|---|---|
| "Urutannya sudah jelas, langsung input saja" | Show the table and wait for the user's approval. |
| "Order mulai dari 1 lagi tiap modul" | `order` is one sequence across the course, after any existing lessons and tests. |
| "Publish biar langsung kelihatan" | Save as draft. Publish only when the user asks. |
| "Upload videonya lewat browser" | Use **Import dari Drive**. The server copies the file. |
| "Strapi minta login, isi saja passwordnya" | Ask the user to sign in. |
