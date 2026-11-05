"""Self-check for word timing, beat ranges and the voice master: python3 scripts/test_tts.py"""
import subprocess
import tempfile
from pathlib import Path

from tts import beat_ranges, master_voice, measure_loudness, window_peaks, words_from_alignment


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


def decoded_samples(path):
    return len(subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-"],
                              capture_output=True, check=True).stdout) // 2


def test_master_brings_a_quiet_peaky_voice_to_minus_14_lufs_without_clipping_or_moving_it():
    """Shaped like ElevenLabs' voice: about -22 LUFS with clicks near -1.6 dBFS."""
    with tempfile.TemporaryDirectory() as tmp:
        raw, mastered = Path(tmp) / "raw.mp3", Path(tmp) / "voice.mp3"
        syllables_and_clicks = ("0.2*sin(2*PI*180*t)*(0.6+0.4*sin(2*PI*4*t))*lt(mod(t,2),1.6)"
                                "+0.75*sin(2*PI*1500*t)*(between(t,1,1.004)+between(t,5,5.004))")
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"aevalsrc='{syllables_and_clicks}':d=8:s=44100",
                        "-c:a", "libmp3lame", "-b:a", "128k", str(raw)], check=True)
        master_voice(raw, mastered)
        loudness, peak = measure_loudness(mastered), max(window_peaks(mastered))
        assert (abs(loudness + 14) < 1, peak <= -1.0, decoded_samples(mastered)) == \
               (True, True, decoded_samples(raw)), (loudness, peak)


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("ok")
