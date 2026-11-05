#!/usr/bin/env python3
"""Transcribe an A-roll video with word timestamps (mlx_whisper) and map its silences.

Usage: transcribe.py <video> <work_dir> [--language id] [--model REPO]

Writes into <work_dir>:
  words.json  [{"i", "w", "s", "e"}]  words with source-time seconds
  audio.json  {"loudness", "silences", "window", "levels", "peaks"} used by build_draft.py to cut pauses
              and set the speech volume
and prints an indexed transcript. Pauses longer than 0.3 s show as ‖<sec>.

Each stretch of speech between silences is transcribed on its own, so repeated takes
stay separate and word timestamps do not drift across pauses.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"
PAUSE_MARK = 0.3
# Silence = quieter than the recording's speech loudness minus this many dB.
SILENCE_BELOW_SPEECH_DB = -18
SILENCE_MIN = 0.15
NOISE_BLIP = 0.12
WINDOW = 0.02
SAMPLE_RATE = 16000
PEAK_RATE = 48000
DEFAULT_LUFS = -20.0
# Every pause the edit cuts (build_draft MAX_GAP) also splits whisper's clips: inside one clip
# whisper tidies a retake away ("bisa banget, bisa banget daftar" → "bisa banget daftar").
CLIP_SPLIT_GAP = 0.3
CLIP_PAD = 0.2


def extract_audio(video, wav):
    """Mono 16 kHz WAV on the video's clock: CapCut places audio by the stream timestamps, so a
    late audio start or timestamp drift (common in phone recordings) is padded, not dropped.
    Without this, every cut lands up to seconds away from the speech it was meant for."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE),
                    "-af", "aresample=async=1:first_pts=0", str(wav)], check=True)


def ffmpeg_filter_log(media, audio_filter):
    return subprocess.run(["ffmpeg", "-nostats", "-i", str(media), "-vn", "-af", audio_filter, "-f", "null", "-"],
                          capture_output=True, text=True).stderr


def measure_loudness(wav):
    found = re.findall(r"I:\s+(-?[\d.]+) LUFS", ffmpeg_filter_log(wav, "ebur128=framelog=quiet"))
    return float(found[-1]) if found else DEFAULT_LUFS


def media_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def window_levels(wav):
    """RMS level (dB) of each WINDOW-long slice of the 16 kHz WAV."""
    return _window_stat(wav, "RMS_level", SAMPLE_RATE)


def window_peaks(media):
    """Sample peak (dBFS) of each WINDOW-long slice of the media's loudest channel, on extract_audio's
    clock. Read from the media itself: the 16 kHz mono WAV loses the highs and averages the
    channels, so its peaks read low, while CapCut plays (and clips) the media's own sound."""
    return _window_stat(media, "Peak_level", PEAK_RATE)


def _window_stat(media, stat, rate):
    log = ffmpeg_filter_log(media, f"aresample={rate}:async=1:first_pts=0,"
                                   f"asetnsamples=n={round(rate * WINDOW)}:p=0,"
                                   f"astats=metadata=1:reset=1:measure_perchannel=none:measure_overall={stat},"
                                   f"ametadata=print:key=lavfi.astats.Overall.{stat}")
    return [float(v) if v != "-inf" else -120.0 for v in re.findall(rf"{stat}=(\S+)", log)]


def detect_silences(wav, loudness, duration):
    """Pauses for splitting whisper's clips, judged against the whole file's loudness.
    build_draft.py judges again against the speech it actually keeps."""
    return silences_from_levels(window_levels(wav), loudness + SILENCE_BELOW_SPEECH_DB, duration)


def silences_from_levels(levels, threshold, duration, window=WINDOW):
    """Silent stretches [[start, end]], judged on RMS energy per window rather than per-sample
    peaks: a mouth click peaks loudly but carries no energy, and must not split a pause."""
    silences, start = [], None
    for n, level in enumerate(levels + [0.0]):
        if level < threshold and start is None:
            start = n
        elif level >= threshold and start is not None:
            if (n - start) * window >= SILENCE_MIN:
                silences.append([round(start * window, 3), round(min(n * window, duration), 3)])
            start = None
    merged = []
    for silence in silences:
        if merged and silence[0] - merged[-1][1] < NOISE_BLIP:
            merged[-1][1] = silence[1]
        else:
            merged.append(silence)
    return merged


def speech_clips(silences, duration):
    """Stretches of speech between pauses, padded into the pause but never past its middle,
    so neighbouring clips never hear the same audio twice."""
    clips, cursor, lead = [], 0.0, 0.0
    for start, end in silences:
        if end - start < CLIP_SPLIT_GAP:
            continue
        pad = min(CLIP_PAD, (end - start) / 2)
        if start > cursor:
            clips.append((max(cursor - lead, 0.0), min(start + pad, duration)))
        cursor, lead = end, pad
    if duration > cursor:
        clips.append((max(cursor - lead, 0.0), duration))
    return clips


def run_whisper(wav, out_dir, language, model, clips):
    clip_arg = ",".join(f"{t:.2f}" for clip in clips for t in clip)
    subprocess.run(["mlx_whisper", str(wav), "--model", model, "--language", language,
                    "--word-timestamps", "True", "--output-format", "json",
                    "--output-dir", str(out_dir), "--condition-on-previous-text", "False",
                    "--clip-timestamps", clip_arg, "--verbose", "False"], check=True)
    return json.loads((out_dir / f"{wav.stem}.json").read_text())


def flatten_words(result):
    words = []
    for seg in result["segments"]:
        for w in seg.get("words", []):
            text = w["word"].strip()
            if text:
                words.append({"i": len(words), "w": text, "s": round(w["start"], 3), "e": round(w["end"], 3)})
    return words


def print_transcript(words):
    line, line_start = [], 0.0
    for idx, w in enumerate(words):
        gap = w["s"] - words[idx - 1]["e"] if idx else 0
        if line and gap > PAUSE_MARK:
            print(f"{line_start:7.2f}s  " + " ".join(line) + f"  ‖{gap:.1f}s")
            line = []
        if not line:
            line_start = w["s"]
        line.append(f"[{w['i']}]{w['w']}")
    if line:
        print(f"{line_start:7.2f}s  " + " ".join(line))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("work_dir")
    ap.add_argument("--language", default="id")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    work = Path(args.work_dir)
    work.mkdir(parents=True, exist_ok=True)
    wav = work / "aroll.wav"
    extract_audio(args.video, wav)
    duration = media_duration(wav)
    loudness = measure_loudness(wav)
    levels = window_levels(wav)
    silences = silences_from_levels(levels, loudness + SILENCE_BELOW_SPEECH_DB, duration)
    clips = speech_clips(silences, duration)
    words = flatten_words(run_whisper(wav, work, args.language, args.model, clips))
    if not words:
        sys.exit("No speech found in the video.")
    (work / "words.json").write_text(json.dumps(words, ensure_ascii=False))
    (work / "audio.json").write_text(json.dumps({"loudness": loudness, "silences": silences, "window": WINDOW,
                                                 "levels": [round(v, 1) for v in levels],
                                                 "peaks": [round(v, 1) for v in window_peaks(args.video)]}))
    print_transcript(words)
    print(f"\n{len(words)} words, {len(clips)} speech stretches → {work / 'words.json'}")


if __name__ == "__main__":
    main()
