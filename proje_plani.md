# Proje Planı: Uygulama Üzerinden Gelir Modeli

**Son güncelleme:** 2026-09-08
**Durum:** Ürün canlıda (subly.nexidigitalai.com) — üyelik/Google giriş, 3 katmanlı fiyatlandırma ve async video işleme kuruldu; ödeme entegrasyonu (iyzico) ve Render Starter plan doğrulaması bekliyor

> Bu dosya canlı bir belge. İlerledikçe (fikir netleşince, MVP kapsamı değişince, pazarlama planı oluşunca) revize edilecek. Yeni bir konuşmaya başlarken bu dosyayı oku, kaldığımız yerden devam et.

---

## 1. Amaç / Genel Yön

Kullanıcı, birebir müşteri ilişkisi kurmadan (danışmanlık/ajans modeli değil) gelir elde edebileceği bir sistem kurmak istiyor. İki paralel yol belirlendi:

1. **YouTube otomasyonu** — mevcut, çalışan bir sistem (bkz. `glowtips_momentos_pipeline` hafıza kaydı). GlowTips → Momentos pipeline, İspanyolca versiyon, günlük yükleme.
2. **Uygulama/mikro-SaaS geliştirme** — bu dosyanın odağı. Var olan, talebi kanıtlanmış bir uygulama kategorisini seçip, kullanıcıların o kategoride en çok şikayet ettiği noktayı (fiyatlandırma, kısıtlama, watermark, kredi sistemi) çözerek kendi markamızla piyasaya sürmek.

**Model netliği:** Rakip kopyalanmıyor. Aynı temel işlevi (örn. otomatik altyazı ekleme) yeniden yazıyoruz, ama kullanıcıların asıl kızdığı noktayı (gizli otomatik yenileme, watermark, kredi sınırı) düzelterek. Gelir modeli: abonelik veya tek seferlik ödeme. Dağıtım: App Store/SEO/Reddit organik paylaşım/YouTube kanalları — birebir satış görüşmesi yok.

---

## 2. Araştırma Çıktısı

Tam rapor: [`micro_saas_idea_research.md`](micro_saas_idea_research.md) — 12 fikir, kaynaklı kanıtlarla.

**Kanıt gücü × yapılabilirlik'e göre öne çıkan 4 fikir:**

| # | Fikir | Neden güçlü | Zorluk |
|---|-------|-------------|--------|
| 1 | Watermark'sız, sabit fiyatlı altyazı/caption aracı (Submagic alternatifi) | En güçlü kanıt (fiyatlandırma şikayeti); kullanıcının mevcut inpainting/metin pipeline deneyimiyle doğrudan örtüşüyor | Düşük-orta |
| 2 | Şeffaf fiyatlı sessizlik/jump-cut editörü (Descript alternatifi) | Somut fatura şikayeti (30$→195$); rakip tek-özellikli uygulamalar zaten var, pazar doğrulanmış | Orta |
| 3 | Şeffaf, tek seferlik ücretli ATS/özgeçmiş aracı | Çok somut dark-pattern kanıtı (Zety 1.95$→25.95$); ama pazar kalabalık | Düşük |
| 4 | Niş dil çiftleri için dublaj/çeviri aracı | Kullanıcının becerisiyle tam örtüşüyor (dublaj, dudak senkronu, çeviri); mevcut araçlar uzun/duygusal anlatımda çöküyor | Orta-yüksek |

**Öneri:** 1 numara (altyazı aracı) ile başlamak — en düşük teknik risk + en yakın mevcut beceri + en güçlü kanıt.

Diğer 8 fikir raporda duruyor (alışkanlık takibi, ekran kaydedici, YouTube analitik aracı, faturalama, toplantı not alma, local SEO aracı, içerik filtresi tarayıcı eklentisi vb.) — ya pazar doygunluğu ya da daha zayıf kanıt nedeniyle geride bırakıldı.

---

## 3. Pazarlama Yaklaşımı (kavramsal, henüz kurulmadı)

Kullanıcı birebir satış yapmak istemiyor. Planlanan model — "tek kişilik pazarlama departmanı", Claude Code üzerinden çalışan roller:

