"""
Transkript segmentlerini (zaman damgali metin parcalari) hedef dile cevirir.
Zaman damgalarina dokunmaz, sadece metni cevirir.
"""

import json
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


def translate_segments(segments, target_language: str):
    lines = [{"i": i, "text": seg.text.strip()} for i, seg in enumerate(segments)]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional subtitle translator. Translate each line's "
                    "'text' into the target language, keeping meaning and tone natural for "
                    "short-form video captions. Return JSON with the same schema: "
                    '{"lines": [{"i": 0, "text": "..."}, ...]}. Same number of lines, same order.'
                ),
            },
            {
                "role": "user",
                "content": json.dumps({"target_language": target_language, "lines": lines}),
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    translated_by_index = {item["i"]: item["text"] for item in data["lines"]}

    return [
        SimpleNamespace(
            start=seg.start,
            end=seg.end,
            text=translated_by_index.get(i, seg.text),
        )
        for i, seg in enumerate(segments)
    ]
