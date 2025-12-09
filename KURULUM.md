# 🦅 TUYGUN - "Evde Pişir, Çantaya At" Kurulum Rehberi

## 📋 Genel Bakış

TUYGUN, "Evde Pişir, Çantaya At" (Batch Processing & Sync) modeliyle çalışır:

1. **🏭 EV (Üretimhane)**: Bilgisayarında RSS'lerden makaleleri seç, AI ile özetle, Google Drive'a kaydet
2. **☁️ BULUT**: Google Drive otomatik senkronize eder
3. **📱 DIŞARISI**: Telefon/Tablet'ten Obsidian'da offline oku

## 🛠️ Kurulum Adımları

### 1. Google Drive'da Obsidian Vault Oluştur

1. Google Drive'ını aç
2. Yeni bir klasör oluştur: `ObsidianVault` (veya istediğin isim)
3. Bu klasörün tam yolunu not al (aşağıda kullanacağız)

### 2. Google Drive Yolunu Bul

#### Windows:
1. Google Drive klasörüne sağ tık → "Özellikler"
2. "Konum" kısmındaki yolu kopyala
3. Örnek: `C:\Users\SeninAdin\Google Drive\ObsidianVault`

#### Mac:
1. Finder'da Google Drive klasörüne sağ tık → "Bilgi Al"
2. "Konum" kısmındaki yolu kopyala
3. Örnek: `/Users/SeninAdin/Google Drive/ObsidianVault`

#### Linux:
1. Terminal'de Google Drive klasörüne git
2. `pwd` komutu ile tam yolu al
3. Örnek: `/home/kullanici/Google Drive/ObsidianVault`

### 3. Ayarları Yapılandır (.env)

1. Proje ana dizininde `.env.example` dosyasının bir kopyasını oluşturup adını `.env` yapın (Eğer yoksa otomatik oluşturulmuş olabilir).
2. `.env` dosyasını bir metin editörüyle açın.
3. `OBSIDIAN_VAULT_PATH` değişkenini kendi Google Drive yolunuzla değiştirin.

**Windows için Örnek .env:**
```ini
# ... diğer ayarlar ...
OBSIDIAN_VAULT_PATH=C:/Users/SeninAdin/Google Drive/ObsidianVault
```

**Mac için Örnek .env:**
```ini
# ... diğer ayarlar ...
OBSIDIAN_VAULT_PATH=/Users/SeninAdin/Google Drive/ObsidianVault
```

⚠️ **ÖNEMLİ:** 
- Windows'ta yol `C:/` şeklinde forward slash (`/`) kullanmalı.
- `docker-compose.yml` dosyasını **düzenlemenize gerek yok**, ayarları `.env` dosyasından okuyacak.

### 4. Docker'ı Başlat

```bash
docker-compose down
docker-compose up -d --build
```

### 5. Frontend'i Başlat

```bash
cd frontend
npm install
npm run dev
```

### 6. Test Et

1. Tarayıcıda `http://localhost:5173` aç
2. RSS Okuyucu sekmesine git
3. Bir RSS URL'i ekle (örn: `https://feeds.feedburner.com/TechCrunch/`)
4. Başlıkları çek
5. Bir makaleye tıkla → TUYGUN otomatik analiz edecek
6. "Kaydet" butonuna bas → Kategori seç (örn: `Inbox/AI`)
7. Google Drive klasörünü kontrol et → `.md` dosyası oluşmuş olmalı!

## 📱 Obsidian Kurulumu (Kritik Adım)

TUYGUN'un kaydettiği makaleleri okuyabilmek için, bu klasörü Obsidian'a **"Vault" (Kasa)** olarak tanıtmalısınız.

### Masaüstü (Bilgisayar)
1. Obsidian uygulamasını açın.
2. **"Open folder as vault"** (Klasörü kasa olarak aç) seçeneğine tıklayın.
3. `.env` dosyasında belirlediğiniz klasörü seçin (Örn: `G:\Drive'ım\TUYGUN`).
4. Artık TUYGUN'un kaydettiği her şey anında Obsidian'da belirecek!

