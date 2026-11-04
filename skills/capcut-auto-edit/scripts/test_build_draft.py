"""Self-check for the pace logic: python3 scripts/test_build_draft.py"""
from build_draft import SpeechTimeline, caption_chunks


def words(*spans):
    return [{"i": n, "w": f"w{n}", "s": s, "e": e} for n, (s, e) in enumerate(spans)]


def test_long_pause_inside_a_take_is_cut():
    w = words((1.0, 1.4), (1.5, 2.0), (4.0, 4.5))
    timeline = SpeechTimeline(w, [[0, 2]], media_duration=10, silences=[[0, 1.0], [2.0, 4.0], [4.5, 10]])
    assert len(timeline.pieces) == 2
    assert timeline.duration < 2.0


def test_dropped_take_leaves_no_gap():
    w = words((1.0, 2.0), (3.0, 4.0), (6.0, 7.0))
    timeline = SpeechTimeline(w, [[2, 2], [0, 0]], media_duration=10,
                              silences=[[0, 1.0], [2.0, 3.0], [4.0, 6.0], [7.0, 10]])
    first, second = timeline.pieces
    assert second["out"] == first["out"] + first["dur"]
    assert timeline.start(2) < timeline.start(0)


def test_captions_attach_suffixes_and_percent():
    chunks = caption_chunks([(0, "tim", 0, .2), (1, "IT", .2, .4), (2, "-nya", .4, .5),
                             (3, "100", .6, .8), (4, "%", .8, .9), (5, "gratis.", .9, 1.2)])
    assert [c[0] for c in chunks] == ["tim IT-nya 100%", "gratis"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
