"""
Basit web arayuzu: kullanici video yukler, arka planda transcribe.py +
burn_captions.py calisir, watermark'siz altyazili video indirilebilir hale gelir.

Calistirmak icin: python app.py
Sonra tarayicidan: http://localhost:5001
"""

import os
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, request, render_template_string, send_from_directory, session, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from auth import oauth, init_auth
from transcribe import extract_audio, transcribe, write_srt
from burn_captions import burn
from translate import translate_segments, LANGUAGES
from ui_strings import get_ui_language, get_ui_strings, get_client_ip, RTL_LANGS
from video_utils import get_duration_seconds
from usage_tracker import (
    get_remaining, record_usage, get_ip_remaining, record_ip_usage,
    init_db, upsert_user, get_user_plan, PLAN_LIMITS, FREE_MONTHLY_LIMIT,
    PRO_PRICE_TRY, PREMIUM_PRICE_TRY,
)
from jobs import (
    init_jobs_db, create_job, get_job, mark_processing, mark_done, mark_error,
    queue_position, count_active_jobs, fail_interrupted_jobs,
)
from notify import send_ready_email, send_error_email

app = Flask(__name__)
# Render/Cloudflare HTTPS'i sonlandirip Flask'a duz HTTP olarak iletiyor - bu
# olmadan url_for(_external=True) (ornegin Google OAuth callback adresi) yanlislikla
# http:// uretip Google'in "redirect_uri_mismatch" hatasina yol aciyordu.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ["SECRET_KEY"]
# Tek dosya icin ust sinir: daha buyugu sunucunun diskini/bellegini tek basina
# kilitleyebilir. Flask bunu asan yuklemeyi 413 hatasiyla reddeder (asagida yakalaniyor).
MAX_UPLOAD_MB = 2048
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
init_db()
init_jobs_db()
fail_interrupted_jobs()
init_auth(app)

