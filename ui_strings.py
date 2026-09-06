"""
Site arayuzunun (buton, baslik, etiket metinleri) cok dilli metinleri.
Altyazi diliyle (translate.py) karistirilmasin - bu, sitenin kendi dilidir,
ziyaretcinin bulundugu ulkeye (IP) gore, bulunamazsa tarayici diline gore secilir.
"""

import json
import urllib.request
from typing import Optional

SUPPORTED_UI_LANGS = ["en", "es", "pt", "fr", "de", "it", "tr", "ar", "hi", "zh", "ja", "ko", "ru", "id"]
RTL_LANGS = {"ar"}

# ISO 3166-1 alpha-2 ulke kodu -> arayuz dili
COUNTRY_TO_LANG = {
    "US": "en", "GB": "en", "CA": "en", "AU": "en", "NZ": "en", "IE": "en", "ZA": "en",
    "ES": "es", "MX": "es", "AR": "es", "CO": "es", "CL": "es", "PE": "es", "VE": "es",
    "EC": "es", "GT": "es", "CU": "es", "BO": "es", "DO": "es", "HN": "es", "PY": "es",
    "SV": "es", "NI": "es", "CR": "es", "PA": "es", "UY": "es", "PR": "es",
    "PT": "pt", "BR": "pt",
    "FR": "fr", "BE": "fr", "LU": "fr", "MC": "fr",
    "DE": "de", "AT": "de", "CH": "de",
    "IT": "it", "SM": "it", "VA": "it",
    "TR": "tr",
    "SA": "ar", "AE": "ar", "EG": "ar", "IQ": "ar", "JO": "ar", "KW": "ar", "QA": "ar",
    "BH": "ar", "OM": "ar", "YE": "ar", "SY": "ar", "LB": "ar", "LY": "ar", "TN": "ar",
    "DZ": "ar", "MA": "ar", "SD": "ar",
    "IN": "hi",
    "CN": "zh", "HK": "zh", "TW": "zh", "MO": "zh",
    "JP": "ja",
    "KR": "ko", "KP": "ko",
    "RU": "ru", "BY": "ru", "KZ": "ru",
    "ID": "id",
}


def get_client_ip(request) -> str:
    forwarded = request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or ""


def get_country_lang(ip: str) -> Optional[str]:
    if not ip or ip.startswith(("127.", "10.", "192.168.", "::1")):
        return None
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,countryCode"
        with urllib.request.urlopen(url, timeout=1.5) as response:
            data = json.loads(response.read().decode("utf-8"))
        if data.get("status") == "success":
            return COUNTRY_TO_LANG.get(data.get("countryCode"))
    except Exception:
        return None
    return None

