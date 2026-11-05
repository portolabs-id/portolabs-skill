# Recipe: Explainer Reel ala @mrcreates.ai (motion graphic, tanpa footage)

Referensi: https://www.instagram.com/reel/DfKFK7RJdjl/ (diunggah 2 Nov 2026, 83,6 s, 21 rb like, 16 rb komentar).
Hasil bedah: transkrip per kata (mlx_whisper large-v3-turbo), frame tiap 1 s, scene detection, analisis loudness dan spektrum.

## Temuan utama

1. **Reel ini tidak dibuat dengan workflow yang dia ajarkan.** Isinya mengajarkan "rekam video, drop raw footage, Claude potong dead air". Reel-nya sendiri justru **100% motion graphic tanpa satu frame kamera pun**: kanvas grid, kartu UI tiruan, dan avatar ilustrasi, ditambah voiceover.
2. **Tidak ada satu pun hard cut.** Scene detection di threshold 0,12 tidak menemukan apa-apa. Semua perpindahan berupa animasi kontinu dalam satu komposisi, jadi ini hampir pasti dirender dari kode (HTML/React), bukan diedit di NLE.
3. **Dugaan engine: HyperFrames (HeyGen).** Outro-nya (profil IG, follower naik, tombol Follow → Following, "+1 follower") sangat mirip blok katalog `instagram-follow` milik HyperFrames. Ini dugaan, belum terbukti.
4. Formula yang bisa ditiru: **naskah padat → voiceover → timestamp per kata → komposisi kode yang disinkronkan ke kata → render.**

## 0. Spek

| Hal | Nilai |
|---|---|
| Kanvas | 1080x1920, 30 fps |
| Durasi | ~84 s (bicara 81 s) |
| Kecepatan bicara | **~215 kata/menit** (290 kata), cepat |
| Jeda antar kata > 0,15 s | median 0,22 s, maksimum 0,52 s |
| Loudness | -14,1 LUFS integrated, -2,0 dBTP, LRA 2,0 LU (sangat dikompres, rata) |
| Musik | bed kontinu ~12 dB di bawah suara (jeda ≈ -29 s/d -32 dB, bicara ≈ -17 dB) |
| SFX | blip/pop tonal (~1–1,6 kHz) di pergantian step dan saat checklist recap tercentang |

## 1. Struktur naskah

Pola besarnya: **Hook (musuh + janji) → step bernomor → recap → kalimat tesis → CTA keyword.**

| Waktu | Chip | Isi VO (ringkas) | Visual |
|---|---|---|---|
| 0–7 s | — | Hook: semua orang edit pakai Claude, tapi setup-nya dikunci di balik kursus. Janji: "kasih 60 detik". | Avatar + counter LIVE 1.284.xxx "editing with Claude" yang terus naik. Kartu checkout "AI Video Editing Course $497" dengan badge "Setup locked". Badge timer 60 s. Lalu kartu judul "Empty folder → finished reel · 11 steps · 5 tools · 3 prompts · ~60 s". |
| 7–11,5 s | 01 Desktop app | Download Claude desktop, buka Claude Code di sana, bukan di browser. | Kartu app Claude, progress download 3% → 94% → OPEN. Tab Chat/Cowork/Code dengan Code terpilih. Teks "claude.ai in a browser" dicoret dengan X merah. |
| 11,6–19 s | 02 One folder | Buat folder "AI Video Editor" dengan 3 subfolder. | Folder baru di-rename, lalu bercabang jadi Raw Footage / References / Exports. |
| 19–24,7 s | 03 Local chat | New Claude Code chat → Local → pilih folder. | Toggle Cloud/Local pindah ke Local, path tercentang, panel "Claude can see" (Read/Write). |
| 25–37,4 s | 04 Five tools | Remotion, HyperFrames, FFmpeg, Whisper, yt-dlp. | Hub-and-spoke: logo Claude di tengah dengan counter "0/5 tools". Tiap tool menempel sebagai node saat namanya disebut, plus label fungsinya. |
| 37,6–40,6 s | 05 One prompt | Tidak perlu install manual, paste prompt. | Kartu "Manual setup checklist" (5 item) diganti kartu "PROMPT 01 Install everything". Spinner Claude "Running" dengan 5 ikon tool. |
| 40,8–47,4 s | 06 Your taste | Pilih 3–5 video referensi, paste link ke prompt. | Papan gabus "MY TASTE" bertulisan "Taste: unknown?", lalu polaroid tertempel dengan benang merah. Kartu "PROMPT 02 Learn my taste · 5 links". |
| 47,6–52 s | 07 The key line | Baris terpenting: "inspired by them, not a copy". | Editor `prompt-02.md`, baris 4 di-highlight. Diff: `- make it a copy` (merah), `+ make it inspired by them` (hijau). |
| 52,2–54,7 s | 08 Stand out | Supaya tidak terlihat sama dengan orang lain. | Deretan thumbnail HP abu-abu, satu yang berwarna ("yours") naik. |
| 54,8–59 s | 09 Film & drop | Rekam seperti biasa, drop file mentah. | Viewfinder REC, file `clip_001.mp4` jatuh ke folder Raw Footage. |
| 59,1–64,6 s | 10 Claude edits | Prompt edit: potong dead air, caption, musik, layout untuk review. | Kartu "PROMPT 03 Edit". Layer isometrik (waveform, caption, cut) menumpuk. Badge "Ready for your review". |
| 64,8–69,1 s | 11 Feedback | Revisi pakai bahasa biasa, contohnya "make the hook bigger". | Mockup HP "THE HOOK" dan voice note. Teks hook lalu membesar. |
| 69,2–72,6 s | Recap | "Itu workflow lengkapnya, dari folder kosong ke reel jadi." | Checklist 12 baris tercentang satu per satu sampai "Finished reel". |
| 72,7–75,3 s | Tesis | "Tools yang motong, taste kamu yang menentukan sisanya." | Kartu terbelah dua: TOOLS (ikon + gunting, "do the cutting") vs YOUR TASTE (Aa/Aa, titik warna, kurva, "does the rest"). |
| 75,4–83,6 s | CTA | Comment keyword, dikirimi 3 prompt, follow untuk episode berikutnya. | Kolom komentar IG mengetik "EDI…", DM "sent you all 3 prompts", profil dengan follower naik, kursor klik Follow → Following, "+1 follower", kartu "Next episode: My editing style" dari Locked ke Unlocked. |

