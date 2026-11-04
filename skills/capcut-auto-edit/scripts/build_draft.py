#!/usr/bin/env python3
"""Build a CapCut draft in the "0827" talking-head style from an edit plan.

Usage: build_draft.py <plan.json> [--drafts-root DIR] [--dry-run]

Every segment is cloned from a prototype in assets/template/draft_info.json, so effect IDs,
fonts, animations and colour grading match the reference project. The plan only decides
what is said (word ranges to keep) and where things appear (word indices).
"""
import argparse
import copy
import json
import math
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "template"
DEFAULT_DRAFTS_ROOT = Path.home() / "Movies/CapCut/User Data/Projects/com.lveditor.draft"
BLACK_TEXTURE = "materials/black_texture.jpeg"

FPS = 60
SEC = 1_000_000
CANVAS_W, CANVAS_H = 1080, 1920
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp"}

# Pace: a pause longer than MAX_GAP is cut out; the pads keep word attacks and tails intact.
MAX_GAP = 0.3
PAD_BEFORE = 0.06
# Short on purpose: speakers reading a script glance down at it right as a line ends.
PAD_AFTER = 0.05
EDGE_SEARCH = 0.6
# Tail recheck: frames shown before every visible jump cut, newest last.
TAIL_OFFSETS = [0.3, 0.2, 0.1, 1 / FPS]
TAIL_ROWS_PER_SHEET = 6
MAX_WORD_CLIP = 0.05
# Transcript check: longest phrase looked for when catching "said twice in a row", and how much
# sound a word needs on both sides of a pause before that pause counts as hidden inside it.
MAX_REPEAT_WORDS = 4
MIN_SOUND_AROUND_PAUSE = 0.1
# Visual rhythm
MIN_SHOT = 0.4
LONG_SHOT = 3.0
PUNCH_SCALES = [1.12, 1.2, 1.15]
SLOW_ZOOM_ENDS = [1.1, 1.18, 1.14]
FAST_PUNCH_SCALE = 1.35
FAST_PUNCH_TIME = 0.17
LOGO_STAGGER = 0.24
LOGO_STEP_Y = 0.22
CREDIT_EVERY = 12.0
CREDIT_POSITIONS = [(-0.82, 0.76), (0.53, -0.17), (-0.58, -0.55), (0.60, 0.39), (-0.49, -0.21)]
TARGET_LUFS = -14.0
SPEECH_GAIN_RANGE = (0.5, 6.0)
SFX_LEAD = {"click": 0.1, "swish": 0.2, "pop": 0.0, "woosh": 0.0}

# Prototype segments in the template: name -> (track index, segment index)
PROTO = {
    "aroll": (0, 4), "zoom": (0, 7), "blur": (0, 20), "photo": (0, 18), "transition": (0, 3),
    "card_full": (1, 0), "logo_title": (1, 1), "card_overlay": (1, 2), "cta": (1, 3),
    "poster": (2, 0), "logo": (2, 1), "logo_next": (3, 0),
    "filter": (4, 0), "adjust": (5, 0), "hook": (6, 0), "subtitle": (7, 0), "credit": (8, 0),
    "speech": (9, 0), "swish": (10, 0), "pop": (10, 1), "click": (10, 2), "woosh": (11, 0),
}
TEXT_RENDER_INDEX_BASE = 14000


def uid():
    return str(uuid.uuid4()).upper()


def us(seconds):
    return round(seconds * SEC)


def snap(seconds):
    return round(seconds * FPS) / FPS


def timerange(start, end):
    return {"start": us(start), "duration": us(end) - us(start)}


# ---------------------------------------------------------------- media probing

def probe(path):
    path = Path(path)
    if not path.exists():
        sys.exit(f"File not found: {path}")
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams",
                          "-show_format", str(path)], capture_output=True, text=True, check=True)
    info = json.loads(out.stdout)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        sys.exit(f"No video/image stream in {path}")
    width, height = int(video["width"]), int(video["height"])
    if abs(_rotation(video)) in (90, 270):
        width, height = height, width
    is_image = path.suffix.lower() in IMAGE_EXTS
    duration = float(info["format"].get("duration") or 0)
    return {"width": width, "height": height, "duration": duration, "is_image": is_image,
            "has_audio": any(s["codec_type"] == "audio" for s in info["streams"])}


def _rotation(stream):
    for side in stream.get("side_data_list", []):
        if "rotation" in side:
            return int(side["rotation"])
    return int(stream.get("tags", {}).get("rotate", 0))


def cover_scale(width, height):
    """CapCut scale 1.0 = fit inside the canvas; this returns the scale that fills it."""
    fit = min(CANVAS_W / width, CANVAS_H / height)
    return max(CANVAS_W / (width * fit), CANVAS_H / (height * fit))


def speech_gain(loudness):
    gain = 10 ** ((TARGET_LUFS - loudness) / 20)
    return min(max(gain, SPEECH_GAIN_RANGE[0]), SPEECH_GAIN_RANGE[1])


# ---------------------------------------------------------------- speech timeline

