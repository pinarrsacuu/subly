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

# Render Starter'in 512MB RAM'i, 1080p+ bir videoyu ffmpeg ile kodlarken bellek
# tasmasina (OOM) ve sunucu cokmesine yol aciyordu. Uzun kenari 720p'ye
# indirerek bellek/CPU kullanimini ciddi sekilde azaltiyoruz - kucuk (720p ve
# alti) videolar zaten degismeden kaliyor (min(1280, ...) sayesinde buyutme yok).
SCALE_FILTER = (
    "scale='if(gt(iw,ih),min(1280,iw),-2)':'if(gt(iw,ih),-2,min(1280,ih))'"
)

# Kullanici "videoda zaten yakilmis altyazi var, ustunu kapat" secenegini
# isaretlerse, eski yaziyi silmiyoruz (bu gercek video inpainting gerektirir,
# elimizdeki basit ffmpeg altyapisinin cok otesinde) - bunun yerine ekranin
# alt seridine duz/opak bir kutu ciziyoruz, yeni altyazi bu kutunun uzerine
# geliyor. Boylece eski ve yeni yazi ust uste binmiyor.
COVER_BAR_FILTER = "drawbox=x=0:y=ih*0.80:w=iw:h=ih*0.20:color=black@0.92:t=fill"


def burn(video_path: Path, srt_path: Path, output_path: Path, cover_subs: bool = False):
    srt_escaped = str(srt_path).replace(":", "\\:")
    filters = [SCALE_FILTER]
    if cover_subs:
        filters.append(COVER_BAR_FILTER)
    filters.append(f"subtitles={srt_escaped}:force_style='{CAPTION_STYLE}'")
    vf = ",".join(filters)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            # Tek thread: coklu thread her biri kendi frame tamponunu tuttugu icin
            # 512MB'lik dar bellekte encode hizindan bellekten tasarrufu tercih ediyoruz.
            "-threads", "1",
            # "-c:a copy" orijinal ses akisini oldugu gibi kopyaliyordu; eger
            # telefon kaydi gibi degisken kare hizli (VFR) bir video geldiyse,
            # yeniden kodlanan video ile kopyalanan sesin zaman damgalari
            # uyusmayabiliyor - ffmpeg bunu telafi etmek icin sinirsiz paket
            # biriktirebiliyor (muxing queue), bu da OOM'a yol acan gizli bir
            # sebep olabilir. Sesi de yeniden kodlayarak bunu onluyoruz.
            "-c:a", "aac",
            "-b:a", "128k",
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
