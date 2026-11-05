#!/usr/bin/env python3
"""Run: python3 test_build_webinar.py"""
from build_webinar import KEPT_PAUSE, lesson_speech, unused_spans


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


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