class SpeechTimeline:
    """Kept words → audio pieces with every pause longer than MAX_GAP removed, laid end to end.

    Whisper's word edges drift (a word can swallow seconds of silence), so the audio itself
    decides where speech starts, stops and pauses; the words only decide what is kept.
    """

    def __init__(self, words, keep, media_duration, silences, trim_tail=None):
        """trim_tail: {word index: seconds} cut off the end of the piece that ends on that word,
        for tails where the speaker already looks away (at the script) as the word finishes."""
        self.words = words
        self.silences = silences
        self.media_duration = media_duration
        self.kept = [i for start, end in keep for i in range(start, end + 1)]
        if not self.kept:
            sys.exit("plan.keep selects no words.")
        trim_tail = {int(k): v for k, v in (trim_tail or {}).items()}
        self.warnings = [f"trim_tail[{i}] cuts ~{1000 * (t - PAD_AFTER):.0f} ms off the word itself: "
                         "cover that tail with B-roll instead of trimming"
                         for i, t in trim_tail.items() if t - PAD_AFTER > MAX_WORD_CLIP]
        self.pieces, self.out = [], {}
        cursor = 0.0
        for run in self._runs(self.kept):
            run_pieces = []
            for src_start, src_end in self._drop_pauses(*self._speech_edges(run)):
                last_word = max((i for i in run if words[i]["s"] < src_end), default=run[0])
                dur = snap(src_end - trim_tail.get(last_word, 0) - src_start)
                if dur > 0:
                    run_pieces.append({"src_start": src_start, "out": cursor, "dur": dur, "last_word": last_word})
                    cursor = snap(cursor + dur)
            for i in run:
                start = _to_output(run_pieces, self.words[i]["s"], prefer_next=True)
                end = _to_output(run_pieces, self.words[i]["e"], prefer_next=False)
                self.out[i] = (start, max(start, end))
            self.pieces += run_pieces
        self.duration = cursor
        self.cuts = [p["out"] for p in self.pieces[1:]]

    def transcript_flags(self):
        """Spots in the kept speech that will sound wrong: a phrase said twice in a row, or a word
        whose span swallows a pause (whisper probably hid a repeat or false start in it)."""
        flags = []
        text = [_normalized(self.words[i]["w"]) for i in self.kept]
        n = 0
        while n < len(text):
            size = next((k for k in range(MAX_REPEAT_WORDS, 0, -1)
                         if n + 2 * k <= len(text) and text[n:n + k] == text[n + k:n + 2 * k]
                         and self._sounds_like_retake(n, k)), 0)
            if size:
                first, second = self.kept[n:n + size], self.kept[n + size:n + 2 * size]
                flags.append(f"said twice: [{first[0]}-{first[-1]}] and [{second[0]}-{second[-1]}] "
                             f"\"{' '.join(text[n:n + size])}\": keep only the later take")
            n += size or 1
        for i in self.kept:
            w = self.words[i]
            inner = [e - s for s, e in self.silences
                     if s - w["s"] >= MIN_SOUND_AROUND_PAUSE and w["e"] - e >= MIN_SOUND_AROUND_PAUSE]
            pause = max(inner, default=0)
            if pause > MAX_GAP:
                flags.append(f"[{i}]{w['w']} spans {w['s']:.2f}-{w['e']:.2f}s across a {pause:.2f}s pause: "
                             "whisper may have dropped words there (a repeat or false start)")
        return flags

    def _sounds_like_retake(self, n, size):
        """A repeat of two or more words, or any repeat after a pause; "gua, gua nggak" is just talk."""
        if size >= 2:
            return True
        before, after = self.words[self.kept[n + size - 1]], self.words[self.kept[n + size]]
        return after["s"] - before["e"] > MAX_GAP

    @staticmethod
    def _runs(kept):
        runs = []
        for n, i in enumerate(kept):
            if n and i == kept[n - 1] + 1:
                runs[-1].append(i)
            else:
                runs.append([i])
        return runs

    def _speech_edges(self, run):
        words = self.words
        first, last = words[run[0]], words[run[-1]]
        floor = words[run[0] - 1]["e"] if run[0] > 0 else 0.0
        ceiling = words[run[-1] + 1]["s"] if run[-1] + 1 < len(words) else self.media_duration
        start = self._silence_end_near(first["s"])
        end = self._silence_start_near(last["e"])
        start = max(start - PAD_BEFORE, min(floor, start), 0.0)
        end = min(end + PAD_AFTER, max(ceiling, end), self.media_duration)
        return start, end

    def _silence_end_near(self, t):
        """Where speech really starts around whisper's start time t."""
        containing = [e for s, e in self.silences if s <= t <= e]
        if containing:
            return containing[0]
        just_before = [e for s, e in self.silences if t - EDGE_SEARCH <= e < t]
        return just_before[-1] if just_before else t

    def _silence_start_near(self, t):
        """Where speech really stops around whisper's end time t."""
        containing = [s for s, e in self.silences if s <= t <= e]
        if containing:
            return containing[0]
        just_after = [s for s, e in self.silences if t < s <= t + EDGE_SEARCH]
        return just_after[0] if just_after else t

    def _drop_pauses(self, start, end):
        ranges, cursor = [], start
        for s, e in self.silences:
            s, e = max(s, start), min(e, end)
            if e - s <= MAX_GAP:
                continue
            cut_from = s + PAD_AFTER if s > start else start
            cut_to = e - PAD_BEFORE if e < end else end
            if cut_from > cursor:
                ranges.append((cursor, cut_from))
            cursor = max(cursor, cut_to)
        if end > cursor:
            ranges.append((cursor, end))
        return [(a, b) for a, b in ranges if b - a >= 1 / FPS]

    def start(self, i):
        return self._lookup(i)[0]

    def end(self, i):
        return self._lookup(i)[1]

    def _lookup(self, i):
        if int(i) not in self.out:
            sys.exit(f"Word [{i}] is referenced in the plan but not inside plan.keep.")
        return self.out[int(i)]

    def source_at(self, t):
        """(piece, source time) for output time t; t on a cut belongs to the later piece."""
        for piece in reversed(self.pieces):
            if t >= piece["out"] - 1e-6:
                return piece, piece["src_start"] + (t - piece["out"])
        return self.pieces[0], self.pieces[0]["src_start"]

    def piece_end(self, t):
        piece, _ = self.source_at(t)
        return snap(piece["out"] + piece["dur"])


