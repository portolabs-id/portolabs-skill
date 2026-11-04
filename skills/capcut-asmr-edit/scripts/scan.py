#!/usr/bin/env python3
"""Contact sheets of a long video, so its moments can be read by eye.

Usage: scan.py <video> <out_dir> [--every SECONDS] [--start S] [--end S]

Each sheet is a 5x4 grid read left to right, top to bottom. Every cell is stamped with its time in
the source video (HH:MM:SS.mmm). Without --every the step is chosen so the span fits in about
MAX_FRAMES frames: a coarse pass over the whole video, then fine passes (--every 1) over the
windows worth a closer look.
"""
import argparse
import json
import math
import subprocess
from pathlib import Path

COLS, ROWS = 5, 4
CELL_WIDTH = 384
MAX_FRAMES = 200
MIN_STEP = 1.0


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out_dir")
    ap.add_argument("--every", type=float)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    args = ap.parse_args()

    end = min(args.end or math.inf, duration(args.video))
    span = end - args.start
    every = args.every or max(MIN_STEP, round(span / MAX_FRAMES))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("sheet-*.jpg"):
        old.unlink()

    # select, not fps: fps hands over a frame up to a step late while stamping the step's time.
    pick = f"select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,{every - 0.5 / 60})'"
    stamp = f"drawtext=text='%{{pts\\:hms\\:{args.start}}}':x=6:y=6:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.6"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(args.start), "-t", str(span), "-i", args.video,
                    "-vf", f"{pick},scale={CELL_WIDTH}:-2,{stamp},tile={COLS}x{ROWS}", "-fps_mode", "vfr",
                    str(out / "sheet-%02d.jpg")], check=True)

    per_sheet = COLS * ROWS * every
    for n, sheet in enumerate(sorted(out.glob("sheet-*.jpg"))):
        first = args.start + n * per_sheet
        print(f"{sheet}  {first:.0f}s – {min(first + per_sheet - every, end):.0f}s, every {every:g}s")


if __name__ == "__main__":
    main()
