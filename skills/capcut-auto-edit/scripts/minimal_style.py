"""The "minimal" style: a dark, clean talking head carried by kinetic captions.

It keeps della's pace engine (build_draft.Editor: takes, pause cuts, zooms, B-roll, punch-ins) and
changes what lies on the picture:
- kinetic captions: per phrase a small white lead-in, one big lime keyword with a glow and a small
  tail, each word blurring in as it is spoken; a red strike across a keyword; dark red alert cards
- captions behind the speaker's head, cut out with an Apple Vision person matte
- a REC viewfinder and a glowing ring (PNGs from overlays.py), Signal Glitch 2 transitions on chosen
  words, a moody grade with a vignette, a fade to black

The captions and alerts are one transparent video (ProRes 4444) rendered with HyperFrames from
assets/minimal/captions.html: CapCut's own text cannot do the font, the blur-in or the cut-out.
They are not editable in CapCut; change the plan and build again.
"""
import itertools
import json
import os
import shutil
import subprocess
import sys

import overlays as draw
from build_draft import (ATTACH, CANVAS_H, CANVAS_W, MIN_SHOT, SKILL_DIR, TRAILING_PUNCT, Editor, _split_at, join_words,
                         snap, us)

PROTOTYPES = json.loads((SKILL_DIR / "assets/minimal/prototypes.json").read_text())
ANIMATIONS = PROTOTYPES["animations"]
GLITCH = PROTOTYPES["materials"]["transitions"][0]["id"]
CAPTIONS_HTML = SKILL_DIR / "assets/minimal/captions.html"
PERSON_MATTE = SKILL_DIR / "scripts/person_matte.js"
HYPERFRAMES = "hyperframes@0.9.14"
LAYER_FPS = 30

# Positions in CapCut units (-1 bottom … 1 top), as in the plan.
CAPTION_Y = -0.3
CAPTION_TOP_Y = 0.62
CAPTION_UNDER_POSTER_Y = -0.58
HEAD_Y = 0.45
ALERT_Y = -0.2
ALERT_STEP = 0.13
ALERT_ICONS = {"⚠️": "warning", "⚠": "warning", "✖️": "x", "✖": "x", "❌": "x", "✅": "check", "✔️": "check"}
# Captions come only around highlighted words, with no text between them: a few small words before
# and after the big keyword, which holds KEY_HOLD (BEHIND_HOLD behind the head) from its word.
LEAD_WORDS = 2
TAIL_WORDS = 3
HOLD = 0.25
KEY_HOLD = 1.6
BEHIND_HOLD = 2.8
BREATH = 0.15
# The dry-run asks to drop a highlight closer than MIN_SPACING to the one before; without any in
# the plan, the builder picks one about every AUTO_SPACING.
MIN_SPACING = 2.0
AUTO_SPACING = 3.5
# ponytail: a short list of Indonesian glue words never picked automatically; the plan's
# "emphasis" is the real choice.
GLUE_WORDS = {"yang", "dan", "tapi", "kalau", "kalo", "karena", "sekarang", "terus", "untuk", "juga", "bakal",
              "udah", "sudah", "cuman", "cuma", "gimana", "kayak", "bisa", "ini", "itu", "gue", "gua", "aku",
              "lo", "lu", "kamu", "aja", "dari", "dengan", "di", "ke", "buat", "pake", "jadi", "mau", "lagi"}
# Contrast (WCAG): the lime keyword is large text (3:1), the small white words need 4.5:1. The
# picture is sampled small, in the band a caption covers, at its bright end.
LIME_LUMINANCE = 0.859  # #d4ff3f
KEY_CONTRAST = 3.0
SMALL_CONTRAST = 4.5
SAMPLE_SIZE = (108, 192)
CAPTION_BAND = 340
SAMPLE_BEFORE_END = 0.3  # captions.html fades a phrase out over its last 0.15 s
BACKDROP_REACH = 1.2  # the backdrop fades out towards its edges, so it must be stronger than the bare need
BACKDROP_MIN = 0.4
BACKDROP_MAX = 0.85
MATTE_SOFTEN = 1.5
RING = {"x": 0.0, "y": 0.3, "size": 0.5}
RING_FADE = 0.25
END_FADE = 0.8
MOODY_GRADE = {"shadow": -0.3, "black": -0.15, "highlight": -0.15}
RENDER_BASE = {"vignette": 1, "overlay": 2, "captions": 20, "fade": 30}