def _normalized(word):
    return word.lower().strip(".,!?…:;\"'")


def _to_output(pieces, src_time, prefer_next):
    """Map a source time onto the output; a time inside a removed pause lands on its edge."""
    for n, piece in enumerate(pieces):
        src_end = piece["src_start"] + piece["dur"]
        if piece["src_start"] <= src_time <= src_end:
            return piece["out"] + (src_time - piece["src_start"])
        if src_time < piece["src_start"]:
            if prefer_next or n == 0:
                return piece["out"]
            return pieces[n - 1]["out"] + pieces[n - 1]["dur"]
    return pieces[-1]["out"] + pieces[-1]["dur"] if pieces else 0.0


# ---------------------------------------------------------------- draft assembly

class Draft:
    def __init__(self, template, draft_dir):
        self.tpl = template
        self.draft_dir = draft_dir
        self.data = copy.deepcopy(template)
        self.by_id = {}
        self.tpl_materials = {}
        for kind, items in template["materials"].items():
            if isinstance(items, list):
                for m in items:
                    if isinstance(m, dict) and "id" in m:
                        self.tpl_materials[m["id"]] = (kind, m)
        for items in self.data["materials"].values():
            if isinstance(items, list):
                items.clear()
        self.lanes = {}
        self.media = {}

    # -- prototypes
    def proto_segment(self, name):
        track, index = PROTO[name]
        return self.tpl["tracks"][track]["segments"][index]

    def proto_track(self, name):
        return self.tpl["tracks"][PROTO[name][0]]

    def proto_material(self, name, kind):
        for ref in self.proto_segment(name)["extra_material_refs"]:
            if self.tpl_materials[ref][0] == kind:
                return ref
        raise KeyError(f"{name} has no {kind}")

    # -- cloning
    def clone_material(self, material_id):
        kind, proto = self.tpl_materials[material_id]
        clone = copy.deepcopy(proto)
        clone["id"] = uid()
        self.data["materials"][kind].append(clone)
        self.by_id[clone["id"]] = clone
        return clone["id"]

    def segment(self, name, start, end, material_id=None, drop_kinds=()):
        proto = self.proto_segment(name)
        seg = copy.deepcopy(proto)
        seg["id"] = uid()
        seg["material_id"] = material_id or self.clone_material(proto["material_id"])
        seg["extra_material_refs"] = [self.clone_material(ref) for ref in proto["extra_material_refs"]
                                      if self.tpl_materials[ref][0] not in drop_kinds]
        old_duration = proto["target_timerange"]["duration"]
        seg["target_timerange"] = timerange(start, end)
        self._stretch_keyframes(seg, old_duration)
        return seg

    def _stretch_keyframes(self, seg, old_duration):
        """Keep a prototype's relative keyframe motion when the segment length changes."""
        new_duration = seg["target_timerange"]["duration"]
        base = (seg.get("source_timerange") or {}).get("start", 0)
        for track in seg.get("common_keyframes") or []:
            track["id"] = uid()
            for kf in track["keyframe_list"]:
                kf["id"] = uid()
                kf["time_offset"] = round((kf["time_offset"] - base) * new_duration / old_duration)

    def add_material(self, proto_id, **fields):
        clone_id = self.clone_material(proto_id)
        self.by_id[clone_id].update(fields)
        return clone_id

    # -- media
    def media_material(self, path):
        path = str(Path(path).resolve())
        if path in self.media:
            return self.media[path]
        info = probe(path)
        proto_name = "photo" if info["is_image"] else "aroll"
        fields = {"path": path, "material_name": Path(path).name, "width": info["width"],
                  "height": info["height"], "local_material_id": str(uuid.uuid4()),
                  "type": "photo" if info["is_image"] else "video", "has_audio": info["has_audio"]}
        if not info["is_image"]:
            fields["duration"] = us(info["duration"])
        material_id = self.add_material(self.proto_segment(proto_name)["material_id"], **fields)
        self.media[path] = (material_id, info)
        return self.media[path]

    # -- text
    def set_text(self, seg, text, highlight=None):
        material = self.by_id[seg["material_id"]]
        styles = json.loads(material["content"])["styles"]
        full = f"{text}\n{highlight}" if highlight else text
        split = _utf16_len(text) + (1 if highlight else 0)
        new_styles = [dict(copy.deepcopy(styles[0]), range=[0, split if highlight else _utf16_len(full)])]
        if highlight:
            new_styles.append(dict(copy.deepcopy(styles[-1]), range=[split, _utf16_len(full)]))
        material["content"] = json.dumps({"styles": new_styles, "text": full}, ensure_ascii=False)
        if material.get("recognize_text"):
            material["recognize_text"] = full
        if isinstance(material.get("words"), dict):
            material["words"] = {"start_time": [], "end_time": [], "text": []}

    # -- tracks
    def place(self, lane_key, proto_name, seg):
        """Put seg on the first lane of this kind where it does not overlap, else open a lane."""
        lanes = self.lanes.setdefault(lane_key, [])
        start = seg["target_timerange"]["start"]
        end = start + seg["target_timerange"]["duration"]
        for lane in lanes:
            if all(end <= s["target_timerange"]["start"] or
                   start >= s["target_timerange"]["start"] + s["target_timerange"]["duration"]
                   for s in lane["segments"]):
                lane["segments"].append(seg)
                return len(lanes) - 1
        track = {k: copy.deepcopy(v) for k, v in self.proto_track(proto_name).items() if k != "segments"}
        track["id"] = uid()
        track["segments"] = [seg]
        lanes.append(track)
        return len(lanes) - 1

    def finish(self, lane_order, duration):
        tracks = []
        for key in lane_order:
            for track in self.lanes.get(key, []):
                track["segments"].sort(key=lambda s: s["target_timerange"]["start"])
                tracks.append(track)
        render_index = TEXT_RENDER_INDEX_BASE
        for track in tracks:
            if track["type"] == "text":
                for seg in track["segments"]:
                    seg["render_index"] = render_index
                    render_index += 1
        self.data["tracks"] = tracks
        self.data["duration"] = us(duration)
        self.data["fps"] = float(FPS)
        self.data["cover"] = None
        self.data["extra_info"]["subtitle_fragment_info_list"] = []
        self._check_references()
        return self.data

    def _check_references(self):
        known = set(self.by_id)
        for track in self.data["tracks"]:
            for seg in track["segments"]:
                for ref in [seg["material_id"], *seg["extra_material_refs"]]:
                    if ref not in known:
                        raise RuntimeError(f"Segment {seg['id']} points to missing material {ref}")


