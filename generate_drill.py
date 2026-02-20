#!/usr/bin/env python3
"""
Generate a sight-singing / music-reading drill MP3.

Produces one MP3 containing 14 questions (one sharp and one flat for each
note letter A-G) in randomized order.  Each question follows this pattern:

  1. TTS: "This note is <LETTER>."
  2. Sustained tone for the base letter pitch (1.0 s, sine wave, octave 4)
  3. TTS: "What would <LETTER> sharp/flat sound like?"
  4. 4-second silent thinking pause
  5. TTS: "Did you get it?"
  6. 0.75-second gap before next question

Usage:
    python generate_drill.py [--seed SEED] [--output FILE] [--order FILE]
"""

import argparse
import io
import math
import random
import struct
import subprocess
import sys
import tempfile
import os
from pathlib import Path

import numpy as np
from gtts import gTTS
from pydub import AudioSegment


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit

# Equal-temperament frequencies for octave 4 (A4 = 440 Hz)
# Using the formula: freq = 440 * 2^((semitone - A4_semitone) / 12)
# where A4 = MIDI 69
MIDI_NOTES = {
    "C": 60,
    "D": 62,
    "E": 64,
    "F": 65,
    "G": 67,
    "A": 69,
    "B": 71,
}

FREQ_TABLE = {
    letter: 440.0 * (2.0 ** ((midi - 69) / 12.0))
    for letter, midi in MIDI_NOTES.items()
}

LETTERS = list("ABCDEFG")
ACCIDENTALS = ["sharp", "flat"]

TONE_DURATION_S = 1.0       # seconds for sustained pitch
THINK_PAUSE_S = 4.0         # seconds of silence for thinking
GAP_S = 0.75                # seconds gap between questions


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def generate_sine_tone(frequency: float, duration_s: float,
                       sample_rate: int = SAMPLE_RATE,
                       amplitude: float = 0.7) -> AudioSegment:
    """Generate a sine-wave tone as a pydub AudioSegment.

    Applies a short fade-in/out to avoid clicks.
    """
    n_samples = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, n_samples, endpoint=False)
    samples = amplitude * np.sin(2 * math.pi * frequency * t)

    # Apply 10 ms fade-in and fade-out to avoid pops/clicks
    fade_samples = int(sample_rate * 0.01)
    if fade_samples > 0 and 2 * fade_samples < n_samples:
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        samples[:fade_samples] *= fade_in
        samples[-fade_samples:] *= fade_out

    # Convert to 16-bit PCM
    pcm = (samples * 32767).astype(np.int16).tobytes()

    return AudioSegment(
        data=pcm,
        sample_width=SAMPLE_WIDTH,
        frame_rate=sample_rate,
        channels=CHANNELS,
    )


def generate_silence(duration_s: float,
                     sample_rate: int = SAMPLE_RATE) -> AudioSegment:
    """Generate silence as a pydub AudioSegment."""
    return AudioSegment.silent(duration=int(duration_s * 1000),
                               frame_rate=sample_rate)


def mp3_bytes_to_segment(mp3_data: bytes) -> AudioSegment:
    """Decode MP3 bytes to an AudioSegment using ffmpeg (avoids ffprobe)."""
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", "pipe:0",
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ar", str(SAMPLE_RATE),
            "-ac", str(CHANNELS),
            "pipe:1",
        ],
        input=mp3_data,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed: {proc.stderr.decode()}")
    return AudioSegment(
        data=proc.stdout,
        sample_width=SAMPLE_WIDTH,
        frame_rate=SAMPLE_RATE,
        channels=CHANNELS,
    )


