"""
Transkript segmentlerini (zaman damgali metin parcalari) hedef dile cevirir.
Zaman damgalarina dokunmaz, sadece metni cevirir.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

LANGUAGES = [
    ("original", "Orijinal dil (ceviri yok)"),
    ("English", "Ingilizce"),
    ("Spanish", "Ispanyolca"),
    ("Portuguese", "Portekizce"),
    ("French", "Fransizca"),
    ("German", "Almanca"),
    ("Italian", "Italyanca"),
    ("Turkish", "Turkce"),
    ("Arabic", "Arapca"),
    ("Hindi", "Hintce"),
    ("Chinese (Simplified)", "Cince (Basitlestirilmis)"),
    ("Japanese", "Japonca"),
    ("Korean", "Korece"),
    ("Russian", "Rusca"),
    ("Indonesian", "Endonezce"),
]


# Uzun videolarda tum satirlari tek istekte cevirmek hem yavasti (21 dakikalik
# videoda ~2 dakika) hem de riskliydi: modelin cikti siniri asilirsa JSON yarim
# gelir ve satirlar cevrilmeden kalir. Satirlari kucuk gruplara bolup gruplari
# ayni anda (paralel) ceviriyoruz.
BATCH_SIZE = 40
MAX_PARALLEL = 6

SYSTEM_PROMPT = (
    "You are a professional subtitle translator. Translate each line's "
    "'text' into the target language, keeping meaning and tone natural for "
    "short-form video captions. Return JSON with the same schema: "
    '{"lines": [{"i": 0, "text": "..."}, ...]}. Same number of lines, same order.'
)


def _translate_batch(lines, target_language: str) -> dict:
    """Bir grup satiri cevirir, {satir_no: ceviri} dondurur. Bir kez yeniden dener."""
    last_error = None
    for _ in range(2):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps({"target_language": target_language, "lines": lines})},
                ],
            )
            data = json.loads(response.choices[0].message.content)
            return {item["i"]: item["text"] for item in data["lines"]}
        except Exception as exc:  # ag hatasi, yarim JSON vb.
            last_error = exc
    raise last_error


def translate_segments(segments, target_language: str):
    lines = [{"i": i, "text": seg.text.strip()} for i, seg in enumerate(segments)]
    batches = [lines[k:k + BATCH_SIZE] for k in range(0, len(lines), BATCH_SIZE)]

    translated_by_index = {}
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        for result in pool.map(lambda batch: _translate_batch(batch, target_language), batches):
            translated_by_index.update(result)

    return [
        SimpleNamespace(
            start=seg.start,
            end=seg.end,
            text=translated_by_index.get(i, seg.text),
        )
        for i, seg in enumerate(segments)
    ]