- **Araştırma kolu:** Rakip fiyat/şikayet takibi, pazar boşluğu tarama (tekrarlayan, `/schedule` veya `/loop` ile zamanlanabilir)
- **İçerik/copy kolu:** App Store açıklaması, landing page metni, Reddit organik paylaşım taslağı, Product Hunt lansman metni, SEO blog yazıları — Claude taslak yazar, kullanıcı onaylayıp paylaşır
- **SEO/keyword araştırması:** Arama hacmi olan terimler etrafında içerik kurmak (örn. "free submagic alternative")
- **Dağıtım kanalı:** Kullanıcının mevcut YouTube kanalları — organik trafik için en güçlü avantaj

**Not:** Claude Code otonom olarak sosyal medyaya paylaşım yapamaz (Reddit/Twitter API entegrasyonu yok şu an). Paylaşım adımı kullanıcıda kalıyor; ileride API entegrasyonu değerlendirilebilir.

---

## 4. Sonraki Adım

Kullanıcı en basit haliyle bir uygulama geliştirmeye başlamak istiyor — birlikte küçük bir MVP kurup projeye başlayacağız.

**Karar:** 1 numaralı fikirle başlanıyor — watermark'sız, sabit fiyatlı altyazı/caption aracı (Submagic alternatifi).