class MinimalEditor(Editor):
    LANES = ["main", "vignette", "overlay", "captions", "fade", "filter", "adjust", "speech", "sfx"]
    FOREIGN_FIELDS = ("hook", "cards", "logos", "cta", "credit")

    def __init__(self, plan, plan_dir, draft, dry_run=False):
        super().__init__(plan, plan_dir, draft, dry_run)
        self.work = plan_dir / "minimal"
        self.phrases, self.alert_items, self.phrase_lines, self.contrast_lines = [], [], [], []
        self.shots = []

    def build(self):
        self.speech_audio()
        self.sfx.append((0.0, "woosh"))
        self.alert_items = self.alerts()
        ring_spans = self.rings()
        if self.plan.get("subtitles", True):
            self.phrases = self.caption_phrases([(a["start"], a["end"]) for a in self.alert_items], ring_spans)
        covers = self.covers()
        self.overlays()
        self.shots = self.main_track(covers, hook_end=None)
        self.rec_frames()
        if self.plan.get("grading", True):
            self.grading()
        if self.plan.get("end_fade", True):
            self.end_fade()
        self.caption_layer()
        self.sound_effects()
        return self.shots

    def report_lines(self):
        lines = ["Captions (lead [KEYWORD] tail; ^ = behind the head):", *self.phrase_lines,
                 f"\nContrast check (keyword ≥ {KEY_CONTRAST}:1, small words ≥ {SMALL_CONTRAST}:1):",
                 *self.contrast_lines]
        if self.dry_run and (self.phrases or self.alert_items):
            lines.append(f"Caption layer: {self.work / 'captions'} is rendered by the build, not the dry-run.")
        else:
            lines.append(f"Contrast sheet: {self.work / 'contrast-sheet.jpg'} (read it: every caption must read clearly)")
        return lines

    def behind_spans(self):
        return [(p["start"], p["end"]) for p in self.phrases if p["behind"]]

    # -- glitch transitions
    def split_for_transitions(self, shots):
        for t in self.glitch_times():
            shots = _split_at(shots, t)
        return shots

    def transitions(self, shots, hook_end):
        bounds = [s["end"] for s in shots[:-1]]
        placed = []
        for t in self.glitch_times():
            at = min(bounds, key=lambda b: abs(b - t), default=None)
            if at is not None and abs(at - t) < MIN_SHOT:
                placed.append((at, GLITCH))
        return placed

    def glitch_times(self):
        return [snap(self.speech.start(i)) for i in self.plan.get("glitch", [])]

    def assign_zoom(self, shots):
        """Shots under a caption behind the head stay still: the matte is cut from the unzoomed frame."""
        super().assign_zoom(shots)
        for shot in shots:
            if any(_overlaps((shot["start"], shot["end"]), span) for span in self.behind_spans()):
                if shot["kind"] != "aroll":
                    self.layout_notes.append(f"FIX: a caption behind the head at {shot['start']:.2f}s sits on "
                                             f"{shot['kind']}: the speaker is not on screen to hide it")
                shot["style"], shot["amount"] = "none", 1.0

    # -- captions and alerts (data for captions.html)
    def caption_phrases(self, hide_during, top_during):
        strike = {int(i) for i in self.plan.get("strike", [])}
        behind = {int(i) for i in self.plan.get("behind", [])}
        emphasis = {int(i) for i in self.plan.get("emphasis", [])} | strike | behind
        icons = {int(item["word"]): item.get("icon", "plane") for item in self.plan.get("icons", [])}
        for i in [*emphasis, *icons]:
            self.speech.start(i)
        head_y = self.plan.get("head_y", HEAD_Y)
        words = [(i, self.words[i]["w"], *self.speech.out[i]) for i in self.speech.kept]
        phrases = highlight_phrases(words, emphasis or auto_highlights(words))
        spans = phrase_spans(phrases, self.T, behind)
        self.check_spacing(phrases, icons)
        breaks = sorted([*self.glitch_times(), *(start for start, _ in hide_during)])
        out = []
        for phrase, (start, end) in zip(phrases, spans):
            # A phrase ends before the next alert or glitch: the alert takes over, the glitch starts a new part.
            end = min([end, *(t - BREATH for t in breaks if t > start)])
            if end - start < MIN_SHOT or any(s <= start < e for s, e in hide_during):
                self.phrase_lines.append(f"  {start:6.2f}  (no room before an alert or glitch) {_phrase_text(phrase)}")
                continue
            key = phrase["key"]
            if key[0] in behind:
                y = head_y
            elif any(_overlaps((start, end), span) for span in top_during):
                y = CAPTION_TOP_Y
            elif any(_overlaps((start, end), self.span(item)) for item in self.plan.get("posters", [])):
                y = CAPTION_UNDER_POSTER_Y
            else:
                y = CAPTION_Y
            icon = next(({"name": icons[w[0]], "start": w[2]} for w in _phrase_words(phrase) if w[0] in icons), None)
            out.append({"start": start, "end": end, "y": _canvas_y(y), "behind": key[0] in behind,
                        "strike": key[0] in strike, "lead": _timed(phrase["lead"]),
                        "key": {"text": _keyword_text(key[1]), "start": key[2]}, "tail": _timed(phrase["tail"]),
                        "icon": icon})
            mark = "^" if key[0] in behind else " "
            extra = f"  + {icon['name']}" if icon else ""
            self.phrase_lines.append(f" {mark}{start:6.2f}-{end:6.2f}  {_phrase_text(phrase)}{extra}")
        return out

    def check_spacing(self, phrases, icons):
        keys = [p["key"] for p in phrases]
        for before, after in zip(keys, keys[1:]):
            if after[2] - before[2] < MIN_SPACING:
                self.layout_notes.append(f"FIX: highlights [{before[0]}]{_bare(before[1])} and "
                                         f"[{after[0]}]{_bare(after[1])} are {after[2] - before[2]:.1f}s apart: "
                                         "drop one from emphasis, so the big words breathe")
        captioned = {w[0] for p in phrases for w in _phrase_words(p)}
        for word in sorted(set(icons) - captioned):
            self.layout_notes.append(f"FIX: icon on [{word}] has no caption around it: put it on a highlight "
                                     "or a word next to one")

    def alerts(self):
        items, shown = [], []
        for item in sorted(self.plan.get("alerts", []), key=lambda a: self.speech.start(a["from_word"])):
            start, end = self.span(item)
            used = {slot for s, e, slot in shown if s <= start < e}
            slot = next(k for k in itertools.count() if k not in used)
            icon = item.get("icon", "⚠️")
            items.append({"start": start, "end": end, "y": _canvas_y(ALERT_Y - slot * ALERT_STEP),
                          "icon": ALERT_ICONS.get(icon, icon), "text": item["text"]})
            shown.append((start, end, slot))
            self.sfx.append((start, "pop"))
        return items

    def caption_layer(self):
        """One overlay video over the whole edit for every caption and alert."""
        if not (self.phrases or self.alert_items):
            return
        self.check_contrast()
        project = self.write_caption_project()
        if self.dry_run:
            return
        layer = self.render_caption_layer(project)
        self.overlay(layer, 0, self.T, lane="captions")
        self.contrast_sheet(layer)

    # -- contrast
    def check_contrast(self):
        """Measure the picture behind each caption. A soft dark backdrop goes behind any caption whose
        lime keyword or white small words would not stand out (bright screens, documents)."""
        for p in self.phrases:
            background = self.picture_luminance(_sample_time(p), p["y"])
            p["scrim"] = backdrop_strength(background)
            state = f"dark backdrop at {p['scrim']:.0%}" if p["scrim"] else "ok"
            self.contrast_lines.append(f"  {p['start']:6.2f}  {p['key']['text']:<14} keyword "
                                       f"{_contrast(LIME_LUMINANCE, background):4.1f}:1, small words "
                                       f"{_contrast(1.0, background):4.1f}:1 → {state}")

    def picture_at(self, t):
        """(file, source second) of what the main track shows at output time t."""
        shot = next((s for s in self.shots if s["start"] <= t < s["end"]), self.shots[-1])
        if shot["kind"] == "broll":
            return shot["file"], shot["src_start"] + (t - shot.get("cover_start", shot["start"]))
        return self.aroll, self.speech.source_at(t)[1]

    def picture_luminance(self, t, y):
        """Relative luminance of the bright end (75th percentile) of the picture where a caption
        centred at canvas height y sits, at time t."""
        path, src = self.picture_at(t)
        w, h = SAMPLE_SIZE
        frame = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{src:.3f}", "-i", str(path), "-frames:v", "1",
                                "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=gray",
                                "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
        row, half = round(y * h / CANVAS_H), round(CAPTION_BAND / 2 * h / CANVAS_H)
        band = sorted(v for r in range(max(0, row - half), min(h, row + half))
                      for v in frame[r * w + w // 10:r * w + w - w // 10])
        return _linear(band[int(len(band) * 0.75)] / 255) if band else 0.0

    def contrast_sheet(self, layer):
        """Every caption over its picture, to read by eye: <work>/minimal/contrast-sheet.jpg."""
        tiles = self.work / "contrast"
        shutil.rmtree(tiles, ignore_errors=True)
        tiles.mkdir(parents=True)
        for n, p in enumerate(self.phrases):
            t = _sample_time(p)
            path, src = self.picture_at(t)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{src:.3f}", "-i", str(path),
                            "-ss", f"{t:.3f}", "-i", str(layer), "-filter_complex",
                            f"[0]setpts=PTS-STARTPTS,scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=increase,"
                            f"crop={CANVAS_W}:{CANVAS_H}[bg];[1]setpts=PTS-STARTPTS[fg];"
                            "[bg][fg]overlay=alpha=premultiplied,scale=270:-1",
                            "-frames:v", "1", str(tiles / f"{n:02d}.jpg")], check=True)
        columns = min(5, len(self.phrases))
        rows = -(-len(self.phrases) // columns)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(tiles / "%02d.jpg"),
                        "-vf", f"tile={columns}x{rows}", "-frames:v", "1", str(self.work / "contrast-sheet.jpg")],
                       check=True)
        shutil.rmtree(tiles)

    def write_caption_project(self):
        project = self.work / "captions"
        if not (project / "hyperframes.json").exists():
            project.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["npx", "-y", HYPERFRAMES, "init", project.name, "--example", "blank", "--resolution",
                            "portrait", "--non-interactive", "--skip-skills"],
                           cwd=project.parent, env=_hyperframes_env(), check=True, capture_output=True)
        data = {"phrases": self.phrases, "alerts": self.alert_items}
        html = CAPTIONS_HTML.read_text().replace("{{DURATION}}", f"{self.T:.3f}") \
            .replace("{{DATA}}", json.dumps(data, ensure_ascii=False))
        (project / "index.html").write_text(html)
        return project

    def render_caption_layer(self, project):
        rendered = self.work / "captions-render.mov"
        print(f"Rendering the caption layer ({self.T:.0f} s) with HyperFrames…", file=sys.stderr)
        subprocess.run(["npx", "-y", HYPERFRAMES, "render", "--format", "mov", "-f", str(LAYER_FPS), "--quiet",
                        "-o", str(rendered), "."], cwd=project, env=_hyperframes_env(), check=True)
        layer = self.work / "captions.mov"
        self.finish_layer(rendered, self.behind_spans(), layer)
        return layer

    def finish_layer(self, rendered, behind, out):
        """Clear the layer wherever the speaker is during the behind spans, and premultiply it: CapCut
        reads ProRes alpha as premultiplied, and a straight-alpha glow turned into a solid lime block."""
        inputs, graph = ["-i", str(rendered)], ["[0]format=rgba[layer]"]
        if behind:
            graph = self.cut_out_speaker(behind, inputs)
        graph.append("[layer]format=yuva444p10le,premultiply=inplace=1[v]")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(graph),
                        "-map", "[v]", "-c:v", "prores_ks", "-profile:v", "4444", str(out)], check=True)

    # -- captions behind the head
    def cut_out_speaker(self, spans, inputs):
        """Filter graph that clears input 0 wherever the speaker is during spans, ending in [layer].
        Adds one matte input per span to inputs."""
        mattes = [self.person_matte(n, start, end) for n, (start, end) in enumerate(spans)]
        graph = [f"color=black:s={CANVAS_W}x{CANVAS_H}:r={LAYER_FPS}:d={self.T:.3f},format=yuv420p[m0]"]
        for n, ((start, _), folder) in enumerate(zip(spans, mattes)):
            inputs += ["-framerate", str(LAYER_FPS), "-i", str(folder / "%05d.png")]
            graph.append(f"[{n + 1}]scale={CANVAS_W}:{CANVAS_H},gblur=sigma={MATTE_SOFTEN},format=yuv420p,"
                         f"setpts=PTS-STARTPTS+{start:.3f}/TB[s{n}]")
            graph.append(f"[m{n}][s{n}]overlay=eof_action=pass[m{n + 1}]")
        return graph + [f"[m{len(spans)}]format=gray,negate[keep]",
                        "[0]format=rgba,split[rgb][alpha]", "[alpha]alphaextract[a]",
                        "[a][keep]blend=all_mode=multiply,format=gray[cut]", "[rgb][cut]alphamerge[layer]"]

    def person_matte(self, n, start, end):
        """The edit's picture from start to end as frames, then Vision's person matte of each."""
        folder = self.work / f"matte-{n}"
        frames = folder / "frames"
        shutil.rmtree(folder, ignore_errors=True)
        frames.mkdir(parents=True)
        number = 1
        for piece in self.speech.pieces:
            a, b = max(start, piece["out"]), min(end, piece["out"] + piece["dur"])
            if b - a <= 0:
                continue
            src = piece["src_start"] + (a - piece["out"])
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{src:.3f}", "-t", f"{b - a:.3f}",
                            "-i", str(self.aroll), "-an", "-vf",
                            f"scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=increase,"
                            f"crop={CANVAS_W}:{CANVAS_H},fps={LAYER_FPS}",
                            "-start_number", str(number), str(frames / "%05d.png")], check=True)
            number = len(list(frames.glob("*.png"))) + 1
        subprocess.run(["osascript", "-l", "JavaScript", str(PERSON_MATTE), str(frames), str(folder / "matte")],
                       check=True, capture_output=True)
        return folder / "matte"

    # -- ring, REC
    def rings(self):
        spans = []
        for item in self.plan.get("rings", []):
            start, end = self.span(item)
            ring = {**RING, **item}
            png = draw.ring(self.work, round(ring["size"] * CANVAS_W))
            self.overlay(png, start, end, x=ring["x"], y=ring["y"], fade=RING_FADE)
            self.sfx.append((start, "pop"))
            spans.append((start, end))
        return spans

    def rec_frames(self):
        for item in self.plan.get("rec", []):
            start, end = self.span(item)
            self.overlay(draw.rec_frame(self.work), start, end)
            self.sfx.append((start, "click"))

    # -- look
    def grading(self):
        d = self.draft
        d.place("filter", "filter", d.segment("filter", 0, self.T))
        adjust = d.segment("adjust", 0, self.T)
        for ref in adjust["extra_material_refs"]:
            effect = d.by_id[ref]
            if effect.get("type") in MOODY_GRADE:
                effect["value"] = MOODY_GRADE[effect["type"]]
        d.place("adjust", "adjust", adjust)
        self.overlay(draw.vignette(self.work), 0, self.T, lane="vignette")

    def end_fade(self):
        start = snap(max(self.T - END_FADE, 0))
        self.overlay(draw.black(self.work), start, self.T, lane="fade", fade=self.T - start)

    # -- layers
    def overlay(self, media, start, end, lane="overlay", x=0.0, y=0.0, fade=None):
        """An image or video made for this draft, at its native pixel size, centred on (x, y)."""
        d = self.draft
        material_id, info = d.bundled_media(media, f"materials/minimal/{media.name}")
        seg = d.segment("poster", snap(start), snap(end), material_id=material_id)
        seg["source_timerange"] = {"start": 0, "duration": seg["target_timerange"]["duration"]}
        scale = 1 / min(CANVAS_W / info["width"], CANVAS_H / info["height"])
        seg["clip"].update(scale={"x": scale, "y": scale}, transform={"x": x, "y": y}, rotation=0.0)
        seg["uniform_scale"] = {"on": True, "value": 1.0}
        seg["common_keyframes"] = []
        seg["volume"] = 0.0
        self.set_animation(seg, "fade_in" if fade else None, fade or 0)
        seg["render_index"] = RENDER_BASE[lane] + d.place(lane, "poster", seg)
        return seg

    def set_animation(self, seg, name, length):
        """Replace the prototype's in-animation; never longer than most of the segment."""
        length = min(length, seg["target_timerange"]["duration"] / 1e6 * 0.8)
        for ref in seg["extra_material_refs"]:
            material = self.draft.by_id[ref]
            if "animations" in material:
                material["animations"] = [dict(ANIMATIONS[name], start=0, duration=us(length))] if name else []


