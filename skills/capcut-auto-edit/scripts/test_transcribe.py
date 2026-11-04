"""Self-check for audio extraction: python3 scripts/test_transcribe.py"""
import subprocess
import tempfile
from pathlib import Path

from transcribe import detect_silences, extract_audio, media_duration, speech_clips


def test_extracted_audio_follows_the_video_clock():
    """CapCut plays audio by the video's timestamps; the WAV must use the same clock."""
    with tempfile.TemporaryDirectory() as tmp:
        video, wav = Path(tmp) / "late-audio.mov", Path(tmp) / "out.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=black:s=64x64:d=3",
                        "-itsoffset", "0.5", "-f", "lavfi", "-i", "sine=d=2.5",
                        "-c:v", "libx264", "-c:a", "aac", str(video)], check=True)
        extract_audio(video, wav)
        assert abs(media_duration(wav) - 3.0) < 0.05, media_duration(wav)


def test_mouth_click_does_not_split_a_pause():
    """A click has a loud peak but almost no energy; the pause around it is still one pause."""
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "click.wav"
        # two 1 ms clicks at -30 dB, 130 ms apart, inside a 1 s pause (shaped like the real ones)
        tone_click_tone = ("if(lt(t,0.5)+gt(t,1.5), 0.3*sin(2*PI*440*t),"
                           " 0.03*(between(t,1.0,1.001)+between(t,1.13,1.131)))")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
                        f"aevalsrc='{tone_click_tone}':d=2:s=16000", str(wav)], check=True)
        silences = detect_silences(wav, loudness=-22.0, duration=2.0)
        assert len(silences) == 1, silences
        start, end = silences[0]
        assert abs(start - 0.5) < 0.05 and abs(end - 1.5) < 0.05, silences


def test_short_pause_between_takes_splits_the_clips():
    """Whisper merges a retake into one clean phrase when both are in one clip ("bisa banget, bisa
    banget daftar" came out as "bisa banget daftar"), so every pause the edit cuts splits a clip."""
    clips = speech_clips([[1.0, 1.35]], duration=3.0)
    assert len(clips) == 2, clips
    assert clips[0][1] <= clips[1][0], clips


if __name__ == "__main__":
    test_extracted_audio_follows_the_video_clock()
    test_mouth_click_does_not_split_a_pause()
    test_short_pause_between_takes_splits_the_clips()
    print("ok")
