"""
Video dosyasindan sesi cikarir, OpenAI Whisper API ile yaziya cevirir,
hem terminale yazdirir hem de altyazi dosyasi (.srt) olarak kaydeder.

Kullanim: python transcribe.py video.mp4
"""

import sys
import subprocess
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()


def extract_audio(video_path: Path) -> Path:
    audio_path = video_path.with_suffix(".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "libmp3lame", str(audio_path)],
        check=True,
        capture_output=True,
    )
    return audio_path


def transcribe(audio_path: Path):
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    return result.segments


def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(segments, srt_path: Path):
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = format_timestamp(seg.start)
            end = format_timestamp(seg.end)
            f.write(f"{i}\n{start} --> {end}\n{seg.text.strip()}\n\n")


def main():
    if len(sys.argv) != 2:
        print("Kullanim: python transcribe.py video.mp4")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    if not video_path.exists():
        print(f"Dosya bulunamadi: {video_path}")
        sys.exit(1)

    print("1/3 - Sesi videodan cikariyorum...")
    audio_path = extract_audio(video_path)

    print("2/3 - OpenAI Whisper API ile yaziya ceviriyorum...")
    segments = transcribe(audio_path)

    print("\n--- TRANSKRIPT ---")
    for seg in segments:
        print(f"[{seg.start:.1f}s - {seg.end:.1f}s] {seg.text.strip()}")

    srt_path = video_path.with_suffix(".srt")
    print(f"\n3/3 - Altyazi dosyasi kaydediliyor: {srt_path}")
    write_srt(segments, srt_path)

    os.remove(audio_path)
    print("Bitti.")


if __name__ == "__main__":
    main()