### Mobil (Telefon/Tablet)
1. Obsidian Mobile uygulamasını indirin.
2. **"Open folder as vault"** seçeneğini seçin.
3. Google Drive'daki `TUYGUN` klasörünü bulun ve seçin.
4. Senkronizasyon tamamlandığında makaleleriniz çevrimdışı (offline) olarak cebinizde!

## 🎯 Kullanım Senaryosu

### Sabah (Evde):
1. TUYGUN'u aç
2. RSS feed'lerden ilginç makaleleri seç
3. Her birini tıkla → AI özetini oku
4. Beğendiğin makaleleri "Kaydet" → Kategori seç (örn: `Inbox/AI`, `Inbox/Sağlık`)
5. Bilgisayarı kapat

### Öğleden Sonra (Dışarıda):
1. Telefon/Tablet'te Obsidian'ı aç
2. Google Drive senkronize olmuş (otomatik)
3. `Inbox/AI` klasöründeki makaleleri offline oku
4. İnternet gerekmez!

## 🔧 Sorun Giderme

### Docker Volume Hatası

**Hata:** `invalid mount config for type "bind"`

**Çözüm:**
- Yol formatını kontrol et (Windows'ta `C:/` şeklinde olmalı)
- Klasörün var olduğundan emin ol
- Docker Desktop'un dosya paylaşımına izin verdiğinden emin ol

### Dosya Yazılamıyor

**Hata:** `Permission denied`

**Çözüm:**
- Google Drive klasörünün yazma izni olduğundan emin ol
- Docker Desktop → Settings → Resources → File Sharing → Google Drive klasörünü ekle

### Google Drive Senkronize Olmuyor

**Çözüm:**
- Google Drive Desktop uygulamasının çalıştığından emin ol
- İnternet bağlantını kontrol et
- Google Drive'ın senkronize olduğunu kontrol et (Drive ikonuna tıkla)

## 🎉 Avantajlar

✅ **Sıfır Maliyet**: Sunucu yok, IP yok, tünel yok  
✅ **Offline Okuma**: Metroda internet çekmese bile notların telefonda  
✅ **Kendi "Pocket" Uygulaman**: Başkalarının algoritması değil, senin seçtiğin içerik  
✅ **AI Özetli**: Her makale TUYGUN tarafından 3 cümlede özetlenmiş  
✅ **Kategorize**: `Inbox/AI`, `Inbox/Sağlık` gibi klasörlerde düzenli  

## 📚 Kategori Önerileri

- `Inbox/Genel` - Genel ilgi alanları
- `Inbox/AI` - Yapay zeka makaleleri
- `Inbox/Sağlık` - Sağlık ve wellness
- `Inbox/Teknoloji` - Teknoloji haberleri
- `Inbox/İş` - İş ve kariyer
- `Inbox/Bilim` - Bilimsel makaleler

Kategoriler otomatik olarak klasör yapısına dönüşür!

## 🏷️ Otomatik Etiketleme (Auto-Tagging)

TUYGUN, her makaleyi analiz ederken **otomatik olarak 3 etiket** belirler:

- **AI Analiz**: Ollama makalenin içeriğine göre en uygun 3 etiketi seçer
- **Obsidian Uyumlu**: Etiketler Markdown frontmatter formatında kaydedilir
- **Arama Kolaylığı**: Obsidian'da `#yapayzeka` gibi etiketlerle hızlıca bulabilirsin

**Örnek Markdown Çıktısı:**
```markdown
---
created: 2023-11-26 10:00
tags: [#yapayzeka, #python, #startup]
source: techcrunch.com
category: Inbox/AI
---
```

Etiketler makale özetinin altında görüntülenir ve kaydetme sırasında otomatik olarak eklenir!

---

**🦅 TUYGUN ile bilgiyi evde pişir, dışarıda ye!**