def _utf16_len(text):
    return len(text.encode("utf-16-le")) // 2


# ---------------------------------------------------------------- edit decisions

class Editor:
    def __init__(self, plan, plan_dir, draft):
        self.plan = plan
        self.plan_dir = plan_dir
        self.draft = draft
        words_path = self.path(plan["words"])
        self.words = json.loads(words_path.read_text())
        audio = json.loads(words_path.with_name("audio.json").read_text())
        for index, text in (plan.get("word_fixes") or {}).items():
            self.words[int(index)]["w"] = text
        self.aroll = self.path(plan["aroll"])
        self.aroll_material, self.aroll_info = draft.media_material(self.aroll)
        self.gain = speech_gain(audio["loudness"])
        self.speech = SpeechTimeline(self.words, plan["keep"], self.aroll_info["duration"], audio["silences"],
                                     plan.get("trim_tail"))
        self.T = self.speech.duration
        self.sfx = []
        self.blur_spans = []

    def path(self, value):
        p = Path(value).expanduser()
        return p if p.is_absolute() else (self.plan_dir / p).resolve()

    def span(self, item, end_default=None):
        start = self.speech.start(item["from_word"])
        end = self.speech.end(item["to_word"]) if "to_word" in item else end_default
        return snap(start), snap(end)

    def build(self):
        self.speech_audio()
        hook_end = self.hook()
        covers = self.covers()
        overlays = self.overlays()
        shots = self.main_track(covers, hook_end)
        self.subtitles()
        self.cta()
        self.credit()
        self.grading()
        self.sound_effects()
        return shots

    # -- audio
    def speech_audio(self):
        d = self.draft
        audio_id = d.add_material(d.proto_segment("speech")["material_id"],
                                  path=str(self.aroll), name=self.aroll.stem,
                                  duration=us(self.aroll_info["duration"]), video_id=self.aroll_material,
                                  local_material_id=d.by_id[self.aroll_material]["local_material_id"])
        for piece in self.speech.pieces:
            seg = d.segment("speech", piece["out"], piece["out"] + piece["dur"], material_id=audio_id)
            seg["source_timerange"] = {"start": us(piece["src_start"]), "duration": seg["target_timerange"]["duration"]}
            seg["volume"] = self.gain
            d.place("speech", "speech", seg)

    # -- hook title
    def hook(self):
        hook = self.plan.get("hook")
        if not hook:
            return None
        end = snap(self.speech.end(hook["until_word"]))
        seg = self.draft.segment("hook", 0, end)
        self.draft.set_text(seg, hook["text"], hook.get("highlight"))
        self.draft.place("hook", "hook", seg)
        self.sfx.append((0.0, "woosh"))
        return end

    # -- things that replace the A-roll picture
    def covers(self):
        covers = []
        for item in self.plan.get("broll", []):
            start, end = self.span(item)
            covers.append({"kind": "broll", "start": start, "end": end, "file": self.path(item["file"]),
                           "src_start": item.get("src_start")})
        for item in self.plan.get("cards", []):
            start, end = self.span(item)
            if item.get("style", "overlay") == "fullscreen":
                covers.append({"kind": "card", "start": start, "end": end, "item": item})
            else:
                self.card(item, start, end)
        covers.sort(key=lambda c: c["start"])
        self._snap_to_cuts(covers)
        for prev, nxt in zip(covers, covers[1:]):
            nxt["start"] = max(nxt["start"], prev["end"])
            if nxt["start"] - prev["end"] < MIN_SHOT:
                prev["end"] = nxt["start"]
        if covers and covers[0]["start"] < MIN_SHOT:
            covers[0]["start"] = 0.0
        if covers and self.T - covers[-1]["end"] < MIN_SHOT:
            covers[-1]["end"] = self.T
        covers = [c for c in covers if c["end"] - c["start"] > 1 / FPS]
        for cover in covers:
            if cover["kind"] == "broll":
                self._fit_broll(cover)
            else:
                self.card(cover["item"], cover["start"], cover["end"])
        return covers

    def _snap_to_cuts(self, covers):
        """Covers that start or end near a jump cut move onto it, hiding the cut."""
        for cover in covers:
            for key in ("start", "end"):
                near = [c for c in self.speech.cuts if abs(c - cover[key]) < MIN_SHOT]
                if near:
                    cover[key] = min(near, key=lambda c: abs(c - cover[key]))

    def _fit_broll(self, cover):
        _, info = self.draft.media_material(cover["file"])
        need = cover["end"] - cover["start"]
        if not info["is_image"] and info["duration"] < need:
            cover["end"] = snap(cover["start"] + info["duration"] - 1 / FPS)
            need = cover["end"] - cover["start"]
        if cover["src_start"] is None:
            cover["src_start"] = 0.0 if info["is_image"] else max((info["duration"] - need) / 2, 0.0)
        cover["src_start"] = min(cover["src_start"], max(info["duration"] - need, 0.0))

    def card(self, item, start, end):
        name = "card_full" if item.get("style") == "fullscreen" else "card_overlay"
        seg = self.draft.segment(name, start, end)
        self.draft.set_text(seg, item["text"])
        self.draft.place("texts", name, seg)
        self.sfx.append((start, "pop"))
        if name == "card_overlay":
            self.blur_spans.append((start, end))

    # -- things floating over the picture
    def overlays(self):
        d = self.draft
        for item in self.plan.get("posters", []):
            start, end = self.span(item)
            material_id, info = d.media_material(self.path(item["file"]))
            if not info["is_image"]:
                end = min(end, snap(start + info["duration"]))
            seg = d.segment("poster", start, end, material_id=material_id)
            seg["source_timerange"] = {"start": 0, "duration": seg["target_timerange"]["duration"]}
            lane = d.place("overlay", "poster", seg)
            seg["render_index"] = lane + 1
            self.blur_spans.append((start, end))
            self.sfx.append((start, "click"))
        for group in self.plan.get("logos", []):
            self.logo_group(group)

    def logo_group(self, group):
        d = self.draft
        start, end = self.span(group)
        if group.get("title"):
            title = d.segment("logo_title", start, end)
            d.set_text(title, group["title"])
            d.place("texts", "logo_title", title)
        drop = () if group.get("chroma", True) else ("chromas",)
        for n, file in enumerate(group["files"]):
            proto = "logo" if n == 0 else "logo_next"
            logo_start = snap(start + n * LOGO_STAGGER)
            material_id, info = d.media_material(self.path(file))
            logo_end = end if info["is_image"] else min(end, snap(logo_start + info["duration"]))
            if logo_end - logo_start < MIN_SHOT:
                continue
            seg = d.segment(proto, logo_start, logo_end, material_id=material_id, drop_kinds=drop)
            seg["source_timerange"] = {"start": 0, "duration": seg["target_timerange"]["duration"]}
            if n > 1:
                seg["clip"]["transform"]["y"] -= LOGO_STEP_Y * (n - 1)
            lane = d.place("overlay", proto, seg)
            seg["render_index"] = lane + 1
            self.sfx.append((logo_start, "click"))
        self.blur_spans.append((start, end))

    # -- main video track
    def main_track(self, covers, hook_end):
        shots = []
        cursor = 0.0
        for cover in covers + [{"kind": "end", "start": self.T, "end": self.T}]:
            shots += self.aroll_shots(cursor, cover["start"])
            if cover["kind"] != "end":
                shots.append(dict(cover, style="none", blur=False))
            cursor = max(cursor, cover["end"])
        shots = self.apply_punch_ins(shots)
        shots = self.apply_blur(shots)
        self.assign_zoom(shots)
        transition_at = self._nearest_boundary(shots, hook_end) if hook_end else None
        for shot in shots:
            self.emit_shot(shot, add_transition=transition_at is not None and abs(shot["end"] - transition_at) < 1e-6)
        if transition_at is not None:
            self.sfx.append((transition_at, "swish"))
        return shots

    def aroll_shots(self, start, end):
        shots = []
        t = start
        while end - t > 1e-6:
            piece_end = min(self.speech.piece_end(t), end)
            if piece_end <= t:
                break
            shots += self.split_long(t, piece_end)
            t = piece_end
        return shots

    def split_long(self, start, end):
        if end - start <= LONG_SHOT:
            return [{"kind": "aroll", "start": start, "end": end, "style": None, "blur": False}]
        mid = (start + end) / 2
        candidates = [self.speech.start(i) for i in self.speech.kept
                      if start + 1.0 < self.speech.start(i) < end - 1.0]
        if not candidates:
            return [{"kind": "aroll", "start": start, "end": end, "style": None, "blur": False}]
        cut = snap(min(candidates, key=lambda c: abs(c - mid)))
        return self.split_long(start, cut) + self.split_long(cut, end)

    def apply_punch_ins(self, shots):
        for index in self.plan.get("punch_in", []):
            t = snap(self.speech.start(index))
            shots = _split_at(shots, t)
            near = [s for s in shots if s["kind"] == "aroll" and abs(s["start"] - t) < MIN_SHOT]
            if near:
                shot = min(near, key=lambda s: abs(s["start"] - t))
                shot["style"] = "fast"
                self.sfx.append((shot["start"], "swish"))
        return shots

    def apply_blur(self, shots):
        for start, end in self.blur_spans:
            edges = [s["start"] for s in shots] + [shots[-1]["end"]]
            start, end = _snap_to(edges, start), _snap_to(edges, end)
            shots = _split_at(_split_at(shots, start), end)
            for shot in shots:
                if shot["start"] >= start - 1e-6 and shot["end"] <= end + 1e-6:
                    shot["blur"] = True
        return shots

    def assign_zoom(self, shots):
        n = 0
        for shot in shots:
            if shot["kind"] != "aroll" or shot["blur"] or shot["style"] == "fast":
                continue
            shot["style"] = ["none", "slow", "punch"][n % 3]
            shot["amount"] = (SLOW_ZOOM_ENDS if shot["style"] == "slow" else PUNCH_SCALES)[(n // 3) % 3]
            n += 1

    def _nearest_boundary(self, shots, t):
        ends = [s["end"] for s in shots[:-1]]
        best = min(ends, key=lambda e: abs(e - t), default=None)
        return best if best is not None and abs(best - t) < 0.5 else None

    def emit_shot(self, shot, add_transition):
        d = self.draft
        if shot["kind"] == "card":
            material_id, _ = d.media_material(TEMPLATE_DIR / BLACK_TEXTURE)
            d.by_id[material_id]["path"] = str(d.draft_dir / BLACK_TEXTURE)
            seg = d.segment("photo", shot["start"], shot["end"], material_id=material_id)
            seg["source_timerange"] = {"start": 0, "duration": seg["target_timerange"]["duration"]}
            d.place("main", "aroll", seg)
            return
        if shot["kind"] == "aroll":
            material_id, info = self.aroll_material, self.aroll_info
            _, src = self.speech.source_at(shot["start"])
        else:
            material_id, info = d.media_material(shot["file"])
            src = shot["src_start"] + (shot["start"] - shot.get("cover_start", shot["start"]))
        proto = "blur" if shot["blur"] else ("zoom" if shot["style"] in ("slow", "fast") else "aroll")
        seg = d.segment(proto, shot["start"], shot["end"], material_id=material_id)
        seg["source_timerange"] = {"start": us(src), "duration": seg["target_timerange"]["duration"]}
        seg["volume"] = 0.0
        if add_transition:
            seg["extra_material_refs"].append(d.clone_material(d.proto_material("transition", "transitions")))
        base = cover_scale(info["width"], info["height"])
        style, amount = shot["style"], shot.get("amount", 1.0)
        scale = base * (amount if style == "punch" else 1.0)
        seg["clip"]["scale"] = {"x": scale, "y": scale}
        seg["clip"]["transform"] = {"x": 0.0, "y": 0.0}
        seg["uniform_scale"] = {"on": True, "value": scale}
        if style == "slow":
            set_scale_keyframes(seg, [(0, base), (shot["end"] - shot["start"], base * amount)])
        elif style == "fast":
            set_scale_keyframes(seg, [(0, base), (FAST_PUNCH_TIME, base * FAST_PUNCH_SCALE)])
        else:
            seg["common_keyframes"] = []
        d.place("main", "aroll", seg)

    # -- text layers
    def subtitles(self):
        chunks = caption_chunks([(i, self.words[i]["w"], *self.speech.out[i]) for i in self.speech.kept])
        for n, (text, start, end) in enumerate(chunks):
            next_start = chunks[n + 1][1] if n + 1 < len(chunks) else self.T
            end = next_start if next_start - end < 0.3 else end + 0.1
            seg = self.draft.segment("subtitle", snap(start), snap(min(end, self.T)))
            self.draft.set_text(seg, text)
            self.draft.place("subtitles", "subtitle", seg)

    def cta(self):
        cta = self.plan.get("cta")
        if not cta:
            return
        start, end = self.span(cta, end_default=self.T)
        seg = self.draft.segment("cta", start, end)
        self.draft.set_text(seg, cta["text"])
        self.draft.place("texts", "cta", seg)
        self.sfx.append((start, "pop"))

    def credit(self):
        name = self.plan.get("credit")
        if not name:
            return
        count = max(1, round(self.T / CREDIT_EVERY))
        for n in range(count):
            start, end = snap(self.T * n / count), snap(self.T * (n + 1) / count)
            seg = self.draft.segment("credit", start, end)
            self.draft.set_text(seg, f"Original content from {name}")
            x, y = CREDIT_POSITIONS[n % len(CREDIT_POSITIONS)]
            seg["clip"]["transform"] = {"x": x, "y": y}
            self.draft.place("credit", "credit", seg)

    def grading(self):
        for name in ("filter", "adjust"):
            self.draft.place(name, name, self.draft.segment(name, 0, self.T))

    def sound_effects(self):
        for click_word in self.plan.get("clicks", []):
            self.sfx.append((self.speech.start(click_word), "click"))
        for t, name in sorted(self.sfx):
            proto = self.draft.proto_segment(name)
            start = snap(max(t - SFX_LEAD[name], 0))
            end = min(snap(start + proto["target_timerange"]["duration"] / SEC), self.T)
            if end - start > 1 / FPS:
                seg = self.draft.segment(name, start, end)
                self.draft.place("sfx", name, seg)


def _snap_to(edges, t):
    """Move t onto an existing shot edge if one is close, so no sliver shot is left behind."""
    nearest = min(edges, key=lambda e: abs(e - t))
    return nearest if abs(nearest - t) < MIN_SHOT else t


def _split_at(shots, t):
    out = []
    for shot in shots:
        if shot["start"] + MIN_SHOT / 2 < t < shot["end"] - MIN_SHOT / 2:
            left, right = dict(shot, end=t), dict(shot, start=t)
            if shot["kind"] == "broll":
                right["cover_start"] = shot.get("cover_start", shot["start"])
                left["cover_start"] = right["cover_start"]
            out += [left, right]
        else:
            out.append(shot)
    return out


def set_scale_keyframes(seg, points):
    """points: [(seconds from segment start, scale)]. Video keyframes use source time."""
    base = seg["source_timerange"]["start"]
    track = (seg.get("common_keyframes") or [None])[0]
    proto_kf = track["keyframe_list"][0]
    seg["common_keyframes"] = [{
        "id": uid(), "material_id": "", "property_type": "KFTypeScaleX",
        "keyframe_list": [dict(copy.deepcopy(proto_kf), id=uid(), time_offset=base + us(t), values=[v])
                          for t, v in points],
    }]
    seg["clip"]["scale"] = {"x": points[0][1], "y": points[0][1]}


ATTACH = re.compile(r"^(-|%|[.,!?…:;])")
TRAILING_PUNCT = ".,!?…:;"


def caption_chunks(words, max_words=3, max_chars=18, max_gap=0.25):
    """words: [(index, text, out_start, out_end)] → [(text, start, end)], 2–3 words each."""
    chunks, current = [], []

    def flush():
        if current:
            text = ""
            for _, w, _, _ in current:
                text += w if (text and ATTACH.match(w)) or not text else " " + w
            chunks.append((text.strip(TRAILING_PUNCT + " "), current[0][2], current[-1][3]))
            current.clear()

    for word in words:
        if current:
            spoken = [w for w in current if not ATTACH.match(w[1])]
            joined = " ".join(w[1] for w in current)
            if (len(spoken) >= max_words and not ATTACH.match(word[1])) or len(joined) > max_chars \
                    or current[-1][1][-1:] in ".,!?" or word[2] - current[-1][3] > max_gap:
                flush()
        current.append(word)
    flush()
    return [c for c in chunks if c[0]]


# ---------------------------------------------------------------- files on disk

def unique_dir(root, name):
    candidate, n = root / name, 1
    while candidate.exists():
        candidate, n = root / f"{name} ({n})", n + 1
    return candidate


def write_draft(data, draft_dir, name, duration, cover_source, cover_time):
    shutil.copytree(TEMPLATE_DIR, draft_dir)
    old_timeline = data["id"]
    new_timeline = uid()
    data["id"] = new_timeline
    (draft_dir / "Timelines" / old_timeline).rename(draft_dir / "Timelines" / new_timeline)
    for rel in ("Timelines/project.json", "timeline_layout.json"):
        p = draft_dir / rel
        p.write_text(p.read_text().replace(old_timeline, new_timeline))
    project = json.loads((draft_dir / "Timelines/project.json").read_text())
    project["id"] = uid()
    (draft_dir / "Timelines/project.json").write_text(json.dumps(project))

    data["static_cover_image_path"] = str(draft_dir / "draft_cover.jpg")
    text = json.dumps(data, ensure_ascii=False)
    text = re.sub(r"##_draftpath_placeholder_[0-9A-Fa-f-]+_##", str(draft_dir).replace("\\", "/"), text)
    for target in (draft_dir / "draft_info.json", draft_dir / "Timelines" / new_timeline / "draft_info.json"):
        target.write_text(text)

    cover = draft_dir / "draft_cover.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{cover_time:.3f}", "-i", str(cover_source),
                    "-frames:v", "1", "-vf",
                    f"scale={CANVAS_W}:{CANVAS_H}:force_original_aspect_ratio=increase,crop={CANVAS_W}:{CANVAS_H}",
                    str(cover)], check=True)
    shutil.copy(cover, draft_dir / "Timelines" / new_timeline / "draft_cover.jpg")

    now = int(time.time() * SEC)
    meta = json.loads((draft_dir / "draft_meta_info.json").read_text())
    for key, value in list(meta.items()):
        if key.startswith("tm_draft_cloud") or key == "cloud_package_completed_time":
            meta[key] = 0 if isinstance(value, int) else ""
    for group in meta.get("draft_materials", []):
        group["value"] = []
    meta.update(draft_id=uid(), draft_name=name, draft_fold_path=str(draft_dir),
                draft_root_path=str(draft_dir.parent), draft_cover="draft_cover.jpg",
                draft_cloud_last_action_download=False, tm_draft_create=now, tm_draft_modified=now,
                tm_duration=us(duration), draft_timeline_materials_size_=0)
    (draft_dir / "draft_meta_info.json").write_text(json.dumps(meta, ensure_ascii=False))
    store = json.loads((draft_dir / "draft_virtual_store.json").read_text())
    for group in store["draft_virtual_store"]:
        if group["type"] == 1:
            group["value"] = []
    (draft_dir / "draft_virtual_store.json").write_text(json.dumps(store))
    seconds = int(time.time())
    (draft_dir / "draft_settings").write_text(
        "[General]\ncloud_last_modify_platform=mac\n"
        f"draft_create_time={seconds}\ndraft_last_edit_time={seconds}\nreal_edit_keys=1\nreal_edit_seconds=0\n")


