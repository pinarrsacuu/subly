"""Yasal sayfalar: mesafeli satis, iptal ve iade, gizlilik/KVKK, iletisim.

Metinler Turk hukukuna gore yazildigi icin yalnizca Turkce. Satici bilgileri
kullanicinin istegiyle marka adiyla (sahis adi olmadan) yazildi; degisirse sadece asagidaki SELLER sozlugu guncellenir.
"""

from usage_tracker import PLAN_LIMITS, PRO_PRICE_TRY, PREMIUM_PRICE_TRY

SELLER = {
    "name": "Nexi Digital",
    "address": "Semerciler Mah. Çevik Sk. No: 2 Adapazarı / Sakarya",
    "tax_office": "Gümrükönü Vergi Dairesi",
    "email": "nexidigital.00@gmail.com",
    "phone": "0535 875 88 48",
    "site": "https://subly.nexidigitalai.com",
}

UPDATED = "2 Ekim 2026"

# (slug, Turkce etiket, diger dillerde gosterilen etiket)
PAGES = [
    ("mesafeli-satis", "Mesafeli Satış Sözleşmesi", "Terms of Sale"),
    ("iptal-iade", "İptal ve İade", "Refunds"),
    ("gizlilik", "Gizlilik ve KVKK", "Privacy"),
    ("iletisim", "İletişim", "Contact"),
]


def legal_links(lang):
    return [(slug, tr if lang == "tr" else other) for slug, tr, other in PAGES]


def _minutes(plan):
    return PLAN_LIMITS[plan]["max_duration"] // 60


def _seller_block():
    rows = [
        ("Satıcı", SELLER["name"]),
        ("Adres", SELLER["address"]),
        ("Vergi dairesi", SELLER["tax_office"]),
        ("E-posta", SELLER["email"]),
        ("Telefon", SELLER["phone"]),
        ("Site", SELLER["site"]),
    ]
    items = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows if v)
    return f"<dl>{items}</dl>"


def _plans_block():
    return f"""
<ul>
  <li><strong>Pro:</strong> aylık {PRO_PRICE_TRY} TL. Ayda {PLAN_LIMITS['pro']['monthly_limit']} video, video başına en fazla {_minutes('pro')} dakika.</li>
  <li><strong>Premium:</strong> aylık {PREMIUM_PRICE_TRY} TL. Ayda {PLAN_LIMITS['premium']['monthly_limit']} video, video başına en fazla {_minutes('premium')} dakika.</li>
</ul>
<p>Fiyatlara tüm vergiler dahildir.</p>"""


def _distance_sales():
    return f"""
<h2>1. Taraflar</h2>
{_seller_block()}
<p>Alıcı, Subly'ye Google hesabıyla giriş yapan ve ücretli bir plan satın alan kişidir. Alıcının adı ve e-posta adresi Google hesabından alınır.</p>

<h2>2. Konu</h2>
<p>Bu sözleşme, Alıcı'nın {SELLER['site']} adresinden satın aldığı Subly aboneliğinin koşullarını düzenler. Sözleşme, 6502 sayılı Tüketicinin Korunması Hakkında Kanun ve Mesafeli Sözleşmeler Yönetmeliği'ne göre hazırlanmıştır.</p>

<h2>3. Hizmet ve fiyat</h2>
<p>Subly, yüklenen videodaki konuşmayı yazıya döker, istenirse çevirir ve altyazıyı videoya gömer. Hizmet elektronik ortamda sunulur; fiziksel bir ürün gönderilmez.</p>
{_plans_block()}

<h2>4. Ödeme</h2>
<p>Ödeme, iyzico ödeme altyapısı üzerinden kredi kartı veya banka kartı ile alınır. Kart bilgileri Subly sunucularında saklanmaz. Abonelik aylıktır ve Alıcı iptal edene kadar her ay aynı tutarla yenilenir.</p>

<h2>5. Hizmetin sunulması</h2>
<p>Plan, ödeme onaylandığı anda Alıcı'nın hesabında etkinleşir. Bir videonun işlenme süresi video uzunluğuna bağlıdır. Hazır videolar 24 saat içinde indirilmelidir; bu sürenin sonunda sunucudan silinir.</p>

<h2>6. Cayma hakkı</h2>
<p>Subly, elektronik ortamda anında ifa edilen bir hizmettir. Mesafeli Sözleşmeler Yönetmeliği'nin 15. maddesine göre, Alıcı'nın onayıyla ifasına başlanan bu tür hizmetlerde cayma hakkı kullanılamaz. Alıcı, ödeme yaparak hizmetin hemen başlamasını onaylar.</p>
<p>Satıcı buna ek olarak gönüllü bir iade hakkı tanır. Koşulları <a href="/yasal/iptal-iade">İptal ve İade</a> sayfasında yazar.</p>

<h2>7. İptal</h2>
<p>Alıcı aboneliğini istediği zaman iptal edebilir. İptal, içinde bulunulan dönemin sonunda geçerli olur; o tarihe kadar plan kullanılmaya devam eder ve sonraki ay için ücret alınmaz.</p>

<h2>8. Alıcının sorumluluğu</h2>
<p>Alıcı, yüklediği videoların haklarına sahip olduğunu veya kullanma iznini aldığını kabul eder. Hukuka aykırı içerik yüklenemez.</p>

<h2>9. Uyuşmazlık</h2>
<p>Alıcı, şikâyet ve itirazlarını Ticaret Bakanlığı'nın her yıl ilan ettiği parasal sınırlar içinde, yerleşim yerindeki veya hizmeti satın aldığı yerdeki Tüketici Hakem Heyeti'ne ya da Tüketici Mahkemesi'ne yapabilir.</p>

<h2>10. Yürürlük</h2>
<p>Alıcı, ödemeyi tamamladığında bu sözleşmeyi ve ön bilgilendirmeyi okuyup kabul etmiş sayılır.</p>"""


