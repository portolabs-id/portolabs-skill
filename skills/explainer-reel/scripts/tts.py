#!/usr/bin/env python3
"""Voice an approved script with ElevenLabs and time every word for the motion and the edit.

Usage: tts.py <script.json> <work_dir> [--voice VOICE_ID] [--model MODEL]
       tts.py --list-voices

Needs ELEVENLABS_API_KEY in the environment (the user sets it; never print it).
The voice comes from --voice or ELEVENLABS_VOICE_ID.

script.json:
  {"title": "Lima tool edit reel",
   "beats": [{"id": "hook", "chip": "Hook", "vo": "Kamu cuma butuh lima tool.",
              "sel": ["lima"], "em": ["tool."], "assets": []}, ...]}

The whole script is one request, so the voice flows across beats. ElevenLabs returns when each
character is spoken; the words are the script's own, so names are never misheard.

Writes into <work_dir>:
  voice.mp3    the voice
  voice.mp4    the voice on a plain frame, the "A-roll" capcut-auto-edit's build_draft.py expects
  words.json   [{"i", "w", "s", "e"}] in the format transcribe.py writes
  audio.json   loudness and silences, as transcribe.py writes them
  beats.json   [{"id", "chip", "from_word", "to_word", "sel": [i], "em": [i]}]
  plan.json    a starting plan for build_draft.py: every word kept, no yellow captions, no grading,
               each beat covered by motion.mp4 locked to the timeline
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "capcut-auto-edit" / "scripts"))
from transcribe import (SILENCE_BELOW_SPEECH_DB, WINDOW, extract_audio, measure_loudness,  # noqa: E402
                        media_duration, silences_from_levels, window_levels)

API = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL = "eleven_v4"
OUTPUT_FORMAT = "mp3_44100_128"
LANGUAGE = "id"
MODELS_WITHOUT_LANGUAGE_CODE = {"eleven_multilingual_v2"}
FRAME_COLOR = "0xFDFDFD"
FRAME_SIZE = "1080x1920"
FRAME_RATE = 60
# The closing card stays this long after the last word, so the CTA can be read.
END_HOLD = 2.0


def api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set. Ask the user to add it to their shell profile; never ask them to paste it in chat.")
    return key


def call(path, body=None):
    request = urllib.request.Request(f"{API}{path}", data=json.dumps(body).encode() if body else None,
                                     headers={"xi-api-key": api_key(), "Content-Type": "application/json"},
                                     method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        sys.exit(f"ElevenLabs {error.code}: {error.read().decode(errors='replace')[:400]}")


def words_from_alignment(alignment):
    """Group ElevenLabs' per-character times into whitespace-separated words."""
    words, current = [], None
    for char, start, end in zip(alignment["characters"], alignment["character_start_times_seconds"],
                                alignment["character_end_times_seconds"]):
        if char.isspace():
            current = None
            continue
        if current is None:
            current = {"i": len(words), "w": "", "s": round(start, 3), "e": round(end, 3)}
            words.append(current)
        current["w"] += char
        current["e"] = round(end, 3)
    return words


def beat_ranges(beats):
    """Word ranges of each beat, with its "sel" and "em" words as word indices."""
    ranges, cursor = [], 0
    for beat in beats:
        words = beat["vo"].split()
        found = {key: [cursor + words.index(w) for w in beat.get(key, []) if w in words] for key in ("sel", "em")}
        missing = [w for key in ("sel", "em") for w in beat.get(key, []) if w not in words]
        if missing:
            sys.exit(f"beat {beat['id']}: {missing} are not words of its vo (match them exactly, punctuation too)")
        ranges.append({"id": beat["id"], "chip": beat.get("chip", beat["id"]),
                       "from_word": cursor, "to_word": cursor + len(words) - 1, **found})
        cursor += len(words)
    return ranges


def starting_plan(title, words, beats):
    return {"name": title, "aroll": "voice.mp4", "words": "words.json", "keep": [[0, len(words) - 1]],
            "subtitles": False, "grading": False, "end_hold": END_HOLD,
            "broll": [{"file": "motion.mp4", "from_word": b["from_word"], "to_word": b["to_word"],
                       "src_start": "timeline"} for b in beats]}


def voice_video(mp3, mp4):
    # ponytail: build_draft.py expects a talking-head video; motion covers the whole frame, so a
    # plain frame carries the voice. Give build_draft.py an audio-only input if this ever shows.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", f"color=c={FRAME_COLOR}:s={FRAME_SIZE}:r={FRAME_RATE}", "-i", str(mp3),
                    "-shortest", "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", str(mp4)], check=True)


def audio_analysis(mp4, work):
    wav = work / "voice.wav"
    extract_audio(mp4, wav)
    loudness, levels = measure_loudness(wav), window_levels(wav)
    silences = silences_from_levels(levels, loudness + SILENCE_BELOW_SPEECH_DB, media_duration(wav))
    return {"loudness": loudness, "silences": silences, "window": WINDOW, "levels": [round(v, 1) for v in levels]}


def list_voices():
    for voice in call("/voices")["voices"]:
        labels = ", ".join(f"{k}: {v}" for k, v in (voice.get("labels") or {}).items())
        print(f"{voice['voice_id']}  {voice['name']}  ({labels})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?")
    ap.add_argument("work_dir", nargs="?")
    ap.add_argument("--voice", default=os.environ.get("ELEVENLABS_VOICE_ID"))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--list-voices", action="store_true")
    args = ap.parse_args()
    if args.list_voices:
        return list_voices()
    if not (args.script and args.work_dir and args.voice):
        ap.error("script, work_dir and a voice (--voice or ELEVENLABS_VOICE_ID) are required")

    script = json.loads(Path(args.script).read_text())
    work = Path(args.work_dir)
    work.mkdir(parents=True, exist_ok=True)
    beats = beat_ranges(script["beats"])
    text = " ".join(beat["vo"].strip() for beat in script["beats"])
    body = {"text": text, "model_id": args.model}
    if args.model not in MODELS_WITHOUT_LANGUAGE_CODE:
        body["language_code"] = LANGUAGE
    result = call(f"/text-to-speech/{args.voice}/with-timestamps?output_format={OUTPUT_FORMAT}", body)

    words = words_from_alignment(result["alignment"])
    if len(words) != beats[-1]["to_word"] + 1:
        sys.exit(f"ElevenLabs timed {len(words)} words, the script has {beats[-1]['to_word'] + 1}")
    (work / "voice.mp3").write_bytes(base64.b64decode(result["audio_base64"]))
    voice_video(work / "voice.mp3", work / "voice.mp4")
    (work / "words.json").write_text(json.dumps(words, ensure_ascii=False))
    (work / "audio.json").write_text(json.dumps(audio_analysis(work / "voice.mp4", work)))
    (work / "beats.json").write_text(json.dumps(beats, ensure_ascii=False, indent=1))
    (work / "plan.json").write_text(json.dumps(starting_plan(script["title"], words, beats), ensure_ascii=False, indent=1))
    print(f"{len(words)} words, {words[-1]['e']:.1f} s of voice, {len(beats)} beats → {work}")


if __name__ == "__main__":
    main()
