#!/usr/bin/env python3
"""Build one CapCut project with a timeline per reel: picked moments of a long video over a background song.

Usage: build_reels.py <plan.json> [--drafts-root DIR] [--dry-run]

Layers are cloned from the capcut-auto-edit template, so they are prototypes CapCut already opens.
Each clip sits sharp in the middle of the 1080x1920 canvas over a blurred, filled copy of itself.
Each reel's song section is cut and faded with ffmpeg into the project folder, so the project owns its audio.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "capcut-auto-edit" / "scripts"))
from build_draft import (CANVAS_H, CANVAS_W, DEFAULT_DRAFTS_ROOT, TEMPLATE_DIR, Draft, cover_scale,  # noqa: E402
                         probe, snap, unique_dir, us, write_project)

# 1 = clip fills the canvas width. 1.7 makes the subject bigger and crops most of a date stamp
# burned into a top corner (2.0 crops all of it); the blurred copy fills the rest.
ZOOM = 1.7
FADE_IN = 1.0
FADE_OUT = 1.5
REEL_LENGTH = (15, 60)
MUSIC_FILE = "bgm-{}.m4a"
PREVIEW_ROWS = 8


def placement(width, height, zoom, focus):
    """Canvas px per source px, and the horizontal shift in canvas px that centres `focus`
    (0 left … 1 right of the source) without pulling an edge of the clip into the frame."""
    scale = min(CANVAS_W / width, CANVAS_H / height) * zoom
    slack = max(width * scale - CANVAS_W, 0) / 2
    return scale, min(max((0.5 - focus) * width * scale, -slack), slack)


def pan_x(width, height, zoom, focus):
    """CapCut transform x: 1 = half the canvas width."""
    _, offset = placement(width, height, zoom, focus)
    return offset / (CANVAS_W / 2)


def visible_box(width, height, zoom, focus):
    """The part of the source that shows sharp on the canvas: (x, y, w, h) in source px."""
    scale, offset = placement(width, height, zoom, focus)
    w, h = min(width, CANVAS_W / scale), min(height, CANVAS_H / scale)
    return (width - w) / 2 - offset / scale, (height - h) / 2, w, h


def audio_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


class Reel:
    def __init__(self, reel, number, video, music, template, project_dir):
        self.reel = reel
        self.video = video
        self.music = music
        self.music_file = project_dir / MUSIC_FILE.format(number)
        self.draft = Draft(template, project_dir)
        self.material, self.info = self.draft.media_material(video)
        self.clips = []
        self.warnings = []
        t = 0.0
        for clip in reel["clips"]:
            speed = clip.get("speed", 1.0)
            end = snap(t + clip["dur"])
            self.clips.append(dict(clip, out=t, end=end, speed=speed, zoom=clip.get("zoom", ZOOM),
                                   src_end=clip["at"] + (end - t) * speed))
            t = end
        self.T = t
        self.check()

    def check(self):
        low, high = REEL_LENGTH
        if not low <= self.T <= high:
            self.warnings.append(f"reel is {self.T:.1f}s, outside {low}–{high}s")
        for clip in self.clips:
            if clip["src_end"] > self.info["duration"]:
                sys.exit(f"{self.reel['name']}: clip at {clip['at']}s runs past the end of the video")
        if self.music and self.reel.get("music_start", 0) + self.T > audio_duration(self.music):
            sys.exit(f"{self.reel['name']}: the song is too short from music_start {self.reel.get('music_start', 0)}s")

    def build(self):
        for clip in self.clips:
            if clip["zoom"] < cover_scale(self.info["width"], self.info["height"]):
                self.video_segment("bg", "blur", clip, cover_scale(self.info["width"], self.info["height"]), 0.0)
            x = pan_x(self.info["width"], self.info["height"], clip["zoom"], clip.get("focus", 0.5))
            self.video_segment("main", "aroll", clip, clip["zoom"], x)
        if self.music:
            self.music_segment()
        return self.draft.finish(["bg", "main", "music"], self.T)

    def video_segment(self, lane, proto, clip, scale, x):
        d = self.draft
        seg = d.segment(proto, clip["out"], clip["end"], material_id=self.material)
        seg["source_timerange"] = {"start": us(clip["at"]), "duration": us(clip["src_end"]) - us(clip["at"])}
        seg["speed"] = clip["speed"]
        for ref in seg["extra_material_refs"]:
            if d.by_id[ref].get("type") == "speed":
                d.by_id[ref]["speed"] = clip["speed"]
        seg["volume"] = 0.0
        seg["clip"]["scale"] = {"x": scale, "y": scale}
        seg["clip"]["transform"] = {"x": x, "y": 0.0}
        seg["uniform_scale"] = {"on": True, "value": 1.0}  # as CapCut writes it; see build_draft.emit_shot
        seg["common_keyframes"] = []
        d.place(lane, proto, seg)

    def music_segment(self):
        d = self.draft
        # The woosh SFX prototype is a plain local audio file; strip its CapCut-library identity.
        audio_id = d.add_material(d.proto_segment("woosh")["material_id"], path=str(self.music_file),
                                  name=self.music.stem, duration=us(self.T), effect_id="", app_id=0,
                                  category_id="", category_name="")
        seg = d.segment("woosh", 0, self.T, material_id=audio_id)
        seg["source_timerange"] = {"start": 0, "duration": us(self.T)}
        seg["volume"] = self.reel.get("music_volume", 1.0)
        d.place("music", "woosh", seg)

    def cover_time(self):
        first = self.clips[0]
        return (first["at"] + first["src_end"]) / 2

    def write_music(self):
        start = self.reel.get("music_start", 0)
        fades = f"afade=t=in:d={FADE_IN},afade=t=out:st={self.T - FADE_OUT:.3f}:d={FADE_OUT}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", f"{self.T:.3f}", "-i", str(self.music),
                        "-af", fades, "-c:a", "aac", "-b:a", "192k", str(self.music_file)], check=True)

    def preview(self, sheet):
        """One row per clip: its first, middle and last frame, cropped to what shows sharp."""
        rows = []
        for n, c in enumerate(self.clips):
            x, y, w, h = visible_box(self.info["width"], self.info["height"], c["zoom"], c.get("focus", 0.5))
            last = c["src_end"] - 1 / 30
            inputs, frames = [], []
            for k, t in enumerate([c["at"], (c["at"] + last) / 2, last]):
                inputs += ["-ss", f"{t:.3f}", "-i", str(self.video)]
                frames.append(f"[{k}:v]crop={w:.0f}:{h:.0f}:{x:.0f}:{y:.0f},scale=320:240:force_original_aspect_ratio=decrease,"
                              f"pad=320:240:(ow-iw)/2:(oh-ih)/2[f{k}]")
            row = sheet.with_name(f"{sheet.stem}-row{n:02d}.jpg")
            subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
                            ";".join(frames) + ";[f0][f1][f2]hstack=inputs=3", "-frames:v", "1", str(row)], check=True)
            rows.append(row)
        for start in range(0, len(rows), PREVIEW_ROWS):
            group = rows[start:start + PREVIEW_ROWS]
            out = sheet.with_name(f"{sheet.stem}-{start // PREVIEW_ROWS + 1}.jpg")
            subprocess.run(["ffmpeg", "-v", "error", "-y", *[a for r in group for a in ("-i", str(r))], "-filter_complex",
                            f"vstack=inputs={len(group)}" if len(group) > 1 else "null", str(out)], check=True)
            print(f"  preview {out}: clips {start + 1}–{start + len(group)}")
        for row in rows:
            row.unlink()

    def summary(self):
        lines = [f"{self.reel['name']}: {self.T:.1f}s, {len(self.clips)} clips"]
        for c in self.clips:
            extra = "".join([f" ×{c['speed']:g}" if c["speed"] != 1 else "",
                             f" zoom {c['zoom']:g}", f" focus {c['focus']:g}" if "focus" in c else ""])
            lines.append(f"  {c['out']:6.2f}-{c['end']:6.2f}  src {c['at']:7.1f}-{c['src_end']:7.1f}{extra}")
        lines += [f"  WARNING: {w}" for w in self.warnings]
        return "\n".join(lines)


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
    probe(video)
    music = resolve(plan["music"]) if plan.get("music") else None
    if music and not music.exists():
        sys.exit(f"File not found: {music}")
    template = json.loads((TEMPLATE_DIR / "draft_info.json").read_text())
    project_dir = unique_dir(Path(args.drafts_root).expanduser(), plan.get("name") or f"ASMR {video.stem}")

    preview_dir = plan_path.parent / "preview"
    reels, timelines = [], []
    for n, spec in enumerate(plan["reels"], 1):
        reel = Reel(spec, n, video, music, template, project_dir)
        timelines.append((spec["name"], reel.build()))
        reels.append(reel)
        print(reel.summary())
        if args.dry_run:
            preview_dir.mkdir(exist_ok=True)
            reel.preview(preview_dir / f"reel-{n}.jpg")
    if args.dry_run:
        return
    write_project(timelines, project_dir, project_dir.name, video, reels[0].cover_time())
    if music:
        for reel in reels:
            reel.write_music()
    print(f"→ {project_dir} ({len(timelines)} timelines)")


if __name__ == "__main__":
    main()