Aturan naskah yang bisa diambil:

- **Hook = musuh + angka + janji waktu.** Musuhnya kursus $497, angkanya counter live, janjinya 60 detik.
- **Satu step = satu kalimat aksi = satu chip = satu visual.** Tidak ada step tanpa visual khusus.
- **Satu "key line" diberi panggung sendiri** (step 07). Ini inti tesisnya.
- **Recap visual** di akhir (checklist semua step) memberi rasa "lengkap".
- **CTA keyword komentar** ("EDITOR") untuk lead magnet via DM. Inilah sumber 16 rb komentar. Ditambah teaser episode berikutnya untuk follow.

## 2. Design system

| Elemen | Nilai |
|---|---|
| Background | `#fdfdfd` dengan grid garis abu tipis (sel ~72 px di 1080 px). Di CTA berubah jadi gradasi putih → biru muda. |
| Aksen | biru `#3170e8` (sampel piksel, perkiraan). Merah hanya untuk X/REC/notifikasi. |
| Teks | hitam untuk kata aktif, abu untuk kata sebelumnya dan sesudahnya. |
| Font sans | geometris, mirip Manrope/Inter (perkiraan). Dipakai untuk caption dan UI. |
| Font serif | serif italic condensed, mirip Instrument Serif (perkiraan). Hanya untuk kata penekanan. |
| Font mono | untuk file prompt/kode. |
| Kartu UI | putih, sudut bulat, bayangan lembut, gaya UI macOS/Apple. |
| Maskot | avatar line-art yang sama di semua scene (playhead rail, kamera, profil). |

### Caption (bagian paling khas)

- Satu baris di atas (~y 300/1920), 1–4 kata per halaman, rata tengah.
- **Muncul per kata dengan blur-in** (blur → tajam + fade). Kata yang belum diucapkan masih blur tipis.
- Kata sebelumnya abu, kata yang sedang diucapkan hitam.
- **Kata kunci dibungkus "kotak seleksi Figma"**: fill biru muda, border biru 1–2 px, handle kotak kecil di sudut.
- Kata penekanan diganti serif italic (misalnya *download*, *folder*, *inspired*, *taste*).

### Progress rail (navigasi)

- Garis vertikal di kiri (x ~60 px). Bagian yang sudah lewat terisi biru, sisanya abu.
- Kepala avatar menjadi playhead dan bergerak turun mengikuti progres.
- Di sebelah avatar ada chip pill biru "NN Nama step" yang berganti tiap step.