# Videolar tek tek islenir: sunucuda tek islemci var, ayni anda birden fazla
# ffmpeg calisirsa hepsi yavaslar ve bellek tasarsa hepsi birden cokerdi.
# Bekleyen isler bu kilidi sirayla alir (gunicorn tek worker ile calistigi surece).
PROCESS_LOCK = threading.Lock()
OUTPUT_TTL_SECONDS = 24 * 60 * 60
# Sure sinirina tolerans: kullanici "20 dakikalik" diye kestigi videonun gercekte
# 21 dakikayi biraz gectigini gordu (CapCut cikti suresi hedeften uzun olabiliyor).
# Siniri saniyesi saniyesine uygulayip geri cevirmek yerine 90 saniye pay birakiyoruz.
DURATION_GRACE_SECONDS = 90

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Nexi Digital marka kimligi (2026-09-30 yenilemesi): nexidigitalai.com ile ayni
# renkler (kobalt + mandalina + gunes sarisi), ayni fontlar (Unbounded + Hanken
# Grotesk) ve ayni dugum-N logo. Boylece Subly ayni ailenin bir urunu gibi durur.
# Not: bu metin Jinja tarafindan da islenir; icinde suslu parantez + diyez yan yana
# (Jinja yorum isareti) ya da cift suslu parantez kullanma.
BRAND_HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400..800&family=Unbounded:wght@500..700&display=swap" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='24' fill='%230B1024'/%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='.2' stop-color='%234A67FF'/%3E%3Cstop offset='.8' stop-color='%23FF7A3D'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpath d='M28 24v52M28 24l44 52M72 24v52' stroke='%23fff' stroke-opacity='.42' stroke-width='7' stroke-linecap='round' fill='none'/%3E%3Ccircle cx='28' cy='24' r='10' fill='%234A67FF'/%3E%3Ccircle cx='28' cy='76' r='10' fill='%234A67FF'/%3E%3Ccircle cx='72' cy='24' r='10' fill='%23FF7A3D'/%3E%3Ccircle cx='72' cy='76' r='10' fill='%23FF7A3D'/%3E%3Ccircle cx='50' cy='50' r='12' fill='url(%23g)'/%3E%3C/svg%3E">
<meta name="theme-color" content="#F5F6FA" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0B1024" media="(prefers-color-scheme: dark)">
<style>
  :root {
    --bg: #F5F6FA; --bg-2: #EAEDF5; --surface: #FFFFFF;
    --ink: #0F1633; --ink-soft: #4E5775; --line: #DDE1EC;
    --blue: #2E4BF0; --blue-hover: #2239CC; --blue-text: #2440DD;
    --tang: #F26B2E; --tang-text: #B8480F; --sun: #FFC94D;
    --scr: #0A0F24; --scr-2: #111936; --scr-line: rgba(236, 240, 255, 0.12); --scr-text: #EEF1FF; --scr-soft: #A9B2D6;
    --shadow: 0 1px 2px rgba(15, 22, 51, 0.05), 0 20px 44px -26px rgba(30, 45, 120, 0.35);
    --ease: cubic-bezier(.32, .72, 0, 1);
    --spring: cubic-bezier(.34, 1.56, .64, 1);
    --font: "Hanken Grotesk", -apple-system, "Segoe UI", "Noto Sans", sans-serif;
    --display: "Unbounded", "Hanken Grotesk", -apple-system, "Segoe UI", sans-serif;
    color-scheme: light;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0B1024; --bg-2: #0F1530; --surface: #151C3A;
      --ink: #EEF1FF; --ink-soft: #A9B2D6; --line: rgba(238, 241, 255, 0.11);
      --blue-text: #93A8FF; --tang-text: #FF9A63;
      --scr: #070B1C; --scr-2: #0F1632;
      --shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 20px 44px -22px rgba(0, 0, 0, 0.8);
      color-scheme: dark;
    }
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0; overflow-x: clip; background: var(--bg); color: var(--ink);
    font-family: var(--font); font-size: 1.0625rem; line-height: 1.6; -webkit-font-smoothing: antialiased;
  }
  a { color: inherit; }
  h1, h2, h3 { margin: 0; text-wrap: balance; }
  h1, h2 { font-family: var(--display); font-weight: 600; letter-spacing: -0.03em; }
  p { margin: 0; text-wrap: pretty; }
  :focus-visible { outline: 2px solid var(--blue); outline-offset: 3px; border-radius: 8px; }
  .shell { max-width: 1180px; margin: 0 auto; padding-inline: 28px; }
  .wrap { max-width: 760px; margin: 0 auto; padding-inline: 24px; }

  /* ---------- Nav ---------- */
  nav.top { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; padding: 22px 0; }
  .brand { display: inline-flex; align-items: center; gap: 11px; text-decoration: none; color: var(--ink); }
  .brand .mark { width: 38px; height: 38px; flex: none; overflow: visible; }
  .brand .names { display: flex; flex-direction: column; line-height: 1.1; }
  .brand .product { font-family: var(--display); font-weight: 600; font-size: 1.28rem; letter-spacing: -0.03em; }
  .brand .by { font-size: 0.8rem; color: var(--ink-soft); }
  .mk-line { stroke: var(--ink); stroke-opacity: 0.42; stroke-width: 6; stroke-linecap: round; fill: none; }
  .mk-node { stroke: var(--bg); stroke-width: 4; paint-order: stroke; transform-box: fill-box; transform-origin: center; }
  .mk-c { fill: #4A67FF; }
  .mk-t { fill: #FF7A3D; }
  .brand:hover .mk-c, .brand:hover .mk-t { animation: nodePop 0.6s var(--spring); }
  .navActions, .userBox { display: flex; align-items: center; gap: 10px; }
  .userAvatar { width: 32px; height: 32px; border-radius: 50%; display: block; }
  .userName { font-size: 0.88rem; color: var(--ink-soft); }

  /* ---------- Buttons ---------- */
  .btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 10px;
    min-height: 46px; padding: 0 22px; border-radius: 999px; border: 0; cursor: pointer;
    font: inherit; font-size: 0.95rem; font-weight: 600; text-decoration: none; white-space: nowrap;
    transition: background-color 0.28s var(--ease), box-shadow 0.28s var(--ease), transform 0.28s var(--ease);
  }
  .btn:active { transform: scale(0.98); }
  .btnBlue { background: var(--blue); color: #fff; }
  .btnBlue:hover { background: var(--blue-hover); box-shadow: 0 12px 28px -12px rgba(46, 75, 240, 0.7); }
  .btnQuiet { background: transparent; color: var(--ink); box-shadow: inset 0 0 0 1px var(--line); }
  .btnQuiet:hover { box-shadow: inset 0 0 0 1px var(--ink-soft); }
  .btnPrimary { margin-top: 24px; }
  .btnGhost { color: var(--ink); text-decoration: none; font-size: 0.92rem; font-weight: 600; border-bottom: 1.5px solid var(--blue); padding-bottom: 2px; }
  .btnGhost:hover { color: var(--blue-text); }

  /* Button-in-button hero CTA */
  .btnNested {
    display: inline-flex; align-items: center; gap: 14px; margin-top: 34px;
    background: var(--blue); color: #fff; text-decoration: none; font-weight: 700; font-size: 1.05rem;
    padding: 7px 7px 7px 26px; border-radius: 999px;
    box-shadow: 0 18px 40px -16px rgba(46, 75, 240, 0.75);
    transition: transform 0.3s var(--ease), box-shadow 0.3s var(--ease), background-color 0.3s var(--ease);
  }
  .btnNested:hover { background: var(--blue-hover); transform: translateY(-2px); }
  .btnNested:active { transform: scale(0.98); }
  .btnNestedBadge {
    display: inline-flex; align-items: center; gap: 8px; background: var(--tang); color: #fff;
    padding: 11px 20px; border-radius: 999px; font-size: 0.92rem; white-space: nowrap;
    transition: transform 0.4s var(--spring);
  }
  .btnNested:hover .btnNestedBadge { transform: translateX(3px); }
  .freeNote { margin-top: 18px; font-size: 0.9rem; color: var(--ink-soft); max-width: 46ch; }

  /* ---------- Hero ---------- */
  .hero { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr); gap: 56px; align-items: center; padding: 56px 0 24px; }
  .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 26px; }
  .chip { font-size: 0.84rem; font-weight: 600; color: var(--ink); background: var(--surface); box-shadow: inset 0 0 0 1px var(--line); padding: 6px 13px; border-radius: 999px; }
  .chip:nth-child(2) { color: var(--blue-text); }
  h1.headline { font-size: clamp(2.1rem, 4.4vw, 3.6rem); line-height: 1.08; letter-spacing: -0.035em; }
  h1.headline em { font-style: normal; color: #fff; background: var(--blue); padding: 0 0.18em; border-radius: 0.2em; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
  h1.headline .h1sub { display: block; color: var(--ink-soft); font-size: 0.62em; letter-spacing: -0.02em; margin-top: 0.5em; line-height: 1.2; }
  h1.headline .h1sub::first-letter { text-transform: uppercase; }
  p.lede { color: var(--ink-soft); font-size: 1.15rem; max-width: 44ch; margin-top: 22px; }

  /* Phone demo: an always-dark "screen" */
  .demoWrap { display: flex; flex-direction: column; align-items: center; position: relative; }
  .demoWrap::before {
    content: ""; position: absolute; inset: -10% -14%; z-index: -1; pointer-events: none; filter: blur(24px);
    background: radial-gradient(45% 40% at 35% 35%, color-mix(in srgb, var(--blue) 24%, transparent), transparent 70%),
                radial-gradient(40% 40% at 70% 72%, color-mix(in srgb, var(--tang) 22%, transparent), transparent 70%);
  }
  .phone { width: min(300px, 78vw); padding: 7px; border-radius: 42px; background: color-mix(in srgb, var(--ink) 6%, transparent); box-shadow: inset 0 0 0 1px var(--line), var(--shadow); }
  .demoFrame { position: relative; aspect-ratio: 9 / 16; border-radius: 35px; overflow: hidden; background: var(--scr); isolation: isolate; }
  .blob { position: absolute; width: 70%; aspect-ratio: 1; border-radius: 50%; filter: blur(34px); opacity: 0.85; z-index: -1; }
  .blob.b1 { background: #3B55F0; top: 6%; left: -12%; animation: drift1 9s ease-in-out infinite alternate; }
  .blob.b2 { background: #FF7A3D; bottom: 16%; right: -18%; animation: drift2 11s ease-in-out infinite alternate; }
  .blob.b3 { background: #FFC94D; width: 40%; top: 42%; left: 30%; opacity: 0.45; animation: drift1 13s ease-in-out infinite alternate-reverse; }
  .demoFrame::after { content: ""; position: absolute; inset: 0; z-index: -1; background: linear-gradient(180deg, rgba(7, 11, 28, 0.1), rgba(7, 11, 28, 0.55)); }
  .demoTime { position: absolute; top: 16px; inset-inline-start: 16px; background: rgba(7, 11, 28, 0.5); color: #fff; font-size: 0.74rem; font-weight: 600; padding: 4px 10px; border-radius: 999px; font-variant-numeric: tabular-nums; }
  .demoPlay { position: absolute; top: 44%; left: 50%; width: 54px; height: 54px; margin: -27px 0 0 -27px; border-radius: 50%; background: rgba(255, 255, 255, 0.18); display: grid; place-items: center; }
  .demoPlay::after { content: ""; border-style: solid; border-width: 9px 0 9px 15px; border-color: transparent transparent transparent #fff; margin-left: 4px; }
  .demoCaption {
    position: absolute; left: 16px; right: 16px; bottom: 58px; text-align: center; color: #fff;
    font-family: var(--display); font-weight: 600; font-size: 1.02rem; line-height: 1.35; letter-spacing: -0.01em;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.45); min-height: 2.8em;
  }
  .demoCaption .cw { display: inline-block; padding: 0 0.12em; border-radius: 0.2em; transition: background-color 0.18s var(--ease), color 0.18s var(--ease), transform 0.3s var(--spring); }
  .demoCaption .cw.on { background: var(--sun); color: #0F1633; text-shadow: none; transform: scale(1.06); }
  .demoBar { position: absolute; left: 16px; right: 16px; bottom: 24px; height: 4px; border-radius: 4px; background: rgba(255, 255, 255, 0.22); overflow: hidden; }
  .demoBar i { display: block; height: 100%; width: 100%; background: #fff; transform-origin: left; transform: scaleX(0.35); }
  .demoLabel { margin-top: 16px; font-size: 0.86rem; color: var(--ink-soft); }

  /* ---------- Language ticker ---------- */
  .ticker { margin-top: 64px; border-block: 1px solid var(--line); overflow: hidden; padding: 18px 0; -webkit-mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent); mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent); }
  .tickTrack { display: flex; width: max-content; animation: tick 40s linear infinite; }
  [dir="rtl"] .tickTrack { animation-name: tickRtl; }
  .ticker:hover .tickTrack { animation-play-state: paused; }
  .tickSet { display: flex; align-items: center; gap: 34px; padding-inline-end: 34px; font-family: var(--display); font-weight: 500; font-size: clamp(1.05rem, 1.7vw, 1.35rem); letter-spacing: -0.02em; white-space: nowrap; }
  .tickSet span:nth-child(4n+3) { color: var(--blue-text); }
  .tickSet svg { width: 22px; height: 22px; flex: none; }

  /* ---------- Upload + steps ---------- */
  .contentSection { margin-top: 112px; }
  .splitRow { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr); gap: 64px; align-items: start; }
  .card { background: var(--surface); border-radius: 24px; padding: 36px 34px; box-shadow: var(--shadow), inset 0 0 0 1px var(--line); }
  .sectionTitle { font-size: clamp(1.6rem, 2.8vw, 2.3rem); line-height: 1.1; margin-bottom: 32px; }
  .stepGrid { list-style: none; margin: 0; padding: 0; display: grid; gap: 30px; position: relative; }
  .stepGrid::before { content: ""; position: absolute; top: 20px; bottom: 20px; inset-inline-start: 19px; width: 2px; background: linear-gradient(180deg, var(--blue), var(--tang)); opacity: 0.55; transform-origin: top; }
  .step { display: grid; grid-template-columns: 40px minmax(0, 1fr); gap: 4px 18px; align-items: start; }
  .stepNum { grid-row: span 2; width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center; font-weight: 700; background: var(--surface); color: var(--ink); box-shadow: inset 0 0 0 2px var(--line), 0 0 0 6px var(--bg); position: relative; }
  .step:first-child .stepNum { box-shadow: inset 0 0 0 2px var(--blue), 0 0 0 6px var(--bg); }
  .step:last-child .stepNum { box-shadow: inset 0 0 0 2px var(--tang), 0 0 0 6px var(--bg); }
  .step h3 { font-size: 1.12rem; font-weight: 700; padding-top: 7px; }
  .step p { color: var(--ink-soft); font-size: 0.98rem; }

  label { display: block; font-size: 0.9rem; font-weight: 600; color: var(--ink); margin: 20px 0 8px; }
  label:first-child { margin-top: 0; }
  input[type=file], input[type=email], select {
    width: 100%; font: inherit; font-size: 0.97rem; color: var(--ink); background: var(--bg);
    border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; min-height: 50px; outline: none;
    transition: border-color 0.25s var(--ease), box-shadow 0.25s var(--ease);
  }
  input[type=file]::file-selector-button { font: inherit; font-weight: 600; font-size: 0.88rem; border: 0; border-radius: 999px; padding: 7px 14px; margin-inline-end: 12px; background: var(--ink); color: var(--bg); cursor: pointer; }
  select:focus, input:focus { border-color: var(--blue); box-shadow: 0 0 0 3px color-mix(in srgb, var(--blue) 22%, transparent); }
  .checkboxRow { display: flex; align-items: flex-start; gap: 10px; margin: 22px 0 4px; font-weight: 500; font-size: 0.93rem; cursor: pointer; }
  .checkboxRow input { width: 18px; height: 18px; margin: 3px 0 0; accent-color: var(--blue); flex: none; }
  .checkboxHint { margin: 0 0 4px; padding-inline-start: 28px; font-size: 0.84rem; color: var(--ink-soft); }
  .subsPreview { margin: 12px 0 4px; }
  .subsPreviewTag { display: inline-block; font-size: 0.8rem; font-weight: 600; color: var(--ink-soft); margin-bottom: 6px; }
  .subsPreviewFrame { position: relative; height: 88px; border-radius: 14px; overflow: hidden; background: linear-gradient(135deg, #1B2A6B, #0A0F24 60%, #5A2A1A); }
  .subsPreviewOld, .subsPreviewNew { position: absolute; left: 0; right: 0; text-align: center; font-size: 0.8rem; font-weight: 700; color: #fff; text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7); }
  .subsPreviewOld { bottom: 24px; transition: opacity 0.25s var(--ease); }
  .subsPreviewNew { bottom: 10px; }
  .subsPreviewBar { position: absolute; left: 0; right: 0; bottom: 4px; height: 28px; background: rgba(7, 11, 28, 0.95); opacity: 0; transition: opacity 0.25s var(--ease); }
  .subsPreview.covered .subsPreviewOld { opacity: 0; }
  .subsPreview.covered .subsPreviewBar { opacity: 1; }
  .formNote { font-size: 0.84rem; color: var(--ink-soft); margin: 12px 0 0; }
  .uploadError { margin: 10px 0 0; font-size: 0.92rem; font-weight: 600; color: var(--tang-text); }
  .uploadProgress { margin-top: 18px; }
  .uploadProgress > p:first-child { display: flex; justify-content: space-between; font-size: 0.92rem; font-weight: 600; }
  .uploadProgress .working { margin-top: 8px; }
  .uploadProgress .working i { width: 100%; animation: none; transform-origin: left; transform: scaleX(0); transition: transform 0.3s var(--ease); }
  [dir="rtl"] .uploadProgress .working i { transform-origin: right; }
  .btn[disabled] { opacity: 0.6; cursor: not-allowed; }

  .lockedForm { position: relative; min-height: 280px; }
  .lockedForm fieldset { border: none; padding: 0; margin: 0; opacity: 0.35; pointer-events: none; }
  .lockedOverlay { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 4px; background: linear-gradient(180deg, transparent, var(--surface) 40%); }
  .lockedOverlay .lede { margin: 0 0 6px; max-width: 280px; font-size: 1rem; }
  .lockedOverlay .btnPrimary { margin-top: 8px; }

  /* ---------- Pricing ---------- */
  .pricing { margin-top: 128px; }
  .planGrid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }
  .planCard {
    background: var(--surface); border-radius: 22px; padding: 30px 28px; position: relative; cursor: pointer;
    box-shadow: var(--shadow), inset 0 0 0 1px var(--line);
    transition: transform 0.5s var(--ease), box-shadow 0.5s var(--ease);
  }
  .planCard:hover { transform: translateY(-6px); box-shadow: 0 30px 60px -28px rgba(46, 75, 240, 0.45), inset 0 0 0 1px var(--line); }
  .planCard.selected { box-shadow: 0 30px 60px -28px rgba(46, 75, 240, 0.5), inset 0 0 0 2px var(--blue); }
  .planCard.selected::after { content: "\\2713"; position: absolute; top: 22px; inset-inline-end: 24px; color: var(--blue-text); font-weight: 800; }
  .planCard h3 { font-size: 1rem; font-weight: 700; color: var(--ink-soft); margin: 0 0 10px; }
  .planPrice { font-family: var(--display); font-size: 2.2rem; font-weight: 600; letter-spacing: -0.04em; line-height: 1; margin: 0 0 16px; }
  .planPrice span { font-family: var(--font); font-size: 0.9rem; font-weight: 500; letter-spacing: 0; color: var(--ink-soft); }
  .planCard p:last-child { font-size: 0.95rem; color: var(--ink-soft); margin: 0; padding-top: 16px; border-top: 1px solid var(--line); }
  .planBadge { display: inline-block; font-size: 0.78rem; font-weight: 700; color: var(--tang-text); background: color-mix(in srgb, var(--tang) 12%, transparent); padding: 3px 11px; border-radius: 999px; margin-bottom: 12px; }
  .trustNote { margin-top: 26px; font-size: 0.92rem; color: var(--ink-soft); max-width: 70ch; }

  /* ---------- FAQ ---------- */
  .faq { margin-top: 128px; }
  .faq details { border-top: 1px solid var(--line); padding: 20px 0; }
  .faq details:last-of-type { border-bottom: 1px solid var(--line); }
  .faq summary { cursor: pointer; list-style: none; font-weight: 700; font-size: 1.1rem; display: flex; justify-content: space-between; gap: 20px; align-items: center; }
  .faq summary::-webkit-details-marker { display: none; }
  .faq summary::after { content: "+"; flex: none; width: 32px; height: 32px; border-radius: 50%; display: grid; place-items: center; font-weight: 500; font-size: 1.3rem; color: var(--blue-text); box-shadow: inset 0 0 0 1px var(--line); transition: transform 0.4s var(--spring); }
  .faq details[open] summary::after { transform: rotate(45deg); }
  .faq p { margin-top: 12px; color: var(--ink-soft); max-width: 64ch; }
  .faqGrid { display: grid; grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr); gap: 32px 64px; }

  footer.siteFoot { margin-top: 128px; border-top: 1px solid var(--line); padding: 32px 0 48px; font-size: 0.9rem; color: var(--ink-soft); display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px; }
  footer.siteFoot a { color: var(--ink); font-weight: 600; text-decoration: none; }
  footer.siteFoot a:hover { color: var(--blue-text); }

  /* ---------- Result / status / error pages ---------- */
  .page .card { margin-top: 32px; }
  .page h1.headline { font-size: clamp(1.8rem, 4vw, 2.6rem); margin: 6px 0 12px; }
  .page p.lede { margin: 0; }
  .badge { display: inline-flex; align-items: center; gap: 6px; font-size: 0.84rem; font-weight: 700; color: var(--blue-text); background: color-mix(in srgb, var(--blue) 12%, transparent); padding: 5px 13px; border-radius: 999px; margin-bottom: 16px; }
  video { width: 100%; border-radius: 16px; display: block; margin: 22px 0 0; background: var(--scr); }
  .working { height: 6px; border-radius: 6px; background: var(--bg-2); overflow: hidden; margin-top: 26px; }
  .working i { display: block; width: 40%; height: 100%; border-radius: 6px; background: linear-gradient(90deg, var(--blue), var(--tang)); animation: slide 1.6s var(--ease) infinite; }

  /* ---------- Motion ---------- */
  @media (prefers-reduced-motion: no-preference) {
    @supports (animation-timeline: view()) {
      .rv, .step, .planCard, .faq details { animation: rise linear both; animation-timeline: view(); animation-range: entry 5% entry 75%; }
      .step:nth-child(2), .planCard:nth-child(2) { animation-range: entry 14% entry 88%; }
      .step:nth-child(3), .planCard:nth-child(3) { animation-range: entry 22% cover 35%; }
      .stepGrid::before { animation: drawY linear both; animation-timeline: view(); animation-range: entry 20% cover 50%; }
    }
    .stepNum { animation: nodeBreath 3.2s var(--ease) infinite; }
    .step:nth-child(2) .stepNum { animation-delay: 1s; }
    .step:nth-child(3) .stepNum { animation-delay: 2s; }
  }
  @keyframes rise { from { opacity: 0; transform: translateY(40px); } to { opacity: 1; transform: none; } }
  @keyframes drawY { from { transform: scaleY(0); } to { transform: scaleY(1); } }
  @keyframes tick { to { transform: translateX(-50%); } }
  @keyframes tickRtl { to { transform: translateX(50%); } }
  @keyframes drift1 { to { transform: translate(30%, 22%) scale(1.15); } }
  @keyframes drift2 { to { transform: translate(-28%, -30%) scale(0.9); } }
  @keyframes nodePop { 40% { transform: scale(1.35); } }
  @keyframes nodeBreath { 0%, 60%, 100% { transform: scale(1); } 25% { transform: scale(1.12); } }
  @keyframes slide { from { transform: translateX(-100%); } to { transform: translateX(250%); } }
  @media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
    .tickTrack, .blob, .working i, .brand .mk-c, .brand .mk-t { animation: none !important; }
    .tickTrack { flex-wrap: wrap; width: auto; }
    .tickSet[aria-hidden] { display: none; }
    .tickSet { flex-wrap: wrap; white-space: normal; gap: 10px 26px; }
    .ticker { -webkit-mask-image: none; mask-image: none; }
    .btn, .btnNested, .btnNestedBadge, .planCard, .demoCaption .cw, .faq summary::after { transition: none !important; }
  }

  /* ---------- Responsive ---------- */
  @media (max-width: 900px) {
    .hero, .splitRow, .faqGrid { grid-template-columns: minmax(0, 1fr); }
    .hero { gap: 56px; padding-top: 32px; }
    .planGrid { grid-template-columns: minmax(0, 1fr); max-width: 520px; }
    .contentSection { margin-top: 88px; }
    .pricing, .faq, footer.siteFoot { margin-top: 96px; }
  }
  @media (max-width: 560px) {
    .shell { padding-inline: 18px; }
    .wrap { padding-inline: 18px; }
    nav.top { padding: 16px 0; }
    .navActions .btnQuiet { display: none; }
    .userName { display: none; }
    h1.headline { font-size: 2rem; }
    p.lede { font-size: 1.04rem; }
    .btnNested { font-size: 0.98rem; padding-inline-start: 20px; }
    .card { padding: 26px 20px; }
    .ticker { margin-top: 48px; padding: 14px 0; }
  }
</style>
"""

LOGO_SVG = """
<svg class="mark" viewBox="0 0 100 100" aria-hidden="true">
  <defs><linearGradient id="nxg" x1="0" y1="0" x2="1" y2="1"><stop offset=".2" stop-color="#4A67FF"/><stop offset=".8" stop-color="#FF7A3D"/></linearGradient></defs>
  <path class="mk-line" d="M24 20v60M24 20l52 60M76 20v60"/>
  <circle class="mk-node mk-c" cx="24" cy="20" r="10"/><circle class="mk-node mk-c" cx="24" cy="80" r="10"/>
  <circle class="mk-node mk-t" cx="76" cy="20" r="10"/><circle class="mk-node mk-t" cx="76" cy="80" r="10"/>
  <circle class="mk-node" cx="50" cy="50" r="12.5" fill="url(#nxg)"/>
</svg>
"""

NAV = f"""
<nav class="top">
  <a class="brand" href="/" aria-label="Subly">
    {LOGO_SVG}
    <span class="names">
      <span class="product">Subly</span>
      <span class="by">Nexi Digital</span>
    </span>
  </a>
  {{% if user %}}
    <div class="userBox">
      {{% if user.picture %}}<img class="userAvatar" src="{{{{ user.picture }}}}" alt="">{{% endif %}}
      <span class="userName">{{{{ user.name }}}}</span>
      <a href="/logout" class="btnGhost">{{{{ t.logout }}}}</a>
    </div>
  {{% else %}}
    <div class="navActions">
      <a href="/login/google" class="btn btnQuiet">{{{{ t.nav_login }}}}</a>
      <a href="/login/google" class="btn btnBlue">{{{{ t.nav_cta }}}}</a>
    </div>
  {{% endif %}}
</nav>
"""

# The 14 caption languages, each written in its own script.
TICKER_LANGS = ["English", "Español", "Português", "Français", "Deutsch", "Italiano", "Türkçe",
                "العربية", "हिन्दी", "中文", "日本語", "한국어", "Русский", "Bahasa Indonesia"]
TICKER_SEP = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 12h12" stroke="currentColor" stroke-opacity=".3" stroke-width="2"/>'
              '<circle cx="5" cy="12" r="4" fill="#4A67FF"/><circle cx="19" cy="12" r="4" fill="#FF7A3D"/></svg>')
TICKER_ITEMS = "".join(f"<span>{name}</span>{TICKER_SEP}" for name in TICKER_LANGS)

# Hero phone demo: captions light up word by word, like the karaoke style many
# creators use. Plain string (not an f-string) so the JS braces stay single.
DEMO_JS = """
<script>
(function () {
  var cap = document.getElementById("demoCaption");
  var timeEl = document.getElementById("demoTime");
  var bar = document.getElementById("demoBar");
  var captions = window.SUBLY_CAPTIONS || [];
  if (!cap || !captions.length) return;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function render(text) {
    cap.textContent = "";
    return text.split(/\\s+/).map(function (w, i, all) {
      var s = document.createElement("span");
      s.className = "cw";
      s.textContent = w;
      cap.appendChild(s);
      if (i < all.length - 1) cap.appendChild(document.createTextNode(" "));
      return s;
    });
  }
  if (reduce) { render(captions[0]); return; }
  var ci = 0, seconds = 7, visible = true;
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (es) { visible = es[0].isIntersecting; }).observe(cap);
  }
  function play() {
    if (!visible || document.hidden) { setTimeout(play, 600); return; }
    var words = render(captions[ci]);
    if (cap.animate) cap.animate([{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "none" }], { duration: 380, easing: "cubic-bezier(.32,.72,0,1)" });
    var wi = 0;
    var step = setInterval(function () {
      words.forEach(function (w, i) { w.classList.toggle("on", i === wi); });
      wi++;
      seconds++;
      timeEl.textContent = "0:" + (seconds < 10 ? "0" : "") + seconds;
      if (bar && bar.animate) {
        var from = ((seconds - 1) % 30) / 30, to = (seconds % 30) / 30;
        bar.animate([{ transform: "scaleX(" + from + ")" }, { transform: "scaleX(" + to + ")" }], { duration: 420, fill: "forwards" });
      }
      if (wi > words.length) {
        clearInterval(step);
        ci = (ci + 1) % captions.length;
        setTimeout(play, 500);
      }
    }, 420);
  }
  setTimeout(play, 500);
})();
</script>
"""

# Yukleme formu: dosya secilince boyut ve sure tarayicida kontrol edilir (buyuk bir
# dosyayi dakikalarca yukleyip sonra "cok uzun" hatasi almamak icin), yukleme
# sirasinda yuzde gosterilir. Plain string - JS suslu parantezleri tek kaliyor.
UPLOAD_JS = """
<script>
(function () {
  var form = document.getElementById("uploadFormEl");
  if (!form || !window.XMLHttpRequest) return;
  var input = document.getElementById("video");
  var note = document.getElementById("uploadError");
  var box = document.getElementById("uploadProgress");
  var bar = document.getElementById("uploadBar");
  var pct = document.getElementById("uploadPct");
  var button = form.querySelector("button[type=submit]");
  var blocked = false;
  function fail(msg) { blocked = true; note.textContent = msg; note.hidden = false; button.disabled = true; }
  function clear() { blocked = false; note.hidden = true; button.disabled = false; }
  input.addEventListener("change", function () {
    clear();
    var file = input.files[0];
    if (!file) return;
    if (file.size > Number(form.dataset.maxBytes)) { fail(form.dataset.msgSize); return; }
    var probe = document.createElement("video");
    probe.preload = "metadata";
    probe.onloadedmetadata = function () {
      URL.revokeObjectURL(probe.src);
      if (isFinite(probe.duration) && probe.duration > Number(form.dataset.maxSeconds)) fail(form.dataset.msgDuration);
    };
    probe.src = URL.createObjectURL(file);
  });
  form.addEventListener("submit", function (e) {
    if (blocked) { e.preventDefault(); return; }
    e.preventDefault();
    var xhr = new XMLHttpRequest();
    xhr.open("POST", form.action);
    box.hidden = false;
    button.disabled = true;
    xhr.upload.onprogress = function (ev) {
      if (!ev.lengthComputable) return;
      var p = Math.round(ev.loaded / ev.total * 100);
      bar.style.transform = "scaleX(" + (p / 100) + ")";
      pct.textContent = p + "%";
    };
    xhr.onload = function () {
      // Basarili yuklemede sunucu durum sayfasina yonlendirir; hata sayfalari ayni adreste doner.
      if (xhr.responseURL && xhr.responseURL.indexOf("/status/") !== -1) { window.location.href = xhr.responseURL; return; }
      document.open(); document.write(xhr.responseText); document.close();
    };
    xhr.onerror = function () { box.hidden = true; fail(form.dataset.msgNetwork); button.disabled = false; blocked = false; };
    xhr.send(new FormData(form));
  });
})();
</script>
"""

UPLOAD_FORM = f"""
<!doctype html>
<html lang="{{{{ lang }}}}" dir="{{{{ dir }}}}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Subly | Nexi Digital</title>
  <meta name="description" content="{{{{ t.lede }}}}">
  {BRAND_HEAD}
</head>
<body>
<div class="shell">
  {NAV}
  <section class="hero">
    <div class="heroText">
      <div class="chips">
        {{% for chip in t.eyebrow.split(' &middot; ') %}}<span class="chip">{{{{ chip|safe }}}}</span>{{% endfor %}}
      </div>
      {{% set hp = t.headline.split(' &mdash; ') %}}
      <h1 class="headline">{{{{ hp[0]|safe }}}}{{% if hp|length > 1 %}}<span class="h1sub">{{{{ hp[1]|safe }}}}</span>{{% endif %}}</h1>
      <p class="lede">{{{{ t.lede }}}}</p>
      <a href="#uploadForm" class="btnNested">
        {{{{ t.hero_cta_outer }}}}
        <span class="btnNestedBadge">{{{{ t.hero_cta_badge }}}}</span>
      </a>
      <p class="freeNote">{{{{ t.free_note|safe }}}}</p>
    </div>

    <div class="demoWrap">
      <div class="phone">
        <div class="demoFrame">
          <span class="blob b1"></span><span class="blob b2"></span><span class="blob b3"></span>
          <span class="demoTime" id="demoTime">0:07</span>
          <span class="demoPlay" aria-hidden="true"></span>
          <div class="demoCaption" id="demoCaption">{{{{ t.demo_caption }}}}</div>
          <div class="demoBar" aria-hidden="true"><i id="demoBar"></i></div>
        </div>
      </div>
      <p class="demoLabel">{{{{ t.demo_label }}}}</p>
    </div>
  </section>
</div>

<div class="ticker" aria-label="{{{{ t.step2_desc }}}}">
  <div class="tickTrack">
    <div class="tickSet">{TICKER_ITEMS}</div>
    <div class="tickSet" aria-hidden="true">{TICKER_ITEMS}</div>
  </div>
</div>

<script>
  window.SUBLY_CAPTIONS = [{{{{ t.demo_caption|tojson }}}}, {{{{ t.demo_caption2|tojson }}}}, {{{{ t.demo_caption3|tojson }}}}];
</script>
{DEMO_JS}

<div class="shell contentSection">
  <div class="splitRow">
    <div class="card rv" id="uploadForm">
      {{% if user %}}
        <form action="/process" method="post" enctype="multipart/form-data" id="uploadFormEl"
              data-max-bytes="{{{{ max_upload_mb * 1024 * 1024 }}}}" data-max-seconds="{{{{ max_duration + duration_grace }}}}"
              data-msg-size="{{{{ t.error_size_body.format(max_mb=max_upload_mb) }}}}"
              data-msg-duration="{{{{ t.error_duration_body.format(max_min=(max_duration / 60)|round|int) }}}}"
              data-msg-network="{{{{ t.processing_error_body }}}}">
          <label for="video">{{{{ t.label_video }}}}</label>
          <input type="file" id="video" name="video" accept="video/*" required>
          <p class="uploadError" id="uploadError" role="alert" hidden></p>
          <label for="language">{{{{ t.label_language }}}}</label>
          <select name="language" id="language">
            {{% for value, label in languages %}}
              <option value="{{{{ value }}}}">{{{{ label }}}}</option>
            {{% endfor %}}
          </select>

          <label class="checkboxRow" for="coverSubs">
            <input type="checkbox" id="coverSubs" name="cover_subs" onchange="toggleSubsPreview(this)">
            <span>{{{{ t.cover_subs_label }}}}</span>
          </label>
          <p class="checkboxHint">{{{{ t.cover_subs_hint }}}}</p>

          <div class="subsPreview" id="subsPreviewBox">
            <span class="subsPreviewTag" id="subsPreviewTag">{{{{ t.cover_subs_before }}}}</span>
            <div class="subsPreviewFrame">
              <span class="subsPreviewOld">こんにちは</span>
              <span class="subsPreviewBar"></span>
              <span class="subsPreviewNew">Hola, ¿qué tal?</span>
            </div>
          </div>

          <button type="submit" class="btn btnBlue btnPrimary">{{{{ t.button_process|safe }}}}</button>
          <div class="uploadProgress" id="uploadProgress" role="status" hidden>
            <p><span>{{{{ t.uploading }}}}</span><b id="uploadPct">0%</b></p>
            <div class="working"><i id="uploadBar"></i></div>
            <p class="formNote">{{{{ t.upload_wait }}}}</p>
          </div>
          <p class="formNote">{{{{ t.free_note|safe }}}}</p>
        </form>
        {UPLOAD_JS}
        <script>
          function toggleSubsPreview(cb) {{
            var box = document.getElementById("subsPreviewBox");
            var tag = document.getElementById("subsPreviewTag");
            box.classList.toggle("covered", cb.checked);
            tag.textContent = cb.checked ? {{{{ t.cover_subs_after|tojson }}}} : {{{{ t.cover_subs_before|tojson }}}};
          }}
        </script>
      {{% else %}}
        <div class="lockedForm">
          <fieldset disabled>
            <label for="video_locked">{{{{ t.label_video }}}}</label>
            <input type="file" id="video_locked">
            <label for="language_locked">{{{{ t.label_language }}}}</label>
            <select id="language_locked">
              {{% for value, label in languages %}}
                <option value="{{{{ value }}}}">{{{{ label }}}}</option>
              {{% endfor %}}
            </select>
            <label class="checkboxRow"><input type="checkbox"> <span>{{{{ t.cover_subs_label }}}}</span></label>
            <button type="button" class="btn btnBlue btnPrimary">{{{{ t.button_process|safe }}}}</button>
          </fieldset>
          <div class="lockedOverlay">
            <p class="lede">{{{{ t.login_prompt }}}}</p>
            <a href="/login/google" class="btn btnBlue btnPrimary">{{{{ t.login_google }}}}</a>
          </div>
        </div>
      {{% endif %}}
    </div>

    <div class="stepsPanel">
      <h2 class="sectionTitle">{{{{ t.how_it_works_title }}}}</h2>
      <ol class="stepGrid">
        <li class="step"><span class="stepNum">1</span><h3>{{{{ t.step1_title }}}}</h3><p>{{{{ t.step1_desc }}}}</p></li>
        <li class="step"><span class="stepNum">2</span><h3>{{{{ t.step2_title }}}}</h3><p>{{{{ t.step2_desc }}}}</p></li>
        <li class="step"><span class="stepNum">3</span><h3>{{{{ t.step3_title }}}}</h3><p>{{{{ t.step3_desc }}}}</p></li>
      </ol>
    </div>
  </div>

  <section class="pricing">
    <h2 class="sectionTitle">{{{{ t.pricing_title }}}}</h2>
    <div class="planGrid">
      <div class="planCard" data-plan="free" onclick="selectPlan(this, true)">
        <h3>Free</h3>
        <p class="planPrice">$0</p>
        <p>{{{{ t.free_note|safe }}}}</p>
      </div>
      <div class="planCard" data-plan="pro" onclick="selectPlan(this, false)">
        <span class="planBadge">{{{{ t.pricing_soon }}}}</span>
        <h3>Pro</h3>
        <p class="planPrice">&#8378;{{{{ pro_price }}}}<span>{{{{ t.per_month }}}}</span></p>
        <p>{{{{ t.pricing_pro_desc }}}}</p>
      </div>
      <div class="planCard" data-plan="premium" onclick="selectPlan(this, false)">
        <span class="planBadge">{{{{ t.pricing_soon }}}}</span>
        <h3>Premium</h3>
        <p class="planPrice">&#8378;{{{{ premium_price }}}}<span>{{{{ t.per_month }}}}</span></p>
        <p>{{{{ t.pricing_premium_desc }}}}</p>
      </div>
    </div>
    <p class="trustNote">{{{{ t.trust_note }}}}</p>
  </section>

  <script>
    function selectPlan(card, scrollToForm) {{
      document.querySelectorAll(".planCard").forEach(function (c) {{ c.classList.remove("selected"); }});
      card.classList.add("selected");
      if (scrollToForm) {{
        var form = document.getElementById("uploadForm");
        if (form) form.scrollIntoView({{ behavior: "smooth", block: "center" }});
      }}
    }}
  </script>

  <section class="faq faqGrid">
    <h2 class="sectionTitle">{{{{ t.faq_title }}}}</h2>
    <div>
      <details open><summary>{{{{ t.faq_q1 }}}}</summary><p>{{{{ t.faq_a1 }}}}</p></details>
      <details><summary>{{{{ t.faq_q2 }}}}</summary><p>{{{{ t.faq_a2 }}}}</p></details>
      <details><summary>{{{{ t.faq_q3 }}}}</summary><p>{{{{ t.faq_a3|safe }}}}</p></details>
      <details><summary>{{{{ t.faq_q4 }}}}</summary><p>{{{{ t.faq_a4 }}}}</p></details>
    </div>
  </section>

  <footer class="siteFoot"><span>{{{{ t.footer }}}}</span><a href="https://nexidigitalai.com/">nexidigitalai.com</a></footer>
</div>
</body>
</html>
"""

RESULT_PAGE = f"""
<!doctype html>
<html lang="{{{{ lang }}}}" dir="{{{{ dir }}}}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Subly</title>
  {BRAND_HEAD}
</head>
<body class="page">
<div class="wrap">
  {NAV}
  <div class="card">
    <span class="badge">{{{{ t.badge_ready|safe }}}}</span>
    <h1 class="headline">{{{{ t.result_headline|safe }}}}</h1>
    <video src="/outputs/{{{{ filename }}}}" controls></video>
    <a href="/outputs/{{{{ filename }}}}" download class="btn btnBlue btnPrimary">{{{{ t.download|safe }}}}</a>
    <p style="margin-top: 22px"><a href="/" class="btnGhost">{{{{ t.back_link|safe }}}}</a></p>
  </div>
  <footer class="siteFoot"><span>{{{{ t.footer }}}}</span><a href="https://nexidigitalai.com/">nexidigitalai.com</a></footer>
</div>
</body>
</html>
"""

STATUS_PAGE = f"""
<!doctype html>
<html lang="{{{{ lang }}}}" dir="{{{{ dir }}}}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="4">
  <title>Subly</title>
  {BRAND_HEAD}
</head>
<body class="page">
<div class="wrap">
  {NAV}
  <div class="card">
    <span class="badge">{{{{ status_badge|safe }}}}</span>
    <h1 class="headline">{{{{ status_title|safe }}}}</h1>
    <p class="lede">{{{{ status_body }}}}</p>
    <div class="working" aria-hidden="true"><i></i></div>
  </div>
  <footer class="siteFoot"><span>{{{{ t.footer }}}}</span><a href="https://nexidigitalai.com/">nexidigitalai.com</a></footer>
</div>
</body>
</html>
"""

ERROR_PAGE = f"""
<!doctype html>
<html lang="{{{{ lang }}}}" dir="{{{{ dir }}}}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Subly</title>
  {BRAND_HEAD}
</head>
<body class="page">
<div class="wrap">
  {NAV}
  <div class="card">
    <h1 class="headline">{{{{ error_title }}}}</h1>
    <p class="lede">{{{{ error_body }}}}</p>
    <p style="margin-top: 22px"><a href="/" class="btnGhost">{{{{ t.back_link|safe }}}}</a></p>
  </div>
  <footer class="siteFoot"><span>{{{{ t.footer }}}}</span><a href="https://nexidigitalai.com/">nexidigitalai.com</a></footer>
</div>
</body>
</html>
"""


@app.route("/login/google")
def login_google():
    redirect_uri = url_for("login_google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/login/google/callback")
def login_google_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token["userinfo"]
    session["user"] = {
        "email": userinfo["email"],
        "name": userinfo.get("name") or userinfo["email"],
        "picture": userinfo.get("picture", ""),
    }
    upsert_user(userinfo["email"], session["user"]["name"], session["user"]["picture"])
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


def resolve_lang():
    """Dili session'da onbellekler - /status sayfasi her birkac saniyede bir
    kendini yeniledigi icin, her seferinde IP-konum servisine tekrar
    sormamak (hem yavas hem de ucretsiz limiti zorlar) icin."""
    if "lang" not in session:
        session["lang"] = get_ui_language(request.accept_languages, get_client_ip(request))
    return session["lang"]


@app.route("/")
def index():
    lang = resolve_lang()
    t = get_ui_strings(lang)
    direction = "rtl" if lang in RTL_LANGS else "ltr"
    user = session.get("user")
    plan = get_user_plan(user["email"]) if user else "free"
    return render_template_string(
        UPLOAD_FORM, languages=LANGUAGES, t=t, lang=lang, dir=direction, user=user,
        pro_price=PRO_PRICE_TRY, premium_price=PREMIUM_PRICE_TRY,
        max_upload_mb=MAX_UPLOAD_MB, max_duration=PLAN_LIMITS[plan]["max_duration"],
        duration_grace=DURATION_GRACE_SECONDS,
    )


@app.route("/process", methods=["POST"])
def process():
    lang = resolve_lang()
    t = get_ui_strings(lang)
    direction = "rtl" if lang in RTL_LANGS else "ltr"
    user = session.get("user")

    if not user:
        return redirect(url_for("index"))

    uploaded = request.files["video"]
    target_language = request.form.get("language", "original")
    cover_subs = request.form.get("cover_subs") == "on"
    email = user["email"]
    ip = get_client_ip(request)
    file_id = uuid.uuid4().hex[:8]
    plan = get_user_plan(email)
    limits = PLAN_LIMITS[plan]
    is_free = plan == "free"

    # Plan kontrolu 1: bu ay hakki kalmis mi? Dosyayi kaydetmeden once
    # bakiyoruz ki API maliyetine hic girmeyelim.
    # Bitmemis isler de hakka sayilir - yoksa ayni anda 10 video yukleyip limiti asabilirdi.
    active = count_active_jobs(email)
    if get_remaining(email, limits["monthly_limit"]) - active <= 0:
        return render_template_string(
            ERROR_PAGE, t=t, lang=lang, dir=direction, user=user,
            error_title=t["error_limit_title"],
            error_body=t["error_limit_body"].format(limit=limits["monthly_limit"]),
        )

    # Plan kontrolu 1b: sadece ucretsiz plan icin - ayni IP'den farkli Google
    # hesaplariyla (email degistirerek) limiti asma girisimini zorlastirmak
    # icin ayrica IP bazli da sayiyoruz. Odeme yapan kullanicilar (pro/premium)
    # bundan etkilenmiyor.
    if is_free and get_ip_remaining(ip, FREE_MONTHLY_LIMIT) - active <= 0:
        return render_template_string(
            ERROR_PAGE, t=t, lang=lang, dir=direction, user=user,
            error_title=t["error_limit_title"],
            error_body=t["error_limit_body"].format(limit=FREE_MONTHLY_LIMIT),
        )

    video_path = UPLOAD_DIR / f"{file_id}_{uploaded.filename}"
    uploaded.save(video_path)

    # Plan kontrolu 2: video suresi sinirin altinda mi?
    duration = get_duration_seconds(video_path)
    if duration > limits["max_duration"] + DURATION_GRACE_SECONDS:
        video_path.unlink()
        return render_template_string(
            ERROR_PAGE, t=t, lang=lang, dir=direction, user=user,
            error_title=t["error_duration_title"],
            error_body=t["error_duration_body"].format(max_min=round(limits["max_duration"] / 60)),
        )

    # Asil isleme (transkript + ceviri + altyazi yakma) arka planda bir thread'de
    # calisir - boylece uzun videolarda HTTP istegi/Cloudflare proxy timeout'una
    # takilmadan kullaniciyi hemen /status sayfasina yonlendirebiliyoruz.
    job_id = create_job(email)
    status_url = url_for("job_status", job_id=job_id, _external=True)
    thread = threading.Thread(
        target=run_job,
        args=(job_id, file_id, video_path, target_language, cover_subs, email, ip, is_free, status_url, t),
        daemon=True,
    )
    thread.start()

    return redirect(url_for("job_status", job_id=job_id))


def cleanup_old_outputs():
    """Indirilmis/unutulmus eski cikti videolarini siler - disk dolmasin."""
    cutoff = time.time() - OUTPUT_TTL_SECONDS
    for path in OUTPUT_DIR.glob("*"):
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            pass


def run_job(job_id, file_id, video_path, target_language, cover_subs, email, ip, is_free, status_url, t):
    srt_path = video_path.with_suffix(".srt")
    audio_path = None
    with PROCESS_LOCK:
        mark_processing(job_id)
        try:
            cleanup_old_outputs()
            # Her adimin suresini Render loglarina yaziyoruz - yavaslik sikayetinde
            # zamanin nereye gittigini (ses, transkript, ceviri, kodlama) gormek icin.
            started = time.time()
            size_mb = video_path.stat().st_size / (1024 * 1024)
            audio_path = extract_audio(video_path)
            t_audio = time.time()
            segments = transcribe(audio_path)
            t_transcribe = time.time()
            if target_language != "original":
                segments = translate_segments(segments, target_language)
            write_srt(segments, srt_path)
            t_translate = time.time()

            output_filename = f"{file_id}_captioned.mp4"
            output_path = OUTPUT_DIR / output_filename
            burn(video_path, srt_path, output_path, cover_subs=cover_subs)
            t_burn = time.time()
            print(
                f"[job {job_id[:8]}] size={size_mb:.0f}MB audio={t_audio - started:.0f}s "
                f"transcribe={t_transcribe - t_audio:.0f}s translate={t_translate - t_transcribe:.0f}s "
                f"burn={t_burn - t_translate:.0f}s total={t_burn - started:.0f}s",
                flush=True,
            )

            record_usage(email)
            if is_free:
                record_ip_usage(ip)
            mark_done(job_id, output_filename)
            send_ready_email(email, status_url)
        except Exception as exc:
            mark_error(job_id, t["processing_error_title"], f'{t["processing_error_body"]} ({exc})')
            send_error_email(email, status_url)
        finally:
            # Basarili da olsa hata da olsa yuklenen video ve ara dosyalar silinir.
            for path in (video_path, srt_path, audio_path):
                try:
                    if path is not None and Path(path).exists():
                        Path(path).unlink()
                except OSError:
                    pass


@app.errorhandler(413)
def upload_too_large(_error):
    lang = resolve_lang()
    t = get_ui_strings(lang)
    direction = "rtl" if lang in RTL_LANGS else "ltr"
    return render_template_string(
        ERROR_PAGE, t=t, lang=lang, dir=direction, user=session.get("user"),
        error_title=t["error_size_title"],
        error_body=t["error_size_body"].format(max_mb=MAX_UPLOAD_MB),
    ), 413


@app.route("/status/<job_id>")
def job_status(job_id):
    lang = resolve_lang()
    t = get_ui_strings(lang)
    direction = "rtl" if lang in RTL_LANGS else "ltr"
    user = session.get("user")

    job = get_job(job_id)
    if not job:
        return redirect(url_for("index"))

    if job["status"] == "done":
        return render_template_string(
            RESULT_PAGE, filename=job["output_filename"], t=t, lang=lang, dir=direction, user=user,
        )
    if job["status"] == "error":
        return render_template_string(
            ERROR_PAGE, t=t, lang=lang, dir=direction, user=user,
            # Sunucu yeniden basladigi icin yarida kalan islerde metin bos gelir.
            error_title=job["error_title"] or t["processing_error_title"],
            error_body=job["error_body"] or t["processing_error_body"],
        )
    if job["status"] == "queued":
        ahead = queue_position(job_id)
        return render_template_string(
            STATUS_PAGE, t=t, lang=lang, dir=direction, user=user,
            status_badge=t["queued_badge"], status_title=t["queued_title"],
            status_body=t["queued_body"].format(ahead=ahead),
        )
    return render_template_string(
        STATUS_PAGE, t=t, lang=lang, dir=direction, user=user,
        status_badge=t["processing_badge"], status_title=t["processing_title"],
        status_body=t["processing_body"],
    )


@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
