#!/usr/bin/env python3
"""Start the HyperFrames composition for a reel, with its timing and assets filled in.

Usage: new_composition.py <work_dir>

Reads from <work_dir>: timeline.json (build_draft.py --timeline), beats.json (tts.py) and
assets/manifest.json (fetch_assets.py, optional). Writes <work_dir>/motion/, a HyperFrames
project whose index.html is the template with that data in place and assets/ copied in.
Only the SCENES block is left to write. Run again after the voice or the assets change: it
keeps the SCENES block already written.

It also prints the moment each scene is fully built, for `hyperframes check --at` and
`snapshot --at`: a bare `check` samples 9 points across the reel and can miss a whole scene.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "template" / "index.html"
HYPERFRAMES = "hyperframes@0.9.14"
SCENES_BLOCK = re.compile(r"const SCENES = \{.*?\n      \};", re.S)
# The engine starts fading a scene out 0.22 s before the next beat; sample just before that.
SETTLE = 0.3


def settled_times(timeline, beats):
    """When each beat's scene is fully built: just before the next beat starts, and near the end."""
    starts = [0.0] + [next(w["start"] for w in timeline["words"] if w["i"] >= beat["from_word"]) for beat in beats[1:]]
    ends = starts[1:] + [timeline["duration"]]
    return [round(max(start, end - SETTLE), 2) for start, end in zip(starts, ends)]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    work = Path(sys.argv[1]).resolve()
    timeline = json.loads((work / "timeline.json").read_text())
    beats = json.loads((work / "beats.json").read_text())
    manifest_path = work / "assets" / "manifest.json"
    assets = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    project = work / "motion"
    if not project.exists():
        env = dict(os.environ, DO_NOT_TRACK="1", HYPERFRAMES_SKIP_SKILLS="1")
        subprocess.run(["npx", "-y", HYPERFRAMES, "init", "motion", "--example", "blank", "--resolution", "portrait",
                        "--non-interactive", "--skip-skills"], cwd=work, env=env, check=True, capture_output=True)
    if (work / "assets").exists():
        shutil.copytree(work / "assets", project / "assets", dirs_exist_ok=True)
    for extra in TEMPLATE.parent.iterdir():  # the mascot and anything else the template draws
        if extra.name != TEMPLATE.name:
            shutil.copy(extra, project / extra.name)

    html = TEMPLATE.read_text()
    index = project / "index.html"
    if index.exists() and SCENES_BLOCK.search(index.read_text()):
        html = SCENES_BLOCK.sub(lambda _: SCENES_BLOCK.search(index.read_text()).group(0), html)
    html = (html.replace("{{DURATION}}", f"{timeline['duration']:.3f}")
            .replace("{{TIMELINE}}", json.dumps(timeline, ensure_ascii=False))
            .replace("{{BEATS}}", json.dumps(beats, ensure_ascii=False))
            .replace("{{ASSETS}}", json.dumps(assets, ensure_ascii=False)))
    index.write_text(html)
    print(f"{index}\nBeats to write in SCENES: {', '.join(b['id'] for b in beats)}")
    print(f"Each scene fully built (check --at ... --no-collapse-static, snapshot --at): "
          f"{','.join(map(str, settled_times(timeline, beats)))}")


if __name__ == "__main__":
    main()
