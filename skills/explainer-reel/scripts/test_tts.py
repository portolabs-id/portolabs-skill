"""Self-check for word timing and beat ranges: python3 scripts/test_tts.py"""
from tts import beat_ranges, words_from_alignment


def alignment(text, step=0.1):
    return {"characters": list(text),
            "character_start_times_seconds": [n * step for n in range(len(text))],
            "character_end_times_seconds": [(n + 1) * step for n in range(len(text))]}


def test_words_span_their_first_to_last_character():
    words = words_from_alignment(alignment("Hai  kamu."))
    assert [(w["w"], w["s"], w["e"]) for w in words] == [("Hai", 0.0, 0.3), ("kamu.", 0.5, 1.0)]


def test_beats_take_consecutive_word_ranges_with_styled_words_as_indices():
    beats = beat_ranges([{"id": "a", "vo": "Kamu butuh lima tool.", "sel": ["lima"], "em": ["tool."]},
                         {"id": "b", "vo": "Claude bikin motion.", "sel": ["Claude"]}])
    assert beats[1] == {"id": "b", "chip": "b", "from_word": 4, "to_word": 6, "sel": [4], "em": []}


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("ok")
