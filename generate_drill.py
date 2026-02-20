#!/usr/bin/env python3
"""
Generate a sight-singing / music-reading drill MP3.

Produces one MP3 containing 14 questions (one sharp and one flat for each
note letter A-G) in randomized order.  Each question follows this pattern:

  1. TTS: "Question N:"                          (brief pause)
  2. TTS: "This note is <LETTER>."                (brief pause)
  3. Piano tone for the base letter pitch (1.5 s, octave 4)
  4. Brief pause
  5. TTS: "What would <LETTER> sharp/flat sound like?"
  6. 4-second silent thinking pause
  7. TTS: "The answer is"                         (brief pause)
  8. Piano tone for the answer pitch (1.5 s)      (brief pause)
  9. TTS: "Did you get it?"
 10. 2-second gap before next question

Uses a British male voice (gTTS British English, pitch-shifted lower).
Generates two files: standard (octave 4) and low (octave 3) for men.

Usage:
    python generate_drill.py [--seed SEED] [--output FILE] [--order FILE]
"""

import argparse
import io
import math
import random
import subprocess
import tempfile
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

TONE_DURATION_S = 1.5       # seconds for piano tone
BRIEF_PAUSE_S = 0.8         # short pause between speech and tones
THINK_PAUSE_S = 4.0         # seconds of silence for thinking
GAP_S = 2.0                 # seconds gap between questions

# Pitch-shift factor for male-sounding voice (lower = deeper)
VOICE_PITCH_FACTOR = 0.88


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def generate_piano_tone(frequency: float, duration_s: float,
                        sample_rate: int = SAMPLE_RATE,
                        amplitude: float = 0.6) -> AudioSegment:
    """Generate a piano-like tone using additive synthesis.

    Uses multiple harmonics with decreasing amplitudes and an exponential
    decay envelope to approximate a piano sound.
    """
    n_samples = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, n_samples, endpoint=False)
    samples = np.zeros(n_samples, dtype=np.float64)

    # Piano harmonics: fundamental + overtones with decreasing amplitude
    # and faster decay for higher harmonics
    harmonics = [
        (1, 1.00, 1.5),   # fundamental, full amplitude, slow decay
        (2, 0.50, 2.0),   # 2nd harmonic
        (3, 0.25, 2.5),   # 3rd harmonic
        (4, 0.15, 3.0),   # 4th harmonic
        (5, 0.08, 3.5),   # 5th harmonic
        (6, 0.04, 4.0),   # 6th harmonic
    ]

    for harmonic_num, rel_amp, decay_rate in harmonics:
        freq = frequency * harmonic_num
        if freq > sample_rate / 2:
            break  # skip harmonics above Nyquist
        envelope = rel_amp * np.exp(-decay_rate * t)
        samples += envelope * np.sin(2 * math.pi * freq * t)

    # Quick attack (5 ms ramp) to simulate hammer strike
    attack_samples = int(sample_rate * 0.005)
    if attack_samples > 0 and attack_samples < n_samples:
        attack = np.linspace(0, 1, attack_samples)
        samples[:attack_samples] *= attack

    # Soft release (20 ms fade-out) to avoid clicks
    release_samples = int(sample_rate * 0.02)
    if release_samples > 0 and release_samples < n_samples:
        release = np.linspace(1, 0, release_samples)
        samples[-release_samples:] *= release

    # Normalize peak to target amplitude
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = amplitude * samples / peak

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


def pitch_shift_segment(segment: AudioSegment,
                        factor: float) -> AudioSegment:
    """Pitch-shift an AudioSegment by changing sample rate and resampling.

    factor < 1.0 = lower pitch, factor > 1.0 = higher pitch.
    Compensates speed so duration stays roughly the same.
    """
    raw = segment.raw_data
    # Write raw PCM, shift pitch via asetrate, restore speed via atempo,
    # resample back to original rate
    atempo = 1.0 / factor
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-f", "s16le",
            "-ar", str(segment.frame_rate),
            "-ac", str(segment.channels),
            "-i", "pipe:0",
            "-af", (
                f"asetrate={segment.frame_rate}*{factor},"
                f"aresample={segment.frame_rate},"
                f"atempo={atempo:.6f}"
            ),
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ar", str(segment.frame_rate),
            "-ac", str(segment.channels),
            "pipe:1",
        ],
        input=raw,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"pitch shift failed: {proc.stderr.decode()}")
    return AudioSegment(
        data=proc.stdout,
        sample_width=segment.sample_width,
        frame_rate=segment.frame_rate,
        channels=segment.channels,
    )


def tts_to_segment(text: str, slow: bool = True) -> AudioSegment:
    """Convert text to speech using gTTS British English, pitch-shifted
    lower to sound like a male voice."""
    tts = gTTS(text=text, lang="en", tld="co.uk", slow=slow)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    segment = mp3_bytes_to_segment(buf.getvalue())
    return pitch_shift_segment(segment, VOICE_PITCH_FACTOR)


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


