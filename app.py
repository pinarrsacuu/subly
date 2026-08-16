"""
Basit web arayuzu: kullanici video yukler, arka planda transcribe.py +
burn_captions.py calisir, watermark'siz altyazili video indirilebilir hale gelir.

Calistirmak icin: python app.py
Sonra tarayicidan: http://localhost:5001
"""

import uuid
from pathlib import Path

from flask import Flask, request, render_template_string, send_from_directory

from transcribe import extract_audio, transcribe, write_srt
from burn_captions import burn
from translate import translate_segments, LANGUAGES
from ui_strings import get_ui_language, get_ui_strings, RTL_LANGS

app = Flask(__name__)

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

  nav.top { display: flex; align-items: center; justify-content: space-between; padding: 26px 0; }
  .brand { display: flex; align-items: center; gap: 10px; }
  .brand .mark { width: 28px; height: 28px; flex: none; display: block; }
  .brand .names { display: flex; flex-direction: column; line-height: 1.15; }
  .brand .product { font-family: Georgia, serif; font-weight: 700; font-size: 1.15rem; letter-spacing: -0.01em; }
  .brand .by { font-size: 0.72rem; color: var(--ink-soft); }

  .card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 18px;
    padding: 34px; box-shadow: 0 24px 54px -34px rgba(0,0,0,0.35);
  }
  .eyebrow {
    font-family: ui-monospace, monospace; font-size: 0.72rem; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--teal); margin: 0 0 14px; font-weight: 600;
  }
  h1.headline { font-size: clamp(1.7rem, 4.5vw, 2.3rem); line-height: 1.12; letter-spacing: -0.02em; margin: 0 0 12px; }
  h1.headline em { font-style: italic; color: var(--coral); }
  p.lede { color: var(--ink-soft); line-height: 1.55; margin: 0 0 30px; font-size: 1rem; }

  label { display: block; font-size: 0.82rem; color: var(--ink-soft); margin: 18px 0 8px; }
  input[type=file], select {
    width: 100%; font: inherit; font-size: 0.95rem; color: var(--ink);
    background: var(--paper); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 14px; outline: none;
  }
  select:focus, input:focus { border-color: var(--coral); }

  .btnPrimary {
    background: var(--ink); color: var(--paper); border: none; cursor: pointer;
    padding: 13px 28px; border-radius: 999px; font: inherit; font-size: 0.95rem; font-weight: 600;
    display: inline-flex; align-items: center; gap: 8px; margin-top: 26px; transition: transform 0.15s ease;
  }
  .btnPrimary:hover { transform: translateY(-2px); }

  .badge {
    display: inline-flex; align-items: center; gap: 6px; font-family: ui-monospace, monospace;
    font-size: 0.72rem; letter-spacing: 0.06em; background: var(--teal-soft); color: var(--teal);
    padding: 5px 12px; border-radius: 999px; margin-bottom: 18px;
  }

  video { width: 100%; border-radius: 12px; border: 1px solid var(--border); display: block; margin: 22px 0; }
  .btnGhost { color: var(--ink); text-decoration: none; font-size: 0.9rem; border-bottom: 1px solid var(--ink-soft); padding-bottom: 2px; }

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
  <div class="brand">
    {LOGO_SVG}
    <div class="names">
      <span class="product">Subly</span>
      <span class="by">Nexi Digital</span>
    </div>
  </div>
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
<div class="wrap">
  {NAV}
  <div class="card">
    <p class="eyebrow">{{{{ t.eyebrow|safe }}}}</p>
    <h1 class="headline">{{{{ t.headline|safe }}}}</h1>
    <p class="lede">{{{{ t.lede }}}}</p>
    <form action="/process" method="post" enctype="multipart/form-data">
      <label for="video">{{{{ t.label_video }}}}</label>
      <input type="file" id="video" name="video" accept="video/*" required>
      <label for="language">{{{{ t.label_language }}}}</label>
      <select name="language" id="language">
        {{% for value, label in languages %}}
          <option value="{{{{ value }}}}">{{{{ label }}}}</option>
        {{% endfor %}}
      </select>
      <button type="submit" class="btnPrimary">{{{{ t.button_process|safe }}}}</button>
    </form>
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


@app.route("/")
def index():
    lang = get_ui_language(request.accept_languages)
    t = get_ui_strings(lang)
    direction = "rtl" if lang in RTL_LANGS else "ltr"
    return render_template_string(UPLOAD_FORM, languages=LANGUAGES, t=t, lang=lang, dir=direction)


@app.route("/process", methods=["POST"])
def process():
    lang = get_ui_language(request.accept_languages)
    t = get_ui_strings(lang)
    direction = "rtl" if lang in RTL_LANGS else "ltr"

    uploaded = request.files["video"]
    target_language = request.form.get("language", "original")
    job_id = uuid.uuid4().hex[:8]

    video_path = UPLOAD_DIR / f"{job_id}_{uploaded.filename}"
    uploaded.save(video_path)

    audio_path = extract_audio(video_path)
    segments = transcribe(audio_path)
    if target_language != "original":
        segments = translate_segments(segments, target_language)
    srt_path = video_path.with_suffix(".srt")
    write_srt(segments, srt_path)
    audio_path.unlink()

    output_filename = f"{job_id}_captioned.mp4"
    output_path = OUTPUT_DIR / output_filename
    burn(video_path, srt_path, output_path)

    return render_template_string(RESULT_PAGE, filename=output_filename, t=t, lang=lang, dir=direction)


@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
