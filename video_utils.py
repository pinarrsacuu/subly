"""
Video dosyasi hakkinda teknik bilgi almak icin kucuk yardimcilar (ffprobe).
"""

import json
import subprocess
from pathlib import Path


def get_duration_seconds(video_path: Path) -> float:
    """ffprobe ile videonun toplam suresini saniye cinsinden dondurur."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def get_frame_rate(video_path: Path) -> float:
    """Videonun saniyedeki kare sayisi (ornegin 30.0 ya da 59.94). Okunamazsa 0 doner."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=avg_frame_rate",
            "-of", "json",
            str(video_path),
        ],
        capture_output=True,
        text=True,
    )
    try:
        rate = json.loads(result.stdout)["streams"][0]["avg_frame_rate"]
        num, den = rate.split("/")
        return float(num) / float(den)
    except (KeyError, IndexError, ValueError, ZeroDivisionError):
        return 0.0