def highlight_phrases(words, keys):
    """words: [(index, text, out_start, out_end)] in edit order; keys: indices of the highlighted
    words. → one phrase per highlight, in time order: {"lead": up to LEAD_WORDS small words before,
    "key": the word, "tail": up to TAIL_WORDS after}, never across a sentence or into the next
    phrase. Words outside every phrase get no caption."""
    words = _glued(words)
    positions = sorted(n for n, w in enumerate(words) if w[0] in keys)
    phrases, free_from = [], 0
    for m, p in enumerate(positions):
        until = positions[m + 1] if m + 1 < len(positions) else len(words)
        lead = []
        for q in range(p - 1, max(free_from, p - LEAD_WORDS) - 1, -1):
            if _ends_clause(words[q][1]) or words[q + 1][1].istitle():
                break
            lead.insert(0, words[q])
        tail = []
        for q in range(p + 1, min(until, p + 1 + TAIL_WORDS)):
            if _ends_clause((tail or [words[p]])[-1][1]) or words[q][1].istitle():
                break
            tail.append(words[q])
        phrases.append({"lead": lead, "key": words[p], "tail": tail})
        free_from = p + 1 + len(tail)
    return phrases


def phrase_spans(phrases, duration, behind=()):
    """(start, end) per phrase: from its first word until the tail is said and the keyword has held
    KEY_HOLD (BEHIND_HOLD behind the head), stopping a breath before the next phrase."""
    spans = []
    for n, phrase in enumerate(phrases):
        words = _phrase_words(phrase)
        hold = BEHIND_HOLD if phrase["key"][0] in behind else KEY_HOLD
        end = max(words[-1][3] + HOLD, phrase["key"][2] + hold)
        if n + 1 < len(phrases):
            end = min(end, _phrase_words(phrases[n + 1])[0][2] - BREATH)
        spans.append((snap(words[0][2]), snap(min(end, duration))))
    return spans


