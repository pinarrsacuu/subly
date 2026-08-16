"""
.srt altyazi dosyasini videoya kalin, stilize (Submagic/CapCut tarzi) yazi
olarak gomer. Watermark yok.

Kullanim: python burn_captions.py video.mp4 video.srt
"""

import sys
import subprocess
from pathlib import Path

# Altyazi stili: kalin beyaz yazi, siyah kalin kontur, ekranin alt-orta kismi
CAPTION_STYLE = (
    "FontName=Arial,"
    "FontSize=14,"
    "PrimaryColour=&H00FFFFFF,"   # beyaz yazi
    "OutlineColour=&H00000000,"   # siyah kontur
    "BorderStyle=1,"
    "Outline=3,"
    "Bold=1,"
    "Alignment=2,"                # alt-orta
    "MarginV=60"
)


def burn(video_path: Path, srt_path: Path, output_path: Path):
    srt_escaped = str(srt_path).replace(":", "\\:")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"subtitles={srt_escaped}:force_style='{CAPTION_STYLE}'",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "copy",
            str(output_path),
        ],
        check=True,
    )


def main():
    if len(sys.argv) != 3:
        print("Kullanim: python burn_captions.py video.mp4 video.srt")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    srt_path = Path(sys.argv[2])

    if not video_path.exists() or not srt_path.exists():
        print("Video veya altyazi dosyasi bulunamadi.")
        sys.exit(1)

    output_path = video_path.with_name(video_path.stem + "_captioned.mp4")
    print(f"Altyazi gomuluyor: {output_path}")
    burn(video_path, srt_path, output_path)
    print("Bitti.")


if __name__ == "__main__":
    main()
