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
        [
            "ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "libmp3lame",
            # Mono + dusuk bit hizi: konusma icin yeterli, ama dosya boyutunu
            # kucultuyor - Premium'da 20 dakikaya kadar video izin verdigimiz
            # icin Whisper API'nin 25MB dosya sinirina yeterli pay birakiyoruz
            # (64kbps'de 20 dk ses ~9.6MB, varsayilan ayarlarla sinira yakindi).
            "-ac", "1", "-b:a", "64k",
            str(audio_path),
        ],
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


# Cince/Japonca gibi kelime arasi bosluk kullanmayan dillerde altyazi motoru
# satiri bolecek yer bulamiyor ve tum cumle tek, cok uzun bir satir oluyordu.
# Bu satirlari kendimiz boluyoruz (tercihen noktalama isaretinden sonra).
NO_SPACE_LINE_CHARS = 18
_BREAK_AFTER = "，。、！？；：,.!?;:"


def _is_wide(ch: str) -> bool:
    return "\u3040" <= ch <= "\u30ff" or "\u3400" <= ch <= "\u9fff" or "\uf900" <= ch <= "\ufaff" or "\uff00" <= ch <= "\uffef"


def wrap_caption(text: str) -> str:
    text = text.strip()
    wide = sum(1 for ch in text if _is_wide(ch))
    if wide < len(text) * 0.5 or len(text) <= NO_SPACE_LINE_CHARS:
        return text  # bosluklu diller: altyazi motoru zaten kendisi boluyor
    lines, current = [], ""
    for index, ch in enumerate(text):
        current += ch
        following = text[index + 1] if index + 1 < len(text) else ""
        # Latin harfli bir kelimenin (ornegin "Cloud") ortasindan bolme.
        inside_word = ch.isascii() and ch.isalnum() and following.isascii() and following.isalnum()
        long_enough = len(current) >= NO_SPACE_LINE_CHARS and not inside_word
        natural_break = ch in _BREAK_AFTER and len(current) >= NO_SPACE_LINE_CHARS * 0.6
        if long_enough or natural_break:
            lines.append(current.strip())
            current = ""
    if current.strip():
        # Tek-iki karakterlik artik satir birakma, oncekine ekle.
        if lines and len(current.strip()) <= 2:
            lines[-1] += current.strip()
        else:
            lines.append(current.strip())
    return "\n".join(lines)


def write_srt(segments, srt_path: Path):
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = format_timestamp(seg.start)
            end = format_timestamp(seg.end)
            f.write(f"{i}\n{start} --> {end}\n{wrap_caption(seg.text)}\n\n")


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