**Öğretim yaklaşımı:** Kullanıcının hiç kodlama/teknik geçmişi yok. Claude, adım adım öğretmen rolünde ilerleyecek — her adımda "ne yapıyoruz" ve "neden yapıyoruz" açıklanacak. Önce arayüzsüz/basit bir script ile çekirdek özelliğin (video → otomatik altyazı → watermark'sız çıktı) çalıştığını kanıtlamak hedef; arayüz (web app) ve ödeme sistemi daha sonraki aşama.

**Yol haritası (kaba sıra):**
1. Ortam kurulumu (gerekli araçlar: Python, ffmpeg vb.) — kullanıcıya öğretilerek
2. Çekirdek özellik: bir video dosyasını al → konuşmayı metne çevir (transkripsiyon API'si) → stilize altyazı olarak videoya göm (ffmpeg) → watermark'sız çıktı ver. Önce komut satırından çalışan basit bir script olarak.
3. Script çalıştıktan sonra basit bir web arayüzü (kullanıcı video yükler, indirir)
4. Ödeme/abonelik sistemi entegrasyonu
5. Dağıtım/pazarlama (bkz. bölüm 3)

**Gerekli API/servisler (ileride hesap açılacak):** Konuşma-metin (transkripsiyon) API'si (örn. OpenAI Whisper API veya AssemblyAI) — bu adıma gelince birlikte hesap açılıp API key alınacak.

---

## Revizyon Geçmişi
- 2026-08-15: İlk oluşturma. Yön belirleme + fikir araştırması tamamlandı.
- 2026-08-15: Fikir #1 (altyazı aracı) ile başlama kararı verildi. Öğretim modunda, adım adım ilerlenecek. Yol haritası eklendi.
- 2026-08-15: **MVP çekirdek özelliği tamamlandı ve test edildi.** Ortam kuruldu (Homebrew, Python venv, ffmpeg). OpenAI API hesabı açıldı, anahtar `.env` dosyasında güvenli saklanıyor. İki script yazıldı:
  - `transcribe.py` — video → ses çıkarma → OpenAI Whisper API ile transkript → `.srt` altyazı dosyası
  - `burn_captions.py` — `.srt`'yi ffmpeg ile videoya kalın/beyaz/konturlu, watermark'sız altyazı olarak gömüyor
  - **Karşılaşılan ve çözülen sorun:** Homebrew'un standart `ffmpeg` paketi `libass` (altyazı render kütüphanesi) içermiyor, `subtitles` filtresi çalışmıyordu. Çözüm: `homebrew-ffmpeg/ffmpeg` tap'inden libass dahil sürüm kuruldu.
  - Uçtan uca gerçek bir videoyla (ktown_video_es.mp4'ün outro bölümü) test edildi, çıktı `test_input/real_test_captioned.mp4` içinde — görsel kontrol kullanıcı tarafından yapılacak.
  - **Sonraki adım:** Script'i basit bir web arayüzüne sarmak (kullanıcı video yükler, işlenmiş videoyu indirir).
- 2026-08-15: **Web arayüzü + marka kimliği tamamlandı.**
  - `app.py` (Flask) yazıldı: video yükleme formu → işlenmiş videoyu tarayıcıdan izleme/indirme. `localhost:5001`'de çalışıyor (5000 portu macOS AirPlay ile çakıştığı için 5001 kullanıldı).
  - Kullanıcı isteği üzerine **çoklu dil desteği** eklendi: `translate.py` — Whisper transkriptini OpenAI (gpt-4o-mini) ile hedef dile çeviriyor, kullanıcı web formunda 14 dilden birini seçebiliyor (İngilizce, İspanyolca, Türkçe, Arapça, Çince, vb.). Rusça ile test edildi, çalıştı.
  - **Marka kararı:** Ürün, kullanıcının mevcut ajans şirketi **Nexi Digital** çatısı altında ayrı bir ürün olarak konumlandırılıyor. Ürün adı: **Subly**. Nexi Digital'in kurumsal sitesinden (mevcut Claude artifact) renk paleti (mercan `#D6455C`, deniz mavisi-yeşil `#17948C`, koyu mürekkep `#241B2E`, sıcak kağıt `#F1ECE6`), fontlar (başlıklarda Georgia serif, gövdede sistem sans-serif) ve logo mark'ı alınıp `app.py` içindeki arayüze uygulandı. Kullanıcı sonucu onayladı ("çok iyi").
  - **Sonraki adım:** Ödeme/abonelik sistemi ve siteyi internete yayınlama (domain + hosting).
- 2026-08-15: **Fiyatlandırma/monetizasyon mantığı ve ödeme altyapısı için kararlar netleşti (henüz uygulanmadı, not olarak kayıtlı):**
  - **Paywall mekanizması watermark değil, kullanım limiti olacak.** Watermark'ı "fidye" olarak kullanmayacağız (rakiplerin en çok şikayet edilen yönü buydu) — ücretsiz plan gerçekten temiz sonuç verir ama sınırlıdır (örn. ayda 3 video, video başına birkaç dakika sınırı, standart hız). Ücretli plan: yüksek/sınırsız limit, uzun video, öncelikli işlem. Bu hem pazarlama mesajıyla tutarlı hem de gerçek bir zorunluluk: her video işlemenin bize gerçek OpenAI API maliyeti var, sınırsız ücretsiz kullanım zarar ettirir.
  - **Freemium abuse / çoklu hesap sorunu ele alınacak.** Kullanıcı kendi deneyiminden (6-7 Google hesabıyla ücretsiz limitleri aşma) bunun gerçek bir risk olduğunu belirtti. %100 önlenemez ama şu önlemlerle azaltılacak: (1) ücretsiz plan için bile kredi kartı doğrulaması istemek (0$ tahsilat, sadece kart kaydı — Submagic/Opus Clip gibi rakiplerin de yaptığı), (2) hesaba ek olarak IP adresi/cihaz bazlı takip, (3) opsiyonel telefon (SMS) doğrulaması. Hedef kitle (düzenli video üreten içerik üreticisi/ajans) için bu zaten yeterli caydırıcı — birkaç video için kaçak hesap açan kullanıcı zaten ödeme yapmayacak kişidir, ona karşı mükemmel savunma yerine "çoğu kullanıcı için yeterince zahmetli" seviyesi hedefleniyor.
  - **Ödeme sağlayıcısı seçimi Türkiye vergi mevzuatına bağlı, henüz karar verilmedi.** Türkiye'de dijital hizmet/içerik üreticileri için özel bir stopaj rejimi var (kazanç Türk banka hesabına yatınca banka otomatik %15 stopaj kesiyor, belli sınırın altında ek beyan gerekmiyor). Hangi ödeme sağlayıcısının (Iyzico/PayTR gibi yerel, veya Paddle/LemonSqueezy gibi merchant-of-record uluslararası) bu rejime tam uyduğu belirsiz — **kullanıcı ödeme sistemini kurmadan önce bir mali müşavire danışacak.** Bu konuda Claude kesin vergi tavsiyesi vermedi, bilinçli olarak kaçındı.
- 2026-08-15: **Site arayüzü çok dilli hale getirildi (ürün UI'ı, altyazı dilinden ayrı).** `ui_strings.py` — ziyaretçinin tarayıcı dil ayarına göre (Accept-Language header, `best_match` ile) sitenin kendisi 14 dilde otomatik açılıyor: en, es, pt, fr, de, it, tr, ar, hi, zh, ja, ko, ru, id. Arapça için `dir="rtl"` desteği eklendi. Varsayılan (eşleşme yoksa) İngilizce. `app.py`'deki `index()`/`process()` route'ları `Accept-Language` header'ını okuyup doğru dil sözlüğünü template'e geçiriyor. Almanca ve Rusça header'larla test edildi, doğru çalıştı.
- 2026-08-16: **GitHub + Render ile canlıya alındı, domain henüz alınmadı.** Kod GitHub'a (`github.com/pinarrsacuu/subly`, SSH anahtarıyla) taşındı. Render.com'da Docker tabanlı bir Web Service olarak yayınlandı (free plan, `Dockerfile` ffmpeg/libass'ı Debian apt'tan kuruyor, `requirements.txt` + `gunicorn` eklendi). **Free plan gerçek kısıtları canlıda görüldü:** 0.1 CPU çok yavaş (5 dakikalık video ~35 dk sürüyor, worker timeout/OOM ile çöküyor) — `burn_captions.py`'ye `-preset ultrafast` eklenerek kısmen hafifletildi, ama gerçek çözüm gerçek kullanıcıya açılırken ücretli plana (Starter, ~7$/ay) geçmek. Kısa klipler (6-20 sn) uçtan uca başarıyla test edildi. Domain (`getsubly.io` düşünülüyor, `subly.app/.co/.io` hepsi alınmış) bütçe nedeniyle Eylül 2026'ya ertelendi, kullanıcı bu ay alacak.
- 2026-09-06: **Ücretsiz plan kullanım limiti kodlandı.** `usage_tracker.py` (email bazlı, aylık sayaç, `usage.json`) ve `video_utils.py` (`ffprobe` ile süre kontrolü) eklendi. Kurallar: ayda `FREE_MONTHLY_LIMIT=3` video, video başına `FREE_MAX_DURATION_SECONDS=90` (1.5 dk) sınırı — hem üründeki freemium kararını hem de free-tier hosting'in CPU kısıtını aynı anda çözüyor. Form'a email alanı eklendi, limit/süre aşımında yerelleştirilmiş (14 dil) hata sayfası (`ERROR_PAGE`) gösteriliyor. Yerelde 4 ardışık istekle (3 başarılı + 1 limit hatası) ve 126 saniyelik sentetik videoyla (süre hatası) test edildi, ikisi de doğru çalıştı. GitHub'a push edildi, Render otomatik yeniden deploy ediyor. **Bilinen sınırlama:** `usage.json` Render free plan'da kalıcı disk olmadığı için sunucu yeniden başladığında sıfırlanabilir — gerçek kullanıcıya açmadan önce bir veritabanına (örn. Render'ın ücretsiz Postgres'i) taşınması gerekiyor, henüz yapılmadı.
- 2026-09-08: **Büyük bir oturumda altyapı, üyelik, ödeme hazırlığı ve marka/landing page yeniden tasarımı tamamlandı.**
  - **UI küçük düzeltme:** Email input alanı `input[type=email]` CSS seçicisine eklenmediği için tam genişlik almıyor, submit butonunu sıkıştırıyordu — düzeltildi.
  - **IP tabanlı otomatik dil tespiti eklendi.** Sadece tarayıcı `Accept-Language` header'ına değil, ziyaretçinin IP'sinden ülkesine bakılarak (ip-api.com ücretsiz servisi + `COUNTRY_TO_LANG` ISO-3166 eşlemesi) site dili otomatik seçiliyor; header eşleşmesi yedek olarak duruyor. `/status` sayfası birkaç saniyede bir kendini yenilediği için (aşağıda), dil sonucu `session['lang']` içinde önbelleğe alınıyor — her yenilemede IP servisine tekrar sorup hız sınırına takılmamak için.
  - **Kullanım takibi JSON'dan Neon Postgres'e taşındı.** `usage_tracker.py` artık `usage` ve `users` tablolarını Postgres'te tutuyor (`DATABASE_URL` ortam değişkeni) — Render sunucusu yeniden başladığında sayaçlar artık sıfırlanmıyor. Önceki oturumun "bilinen sınırlama" notu bununla kapandı.
  - **Google ile üyelik/giriş sistemi eklendi** (kullanıcının kararı: şifre yok, sadece Google OAuth). `auth.py` (Authlib ile Google OAuth2/OIDC kaydı), `users` tablosuna `plan`, `subscription_reference`, `current_period_end` kolonları eklendi. `/login/google`, `/login/google/callback`, `/logout` route'ları; nav'da giriş yapmışsa avatar/isim + çıkış, yapmamışsa "Google ile giriş" butonu gösteriliyor. Serbestçe yazılan email alanı yerine artık kimlik doğrulanmış hesap kullanılıyor.
  - **3 katmanlı fiyatlandırma modeline geçildi: Free / Pro / Premium.** Kullanıcı, ilk planlanan "Pro'da 10 dakikalık video" vaadinin gerçekten karşılanıp karşılanamayacağını sorguladı (proje_plani.md'deki geçmiş veriye dayanarak: free plan'da 5 dakikalık video ~35 dk sürüyordu, worker timeout/OOM riski var). Bu haklı çıktı — asıl darboğazın video *uzunluğu* değil işlem *süresi* (ffmpeg CPU-bound gömme adımı) olduğu, ayrıca Cloudflare'in tek bir HTTP isteğini ~100 saniyeden uzun sürerse muhtemelen kestiği belirlendi (free plandaki 90 saniyelik sınırın rastgele olmadığı, bu senkron-istek tavanına bağlı olduğu ortaya çıktı). Sonuçta: **Free** (3 video/ay, 90 sn), **Pro** (149 TL/ay, 20 video/ay, 5 dk/video), **Premium** (349 TL/ay, 10 video/ay, 15 dk/video). Premium'un 15 dakikalık sınırının gerçek işlem süresiyle uyumluluğu Render Starter planında ampirik olarak henüz doğrulanmadı — bir sonraki adım.
  - **Asenkron (arka planda) video işleme mimarisine geçildi** — yukarıdaki 100 saniyelik Cloudflare/gunicorn zaman aşımı riskini tamamen ortadan kaldırmak için. `jobs.py`: Postgres'te `jobs` tablosu + `create_job/get_job/mark_processing/mark_done/mark_error`. `/process` artık videoyu kaydedip bir `threading.Thread` başlatıyor ve kullanıcıyı hemen `/status/<job_id>`'e yönlendiriyor; asıl işlem (`run_job`) arka planda çalışıyor. `/status/<job_id>` sayfası `<meta http-equiv="refresh" content="4">` ile kendini yeniliyor, iş bitince sonuç/hata sayfasına dönüyor. Bu şu an `threading.Thread` ile yapılıyor (Celery/RQ gibi bir kuyruk sistemi değil) — küçük ölçekli bu uygulama için bilinçli, basit bir tercih.
  - **Email bildirimi eklendi (Resend).** `notify.py` — video hazır olunca (veya hata olunca) kullanıcıya indirme linkli bir email gönderiliyor. `RESEND_API_KEY` yoksa veya istek başarısız olursa sessizce geçiliyor — kritik yol değil, ek kolaylık.
  - **Landing page tamamen yeniden tasarlandı**, kullanıcının elle çizdiği ekran görüntüsü notlarına göre birkaç turda: masaüstünde yan yana hero → tek birleşik hero banner'a geçildi, logo büyütüldü, "Nasıl çalışır" bölümü upload formunun yanına (SSS'nin hemen üstüne) taşındı. Yeni CSS sınıfları: `.heroOuter`, `.splitRow`/`.half`, `.heroBanner`, `.contentSection`/`.stepsPanel`, `.userBox`/`.navLogin`, `.pricing`/`.planGrid`/`.planCard` (3 sütunlu fiyat kartları). Pazarlama metni, tek video içerik üreticilerini hedefleyecek şekilde yeniden yazıldı — free plan sınırları konusunda tamamen şeffaf (kullanıcının açık isteği: "yanıltıcı olsun istemiyorum").
  - **Ödeme sağlayıcısı olarak iyzico seçildi** (kullanıcının şahıs şirketi + vergi mükellefiyeti olduğu için). iyzico başvurusu VKN (Vergi Kimlik No, 10 hane) ile TC kimlik no (11 hane) karışıklığında takıldı, kullanıcı kendi halledecek ("iyzico uzun sürecek ben ayarlayacağım"). Entegrasyon (`iyzipay` SDK, Checkout Form/Subscription API, `set_plan()` webhook'u) henüz yapılmadı — Pro/Premium kartlarında hâlâ "Yakında" rozeti var.
  - **Prodüksiyonda çıkan Google OAuth `redirect_uri_mismatch` hatası düzeltildi.** Render/Cloudflare HTTPS'i sonlandırıp Flask'a düz HTTP ilettiği için `url_for(_external=True)` yanlışlıkla `http://` üretiyor, Google Cloud Console'da kayıtlı `https://` adresiyle eşleşmiyordu. `werkzeug.middleware.proxy_fix.ProxyFix` eklenerek çözüldü (commit `8a60108`), sunucu tarafında curl ile doğrulandı (redirect artık doğru `https://` içeriyor) — kullanıcının tarayıcıdan gerçek girişle son doğrulaması bekleniyor.
  - **Render Starter plan ($7/ay) yükseltmesi belirsiz durumda.** Kullanıcı en az iki kez "Plan update error: ... Plan requires payment information on file" hatası aldı; ödeme yöntemi eklenip eklenmediği ve yükseltmenin gerçekten uygulanıp uygulanmadığı netleşmedi — kontrol edilmesi gerekiyor.
  - **Google girişi ve async video işleme akışı prodüksiyonda uçtan uca doğrulandı** (2026-09-08). Ancak Render Starter (0.5 CPU/512MB) planında 1080p bir video işlerken tekrarlayan OOM ("Ran out of memory (used over 512MB)") çökmeleri görüldü — Render Events'te "Instance failed" olarak kayıtlı. 720p'ye indirmek tek başına yetmedi; asıl şüpheli sebep, video yeniden kodlanırken orijinal ses akışının "copy" ile değişmeden kopyalanması (`-c:a copy`) — telefon kaydı gibi değişken kare hızlı (VFR) videolarda bu, video/ses zaman damgalarının uyuşmamasına ve ffmpeg'in muxing queue'sunda sınırsız paket biriktirmesine yol açabiliyor. Çözüm: `burn_captions.py`'ye 720p'ye ölçekleme + `-threads 1` + sesi de yeniden kodlama (`-c:a aac -b:a 128k`) eklendi (commit `23f117e`, `94df8f5`). Bu değişiklikten sonra gerçek bir video (telefon kaydı, İspanyolca) hatasız işlendi, sonuç sayfası video oynatıcı + indirme linkiyle doğru çalıştı. **Not:** Bu düzeltme küçük/orta videolar için yeterli görünüyor ama Premium'un vaat ettiği 15 dakikalık videolarla henüz test edilmedi — büyük ölçekte tekrar OOM görülürse bir üst plana (Standard, ~2GB RAM) geçmek gerekebilir.
  - Nav'daki logo tıklanınca ana sayfaya dönecek şekilde link yapıldı (commit `1154895`).
  - **Fiyat kartları hareketli/seçilebilir yapıldı, güvenlik/gizlilik notu eklendi** (commit `1a397ac`). Kartlar hover'da kalkıyor, tıklayınca seçili işaretleniyor (Free seçimi upload formuna kaydırıyor). 14 dilde "trust_note" eklendi (HTTPS, şifre saklanmıyor — Google girişi, video işlem bitince siliniyor). Bu son iddiayı gerçek yapmak için `run_job()`'a orijinal video + `.srt` dosyasının `burn()` sonrası silinmesi eklendi (önceden sunucuda süresiz kalıyorlardı).
  - **"Zaten yakılmış (var olan) altyazıyı kapat" seçeneği eklendi** (commit `d5ed9c7`) — kullanıcı, indirdiği bir videoda başka dilde halihazırda görüntüye işlenmiş altyazı varsa (örn. Korece videoya yakılmış İngilizce fan-sub), bunun üstüne yeni altyazı eklemek isteyebiliyor; bu durumda metinler üst üste biniyordu. Yükleme formuna bir kutucuk + canlı mockup önizleme (JS ile checkbox değişince "önce/sonra" örneği güncelleniyor) eklendi. Arka planda `burn_captions.py`'ye `cover_subs` parametresi eklendi: işaretlenirse ffmpeg `drawbox` filtresiyle ekranın alt %20'lik şeridine opak bir kutu çiziliyor, yeni altyazı bunun üstüne geliyor. **Önemli sınırlama (kullanıcıya UI'da dürüstçe belirtildi):** bu gerçek bir "silme" değil — eski yazı görüntüden kaldırılmıyor, üstü kapatılıyor. Gerçek video inpainting (arka planı yeniden oluşturarak görünmez silme) çok daha ağır bir iş (muhtemelen GPU gerektiren ayrı bir model) ve şu anki ffmpeg tabanlı altyapının kapsamı dışında — talep gelirse ayrı bir proje olarak değerlendirilecek.
  - **Sonraki adımlar:** (1) gerçek ~15 dakikalık videoyla Premium'un süre sınırını ve bellek dayanıklılığını ampirik olarak doğrula (gerekirse Render planını yükselt), (2) iyzico başvurusu tamamlanınca ödeme entegrasyonunu kur, (3) ondan sonra pazarlama/lansman (Product Hunt, Indie Hackers, SEO) adımına dön.
