#!/usr/bin/env python3
"""Run: python3 test_build_webinar.py"""
import json
import shutil
import tempfile
from pathlib import Path

from build_webinar import KEPT_PAUSE, TEMPLATE_DIR, add_timelines, lesson_speech, unused_spans


def words(*spans):
    return [{"i": n, "w": f"w{n}", "s": s, "e": e} for n, (s, e) in enumerate(spans)]


def test_long_pause_shrinks_to_kept_pause():
    w = words((1.0, 1.4), (1.5, 2.0), (8.0, 8.5))
    speech = lesson_speech(w, [[0, 2]], 10, [[0, 1.0], [2.0, 8.0], [8.5, 10]])
    removed = (8.0 - 2.0) - KEPT_PAUSE
    full = speech.pieces[-1]["src_start"] + speech.pieces[-1]["dur"] - speech.pieces[0]["src_start"]
    assert abs(speech.duration - (full - removed)) < 2 / 60


def test_short_pause_is_kept_whole():
    w = words((1.0, 1.4), (1.5, 2.0), (4.0, 4.5))
    speech = lesson_speech(w, [[0, 2]], 10, [[0, 1.0], [2.0, 4.0], [4.5, 10]])
    assert len(speech.pieces) == 1


def test_unused_spans_measure_the_time_cut_between_kept_words():
    # One dropped word inside 19 s of cut time counts as 19 s, not as the word's own 1 s.
    w = words((0, 1), (10, 11), (20, 21), (22, 23), (24, 25))
    assert unused_spans(w, [[[0, 0]], [[2, 2], [4, 4]]], min_seconds=10) == [(1, 1)]


def test_lessons_become_named_timelines_of_one_project():
    template_id = json.loads((TEMPLATE_DIR / "draft_info.json").read_text())["id"]
    with tempfile.TemporaryDirectory() as tmp:
        draft = Path(tmp) / "Webinar"
        shutil.copytree(TEMPLATE_DIR / "Timelines", draft / "Timelines")
        shutil.copy(TEMPLATE_DIR / "timeline_layout.json", draft)
        main, second = {"id": template_id}, {"id": template_id}
        add_timelines(draft, [("#1 Intro", main), ("#2 Prinsip", second)])
        project = json.loads((draft / "Timelines/project.json").read_text())
        layout = json.loads((draft / "timeline_layout.json").read_text())["dockItems"][0]
        assert [t["name"] for t in project["timelines"]] == ["#1 Intro", "#2 Prinsip"]
        assert [t["id"] for t in project["timelines"]] == layout["timelineIds"] == [main["id"], second["id"]]
        assert project["main_timeline_id"] == main["id"] != second["id"]
        assert json.loads((draft / "Timelines" / second["id"] / "draft_info.json").read_text())["id"] == second["id"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
