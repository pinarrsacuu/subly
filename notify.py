"""
Video isleme bitince kullaniciya email bildirimi (Resend uzerinden).
Email gonderimi opsiyoneldir: RESEND_API_KEY yoksa ya da istek basarisiz
olursa sessizce gecilir - kullanici zaten /status sayfasinda sonucu gorebilir,
email sadece ek bir kolaylik, kritik yol degil.
"""

import os

import requests

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = os.environ.get("NOTIFY_FROM_EMAIL", "Subly <onboarding@resend.dev>")


def send_ready_email(to_email: str, status_url: str) -> None:
    if not RESEND_API_KEY:
        return
    try:
        requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": FROM_EMAIL,
                "to": [to_email],
                "subject": "Videon hazır — Subly",
                "html": (
                    f'<p>Videon watermark\'sız olarak hazır.</p>'
                    f'<p><a href="{status_url}">İndirmek için tıkla</a></p>'
                ),
            },
            timeout=10,
        )
    except Exception:
        pass


def send_error_email(to_email: str, status_url: str) -> None:
    if not RESEND_API_KEY:
        return
    try:
        requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": FROM_EMAIL,
                "to": [to_email],
                "subject": "Video işlenirken bir sorun oluştu — Subly",
                "html": (
                    f'<p>Videon işlenirken beklenmedik bir hata oluştu, özür dileriz.</p>'
                    f'<p><a href="{status_url}">Detay için tıkla</a></p>'
                ),
            },
            timeout=10,
        )
    except Exception:
        pass