def print_summary(editor, shots):
    sp = editor.speech
    print(f"Duration {editor.T:.2f}s · {len(sp.pieces)} speech pieces · {len(shots)} shots")
    longest = max(shots, key=lambda s: s["end"] - s["start"])
    print(f"Longest shot {longest['end'] - longest['start']:.2f}s at {longest['start']:.2f}s")
    for s in shots:
        label = s["kind"] + (" blur" if s["blur"] else "") + (f" {s['style']}" if s.get("style") not in (None, "none") else "")
        print(f"  {s['start']:6.2f}-{s['end']:6.2f}  {label}")
    for warning in sp.warnings:
        print(f"WARNING: {warning}")
    flags = sp.transcript_flags()
    print(f"\nTranscript check: {len(flags) or 'nothing'} to fix")
    for flag in flags:
        print(f"  FIX: {flag}")


def visible_tails(editor, shots):
    """Speech pieces whose last frame is on screen: an A-roll shot that ends where the piece ends."""
    tails = []
    for shot in shots:
        if shot["kind"] != "aroll":
            continue
        piece, _ = editor.speech.source_at(shot["end"] - 1 / FPS)
        if abs(snap(piece["out"] + piece["dur"]) - shot["end"]) < 1e-6:
            tails.append(piece)
    return tails


