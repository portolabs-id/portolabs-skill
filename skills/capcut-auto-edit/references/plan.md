# plan.json

Every time position is a **word index** from the transcript (`[index]word`). The builder converts it to output time after pauses and dropped takes are cut. A referenced word must be inside `keep`, or the build stops and names it. Relative paths resolve from the plan's folder.

```json
{
  "name": "Remote kerja - Dicoding",
  "aroll": "/Users/me/Videos/aroll.MOV",
  "words": "words.json",
  "keep": [[28, 43], [44, 67], [136, 149], [82, 99]],
  "word_fixes": {"169": "Della", "252": "Dicoding."},

  "hook": {"text": "Bidang ini buka banyak posisi kerja remote", "highlight": "Gw saksinya!", "until_word": 43},
  "broll": [
    {"file": "/Users/me/Videos/laptop.mp4", "from_word": 30, "to_word": 33},
    {"file": "/Users/me/Videos/kantor.mp4", "from_word": 34, "to_word": 43, "src_start": 12.5}
  ],
  "cards": [
    {"style": "fullscreen", "text": "100% full beasiswa\nbelajar Coding dan AI", "from_word": 175, "to_word": 180},
    {"style": "overlay", "text": "Terbuka untuk umum untuk peserta di atas 18 tahun", "from_word": 302, "to_word": 311}
  ],
  "posters": [{"file": "/Users/me/Videos/poster.jpg", "from_word": 225, "to_word": 231}],
  "logos": [{"title": "Kolaborasi antara", "files": ["logo-a.mp4", "logo-b.mp4"], "chroma": true, "from_word": 245, "to_word": 252}],
  "clicks": [272, 274, 277],
  "punch_in": [324],
  "cta": {"text": "daftar di link berikut\ndicoding.id/arcade-7", "from_word": 326},
  "credit": "Della Miranti"
}
```

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | Draft name in CapCut. A number is added if it already exists. |
| `aroll` | yes | The talking-head video. |
| `words` | yes | `words.json` from `transcribe.py`. Its `audio.json` must sit next to it. |
| `keep` | yes | Inclusive `[first, last]` word ranges, in video order. Anything not listed is cut. |
| `word_fixes` | no | `{index: "text"}` corrections for subtitles. |
| `trim_tail` | no | `{index: seconds}`: cut that much off the end of the cut that ends on this word, when the tail recheck shows the speaker looking away in the last frame. More than about 0.05 s clips the word itself; cover that tail with B-roll instead. |
| `hook` | no | Top title from 0 s until `until_word` ends. `highlight` is a second line in yellow. Adds the opening woosh, plus a Glare II transition and swish where the hook ends. |
| `broll` | no | Replaces the picture from `from_word` to `to_word`. `src_start` (seconds into the clip) is optional; the default is the middle of the clip. A clip shorter than its span ends early. `"src_start": "timeline"` is for a clip rendered on the edit's own timeline (a motion graphic timed from `timeline.json`): each moment plays at the time it has in the edit, so several covers can cut pieces from one clip and stay in sync. |
| `subtitles` | no | `false` leaves out the yellow captions, e.g. when a motion graphic already carries its own. Default `true`. |
| `grading` | no | `false` leaves out the 4K filter and colour grade, which would tint a motion graphic's flat colours. Default `true`. |
| `end_hold` | no | Seconds the picture stays after the last word, e.g. for an end card. Needs a `broll` cover over the last word: that cover is stretched to the new end. Default `0`. |

To time a motion graphic to the edit, run `build_draft.py <plan.json> --timeline` first. It writes `timeline.json` next to the plan: every kept word with its start and end in the edit, after pauses are cut. Render the motion from those times, then add it as `broll` with `"src_start": "timeline"`. Covers cut from one timeline-locked clip always meet: the gap between two of them shows that clip, never the A-roll. Do not change `keep`, `trim_tail` or `end_hold` after that, or the motion falls out of sync.
| `cards` | no | `fullscreen`: black textured background with ART PAPER text. `overlay`: the same text over the blurred A-roll. Both pop in with a "pop" SFX. Use `\n` for a line break. |
| `posters` | no | Image or video floating over the blurred A-roll, Shake Down in, with a click. A video plays from `src_start` (seconds, default 0). Use posters for landscape screen recordings: as `broll` they would be cropped to a narrow vertical slice. |
| `logos` | no | Each group: optional `title` text, then the logos staggered in from the right, each with a click. Set `chroma` to false for plain images. |
| `clicks` | no | Words that get a mouse-click SFX, e.g. each item of a spoken list. |
| `punch_in` | no | Words that get a fast zoom-in and a swish: the punchline, the CTA. |
| `cta` | no | Black text in a white box from `from_word` to the end (or `to_word`). |
| `credit` | no | Creator name for the "Original content from …" watermark that moves corners. |

`hook`, each card, each logo group (its title) and `cta` also take an optional `"y"`: the vertical position from −1 (bottom) to 1 (top), used when the layout check reports two texts overlapping. Captions move out of the way on their own.
