"""
Basit web arayuzu: kullanici video yukler, arka planda transcribe.py +
burn_captions.py calisir, watermark'siz altyazili video indirilebilir hale gelir.

Calistirmak icin: python app.py
Sonra tarayicidan: http://localhost:5001
"""

import os
import threading
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
    get_remaining, record_usage, init_db, upsert_user, get_user_plan, PLAN_LIMITS,
    PRO_PRICE_TRY, PREMIUM_PRICE_TRY,
)
from jobs import init_jobs_db, create_job, get_job, mark_processing, mark_done, mark_error
from notify import send_ready_email, send_error_email

app = Flask(__name__)
# Render/Cloudflare HTTPS'i sonlandirip Flask'a duz HTTP olarak iletiyor - bu
# olmadan url_for(_external=True) (ornegin Google OAuth callback adresi) yanlislikla
# http:// uretip Google'in "redirect_uri_mismatch" hatasina yol aciyordu.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ["SECRET_KEY"]
init_db()
init_jobs_db()
init_auth(app)

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Nexi Digital marka kimligi: renkler, fontlar, logo mark'i mevcut kurumsal
# siteden (Nexi Digital) alindi, boylece Subly ayni ailenin bir urunu gibi durur.
BRAND_HEAD = """
<style>
  :root {
    --paper: #F1ECE6;
    --ink: #241B2E;
    --ink-soft: #6B5F72;
    --coral: #D6455C;
    --coral-soft: rgba(214, 69, 92, 0.12);
    --teal: #17948C;
    --teal-soft: rgba(23, 148, 140, 0.12);
    --surface: #FBF9F6;
    --border: rgba(36, 27, 46, 0.14);
    color-scheme: light dark;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --paper: #1A1420; --ink: #F3EFEF; --ink-soft: #B9AEC2;
      --coral: #FF7C8E; --coral-soft: rgba(255, 124, 142, 0.14);
      --teal: #3FD9CE; --teal-soft: rgba(63, 217, 206, 0.14);
      --surface: #241B2E; --border: rgba(243, 239, 239, 0.14);
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--paper); color: var(--ink);
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  h1, h2 { font-family: Georgia, "Iowan Old Style", "Times New Roman", serif; }
  .mono { font-family: ui-monospace, "SF Mono", "Cascadia Code", monospace; }
  .wrap { max-width: 640px; margin: 0 auto; padding: 0 24px; }
  .heroOuter { max-width: 1080px; margin: 0 auto; padding: 0 24px; }
  .splitRow { display: block; }
  @media (min-width: 860px) {
    .splitRow { display: flex; align-items: center; gap: 56px; }
    .splitRow > .half { flex: 1 1 50%; min-width: 0; }
  }
  .heroBanner { padding: 40px; }
  .heroBanner .demoWrap { margin: 40px 0 0; }
  @media (min-width: 860px) {
    .heroBanner { padding: 48px; }
    .heroBanner .demoWrap { margin: 0; }
  }
  .contentSection { margin-top: 48px; }
  .contentRow { margin: 8px 0 0; }
  .contentRow .stepsPanel { padding: 6px 0; }
  .contentRow .stepGrid { grid-template-columns: 1fr; gap: 26px; }
  .contentRow .step { text-align: left; }
  .contentRow .sectionTitle { text-align: left; }

  nav.top { display: flex; align-items: center; justify-content: space-between; padding: 26px 0; flex-wrap: wrap; gap: 12px; }
  .userBox { display: flex; align-items: center; gap: 10px; }
  .userAvatar { width: 30px; height: 30px; border-radius: 50%; display: block; }
  .userName { font-size: 0.85rem; color: var(--ink-soft); }
  .navLogin { margin-top: 0; padding: 9px 18px; font-size: 0.85rem; }
  .brand { display: flex; align-items: center; gap: 10px; text-decoration: none; color: inherit; }
  .brand .mark { width: 40px; height: 40px; flex: none; display: block; }
  .brand .names { display: flex; flex-direction: column; line-height: 1.15; }
  .brand .product { font-family: Georgia, serif; font-weight: 700; font-size: 1.5rem; letter-spacing: -0.01em; }
  .brand .by { font-size: 0.82rem; color: var(--ink-soft); }

  .card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 22px;
    padding: 36px 32px; box-shadow: 0 32px 64px -36px rgba(0,0,0,0.32);
  }
  .eyebrow {
    font-family: ui-monospace, monospace; font-size: 0.72rem; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--teal); margin: 0 0 14px; font-weight: 600;
  }
  @media (max-width: 420px) {
    .eyebrow { font-size: 0.62rem; letter-spacing: 0.06em; }
  }
  h1.headline { font-size: clamp(1.9rem, 5.5vw, 2.7rem); line-height: 1.08; letter-spacing: -0.03em; margin: 0 0 14px; }
  h1.headline em { font-style: italic; color: var(--coral); }
  p.lede { color: var(--ink-soft); line-height: 1.55; margin: 0 0 30px; font-size: 1rem; }

  label { display: block; font-size: 0.82rem; color: var(--ink-soft); margin: 18px 0 8px; }
  input[type=file], input[type=email], select {
    width: 100%; font: inherit; font-size: 0.95rem; color: var(--ink);
    background: var(--paper); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 14px; outline: none;
  }
  select:focus, input:focus { border-color: var(--coral); }

  .checkboxRow {
    display: flex; align-items: center; gap: 8px; margin: 18px 0 4px;
    font-size: 0.86rem; color: var(--ink); cursor: pointer;
  }
  .checkboxRow input { width: auto; margin: 0; }
  .checkboxHint { margin: 0 0 4px; font-size: 0.76rem; color: var(--ink-soft); }
  .subsPreview { margin: 10px 0 4px; }
  .subsPreviewTag {
    display: inline-block; font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.04em; color: var(--ink-soft); margin-bottom: 6px;
  }
  .subsPreviewFrame {
    position: relative; height: 84px; border-radius: 10px; overflow: hidden;
    background: linear-gradient(135deg, #3a2d47, #241b2e);
  }
  .subsPreviewOld, .subsPreviewNew {
    position: absolute; left: 0; right: 0; text-align: center;
    font-size: 0.78rem; font-weight: 600; color: #fff;
    text-shadow: 0 1px 3px rgba(0,0,0,0.7);
  }
  .subsPreviewOld { bottom: 22px; transition: opacity 0.2s ease; }
  .subsPreviewNew { bottom: 10px; }
  .subsPreviewBar {
    position: absolute; left: 0; right: 0; bottom: 4px; height: 26px;
    background: rgba(15, 12, 20, 0.94); border-radius: 4px;
    opacity: 0; transition: opacity 0.2s ease;
  }
  .subsPreview.covered .subsPreviewOld { opacity: 0; }
  .subsPreview.covered .subsPreviewBar { opacity: 1; }

  .btnPrimary {
    background: var(--ink); color: var(--paper); border: none; cursor: pointer;
    padding: 13px 28px; border-radius: 999px; font: inherit; font-size: 0.95rem; font-weight: 600;
    display: inline-flex; align-items: center; gap: 8px; margin-top: 26px; transition: transform 0.15s ease;
  }
  .btnPrimary:hover { transform: translateY(-2px); }

  .btnHero {
    display: inline-flex; align-items: center; gap: 8px; margin-top: 22px;
    background: transparent; color: var(--coral); border: 1.5px solid var(--coral); cursor: pointer;
    padding: 11px 24px; border-radius: 999px; font: inherit; font-size: 0.92rem; font-weight: 600;
    text-decoration: none; transition: transform 0.15s ease, background 0.15s ease;
  }
  .btnHero:hover { transform: translateY(-2px); background: var(--coral-soft); }

  .badge {
    display: inline-flex; align-items: center; gap: 6px; font-family: ui-monospace, monospace;
    font-size: 0.72rem; letter-spacing: 0.06em; background: var(--teal-soft); color: var(--teal);
    padding: 5px 12px; border-radius: 999px; margin-bottom: 18px;
  }

  video { width: 100%; border-radius: 12px; border: 1px solid var(--border); display: block; margin: 22px 0; }
  .btnGhost { color: var(--ink); text-decoration: none; font-size: 0.9rem; border-bottom: 1px solid var(--ink-soft); padding-bottom: 2px; }

  .freeNote {
    display: inline-block; font-size: 0.8rem; color: var(--ink-soft);
    background: var(--teal-soft); border-radius: 10px; padding: 7px 12px; margin-top: 14px;
  }
  .formNote {
    font-size: 0.78rem; color: var(--ink-soft); margin: 10px 0 0; text-align: center;
  }

  .demoWrap { display: flex; flex-direction: column; align-items: center; margin: 56px 0; }
  .demoFrame {
    width: 210px; aspect-ratio: 9 / 16; border-radius: 28px; position: relative; overflow: hidden;
    background: linear-gradient(160deg, var(--ink) 0%, var(--teal) 140%);
    border: 1px solid var(--border); box-shadow: 0 40px 70px -32px rgba(0,0,0,0.42);
  }
  .demoCaption {
    position: absolute; left: 12px; right: 12px; bottom: 22px;
    background: rgba(0,0,0,0.55); color: #fff; font-weight: 700; font-size: 0.82rem; line-height: 1.35;
    padding: 9px 10px; border-radius: 10px; text-align: center; border: 2px solid var(--coral);
  }
  .demoTime {
    position: absolute; top: 12px; left: 12px; background: rgba(0,0,0,0.4); color: #fff;
    font-family: ui-monospace, monospace; font-size: 0.68rem; padding: 3px 8px; border-radius: 999px;
  }
  .demoPlay {
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -62%);
    width: 46px; height: 46px; border-radius: 50%; background: rgba(255,255,255,0.22);
    display: flex; align-items: center; justify-content: center;
  }
  .demoPlay::after {
    content: ""; border-style: solid; border-width: 8px 0 8px 13px;
    border-color: transparent transparent transparent #fff; margin-left: 3px;
  }
  .demoLabel { margin-top: 14px; font-size: 0.78rem; color: var(--ink-soft); }

  .sectionTitle {
    font-family: Georgia, serif; font-size: 1.25rem; text-align: center; margin: 0 0 22px;
  }
  .stepGrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }
  .step { text-align: center; padding: 0 6px; }
  .stepNum {
    display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px;
    border-radius: 50%; background: var(--coral-soft); color: var(--coral); font-weight: 700;
    font-size: 0.86rem; margin-bottom: 12px;
  }
  .step h3 { font-size: 0.94rem; margin: 4px 0 6px; }
  .step p { font-size: 0.83rem; color: var(--ink-soft); margin: 0; line-height: 1.45; }

  .pricing { margin: 56px 0 0; }
  .planGrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
  .planCard {
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
    padding: 22px; position: relative; cursor: pointer;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  }
  .planCard:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px -12px rgba(36, 27, 46, 0.25);
  }
  .planCard.selected {
    border-color: var(--coral); box-shadow: 0 12px 28px -14px rgba(214, 69, 92, 0.4);
  }
  .planCard.selected::after {
    content: "✓"; position: absolute; top: 14px; right: 16px;
    color: var(--coral); font-weight: 700;
  }
  .planCard h3 { margin: 0 0 8px; font-family: Georgia, serif; font-size: 1.05rem; }
  .planPrice { font-size: 1.6rem; font-weight: 700; margin: 0 0 10px; }
  .planPrice span { font-size: 0.8rem; font-weight: 400; color: var(--ink-soft); }
  .planCard p:last-child { font-size: 0.85rem; color: var(--ink-soft); margin: 0; line-height: 1.5; }
  .planPro { border-color: var(--coral); }
  .planBadge {
    display: inline-block; background: var(--coral-soft); color: var(--coral);
    font-size: 0.62rem; font-weight: 700; padding: 3px 9px; border-radius: 999px;
    text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 8px;
  }
  @media (max-width: 560px) {
    .planGrid { grid-template-columns: 1fr; }
  }

  .trustNote {
    margin: 18px auto 0; max-width: 640px; text-align: center;
    font-size: 0.82rem; color: var(--ink-soft); line-height: 1.5;
  }

  .faq { margin: 56px 0 8px; }
  .faq details {
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    padding: 14px 18px; margin-bottom: 10px;
  }
  .faq summary { cursor: pointer; font-weight: 600; font-size: 0.92rem; list-style: none; }
  .faq summary::-webkit-details-marker { display: none; }
  .faq summary::after { content: "+"; float: right; color: var(--teal); font-weight: 700; }
  .faq details[open] summary::after { content: "\\2212"; }
  .faq p { margin: 10px 0 0; color: var(--ink-soft); font-size: 0.88rem; line-height: 1.55; }

  @media (max-width: 560px) {
    .stepGrid { grid-template-columns: 1fr; }
  }

  footer.siteFoot { padding: 30px 0 48px; font-size: 0.8rem; color: var(--ink-soft); text-align: center; }
  footer.siteFoot a { color: inherit; }
</style>
"""

