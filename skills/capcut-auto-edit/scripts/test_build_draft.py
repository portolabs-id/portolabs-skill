"""Self-check for the pace logic: python3 scripts/test_build_draft.py"""
import copy
import json

from build_draft import (TEMPLATE_DIR, PROTO, SpeechTimeline, caption_chunks, kept_loudness, resolve_text_layout,
                         silences_for_kept, text_box)

TEMPLATE = json.loads((TEMPLATE_DIR / "draft_info.json").read_text())
TEXT_MATERIALS = {m["id"]: m for m in TEMPLATE["materials"]["texts"]}


def proto_text(name, start=0.0, end=2.0, text=None):
    track, index = PROTO[name]
    seg = copy.deepcopy(TEMPLATE["tracks"][track]["segments"][index])
    material = copy.deepcopy(TEXT_MATERIALS[seg["material_id"]])
    if text is not None:
        content = json.loads(material["content"])
        content["text"] = text
        material["content"] = json.dumps(content)
    seg["target_timerange"] = {"start": int(start * 1e6), "duration": int((end - start) * 1e6)}
    kind = {"subtitle": "subtitle", "credit": "credit"}.get(name, "text")
    return {"label": name, "kind": kind, "seg": seg, "material": material, "effect": name.startswith("card")}


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


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


def test_silence_threshold_follows_the_kept_speech_not_the_whole_file():
    """A file with a long quiet stretch (another recording far from the mic) drags its overall
    loudness down; the soft tail after a kept line (-45 dB under -20 dB speech) is still silence."""
    window = 0.02
    levels = [-20.0] * 50 + [-45.0] * 10 + [-80.0] * 40 + [-50.0] * 900  # speech, tail, pause, quiet chatter
    audio = {"window": window, "levels": levels, "loudness": -32.0, "silences": []}
    w = [{"i": 0, "w": "halo", "s": 0.0, "e": 1.0}]
    silences = silences_for_kept(audio, w, [[0, 0]], media_duration=len(levels) * window)
    assert abs(silences[0][0] - 1.0) < 0.03, silences


def test_speech_gain_follows_the_kept_speech_not_the_whole_file():
    """With the whole-file loudness (-32) the voice would be boosted ~6x and clip."""
    levels = [-20.0] * 50 + [-80.0] * 50 + [-50.0] * 900
    audio = {"window": 0.02, "levels": levels, "loudness": -32.0, "silences": []}
    w = [{"i": 0, "w": "halo", "s": 0.0, "e": 1.0}]
    assert abs(kept_loudness(audio, w, [[0, 0]]) - (-20.0)) < 0.5


def test_text_box_matches_capcut_render_of_the_0827_hook():
    """CapCut drew this hook at y 284-484 px, its widest line 764 px wide (0827 cover)."""
    hook = proto_text("hook")
    left, top, right, bottom = text_box(hook["seg"], hook["material"], hook["effect"])
    assert abs(top - 284) < 25 and abs(bottom - 484) < 25 and abs((right - left) - 764) < 60, (left, top, right, bottom)


def test_caption_moves_off_the_cta_it_would_hit():
    caption, cta = proto_text("subtitle", 0, 1, "bisa banget daftar"), proto_text("cta", 0.5, 3)
    notes = resolve_text_layout([caption, cta])
    assert not overlaps(text_box(caption["seg"], caption["material"], False),
                        text_box(cta["seg"], cta["material"], False)), notes
    assert any("moved" in n for n in notes), notes


def test_credit_watermark_moves_to_a_free_spot():
    credit, cta = proto_text("credit", 0, 3), proto_text("cta", 1, 3)
    credit["seg"]["clip"]["transform"] = {"x": -0.49, "y": -0.21}
    notes = resolve_text_layout([credit, cta])
    assert not overlaps(text_box(credit["seg"], credit["material"], False),
                        text_box(cta["seg"], cta["material"], False)), notes
    assert not any(n.startswith("FIX") for n in notes), notes


def test_two_fixed_texts_on_top_of_each_other_are_reported():
    hook, title = proto_text("hook", 0, 3), proto_text("logo_title", 1, 2)
    notes = resolve_text_layout([hook, title])
    assert any(n.startswith("FIX") for n in notes), notes


def test_captions_attach_suffixes_and_percent():
    chunks = caption_chunks([(0, "tim", 0, .2), (1, "IT", .2, .4), (2, "-nya", .4, .5),
                             (3, "100", .6, .8), (4, "%", .8, .9), (5, "gratis.", .9, 1.2)])
    assert [c[0] for c in chunks] == ["tim IT-nya 100%", "gratis"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
