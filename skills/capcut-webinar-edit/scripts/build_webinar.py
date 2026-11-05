#!/usr/bin/env python3
"""Build one landscape CapCut project from a long webinar recording, one timeline per lesson.

Usage: build_webinar.py <plan.json> [--drafts-root DIR] [--dry-run]

Each timeline is: intro sting, the kept speech of one lesson, outro sting, on a 1920x1080 canvas.
The words decide what is kept (word-index ranges from transcribe.py); the audio decides where each
piece starts and stops, so no word is clipped. Pauses longer than MAX_PAUSE shrink to KEPT_PAUSE.
Layers are cloned from the capcut-auto-edit template through its draft writer, so both skills
must sit side by side (they ship together in this plugin).
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "capcut-auto-edit" / "scripts"))
from build_draft import (DEFAULT_DRAFTS_ROOT, TEMPLATE_DIR, Draft, SpeechTimeline, kept_loudness,  # noqa: E402
                         silences_for_kept, snap, speech_gain, timeline_text, uid, unique_dir, us, write_draft)

STING = Path(__file__).resolve().parent.parent / "assets" / "portolabs-sting.mp4"
CANVAS = (1920, 1080)
FPS = 30.0
# Dead air while the speaker clicks around or waits shrinks to a short beat instead of vanishing,
# so a screen-share demo does not jump on every breath.
MAX_PAUSE = 3.0
KEPT_PAUSE = 1.0
LESSON_LENGTH = (120, 1200)
UNUSED_REPORT = 10.0
EDGE_WORDS = 8


def lesson_speech(words, keep, media_duration, silences):
    return SpeechTimeline(words, keep, media_duration, silences, max_gap=MAX_PAUSE, kept_pause=KEPT_PAUSE)


def unused_spans(words, keeps, min_seconds):
    """Runs of words that no lesson keeps, (first, last) word index, where the time between the
    kept words around them is at least min_seconds."""
    kept = {i for keep in keeps for a, b in keep for i in range(a, b + 1)}
    spans, start = [], None
    for i in range(len(words) + 1):
        if i < len(words) and i not in kept:
            start = i if start is None else start
        elif start is not None:
            cut_from = words[start - 1]["e"] if start > 0 else 0.0
            cut_to = words[i]["s"] if i < len(words) else words[-1]["e"]
            if cut_to - cut_from >= min_seconds:
                spans.append((start, i - 1))
            start = None
    return spans


def add_timelines(draft_dir, timelines):
    """Give the project one timeline per (name, data), in order. The first is the main timeline
    write_draft already wrote; every other data still carries the template's timeline id."""
    for _, data in timelines[1:]:
        template_timeline = TEMPLATE_DIR / "Timelines" / data["id"]
        data["id"] = uid()
        target = draft_dir / "Timelines" / data["id"]
        shutil.copytree(template_timeline, target)
        (target / "draft_info.json").write_text(timeline_text(data, draft_dir))
    project_path = draft_dir / "Timelines" / "project.json"
    project = json.loads(project_path.read_text())
    stamp = project["create_time"]
    project["main_timeline_id"] = timelines[0][1]["id"]
    project["timelines"] = [{"create_time": stamp, "id": data["id"], "is_marked_delete": False, "name": name,
                             "update_time": stamp} for name, data in timelines]
    project_path.write_text(json.dumps(project))
    layout_path = draft_dir / "timeline_layout.json"
    layout = json.loads(layout_path.read_text())
    layout["dockItems"][0].update(timelineIds=[data["id"] for _, data in timelines],
                                  timelineNames=[name for name, _ in timelines])
    layout_path.write_text(json.dumps(layout))


def write_project(draft_dir, lessons, datas):
    """The webinar stays linked by its path; the stings are copied into the project folder, so a
    plugin update that moves the skill folder does not break old projects."""
    stings = {}
    for lesson in lessons:
        for media in lesson.stings.values():
            local = draft_dir / media["path"].name
            lesson.draft.by_id[media["material"]]["path"] = str(local)
            lesson.draft.by_id[media["audio"]]["path"] = str(local)
            stings[media["path"]] = local
    first = lessons[0]
    write_draft(datas[0], draft_dir, draft_dir.name, first.T, first.video,
                first.speech.pieces[0]["src_start"] + 1.0, canvas=CANVAS)
    add_timelines(draft_dir, [(lesson.title, data) for lesson, data in zip(lessons, datas)])
    for source, local in stings.items():
        shutil.copy(source, local)