## 3. Aturan gerak

1. **Tidak ada cut.** Scene berganti lewat slide/fade/morph di dalam satu kanvas, grid tetap diam.
2. **Visual mengikuti kata.** Elemen muncul tepat saat namanya diucapkan (tool menempel ke hub saat namanya disebut, folder bercabang saat "three subfolders").
3. **Counter dan progres selalu bergerak**: angka live, persen download, "n/5 tools", follower. Tidak ada frame yang benar-benar diam.
4. **Easing lembut** (spring/ease-out), masuk dari bawah dengan sedikit overshoot.
5. Kedalaman dari bayangan dan tumpukan isometrik, bukan dari 3D berat.

## 4. Audio

1. VO dulu, semua timing diturunkan dari VO.
2. Rapatkan jeda: target median ~0,2 s, maksimum ~0,5 s.
3. Musik bed kontinu ~12 dB di bawah VO (atau ducking otomatis).
4. SFX pop/klik pendek di setiap pergantian chip, centang checklist, dan klik tombol.
5. Master ke -14 LUFS dengan true peak ≤ -1 dBTP.

Catatan: dari analisis sinyal tidak bisa dipastikan VO ini suara asli atau TTS.

## 5. Pipeline produksi

1. **Naskah.** Ikuti struktur di bagian 1. Untuk ~80 s di kecepatan ~200 kata/menit, sekitar 270 kata.
2. **Storyboard sebagai data.** Buat `beats.json`: per step isi chip, kalimat VO, kata kunci (kotak seleksi), kata serif, dan deskripsi visual stage.
3. **Rekam VO**, lalu rapatkan jedanya. Logika potong jeda dan timestamp per kata sudah ada di `skills/capcut-auto-edit/scripts/transcribe.py`, pakai ulang itu.
4. **Transkrip per kata** dengan `mlx_whisper` (large-v3-turbo sudah ter-cache di mesin ini). Perbaiki nama yang salah tangkap (Whisper menulis "ReMotion", "YTDLP").
5. **Petakan timing.** Tiap beat dapat `start`/`end` dari kata pertama dan terakhirnya. Caption dipecah per 1–4 kata.
6. **Bangun komposisi** (lihat bagian 6). Komponennya: `GridBackground`, `CaptionLine`, `ProgressRail`, `Avatar`, dan satu `Scene` per step. Kerjakan satu scene per prompt ke Claude Code, preview, baru lanjut.
7. **Audio**: VO + musik (ducking) + SFX di timestamp pergantian beat.
8. **Render** 1080x1920 30 fps, cek loudness, review, lalu revisi dengan bahasa biasa.

Beban kerja terbesar ada di 13 scene ilustrasi UI. Caption dan rail cukup dibuat sekali lalu dipakai ulang untuk semua video berikutnya.

## 6. Pilih engine

| | HyperFrames | Remotion |
|---|---|---|
| Authoring | HTML/CSS + GSAP, timing lewat `data-start`/`data-duration` | React/TypeScript |
| Untuk agent | dibuat khusus untuk agent, ada plugin Claude Code (`/hyperframes`, `/media-use`) dan katalog blok (`instagram-follow`, dll.) | ada skill `remotion:*` di sesi ini, plus `@remotion/captions` (`createTikTokStyleCaptions`) untuk caption per kata |
| Lisensi | Apache 2.0, bebas komersial | gratis untuk individu/tim kecil, perusahaan di atas ambang wajib beli company license |
| Setup | Node 22+, FFmpeg | Node, FFmpeg |

Rekomendasi: **HyperFrames**, karena lisensinya bebas untuk Portolabs dan kemungkinan memang engine yang dipakai reel ini.

```bash
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes
npx hyperframes init explainer-reel
cd explainer-reel && npx hyperframes preview
npx hyperframes render
```

## 7. Jangan

- Jangan pakai avatar, nama, atau handle mereka. Buat maskot dan aksen warna Portolabs sendiri. Ambil formulanya, bukan aset dan tampilannya.
- Jangan ada scene diam lebih dari ~2 s tanpa elemen yang bergerak.
- Jangan pakai caption lebih dari satu baris, atau lebih dari ~4 kata per halaman.
- Jangan lebih dari satu warna aksen.

## Sumber

- https://github.com/heygen-com/hyperframes
- https://www.remotion.dev/docs/captions/create-tiktok-style-captions
- https://www.remotion.dev/docs/install-whisper-cpp