def get_answer_freq(letter: str, accidental: str) -> float:
    """Return the frequency of the sharp/flat version of a note."""
    midi = MIDI_NOTES[letter]
    if accidental == "sharp":
        midi += 1
    else:  # flat
        midi -= 1
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def render_question(q: dict, index: int, total: int,
                    octave_shift: int = 0) -> AudioSegment:
    """Render a single question to an AudioSegment.

    octave_shift: 0 for standard (octave 4), -1 for one octave lower, etc.
    """
    letter = q["letter"]
    accidental = q["accidental"]
    question_num = index + 1
    brief = generate_silence(BRIEF_PAUSE_S)

    print(f"  [{question_num}/{total}] Generating: {q['label']} "
          f"({letter} {accidental})...")

    # 1) Question number
    seg_number = tts_to_segment(f"Question {question_num}.")

    # 2) Announcement
    seg_announce = tts_to_segment(f"This note is {letter}.")

    # 3) Piano base tone (shifted by octave if needed)
    freq = FREQ_TABLE[letter] * (2.0 ** octave_shift)
    seg_tone = generate_piano_tone(freq, TONE_DURATION_S)

    # 4) Question
    seg_question = tts_to_segment(
        f"What would {letter} {accidental} sound like?"
    )

    # 5) Thinking pause
    seg_think = generate_silence(THINK_PAUSE_S)

    # 6) "The answer is"
    seg_answer_intro = tts_to_segment("The answer is")

    # 7) Answer piano tone
    answer_freq = get_answer_freq(letter, accidental) * (2.0 ** octave_shift)
    seg_answer_tone = generate_piano_tone(answer_freq, TONE_DURATION_S)

    # 8) "Did you get it?"
    seg_confirm = tts_to_segment("Did you get it?")

    # 9) Gap before next question
    seg_gap = generate_silence(GAP_S)

    # Concatenate all pieces with brief pauses
    return (
        seg_number + brief
        + seg_announce + brief
        + seg_tone + brief
        + seg_question
        + seg_think
        + seg_answer_intro + brief
        + seg_answer_tone + brief
        + seg_confirm
        + seg_gap
    )


def export_mp3(audio: AudioSegment, output_path: Path) -> None:
    """Export AudioSegment to MP3 via ffmpeg."""
    raw_pcm = audio.raw_data
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
        help="Output MP3 filename (standard octave 4 version)."
    )
    parser.add_argument(
        "--output-low", type=str,
        default="sight_singing_sharps_flats_low.mp3",
        help="Output MP3 filename (octave-lower version for men)."
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

    # --- Standard version (octave 4) ---
    print(f"\nRendering {len(questions)} questions (standard - octave 4)...")
    full_audio = AudioSegment.empty()
    for i, q in enumerate(questions):
        segment = render_question(q, i, len(questions), octave_shift=0)
        full_audio += segment

    # Normalize loudness
    target_dBFS = -18.0
    change_in_dBFS = target_dBFS - full_audio.dBFS
    full_audio = full_audio.apply_gain(change_in_dBFS)

    output_path = Path(args.output)
    print(f"\nExporting to {output_path}...")
    export_mp3(full_audio, output_path)

    duration_s = len(full_audio) / 1000.0
    minutes = int(duration_s // 60)
    seconds = duration_s % 60
    print(f"  Output:   {output_path} ({output_path.stat().st_size / 1024:.0f} KB)")
    print(f"  Duration: {minutes}m {seconds:.1f}s")

    # --- Low version (octave 3, one octave lower for men) ---
    print(f"\nRendering {len(questions)} questions (low - octave 3 for men)...")
    full_audio_low = AudioSegment.empty()
    for i, q in enumerate(questions):
        segment = render_question(q, i, len(questions), octave_shift=-1)
        full_audio_low += segment

    change_in_dBFS = target_dBFS - full_audio_low.dBFS
    full_audio_low = full_audio_low.apply_gain(change_in_dBFS)

    output_low_path = Path(args.output_low)
    print(f"\nExporting to {output_low_path}...")
    export_mp3(full_audio_low, output_low_path)

    duration_low_s = len(full_audio_low) / 1000.0
    minutes_low = int(duration_low_s // 60)
    seconds_low = duration_low_s % 60
    print(f"  Output:   {output_low_path} ({output_low_path.stat().st_size / 1024:.0f} KB)")
    print(f"  Duration: {minutes_low}m {seconds_low:.1f}s")

    # Summary
    print(f"\nDone!")
    print(f"  Questions: {len(questions)}")
    print(f"  Seed:     {seed}")

    # Final verification
    expected_min_s = 14 * (
        0.5 + BRIEF_PAUSE_S + 0.5 + BRIEF_PAUSE_S + TONE_DURATION_S
        + BRIEF_PAUSE_S + 1.0 + THINK_PAUSE_S + 0.5 + BRIEF_PAUSE_S
        + TONE_DURATION_S + BRIEF_PAUSE_S + 0.5 + GAP_S
    )
    assert duration_s >= expected_min_s, (
        f"Duration {duration_s:.1f}s seems too short "
        f"(expected at least ~{expected_min_s:.0f}s)"
    )
    print(f"  Verification: duration looks reasonable "
          f"(>= {expected_min_s:.0f}s minimum estimate)")


if __name__ == "__main__":
    main()