UI_STRINGS = {
    "en": {
        "eyebrow": "Watermark-Free &middot; Flat Price &middot; Multilingual",
        "headline": "Stylish captions for your video in <em>seconds</em>.",
        "lede": "Upload your video, pick a language, download watermark-free.",
        "label_video": "Video file",
        "label_language": "Caption language",
        "label_email": "Email address",
        "button_process": "Process &rarr;",
        "badge_ready": "&#10003; Ready",
        "result_headline": "Your video is <em>ready</em>.",
        "download": "Download &darr;",
        "back_link": "Process another video &rarr;",
        "error_limit_title": "You've used this month's free videos",
        "error_limit_body": "Free plan includes {limit} videos per month. Paid plans are coming soon — check back shortly!",
        "error_duration_title": "Video is too long",
        "error_duration_body": "Free plan supports videos up to {max_min} minutes. Try a shorter clip, or wait for paid plans.",
        "footer": "Subly is built by Nexi Digital.",
    },
    "es": {
        "eyebrow": "Sin Marca de Agua &middot; Precio Fijo &middot; Multiidioma",
        "headline": "Subtitulos con estilo en <em>segundos</em>.",
        "lede": "Sube tu video, elige un idioma, descarga sin marca de agua.",
        "label_video": "Archivo de video",
        "label_language": "Idioma de subtitulos",
        "label_email": "Correo electronico",
        "button_process": "Procesar &rarr;",
        "badge_ready": "&#10003; Listo",
        "result_headline": "Tu video esta <em>listo</em>.",
        "download": "Descargar &darr;",
        "back_link": "Procesar otro video &rarr;",
        "error_limit_title": "Ya usaste tus videos gratis de este mes",
        "error_limit_body": "El plan gratuito incluye {limit} videos al mes. Los planes de pago llegan pronto.",
        "error_duration_title": "El video es demasiado largo",
        "error_duration_body": "El plan gratuito admite videos de hasta {max_min} minutos. Prueba un clip mas corto.",
        "footer": "Subly esta construido por Nexi Digital.",
    },
    "pt": {
        "eyebrow": "Sem Marca d'Agua &middot; Preco Fixo &middot; Multilingue",
        "headline": "Legendas estilosas em <em>segundos</em>.",
        "lede": "Envie seu video, escolha um idioma, baixe sem marca d'agua.",
        "label_video": "Arquivo de video",
        "label_language": "Idioma da legenda",
        "label_email": "Endereco de email",
        "button_process": "Processar &rarr;",
        "badge_ready": "&#10003; Pronto",
        "result_headline": "Seu video esta <em>pronto</em>.",
        "download": "Baixar &darr;",
        "back_link": "Processar outro video &rarr;",
        "error_limit_title": "Voce ja usou seus videos gratis deste mes",
        "error_limit_body": "O plano gratuito inclui {limit} videos por mes. Os planos pagos chegam em breve.",
        "error_duration_title": "O video e muito longo",
        "error_duration_body": "O plano gratuito aceita videos de ate {max_min} minutos. Tente um video mais curto.",
        "footer": "Subly e desenvolvido pela Nexi Digital.",
    },
    "fr": {
        "eyebrow": "Sans Filigrane &middot; Prix Fixe &middot; Multilingue",
        "headline": "Des sous-titres stylises en <em>secondes</em>.",
        "lede": "Importez votre video, choisissez une langue, telechargez sans filigrane.",
        "label_video": "Fichier video",
        "label_language": "Langue des sous-titres",
        "label_email": "Adresse email",
        "button_process": "Traiter &rarr;",
        "badge_ready": "&#10003; Pret",
        "result_headline": "Votre video est <em>prete</em>.",
        "download": "Telecharger &darr;",
        "back_link": "Traiter une autre video &rarr;",
        "error_limit_title": "Vous avez utilise vos videos gratuites ce mois-ci",
        "error_limit_body": "Le plan gratuit inclut {limit} videos par mois. Les plans payants arrivent bientot.",
        "error_duration_title": "La video est trop longue",
        "error_duration_body": "Le plan gratuit accepte des videos jusqu'a {max_min} minutes. Essayez un clip plus court.",
        "footer": "Subly est developpe par Nexi Digital.",
    },
    "de": {
        "eyebrow": "Ohne Wasserzeichen &middot; Festpreis &middot; Mehrsprachig",
        "headline": "Stilvolle Untertitel in <em>Sekunden</em>.",
        "lede": "Video hochladen, Sprache waehlen, ohne Wasserzeichen herunterladen.",
        "label_video": "Videodatei",
        "label_language": "Untertitelsprache",
        "label_email": "E-Mail-Adresse",
        "button_process": "Verarbeiten &rarr;",
        "badge_ready": "&#10003; Fertig",
        "result_headline": "Dein Video ist <em>fertig</em>.",
        "download": "Herunterladen &darr;",
        "back_link": "Weiteres Video verarbeiten &rarr;",
        "error_limit_title": "Du hast deine kostenlosen Videos fur diesen Monat aufgebraucht",
        "error_limit_body": "Der kostenlose Plan umfasst {limit} Videos pro Monat. Bezahlplane kommen bald.",
        "error_duration_title": "Video ist zu lang",
        "error_duration_body": "Der kostenlose Plan unterstuetzt Videos bis zu {max_min} Minuten. Versuch einen kuerzeren Clip.",
        "footer": "Subly wird von Nexi Digital entwickelt.",
    },
    "it": {
        "eyebrow": "Senza Filigrana &middot; Prezzo Fisso &middot; Multilingua",
        "headline": "Sottotitoli eleganti in <em>secondi</em>.",
        "lede": "Carica il video, scegli una lingua, scarica senza filigrana.",
        "label_video": "File video",
        "label_language": "Lingua sottotitoli",
        "label_email": "Indirizzo email",
        "button_process": "Elabora &rarr;",
        "badge_ready": "&#10003; Pronto",
        "result_headline": "Il tuo video e <em>pronto</em>.",
        "download": "Scarica &darr;",
        "back_link": "Elabora un altro video &rarr;",
        "error_limit_title": "Hai usato i video gratuiti di questo mese",
        "error_limit_body": "Il piano gratuito include {limit} video al mese. I piani a pagamento arrivano presto.",
        "error_duration_title": "Il video e troppo lungo",
        "error_duration_body": "Il piano gratuito supporta video fino a {max_min} minuti. Prova una clip piu corta.",
        "footer": "Subly e sviluppato da Nexi Digital.",
    },
    "tr": {
        "eyebrow": "Watermark'siz &middot; Sabit Fiyat &middot; Cok Dilli",
        "headline": "Videona <em>saniyeler icinde</em> stilli altyazi.",
        "lede": "Videonu yukle, dilini sec, watermark'siz olarak indir.",
        "label_video": "Video dosyasi",
        "label_language": "Altyazi dili",
        "label_email": "E-posta adresi",
        "button_process": "Isle &rarr;",
        "badge_ready": "&#10003; Hazir",
        "result_headline": "Video<em>n</em> hazir.",
        "download": "Indir &darr;",
        "back_link": "Baska video isle &rarr;",
        "error_limit_title": "Bu ayki ucretsiz video hakkini kullandin",
        "error_limit_body": "Ucretsiz plan ayda {limit} video icerir. Ucretli planlar yakinda geliyor!",
        "error_duration_title": "Video cok uzun",
        "error_duration_body": "Ucretsiz planda videolar en fazla {max_min} dakika olabilir. Daha kisa bir video dene.",
        "footer": "Subly, Nexi Digital tarafindan gelistirilmistir.",
    },
    "ar": {
        "eyebrow": "بدون علامة مائية &middot; سعر ثابت &middot; متعدد اللغات",
        "headline": "ترجمات أنيقة لفيديوك في <em>ثوانٍ</em>.",
        "lede": "ارفع الفيديو، اختر اللغة، وحمّله بدون علامة مائية.",
        "label_video": "ملف الفيديو",
        "label_language": "لغة الترجمة",
        "label_email": "البريد الإلكتروني",
        "button_process": "معالجة &larr;",
        "badge_ready": "&#10003; جاهز",
        "result_headline": "فيديوك <em>جاهز</em>.",
        "download": "تحميل &darr;",
        "back_link": "معالجة فيديو آخر &larr;",
        "error_limit_title": "لقد استخدمت فيديوهاتك المجانية لهذا الشهر",
        "error_limit_body": "تشمل الخطة المجانية {limit} فيديو شهريًا. الخطط المدفوعة قادمة قريبًا.",
        "error_duration_title": "الفيديو طويل جدًا",
        "error_duration_body": "تدعم الخطة المجانية فيديوهات حتى {max_min} دقيقة. جرب مقطعًا أقصر.",
        "footer": "تم تطوير Subly بواسطة Nexi Digital.",
    },
    "hi": {
        "eyebrow": "वॉटरमार्क-मुक्त &middot; निश्चित मूल्य &middot; बहुभाषी",
        "headline": "आपके वीडियो के लिए <em>सेकंडों</em> में स्टाइलिश कैप्शन।",
        "lede": "वीडियो अपलोड करें, भाषा चुनें, वॉटरमार्क-मुक्त डाउनलोड करें।",
        "label_video": "वीडियो फ़ाइल",
        "label_language": "कैप्शन भाषा",
        "label_email": "ईमेल पता",
        "button_process": "प्रोसेस करें &rarr;",
        "badge_ready": "&#10003; तैयार",
        "result_headline": "आपका वीडियो <em>तैयार</em> है।",
        "download": "डाउनलोड करें &darr;",
        "back_link": "एक और वीडियो प्रोसेस करें &rarr;",
        "error_limit_title": "आपने इस महीने के मुफ़्त वीडियो इस्तेमाल कर लिए हैं",
        "error_limit_body": "मुफ़्त योजना में हर महीने {limit} वीडियो शामिल हैं। सशुल्क योजनाएं जल्द आ रही हैं।",
        "error_duration_title": "वीडियो बहुत लंबा है",
        "error_duration_body": "मुफ़्त योजना में {max_min} मिनट तक के वीडियो चलते हैं। एक छोटा क्लिप आज़माएं।",
        "footer": "Subly, Nexi Digital द्वारा बनाया गया है।",
    },
    "zh": {
        "eyebrow": "无水印 &middot; 固定价格 &middot; 多语言",
        "headline": "几<em>秒钟</em>内为你的视频添加精美字幕。",
        "lede": "上传视频，选择语言，无水印下载。",
        "label_video": "视频文件",
        "label_language": "字幕语言",
        "label_email": "电子邮箱",
        "button_process": "处理 &rarr;",
        "badge_ready": "&#10003; 已完成",
        "result_headline": "你的视频已<em>完成</em>。",
        "download": "下载 &darr;",
        "back_link": "处理另一个视频 &rarr;",
        "error_limit_title": "本月免费视频额度已用完",
        "error_limit_body": "免费计划每月包含 {limit} 个视频。付费计划即将推出。",
        "error_duration_title": "视频太长",
        "error_duration_body": "免费计划支持最长 {max_min} 分钟的视频。请尝试更短的片段。",
        "footer": "Subly 由 Nexi Digital 开发。",
    },
    "ja": {
        "eyebrow": "透かしなし &middot; 定額料金 &middot; 多言語対応",
        "headline": "<em>数秒</em>でスタイリッシュな字幕。",
        "lede": "動画をアップロードし、言語を選んで、透かしなしでダウンロード。",
        "label_video": "動画ファイル",
        "label_language": "字幕の言語",
        "label_email": "メールアドレス",
        "button_process": "処理する &rarr;",
        "badge_ready": "&#10003; 完了",
        "result_headline": "動画の準備が<em>できました</em>。",
        "download": "ダウンロード &darr;",
        "back_link": "別の動画を処理する &rarr;",
        "error_limit_title": "今月の無料動画枠を使い切りました",
        "error_limit_body": "無料プランは月に{limit}本まで利用できます。有料プランは近日公開予定です。",
        "error_duration_title": "動画が長すぎます",
        "error_duration_body": "無料プランは最大{max_min}分の動画に対応しています。短い動画をお試しください。",
        "footer": "Subly は Nexi Digital が開発しています。",
    },
    "ko": {
        "eyebrow": "워터마크 없음 &middot; 고정 요금 &middot; 다국어 지원",
        "headline": "<em>몇 초 만에</em> 스타일리시한 자막.",
        "lede": "동영상을 업로드하고, 언어를 선택하고, 워터마크 없이 다운로드하세요.",
        "label_video": "동영상 파일",
        "label_language": "자막 언어",
        "label_email": "이메일 주소",
        "button_process": "처리하기 &rarr;",
        "badge_ready": "&#10003; 완료",
        "result_headline": "동영상이 <em>준비</em>되었습니다.",
        "download": "다운로드 &darr;",
        "back_link": "다른 동영상 처리하기 &rarr;",
        "error_limit_title": "이번 달 무료 동영상을 모두 사용했습니다",
        "error_limit_body": "무료 플랜은 월 {limit}개의 동영상을 제공합니다. 유료 플랜이 곧 출시됩니다.",
        "error_duration_title": "동영상이 너무 깁니다",
        "error_duration_body": "무료 플랜은 최대 {max_min}분 동영상을 지원합니다. 더 짧은 클립을 시도해 보세요.",
        "footer": "Subly는 Nexi Digital이 개발했습니다.",
    },
    "ru": {
        "eyebrow": "Без Водяного Знака &middot; Фиксированная Цена &middot; Многоязычный",
        "headline": "Стильные субтитры за <em>секунды</em>.",
        "lede": "Загрузите видео, выберите язык, скачайте без водяного знака.",
        "label_video": "Видеофайл",
        "label_language": "Язык субтитров",
        "label_email": "Электронная почта",
        "button_process": "Обработать &rarr;",
        "badge_ready": "&#10003; Готово",
        "result_headline": "Ваше видео <em>готово</em>.",
        "download": "Скачать &darr;",
        "back_link": "Обработать другое видео &rarr;",
        "error_limit_title": "Вы использовали бесплатные видео за этот месяц",
        "error_limit_body": "Бесплатный план включает {limit} видео в месяц. Платные планы скоро появятся.",
        "error_duration_title": "Видео слишком длинное",
        "error_duration_body": "Бесплатный план поддерживает видео до {max_min} минут. Попробуйте более короткий ролик.",
        "footer": "Subly разработан Nexi Digital.",
    },
    "id": {
        "eyebrow": "Tanpa Watermark &middot; Harga Tetap &middot; Multibahasa",
        "headline": "Teks bergaya untuk videomu dalam <em>hitungan detik</em>.",
        "lede": "Unggah videomu, pilih bahasa, unduh tanpa watermark.",
        "label_video": "File video",
        "label_language": "Bahasa teks",
        "label_email": "Alamat email",
        "button_process": "Proses &rarr;",
        "badge_ready": "&#10003; Siap",
        "result_headline": "Videomu sudah <em>siap</em>.",
        "download": "Unduh &darr;",
        "back_link": "Proses video lain &rarr;",
        "error_limit_title": "Kamu sudah memakai jatah video gratis bulan ini",
        "error_limit_body": "Paket gratis mencakup {limit} video per bulan. Paket berbayar segera hadir.",
        "error_duration_title": "Video terlalu panjang",
        "error_duration_body": "Paket gratis mendukung video hingga {max_min} menit. Coba klip yang lebih pendek.",
        "footer": "Subly dikembangkan oleh Nexi Digital.",
    },
}


def get_ui_language(accept_languages, ip: str = "") -> str:
    country_lang = get_country_lang(ip)
    if country_lang:
        return country_lang
    match = accept_languages.best_match(SUPPORTED_UI_LANGS)
    return match or "en"


def get_ui_strings(lang: str) -> dict:
    return UI_STRINGS.get(lang, UI_STRINGS["en"])
