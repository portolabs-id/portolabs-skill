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


def test_trim_tail_shortens_the_piece_ending_on_that_word():
    w = words((1.0, 1.4), (1.5, 2.0), (4.0, 4.5))
    silences = [[0, 1.0], [2.0, 4.0], [4.5, 10]]
    full = SpeechTimeline(w, [[0, 2]], media_duration=10, silences=silences)
    trimmed = SpeechTimeline(w, [[0, 2]], media_duration=10, silences=silences, trim_tail={"1": 0.2})
    assert abs(trimmed.pieces[0]["dur"] - (full.pieces[0]["dur"] - 0.2)) < 1 / 60
    assert trimmed.pieces[1]["dur"] == full.pieces[1]["dur"]


def test_trim_into_the_word_itself_is_flagged():
    w = words((1.0, 1.4), (1.5, 2.0), (4.0, 4.5))
    silences = [[0, 1.0], [2.0, 4.0], [4.5, 10]]
    timeline = SpeechTimeline(w, [[0, 2]], media_duration=10, silences=silences, trim_tail={"1": 0.25})
    assert len(timeline.warnings) == 1


def test_phrase_said_twice_in_a_row_is_flagged():
    w = [{"i": n, "w": t, "s": n * 0.4, "e": n * 0.4 + 0.3}
         for n, t in enumerate(["bisa", "banget", "Bisa", "banget", "daftar"])]
    timeline = SpeechTimeline(w, [[0, 4]], media_duration=10, silences=[[2.0, 10]])
    flags = timeline.transcript_flags()
    assert len(flags) == 1 and "[0-1]" in flags[0] and "[2-3]" in flags[0], flags


def test_natural_single_word_repeat_is_not_flagged():
    """'karir gua, gua nggak langsung' is how people talk, not a retake."""
    w = [{"i": n, "w": t, "s": n * 0.3, "e": n * 0.3 + 0.28}
         for n, t in enumerate(["karir", "gua,", "gua", "nggak"])]
    timeline = SpeechTimeline(w, [[0, 3]], media_duration=10, silences=[[1.5, 10]])
    assert timeline.transcript_flags() == []


def test_word_starting_in_the_pause_before_it_is_not_flagged():
    """Whisper often starts a clip's first word inside the silence before it; that is not a hidden word."""
    w = words((0.5, 1.6), (1.7, 2.0))
    timeline = SpeechTimeline(w, [[0, 1]], media_duration=10, silences=[[0, 1.2], [2.0, 10]])
    assert timeline.transcript_flags() == []


def test_word_that_swallows_a_pause_is_flagged():
    w = words((1.0, 1.4), (1.5, 3.2), (3.3, 3.6))
    timeline = SpeechTimeline(w, [[0, 2]], media_duration=10, silences=[[0, 1.0], [1.9, 2.5], [3.6, 10]])
    flags = timeline.transcript_flags()
    assert len(flags) == 1 and "[1]" in flags[0], flags


def test_captions_attach_suffixes_and_percent():
    chunks = caption_chunks([(0, "tim", 0, .2), (1, "IT", .2, .4), (2, "-nya", .4, .5),
                             (3, "100", .6, .8), (4, "%", .8, .9), (5, "gratis.", .9, 1.2)])
    assert [c[0] for c in chunks] == ["tim IT-nya 100%", "gratis"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