def _refund():
    return f"""
<h2>Aboneliği iptal etmek</h2>
<p>Aboneliğini istediğin zaman iptal edebilirsin. İptal, ödediğin dönemin sonunda geçerli olur: o tarihe kadar planı kullanırsın, sonraki ay için ücret alınmaz.</p>

<h2>İade</h2>
<p>Ödemeden sonraki 3 gün içinde, o dönemde hiç video işlemediysen ödediğin tutarın tamamını iade ederiz.</p>
<p>O dönemde en az bir video işlediysen hizmet kullanılmış sayılır ve iade yapılmaz. Subly elektronik ortamda anında ifa edilen bir hizmet olduğu için, Mesafeli Sözleşmeler Yönetmeliği'nin 15. maddesi uyarınca yasal cayma hakkı bu durumda kullanılamaz.</p>

<h2>Bizden kaynaklanan sorunlar</h2>
<p>Teknik bir hata yüzünden videon işlenemediyse o video aylık hakkından düşmez. Sorun çözülemezse ve planı bu yüzden kullanamadıysan o dönemin ücretini iade ederiz.</p>

<h2>İade nasıl istenir</h2>
<p>Subly'ye giriş yaptığın e-posta adresini yazarak bize ulaş{': <a href="mailto:' + SELLER['email'] + '">' + SELLER['email'] + '</a>' if SELLER['email'] else ''}. Onaylanan iade, ödemeyi yaptığın karta 14 gün içinde geri gönderilir. Tutarın kart hesabına yansıması bankana göre birkaç gün daha sürebilir.</p>"""


def _privacy():
    return f"""
<h2>Veri sorumlusu</h2>
{_seller_block()}
<p>Bu metin, 6698 sayılı Kişisel Verilerin Korunması Kanunu'nun (KVKK) 10. maddesi uyarınca hazırlanan aydınlatma metnidir.</p>

<h2>Hangi verileri topluyoruz</h2>
<ul>
  <li><strong>Hesap bilgileri:</strong> Google ile giriş yaptığında adın, e-posta adresin ve profil fotoğrafın.</li>
  <li><strong>Videolar:</strong> yüklediğin video, içindeki ses ve bundan üretilen altyazı metni.</li>
  <li><strong>Kullanım bilgileri:</strong> planın, işlediğin video sayısı, işlem zamanları ve IP adresin.</li>
  <li><strong>Ödeme bilgileri:</strong> ödeme iyzico tarafından alınır. Kart numaran Subly'ye ulaşmaz ve saklanmaz; bize yalnızca ödemenin sonucu bildirilir.</li>
</ul>

<h2>Neden topluyoruz</h2>
<ul>
  <li>Videona altyazı eklemek ve sonucu sana teslim etmek (sözleşmenin ifası).</li>
  <li>Plan limitlerini uygulamak ve kötüye kullanımı önlemek (meşru menfaat).</li>
  <li>Ödeme almak ve fatura düzenlemek (hukuki yükümlülük).</li>
</ul>

<h2>Ne kadar saklıyoruz</h2>
<ul>
  <li>Yüklediğin video ve ses dosyası, işlem biter bitmez silinir.</li>
  <li>Altyazılı video, indirebilmen için 24 saat saklanır, sonra silinir.</li>
  <li>Hesap ve kullanım bilgileri, hesabın açık olduğu sürece saklanır.</li>
  <li>Fatura ve ödeme kayıtları, mevzuatın öngördüğü süre boyunca saklanır.</li>
</ul>

<h2>Kimlerle paylaşıyoruz</h2>
<p>Verilerini satmayız ve reklam amacıyla paylaşmayız. Hizmeti sunabilmek için şu sağlayıcılarla çalışıyoruz:</p>
<ul>
  <li><strong>Google:</strong> giriş işlemi.</li>
  <li><strong>OpenAI:</strong> konuşmayı yazıya dökme ve çeviri. Videonun sesi ve altyazı metni bu amaçla gönderilir.</li>
  <li><strong>Render ve Neon:</strong> sunucu ve veritabanı barındırma.</li>
  <li><strong>iyzico:</strong> ödeme.</li>
</ul>
<p>Bu sağlayıcıların bir kısmının sunucuları yurt dışındadır. Video yükleyerek, verilerinin bu amaçla ve bu kapsamda yurt dışına aktarılmasına onay verirsin.</p>

<h2>Çerezler</h2>
<p>Yalnızca oturumunu açık tutan ve dil tercihini hatırlayan zorunlu bir çerez kullanıyoruz. Reklam veya izleme çerezi kullanmıyoruz.</p>

<h2>Hakların</h2>
<p>KVKK'nın 11. maddesine göre verilerinin işlenip işlenmediğini öğrenme, verilerini isteme, düzeltilmesini veya silinmesini isteme ve işlenmesine itiraz etme hakkın var. Talebini <a href="/yasal/iletisim">İletişim</a> sayfasındaki adrese gönder; en geç 30 gün içinde yanıtlarız.</p>"""


def _contact():
    return f"""
<p>Soru, iade talebi ve KVKK başvuruları için bize buradan ulaşabilirsin.</p>
{_seller_block()}"""


_BODIES = {
    "mesafeli-satis": _distance_sales,
    "iptal-iade": _refund,
    "gizlilik": _privacy,
    "iletisim": _contact,
}


def get_legal_page(slug):
    """(baslik, html govde) dondurur; slug taninmiyorsa None."""
    for page_slug, title, _ in PAGES:
        if page_slug == slug:
            return title, _BODIES[slug]()
    return None
