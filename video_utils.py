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