def clock(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def text(words, a, b):
    return " ".join(w["w"] for w in words[a:b + 1])


class Lesson:
    def __init__(self, spec, number, video, words, audio, stings, template, draft_dir):
        self.title = f"#{number} {spec['title']}"
        self.keep = spec["keep"]
        self.words = words
        for a, b in self.keep:
            if not 0 <= a <= b < len(words):
                sys.exit(f"{self.title}: keep [{a}, {b}] is outside the transcript (0–{len(words) - 1}).")
        self.video = video
        self.draft = Draft(template, draft_dir)
        self.loaded = {}
        self.raw = self.media(video, gain=None)
        self.stings = {name: self.media(path, gain=1.0) for name, path in stings.items()}
        silences = silences_for_kept(audio, words, self.keep, self.raw["info"]["duration"])
        self.speech = lesson_speech(words, self.keep, self.raw["info"]["duration"], silences)
        self.raw["gain"] = speech_gain(kept_loudness(audio, words, self.keep))

    def media(self, path, gain):
        """A video material plus an audio material reading the same file, as capcut-auto-edit does:
        the picture track is muted and the sound sits on its own track."""
        if path in self.loaded:
            return self.loaded[path]
        d = self.draft
        material, info = d.media_material(path)
        audio = d.add_material(d.proto_segment("speech")["material_id"], path=str(path), name=path.stem,
                               duration=us(info["duration"]), video_id=material,
                               local_material_id=d.by_id[material]["local_material_id"])
        self.loaded[path] = {"path": path, "material": material, "audio": audio, "info": info, "gain": gain}
        return self.loaded[path]

    def build(self):
        t = 0.0
        if "intro" in self.stings:
            t = self.clip(self.stings["intro"], 0.0, t, self.stings["intro"]["info"]["duration"])
        self.speech_start = t
        for piece in self.speech.pieces:
            self.clip(self.raw, piece["src_start"], t + piece["out"], piece["dur"])
        t = snap(t + self.speech.duration)
        if "outro" in self.stings:
            t = self.clip(self.stings["outro"], 0.0, t, self.stings["outro"]["info"]["duration"])
        self.T = t
        data = self.draft.finish(["main", "audio"], t)
        data["canvas_config"] = {"ratio": "16:9", "width": CANVAS[0], "height": CANVAS[1], "background": None}
        data["fps"] = FPS
        return data

    def clip(self, media, src_start, out, dur):
        d = self.draft
        end = snap(out + dur)
        source = {"start": us(src_start), "duration": us(end) - us(out)}
        seg = d.segment("aroll", out, end, material_id=media["material"])
        seg["source_timerange"] = source
        seg["volume"] = 0.0
        seg["clip"]["scale"] = {"x": 1.0, "y": 1.0}  # 1.0 = fit the canvas; a 16:10 webinar gets thin side bars
        seg["clip"]["transform"] = {"x": 0.0, "y": 0.0}
        seg["uniform_scale"] = {"on": True, "value": 1.0}
        seg["common_keyframes"] = []
        d.place("main", "aroll", seg)
        sound = d.segment("speech", out, end, material_id=media["audio"])
        sound["source_timerange"] = dict(source)
        sound["volume"] = media["gain"]
        d.place("audio", "speech", sound)
        return end

    def summary(self):
        speech = self.speech.duration
        lines = [f"{self.title}: {clock(speech)} of material, {clock(self.T)} with intro/outro, "
                 f"{len(self.speech.pieces)} pieces"]
        w = self.words
        for a, b in self.keep:
            head = text(w, a, min(a + EDGE_WORDS - 1, b))
            tail = text(w, max(b - EDGE_WORDS + 1, a + EDGE_WORDS), b)
            joined = f"{head} … {tail}" if tail else head
            lines.append(f"  [{a}-{b}] {clock(w[a]['s'])}-{clock(w[b]['e'])}  \"{joined}\"")
        low, high = LESSON_LENGTH
        if not low <= speech <= high:
            lines.append(f"  WARNING: {clock(speech)} of material, outside {clock(low)}–{clock(high)}")
        return "\n".join(lines)


def overlaps(lessons):
    seen, notes = {}, []
    for lesson in lessons:
        for a, b in lesson.keep:
            for i in range(a, b + 1):
                if i in seen and seen[i] != lesson.title:
                    notes.append(f"WARNING: word [{i}] is kept in both {seen[i]} and {lesson.title}")
                    break
                seen[i] = lesson.title
    return notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--drafts-root", default=str(DEFAULT_DRAFTS_ROOT))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text())
    resolve = lambda p: (plan_path.parent / Path(p).expanduser()).resolve()
    video = resolve(plan["video"])
    words_path = resolve(plan.get("words", "words.json"))
    words = json.loads(words_path.read_text())
    audio = json.loads(words_path.with_name("audio.json").read_text())
    stings = {name: resolve(plan[name]) if plan.get(name) else STING for name in ("intro", "outro")}
    template = json.loads((TEMPLATE_DIR / "draft_info.json").read_text())
    draft_dir = unique_dir(Path(args.drafts_root).expanduser(), plan.get("name") or video.stem)

    lessons, datas = [], []
    for n, spec in enumerate(plan["lessons"], plan.get("first_number", 1)):
        lesson = Lesson(spec, n, video, words, audio, stings, template, draft_dir)
        datas.append(lesson.build())
        print(lesson.summary())
        lessons.append(lesson)

    for note in overlaps(lessons):
        print(note)
    spans = unused_spans(words, [lesson.keep for lesson in lessons], UNUSED_REPORT)
    total = sum(lesson.speech.duration for lesson in lessons)
    print(f"\n{len(lessons)} lessons, {clock(total)} of material from a {clock(lessons[0].raw['info']['duration'])} recording.")
    print(f"Not used ({len(spans)} stretches of {UNUSED_REPORT:.0f}s or more), check that none is material:")
    for a, b in spans:
        print(f"  [{a}-{b}] {clock(words[a]['s'])}-{clock(words[b]['e'])}  \"{text(words, a, min(a + 15, b))}…\"")
    if not args.dry_run:
        write_project(draft_dir, lessons, datas)
        print(f"\nProject written: {draft_dir} ({len(lessons)} timelines)")


if __name__ == "__main__":
    main()