LOGO_SVG = """
<svg class="mark" viewBox="0 0 100 100" aria-hidden="true">
  <defs>
    <linearGradient id="mark" x1="22" y1="18" x2="78" y2="82" gradientUnits="userSpaceOnUse">
      <stop offset="0.42" stop-color="var(--coral)"/>
      <stop offset="0.58" stop-color="var(--teal)"/>
    </linearGradient>
  </defs>
  <g fill="none" stroke="var(--ink-soft)" stroke-opacity="0.4" stroke-width="5" stroke-linecap="round">
    <line x1="22" y1="18" x2="22" y2="82"/>
    <line x1="22" y1="18" x2="50" y2="50"/>
    <line x1="50" y1="50" x2="78" y2="82"/>
    <line x1="78" y1="18" x2="78" y2="82"/>
  </g>
  <circle cx="22" cy="18" r="9" fill="var(--coral)"/>
  <circle cx="22" cy="82" r="9" fill="var(--coral)"/>
  <circle cx="78" cy="18" r="9" fill="var(--teal)"/>
  <circle cx="78" cy="82" r="9" fill="var(--teal)"/>
  <circle cx="50" cy="50" r="11" fill="url(#mark)"/>
</svg>
"""

NAV = f"""
<nav class="top">
  <a class="brand" href="/">
    {LOGO_SVG}
    <div class="names">
      <span class="product">Subly</span>
      <span class="by">Nexi Digital</span>
    </div>
  </a>
  {{% if user %}}
    <div class="userBox">
      <img class="userAvatar" src="{{{{ user.picture }}}}" alt="">
      <span class="userName">{{{{ user.name }}}}</span>
      <a href="/logout" class="btnGhost">{{{{ t.logout }}}}</a>
    </div>
  {{% else %}}
    <a href="/login/google" class="btnHero navLogin">{{{{ t.login_google }}}}</a>
  {{% endif %}}
</nav>
"""

