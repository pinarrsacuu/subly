# Proje Planı: Uygulama Üzerinden Gelir Modeli

**Son güncelleme:** 2026-08-15
**Durum:** Yön belirleme aşaması — henüz kod yazılmadı

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