def auto_highlights(words, spacing=AUTO_SPACING):
    """Highlights when the plan names none: the longest words that are not glue words, spacing apart."""
    picked = []
    for word in sorted(_glued(words), key=lambda w: len(_bare(w[1])), reverse=True):
        bare = _bare(word[1])
        if bare.lower() not in GLUE_WORDS and len(bare) >= 4 and all(abs(word[2] - p[2]) >= spacing for p in picked):
            picked.append(word)
    return {w[0] for w in picked}


def backdrop_strength(background):
    """Opacity of the dark backdrop a caption needs over a picture of this relative luminance: enough
    to bring the picture down to where the lime keyword and the white words both reach their
    contrast, 0 when they already do."""
    brightest_allowed = min((LIME_LUMINANCE + 0.05) / KEY_CONTRAST, 1.05 / SMALL_CONTRAST) - 0.05
    if background <= brightest_allowed:
        return 0.0
    needed = (1 - brightest_allowed / background) * BACKDROP_REACH
    return round(min(max(needed, BACKDROP_MIN), BACKDROP_MAX), 2)


def _contrast(text, background):
    return (max(text, background) + 0.05) / (min(text, background) + 0.05)


def _linear(value):
    """sRGB value (0–1) → relative luminance."""
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _sample_time(phrase):
    """When to judge a caption: half a second after its keyword lands, before it starts to fade out."""
    return min(phrase["key"]["start"] + 0.5, phrase["end"] - SAMPLE_BEFORE_END)


