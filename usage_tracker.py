"""
Ucretsiz plan kullanim takibi. Simdilik hesap/sifre sistemi yok - kullanicinin
girdigi e-posta, kimligi olarak kullaniliyor. Kullanim sayaci basit bir JSON
dosyasinda (usage.json) tutuluyor, her ay basinda sifirlaniyor.

Not: Bu, coklu hesap (freemium abuse) sorununu tamamen cozmuyor - biri farkli
e-postalarla tekrar tekrar gelebilir. Bu ilk savunma katmani; plana yazdigimiz
gibi ("cogu kullanici icin yeterince caydirici" seviyesi) ileride kart/telefon
dogrulamasiyla guclendirilecek.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

USAGE_FILE = Path("usage.json")

FREE_MONTHLY_LIMIT = 3          # ucretsiz planda ayda islenebilecek video sayisi
FREE_MAX_DURATION_SECONDS = 90  # ucretsiz planda video basina sure sinirI (1.5 dk)


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _load() -> dict:
    if not USAGE_FILE.exists():
        return {}
    with open(USAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_remaining(email: str) -> int:
    """Bu ay icin kalan ucretsiz video hakkini dondurur."""
    data = _load()
    record = data.get(email.lower())
    month = _current_month()
    if not record or record.get("month") != month:
        return FREE_MONTHLY_LIMIT
    return max(0, FREE_MONTHLY_LIMIT - record.get("count", 0))


def record_usage(email: str) -> None:
    """Bir video islendiginde sayaci bir artirir (ay degistiyse sifirdan baslar)."""
    data = _load()
    key = email.lower()
    month = _current_month()
    record = data.get(key)
    if not record or record.get("month") != month:
        record = {"month": month, "count": 0}
    record["count"] += 1
    data[key] = record
    _save(data)
