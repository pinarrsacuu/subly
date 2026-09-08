"""
Google ile giris (OAuth2 / OpenID Connect). Sifre yok - kullanicinin kimligi
Google hesabinin dogruladigi e-posta adresi. Authlib + Flask session kullanir.
"""

import os

from authlib.integrations.flask_client import OAuth

oauth = OAuth()


def init_auth(app) -> None:
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