def _ends_clause(text):
    return text[-1:] in ".,!?"


def _glued(words):
    """Suffixes ("-nya", "%", ".id") join the word before, so a keyword never loses them."""
    out = []
    for word in words:
        if out and ATTACH.match(word[1]):
            index, text, start, _ = out[-1]
            out[-1] = (index, join_words([text, word[1]]), start, word[3])
        else:
            out.append(word)
    return out


def _phrase_words(phrase):
    return [*phrase["lead"], phrase["key"], *phrase["tail"]]


def _phrase_text(phrase):
    lead, tail = join_words(w[1] for w in phrase["lead"]), join_words(w[1] for w in phrase["tail"])
    return f"{lead} [{_bare(phrase['key'][1]).upper()}] {tail}".strip()


def _timed(words):
    """Small-line words for captions.html; the line's last word drops its trailing punctuation."""
    out = [{"text": w[1], "start": w[2]} for w in words]
    if out:
        out[-1]["text"] = out[-1]["text"].rstrip(TRAILING_PUNCT)
    return out


def _keyword_text(text):
    bare = _bare(text)
    return bare[:1].upper() + bare[1:]


def _bare(text):
    return text.strip(TRAILING_PUNCT + "\"' ")


def _canvas_y(y):
    """CapCut units (-1 bottom … 1 top) → captions.html pixels from the top."""
    return round(CANVAS_H / 2 * (1 - y))


def _overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]


def _hyperframes_env():
    return dict(os.environ, DO_NOT_TRACK="1", HYPERFRAMES_SKIP_SKILLS="1")
