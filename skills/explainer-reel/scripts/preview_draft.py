#!/usr/bin/env python3
"""Watch a built draft without CapCut: the motion with the draft's own cut of the voice.

Usage: preview_draft.py <draft_dir> <motion.mp4> <out.mp4>

Each audio segment of the draft (voice and SFX) is cut from its source and placed at its time
in the edit, as CapCut will play it, so a sync problem shows here first. Segment volumes are
ignored; the mix is brought to the edit's -14 LUFS instead.
"""
import json
import subprocess
import sys
from pathlib import Path

SEC = 1_000_000


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    draft_dir, motion, out = (Path(a) for a in sys.argv[1:])
    draft = json.loads((draft_dir / "draft_info.json").read_text())
    sources = {m["id"]: m["path"] for m in draft["materials"]["audios"]}
    audio = [s for track in draft["tracks"] if track["type"] == "audio" for s in track["segments"]
             if s["material_id"] in sources]
    inputs, parts = ["-i", str(motion)], []
    for n, seg in enumerate(audio):
        source = sources[seg["material_id"]]
        start = seg["source_timerange"]["start"] / SEC
        length = seg["target_timerange"]["duration"] / SEC
        at_ms = round(seg["target_timerange"]["start"] / SEC * 1000)
        inputs += ["-i", source]
        parts.append(f"[{n + 1}:a]atrim={start}:{start + length},asetpts=PTS-STARTPTS,adelay={at_ms}:all=1[a{n}]")
    mix = ("".join(f"[a{n}]" for n in range(len(audio)))
           + f"amix=inputs={len(audio)}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=7[voice]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(parts + [mix]),
                    "-map", "0:v", "-map", "[voice]", "-t", str(draft["duration"] / SEC),
                    "-c:v", "copy", "-c:a", "aac", str(out)], check=True)
    print(out)


if __name__ == "__main__":
    main()