def render_tail_sheets(editor, shots, out_dir):
    """One row per visible jump cut: frames 0.3, 0.2, 0.1 s and one frame before the cut."""
    out_dir.mkdir(exist_ok=True)
    for old in out_dir.glob("*.jpg"):
        old.unlink()
    rows = []
    for n, piece in enumerate(visible_tails(editor, shots)):
        src_end = piece["src_start"] + piece["dur"]
        inputs, scales = [], []
        for k, offset in enumerate(TAIL_OFFSETS):
            inputs += ["-ss", f"{max(src_end - offset, 0):.3f}", "-i", str(editor.aroll)]
            scales.append(f"[{k}:v]scale=-2:300[f{k}]")
        stack = "".join(f"[f{k}]" for k in range(len(TAIL_OFFSETS)))
        row = out_dir / f"row-{n:02d}.jpg"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex",
                        ";".join(scales) + f";{stack}hstack=inputs={len(TAIL_OFFSETS)}", "-frames:v", "1",
                        str(row)], check=True)
        rows.append(row)
        word = editor.words[piece["last_word"]]
        sheet = n // TAIL_ROWS_PER_SHEET + 1
        print(f"  sheet-{sheet} row {n % TAIL_ROWS_PER_SHEET + 1}: cut at {piece['out'] + piece['dur']:6.2f}s, "
              f"ends on [{word['i']}]{word['w']}")
    for start in range(0, len(rows), TAIL_ROWS_PER_SHEET):
        group = rows[start:start + TAIL_ROWS_PER_SHEET]
        sheet = out_dir / f"sheet-{start // TAIL_ROWS_PER_SHEET + 1}.jpg"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *[a for r in group for a in ("-i", str(r))],
                        "-filter_complex", f"vstack=inputs={len(group)}" if len(group) > 1 else "null",
                        str(sheet)], check=True)
    for row in rows:
        row.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--drafts-root", default=str(DEFAULT_DRAFTS_ROOT))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text())
    template = json.loads((TEMPLATE_DIR / "draft_info.json").read_text())
    draft_dir = unique_dir(Path(args.drafts_root).expanduser(), plan["name"])
    draft = Draft(template, draft_dir)
    editor = Editor(plan, plan_path.parent, draft)
    shots = editor.build()
    data = draft.finish(["main", "texts", "overlay", "filter", "adjust", "hook", "subtitles", "credit",
                         "speech", "sfx"], editor.T)
    print_summary(editor, shots)
    if args.dry_run:
        tails_dir = plan_path.parent / "tails"
        print(f"\nTail recheck → {tails_dir} (frames 0.3 / 0.2 / 0.1 / 0 s before each cut):")
        render_tail_sheets(editor, shots, tails_dir)
        return
    first_piece = editor.speech.pieces[0]
    write_draft(data, draft_dir, draft_dir.name, editor.T, editor.aroll, first_piece["src_start"] + 0.5)
    print(f"\nDraft written: {draft_dir}\nCapCut lists it on its home screen (restart CapCut if it does not appear).")


if __name__ == "__main__":
    main()
