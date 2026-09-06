"""
Ucretsiz plan kullanim takibi. Simdilik hesap/sifre sistemi yok - kullanicinin
girdigi e-posta, kimligi olarak kullaniliyor. Kullanim sayaci Neon (Postgres)
uzerinde tutuluyor, boylece Render'in ucretsiz plani sunucuyu yeniden
baslattiginda sayaclar sifirlanmiyor.

Not: Bu, coklu hesap (freemium abuse) sorununu tamamen cozmuyor - biri farkli
e-postalarla tekrar tekrar gelebilir. Bu ilk savunma katmani; plana yazdigimiz
gibi ("cogu kullanici icin yeterince caydirici" seviyesi) ileride kart/telefon
dogrulamasiyla guclendirilecek.
"""

import os
from datetime import datetime, timezone

import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

FREE_MONTHLY_LIMIT = 3          # ucretsiz planda ayda islenebilecek video sayisi
FREE_MAX_DURATION_SECONDS = 90  # ucretsiz planda video basina sure sinirI (1.5 dk)


def _connect():
    return psycopg2.connect(DATABASE_URL)


def init_db() -> None:
    """usage tablosu yoksa olusturur. Uygulama baslarken bir kez cagrilir."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    email TEXT PRIMARY KEY,
                    month TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0
                )
            """)
        conn.commit()


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def get_remaining(email: str) -> int:
    """Bu ay icin kalan ucretsiz video hakkini dondurur."""
    key = email.lower()
    month = _current_month()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT month, count FROM usage WHERE email = %s", (key,))
            row = cur.fetchone()
    if not row or row[0] != month:
        return FREE_MONTHLY_LIMIT
    return max(0, FREE_MONTHLY_LIMIT - row[1])


def record_usage(email: str) -> None:
    """Bir video islendiginde sayaci bir artirir (ay degistiyse sifirdan baslar)."""
    key = email.lower()
    month = _current_month()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO usage (email, month, count)
                VALUES (%s, %s, 1)
                ON CONFLICT (email) DO UPDATE SET
                    month = EXCLUDED.month,
                    count = CASE
                        WHEN usage.month = EXCLUDED.month THEN usage.count + 1
                        ELSE 1
                    END
            """, (key, month))
        conn.commit()