def tts_to_segment(text: str) -> AudioSegment:
    """Convert text to speech using gTTS and return as AudioSegment."""
    tts = gTTS(text=text, lang="en", slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    return mp3_bytes_to_segment(buf.getvalue())


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def build_questions() -> list[dict]:
    """Build the full list of 14 questions (one sharp + one flat per letter)."""
    questions = []
    for letter in LETTERS:
        for accidental in ACCIDENTALS:
            questions.append({
                "letter": letter,
                "accidental": accidental,
                "label": f"{letter}{('#' if accidental == 'sharp' else 'b')}",
            })
    return questions


def render_question(q: dict, index: int, total: int) -> AudioSegment:
    """Render a single question to an AudioSegment.

    Structure:
      1. TTS: "This note is <LETTER>."
      2. Sustained tone for base letter (1.0 s)
      3. TTS: "What would <LETTER> sharp/flat sound like?"
      4. 4 s thinking silence
      5. TTS: "Did you get it?"
      6. 0.75 s gap
    """
    letter = q["letter"]
    accidental = q["accidental"]

    print(f"  [{index + 1}/{total}] Generating: {q['label']} "
          f"({letter} {accidental})...")

    # 1) Announcement
    seg_announce = tts_to_segment(f"This note is {letter}.")

    # 2) Sustained tone
    freq = FREQ_TABLE[letter]
    seg_tone = generate_sine_tone(freq, TONE_DURATION_S)

    # 3) Question
    seg_question = tts_to_segment(
        f"What would {letter} {accidental} sound like?"
    )

    # 4) Thinking pause
    seg_think = generate_silence(THINK_PAUSE_S)

    # 5) "Did you get it?"
    seg_confirm = tts_to_segment("Did you get it?")

    # 6) Gap before next question
    seg_gap = generate_silence(GAP_S)

    # Concatenate all pieces
    return seg_announce + seg_tone + seg_question + seg_think + seg_confirm + seg_gap


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a sight-singing sharps & flats drill MP3."
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for deterministic ordering (default: random)."
    )
    parser.add_argument(
        "--output", type=str, default="sight_singing_sharps_flats.mp3",
        help="Output MP3 filename."
    )
    parser.add_argument(
        "--order", type=str, default="question_order.txt",
        help="Output text file listing question order."
    )
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 2**31 - 1)
    print(f"Using seed: {seed}")
    random.seed(seed)

    # Build and shuffle questions
    questions = build_questions()
    assert len(questions) == 14, f"Expected 14 questions, got {len(questions)}"
    random.shuffle(questions)

    # Verify each letter appears exactly twice
    from collections import Counter
    letter_counts = Counter(q["letter"] for q in questions)
    for letter in LETTERS:
        assert letter_counts[letter] == 2, (
            f"Letter {letter} appears {letter_counts[letter]} times, expected 2"
        )

    # Write question order
    order_path = Path(args.order)
    with open(order_path, "w") as f:
        f.write(f"Seed: {seed}\n")
        f.write(f"Generated order ({len(questions)} questions):\n\n")
        for i, q in enumerate(questions, 1):
            f.write(f"{i:2d}. {q['label']:3s}  "
                    f"(base note: {q['letter']}, "
                    f"ask: {q['accidental']})\n")
    print(f"Question order written to: {order_path}")

    # Render each question and concatenate
    print(f"\nRendering {len(questions)} questions...")
    full_audio = AudioSegment.empty()

    for i, q in enumerate(questions):
        segment = render_question(q, i, len(questions))
        full_audio += segment

    # Normalize loudness
    target_dBFS = -18.0
    change_in_dBFS = target_dBFS - full_audio.dBFS
    full_audio = full_audio.apply_gain(change_in_dBFS)

    # Export to MP3 using ffmpeg directly (avoids ffprobe dependency)
    output_path = Path(args.output)
    print(f"\nExporting to {output_path}...")
    raw_pcm = full_audio.raw_data
    proc = subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "s16le",
            "-ar", str(SAMPLE_RATE),
            "-ac", str(CHANNELS),
            "-i", "pipe:0",
            "-b:a", "192k",
            str(output_path),
        ],
        input=raw_pcm,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg export failed: {proc.stderr.decode()}")

    # Summary
    duration_s = len(full_audio) / 1000.0
    minutes = int(duration_s // 60)
    seconds = duration_s % 60
    print(f"\nDone!")
    print(f"  Output:   {output_path} ({output_path.stat().st_size / 1024:.0f} KB)")
    print(f"  Duration: {minutes}m {seconds:.1f}s")
    print(f"  Questions: {len(questions)}")
    print(f"  Seed:     {seed}")

    # Final verification
    expected_min_s = 14 * (0.5 + TONE_DURATION_S + 1.0 + THINK_PAUSE_S + 0.5 + GAP_S)
    assert duration_s >= expected_min_s, (
        f"Duration {duration_s:.1f}s seems too short "
        f"(expected at least ~{expected_min_s:.0f}s)"
    )
    print(f"  Verification: duration looks reasonable "
          f"(>= {expected_min_s:.0f}s minimum estimate)")


if __name__ == "__main__":
    main()
