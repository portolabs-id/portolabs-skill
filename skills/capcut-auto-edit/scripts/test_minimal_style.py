"""Self-check for the minimal style's captions: python3 scripts/test_minimal_style.py"""
from minimal_style import (AUTO_SPACING, BEHIND_HOLD, auto_highlights, backdrop_strength, highlight_phrases,
                           phrase_spans)


def spoken(*texts, pace=0.3):
    return [(n, text, n * pace, n * pace + 0.25) for n, text in enumerate(texts)]


def texts(words):
    return [w[1] for w in words]


def test_only_highlighted_words_get_a_caption():
    phrases = highlight_phrases(spoken("lo", "gak", "perlu", "khawatir", "karena", "sekarang", "gue", "bakal",
                                       "kasih", "lihat"), keys={3})
    assert [texts([*p["lead"], p["key"], *p["tail"]]) for p in phrases] == \
           [["gak", "perlu", "khawatir", "karena", "sekarang", "gue"]]


def test_lead_stops_at_the_start_of_its_sentence():
    phrase = highlight_phrases(spoken("lagi", "tuh", "Untuk", "download", "ulang"), keys={3})[0]
    assert texts(phrase["lead"]) == ["Untuk"]


def test_tail_stops_at_the_end_of_its_clause():
    phrase = highlight_phrases(spoken("jadi", "website", "kayak", "gini.", "Dan", "kalau"), keys={1})[0]
    assert texts(phrase["tail"]) == ["kayak", "gini."]


def test_suffix_stays_on_its_keyword():
    phrase = highlight_phrases(spoken("download", "PDF", "-nya"), keys={1})[0]
    assert phrase["key"][1] == "PDF-nya"


def test_two_close_highlights_do_not_share_words():
    phrases = highlight_phrases(spoken("bisa", "rapi", "bagus", "banget"), keys={1, 2})
    assert [texts(p["tail"]) for p in phrases] == [[], ["banget"]]


def test_caption_behind_the_head_holds_longer():
    phrases = highlight_phrases(spoken("bikin", "portfolio"), keys={1})
    (start, end), = phrase_spans(phrases, duration=10, behind={1})
    assert end - phrases[0]["key"][2] >= BEHIND_HOLD - 0.02


def test_phrase_ends_before_the_next_one_starts():
    phrases = highlight_phrases(spoken("satu", "dua", "tiga", "empat", "lima", "enam", pace=0.5), keys={0, 5})
    spans = phrase_spans(phrases, duration=10)
    assert spans[0][1] < spans[1][0]


def test_automatic_highlights_keep_their_distance():
    words = spoken(*["portfolio", "website", "download", "otomatis", "builder", "contohin"] * 4, pace=0.6)
    starts = sorted(w[2] for w in words if w[0] in auto_highlights(words))
    assert all(b - a >= AUTO_SPACING for a, b in zip(starts, starts[1:]))


def test_bright_picture_gets_a_dark_backdrop():
    assert backdrop_strength(0.9) > 0


def test_dark_picture_needs_no_backdrop():
    assert backdrop_strength(0.05) == 0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