UPLOAD_FORM = f"""
<!doctype html>
<html lang="{{{{ lang }}}}" dir="{{{{ dir }}}}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Subly — Nexi Digital</title>
  {BRAND_HEAD}
</head>
<body>
<div class="heroOuter">
  {NAV}
  <div class="card heroBanner">
    <div class="splitRow">
      <div class="half">
        <p class="eyebrow">{{{{ t.eyebrow|safe }}}}</p>
        <h1 class="headline">{{{{ t.headline|safe }}}}</h1>
        <p class="lede">{{{{ t.lede }}}}</p>
        <a href="#uploadForm" class="btnHero">{{{{ t.cta_scroll }}}}</a>
        <p class="freeNote">{{{{ t.free_note|safe }}}}</p>
      </div>

      <div class="half demoWrap">
        <div class="demoFrame">
          <span class="demoTime">0:07</span>
          <span class="demoPlay"></span>
          <div class="demoCaption">{{{{ t.demo_caption }}}}</div>
        </div>
        <p class="demoLabel">{{{{ t.demo_label }}}}</p>
      </div>
    </div>
  </div>
</div>

<div class="heroOuter contentSection">
  <div class="splitRow contentRow">
    <div class="half card" id="uploadForm">
      {{% if user %}}
        <form action="/process" method="post" enctype="multipart/form-data">
          <label for="video">{{{{ t.label_video }}}}</label>
          <input type="file" id="video" name="video" accept="video/*" required>
          <label for="language">{{{{ t.label_language }}}}</label>
          <select name="language" id="language">
            {{% for value, label in languages %}}
              <option value="{{{{ value }}}}">{{{{ label }}}}</option>
            {{% endfor %}}
          </select>

          <label class="checkboxRow" for="coverSubs">
            <input type="checkbox" id="coverSubs" name="cover_subs" onchange="toggleSubsPreview(this)">
            {{{{ t.cover_subs_label }}}}
          </label>
          <p class="checkboxHint">{{{{ t.cover_subs_hint }}}}</p>

          <div class="subsPreview" id="subsPreviewBox">
            <div class="subsPreviewCol">
              <span class="subsPreviewTag" id="subsPreviewTag">{{{{ t.cover_subs_before }}}}</span>
              <div class="subsPreviewFrame">
                <span class="subsPreviewOld">こんにちは</span>
                <span class="subsPreviewBar"></span>
                <span class="subsPreviewNew">Hola, ¿qué tal?</span>
              </div>
            </div>
          </div>

          <button type="submit" class="btnPrimary">{{{{ t.button_process|safe }}}}</button>
          <p class="formNote">{{{{ t.free_note|safe }}}}</p>
        </form>
        <script>
          function toggleSubsPreview(cb) {{
            var box = document.getElementById("subsPreviewBox");
            var tag = document.getElementById("subsPreviewTag");
            if (cb.checked) {{
              box.classList.add("covered");
              tag.textContent = "{{{{ t.cover_subs_after }}}}";
            }} else {{
              box.classList.remove("covered");
              tag.textContent = "{{{{ t.cover_subs_before }}}}";
            }}
          }}
        </script>
      {{% else %}}
        <p class="lede">{{{{ t.login_prompt }}}}</p>
        <a href="/login/google" class="btnPrimary">{{{{ t.login_google }}}}</a>
      {{% endif %}}
    </div>

    <div class="half stepsPanel">
      <h2 class="sectionTitle">{{{{ t.how_it_works_title }}}}</h2>
      <div class="stepGrid">
        <div class="step">
          <span class="stepNum">1</span>
          <h3>{{{{ t.step1_title }}}}</h3>
          <p>{{{{ t.step1_desc }}}}</p>
        </div>
        <div class="step">
          <span class="stepNum">2</span>
          <h3>{{{{ t.step2_title }}}}</h3>
          <p>{{{{ t.step2_desc }}}}</p>
        </div>
        <div class="step">
          <span class="stepNum">3</span>
          <h3>{{{{ t.step3_title }}}}</h3>
          <p>{{{{ t.step3_desc }}}}</p>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="wrap">
  <div class="pricing">
    <h2 class="sectionTitle">{{{{ t.pricing_title }}}}</h2>
    <div class="planGrid">
      <div class="planCard" data-plan="free" onclick="selectPlan(this, true)">
        <h3>Free</h3>
        <p class="planPrice">$0</p>
        <p>{{{{ t.free_note|safe }}}}</p>
      </div>
      <div class="planCard planPro" data-plan="pro" onclick="selectPlan(this, false)">
        <span class="planBadge">{{{{ t.pricing_soon }}}}</span>
        <h3>Pro</h3>
        <p class="planPrice">&#8378;{{{{ pro_price }}}}<span>{{{{ t.per_month }}}}</span></p>
        <p>{{{{ t.pricing_pro_desc }}}}</p>
      </div>
      <div class="planCard planPro" data-plan="premium" onclick="selectPlan(this, false)">
        <span class="planBadge">{{{{ t.pricing_soon }}}}</span>
        <h3>Premium</h3>
        <p class="planPrice">&#8378;{{{{ premium_price }}}}<span>{{{{ t.per_month }}}}</span></p>
        <p>{{{{ t.pricing_premium_desc }}}}</p>
      </div>
    </div>
    <p class="trustNote">{{{{ t.trust_note }}}}</p>
  </div>

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

  <div class="faq">
    <h2 class="sectionTitle">{{{{ t.faq_title }}}}</h2>
    <details>
      <summary>{{{{ t.faq_q1 }}}}</summary>
      <p>{{{{ t.faq_a1 }}}}</p>
    </details>
    <details>
      <summary>{{{{ t.faq_q2 }}}}</summary>
      <p>{{{{ t.faq_a2 }}}}</p>
    </details>
    <details>
      <summary>{{{{ t.faq_q3 }}}}</summary>
      <p>{{{{ t.faq_a3|safe }}}}</p>
    </details>
    <details>
      <summary>{{{{ t.faq_q4 }}}}</summary>
      <p>{{{{ t.faq_a4 }}}}</p>
    </details>
  </div>

  <footer class="siteFoot">{{{{ t.footer }}}}</footer>
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
<body>
<div class="wrap">
  {NAV}
  <div class="card">
    <span class="badge">{{{{ t.badge_ready|safe }}}}</span>
    <h1 class="headline">{{{{ t.result_headline|safe }}}}</h1>
    <video src="/outputs/{{{{ filename }}}}" controls></video>
    <a href="/outputs/{{{{ filename }}}}" download class="btnPrimary">{{{{ t.download|safe }}}}</a>
    <br><br>
    <a href="/" class="btnGhost">{{{{ t.back_link|safe }}}}</a>
  </div>
  <footer class="siteFoot">{{{{ t.footer }}}}</footer>
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
<body>
<div class="wrap">
  {NAV}
  <div class="card">
    <span class="badge">{{{{ t.processing_badge|safe }}}}</span>
    <h1 class="headline">{{{{ t.processing_title|safe }}}}</h1>
    <p class="lede">{{{{ t.processing_body }}}}</p>
  </div>
  <footer class="siteFoot">{{{{ t.footer }}}}</footer>
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
<body>
<div class="wrap">
  {NAV}
  <div class="card">
    <h1 class="headline">{{{{ error_title }}}}</h1>
    <p class="lede">{{{{ error_body }}}}</p>
    <a href="/" class="btnGhost">{{{{ t.back_link|safe }}}}</a>
  </div>
  <footer class="siteFoot">{{{{ t.footer }}}}</footer>
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
    return render_template_string(
        UPLOAD_FORM, languages=LANGUAGES, t=t, lang=lang, dir=direction, user=session.get("user"),
        pro_price=PRO_PRICE_TRY, premium_price=PREMIUM_PRICE_TRY,
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
    file_id = uuid.uuid4().hex[:8]
    limits = PLAN_LIMITS[get_user_plan(email)]

    # Plan kontrolu 1: bu ay hakki kalmis mi? Dosyayi kaydetmeden once
    # bakiyoruz ki API maliyetine hic girmeyelim.
    if get_remaining(email, limits["monthly_limit"]) <= 0:
        return render_template_string(
            ERROR_PAGE, t=t, lang=lang, dir=direction, user=user,
            error_title=t["error_limit_title"],
            error_body=t["error_limit_body"].format(limit=limits["monthly_limit"]),
        )

    video_path = UPLOAD_DIR / f"{file_id}_{uploaded.filename}"
    uploaded.save(video_path)

    # Plan kontrolu 2: video suresi sinirin altinda mi?
    duration = get_duration_seconds(video_path)
    if duration > limits["max_duration"]:
        video_path.unlink()
        return render_template_string(
            ERROR_PAGE, t=t, lang=lang, dir=direction, user=user,
            error_title=t["error_duration_title"],
            error_body=t["error_duration_body"].format(max_min=limits["max_duration"] / 60),
        )

    # Asil isleme (transkript + ceviri + altyazi yakma) arka planda bir thread'de
    # calisir - boylece uzun videolarda HTTP istegi/Cloudflare proxy timeout'una
    # takilmadan kullaniciyi hemen /status sayfasina yonlendirebiliyoruz.
    job_id = create_job(email)
    status_url = url_for("job_status", job_id=job_id, _external=True)
    thread = threading.Thread(
        target=run_job,
        args=(job_id, file_id, video_path, target_language, cover_subs, email, status_url, t),
        daemon=True,
    )
    thread.start()

    return redirect(url_for("job_status", job_id=job_id))


def run_job(job_id, file_id, video_path, target_language, cover_subs, email, status_url, t):
    mark_processing(job_id)
    try:
        audio_path = extract_audio(video_path)
        segments = transcribe(audio_path)
        if target_language != "original":
            segments = translate_segments(segments, target_language)
        srt_path = video_path.with_suffix(".srt")
        write_srt(segments, srt_path)
        audio_path.unlink()

        output_filename = f"{file_id}_captioned.mp4"
        output_path = OUTPUT_DIR / output_filename
        burn(video_path, srt_path, output_path, cover_subs=cover_subs)
        video_path.unlink()
        srt_path.unlink()

        record_usage(email)
        mark_done(job_id, output_filename)
        send_ready_email(email, status_url)
    except Exception as exc:
        mark_error(job_id, t["processing_error_title"], f'{t["processing_error_body"]} ({exc})')
        send_error_email(email, status_url)


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
            error_title=job["error_title"], error_body=job["error_body"],
        )
    return render_template_string(STATUS_PAGE, t=t, lang=lang, dir=direction, user=user)


@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
