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

FREE_MONTHLY_LIMIT = 3           # ucretsiz planda ayda islenebilecek video sayisi
FREE_MAX_DURATION_SECONDS = 180  # ucretsiz planda video basina sure siniri (3 dk) - async mimariye gecince Cloudflare timeout riski kalkti, 90 sn'den yukselttik

PRO_MONTHLY_LIMIT = 20           # Pro planda ayda islenebilecek video sayisi
PRO_MAX_DURATION_SECONDS = 480   # Pro planda video basina sure siniri (8 dk)
PRO_PRICE_TRY = 149              # Pro plan aylik fiyati (TL)

PREMIUM_MONTHLY_LIMIT = 15            # Premium planda ayda islenebilecek video sayisi
PREMIUM_MAX_DURATION_SECONDS = 1200   # Premium planda video basina sure siniri (20 dk) - Render Starter'da gercek sureyle dogrulanacak
PREMIUM_PRICE_TRY = 349               # Premium plan aylik fiyati (TL)

PLAN_LIMITS = {
    "free": {"monthly_limit": FREE_MONTHLY_LIMIT, "max_duration": FREE_MAX_DURATION_SECONDS},
    "pro": {"monthly_limit": PRO_MONTHLY_LIMIT, "max_duration": PRO_MAX_DURATION_SECONDS},
    "premium": {"monthly_limit": PREMIUM_MONTHLY_LIMIT, "max_duration": PREMIUM_MAX_DURATION_SECONDS},
}


def _connect():
    return psycopg2.connect(DATABASE_URL)


def init_db() -> None:
    """usage ve users tablolari yoksa olusturur. Uygulama baslarken bir kez cagrilir."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    email TEXT PRIMARY KEY,
                    month TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0
                )
            """)
            # Ayni IP'den farkli email'lerle (birden fazla Google hesabi) ucretsiz
            # limiti asma girisimini zorlastirmak icin - sadece free plandaki
            # kullanicilar icin sayiliyor, odeme yapan kullanicilar IP'ye gore
            # kisitlanmiyor (paylasilan ofis/wifi IP'sinde haksiz yere engellenmesinler).
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usage_ip (
                    ip TEXT PRIMARY KEY,
                    month TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    name TEXT,
                    picture TEXT,
                    plan TEXT NOT NULL DEFAULT 'free',
                    subscription_reference TEXT,
                    current_period_end TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            # users tablosu daha once (bu sutunlar olmadan) olusturulmus olabilir - ekle.
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan TEXT NOT NULL DEFAULT 'free'")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_reference TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS current_period_end TIMESTAMPTZ")
        conn.commit()


def upsert_user(email: str, name: str, picture: str) -> None:
    """Google ile giris yapan kullaniciyi kaydeder/gunceller (isim, foto). Plan durumuna dokunmaz."""
    key = email.lower()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (email, name, picture)
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name, picture = EXCLUDED.picture
            """, (key, name, picture))
        conn.commit()


def get_user_plan(email: str) -> str:
    """Kullanicinin plani ('free' ya da 'pro'). Suresi gecmis Pro abonelik otomatik 'free'ye doner."""
    key = email.lower()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT plan, current_period_end FROM users WHERE email = %s", (key,))
            row = cur.fetchone()
    if not row:
        return "free"
    plan, period_end = row
    if plan == "pro" and period_end is not None and period_end < datetime.now(timezone.utc):
        return "free"
    return plan


def set_plan(email: str, plan: str, subscription_reference: str = None, current_period_end=None) -> None:
    """Odeme basarili/iptal oldugunda kullanicinin planini gunceller (webhook'tan cagrilir)."""
    key = email.lower()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users SET plan = %s, subscription_reference = %s, current_period_end = %s
                WHERE email = %s
            """, (plan, subscription_reference, current_period_end, key))
        conn.commit()


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def get_remaining(email: str, monthly_limit: int) -> int:
    """Bu ay icin kalan video hakkini dondurur (plana gore monthly_limit disaridan verilir)."""
    key = email.lower()
    month = _current_month()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT month, count FROM usage WHERE email = %s", (key,))
            row = cur.fetchone()
    if not row or row[0] != month:
        return monthly_limit
    return max(0, monthly_limit - row[1])


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


def get_ip_remaining(ip: str, monthly_limit: int) -> int:
    """Bu ay bu IP icin kalan ucretsiz video hakkini dondurur."""
    if not ip:
        return monthly_limit
    month = _current_month()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT month, count FROM usage_ip WHERE ip = %s", (ip,))
            row = cur.fetchone()
    if not row or row[0] != month:
        return monthly_limit
    return max(0, monthly_limit - row[1])


def record_ip_usage(ip: str) -> None:
    """Ucretsiz plandaki bir kullanici video isledikce IP sayacini bir artirir."""
    if not ip:
        return
    month = _current_month()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO usage_ip (ip, month, count)
                VALUES (%s, %s, 1)
                ON CONFLICT (ip) DO UPDATE SET
                    month = EXCLUDED.month,
                    count = CASE
                        WHEN usage_ip.month = EXCLUDED.month THEN usage_ip.count + 1
                        ELSE 1
                    END
            """, (ip, month))
        conn.commit()
