# TUYGUN - Bilgi Yönetim Sistemi

Modern React frontend ve FastAPI backend ile geliştirilmiş enterprise-grade bilgi yönetim sistemi.

## 🏗️ Mimari

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL + pgvector
- **Containerization**: Docker + Docker Compose

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Docker ve Docker Compose yüklü olmalı
- (Opsiyonel) Node.js 18+ ve Python 3.11+ (geliştirme için)

### Docker ile Çalıştırma

```bash
# Tüm servisleri başlat (Frontend + Backend + Database)
docker-compose up -d

# Logları izle
docker-compose logs -f

# Servisleri durdur
docker-compose down
```

Servisler:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432

### Geliştirme Modu

#### Backend (Python)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

## 📁 Proje Yapısı

```
.
├── frontend/          # React uygulaması
│   ├── src/
│   │   ├── components/   # UI componentleri
│   │   ├── lib/          # API utilities
│   │   └── ...
│   ├── Dockerfile
│   └── package.json
├── backend/           # FastAPI uygulaması
│   ├── main.py        # API endpoints
│   ├── schemas.py     # Pydantic modelleri
│   ├── Dockerfile
│   └── requirements.txt
└── docker-compose.yml # Tüm servislerin orkestrasyonu
```

## 🔌 API Endpoints

### Dashboard
- `GET /api/dashboard/stats` - İstatistik kartları
- `GET /api/dashboard/activities` - Son aktiviteler
- `GET /api/dashboard/sources` - Bilgi kaynakları

### Knowledge Base
- `GET /api/documents` - Tüm belgeler
- `GET /api/sources` - Tüm kaynaklar

Detaylı API dokümantasyonu: http://localhost:8000/docs

## 🛠️ Geliştirme

### Backend'e Yeni Endpoint Ekleme

1. `backend/schemas.py` içine yeni Pydantic modeli ekle
2. `backend/main.py` içine endpoint ekle
3. Frontend'de `frontend/src/lib/api.ts` içine API fonksiyonu ekle
4. Component'lerde kullan

### Frontend'e Yeni Component Ekleme

1. `frontend/src/components/` altına component ekle
2. `frontend/src/App.tsx` içine route ekle
3. Gerekirse `frontend/src/lib/api.ts` içine API çağrısı ekle

## 🦅 "Evde Pişir, Çantaya At" Modeli

TUYGUN, **Batch Processing & Sync** modeliyle çalışır:

1. **🏭 EV (Üretimhane)**: Bilgisayarında RSS'lerden makaleleri seç, AI ile özetle, Google Drive'a kaydet
2. **☁️ BULUT**: Google Drive otomatik senkronize eder
3. **📱 DIŞARISI**: Telefon/Tablet'ten Obsidian'da offline oku

### Kurulum

Detaylı kurulum rehberi için: **[KURULUM.md](./KURULUM.md)**

**Hızlı Başlangıç:**
1. Google Drive'da `ObsidianVault` klasörü oluştur
2. `docker-compose.yml` dosyasında Google Drive yolunu ayarla
3. `docker-compose up -d --build` çalıştır
4. Frontend'i başlat: `cd frontend && npm run dev`

## 📝 Notlar

- ✅ Backend artık PostgreSQL veritabanına bağlı ve gerçek verileri kullanıyor!
- ✅ **The Curation Flow**: RSS → AI Özet → Kaydet (Postgres + Obsidian)
- ✅ **"Evde Pişir, Çantaya At"**: Google Drive entegrasyonu ile offline okuma
- Backend başlatıldığında otomatik olarak tablolar oluşturulur ve örnek veriler eklenir.
- Frontend'deki veri yapıları backend'deki Pydantic modelleriyle birebir eşleşiyor.
- CORS ayarları development için yapılandırıldı. Production'da güvenlik ayarlarını güncelleyin.

## 🗄️ Veritabanı

Sistem PostgreSQL + pgvector kullanıyor. Tablolar:
- `documents` - Belgeler
- `sources` - Bilgi kaynakları
- `activities` - Sistem aktiviteleri

Backend ilk başlatıldığında otomatik olarak örnek veriler eklenir.

## 🔐 Environment Variables

`.env` dosyası oluşturup şunları ekleyebilirsiniz:

```env
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql://tuygun:pass@db:5432/tuygun_db
```

## 🚀 Deployment (Canlıya Alma)

Detaylı kurulum rehberi için [DEPLOYMENT.md](DEPLOYMENT.md) dosyasına bakabilirsiniz.

## 🔮 Gelecek Vizyonu (Roadmap)

Sistem oturduktan sonra yapılması planlanan geliştirmeler:

1.  **Sync Otomasyonu:**
    *   Bilgisayardaki Obsidian notlarını, sunucudaki `/app/data/vault` klasörüne otomatik eşitleyen "Syncthing" veya "Git Sync" yapısı.
2.  **Agent Entegrasyonu:**
    *   LangGraph veya AutoGen ekleyerek, "Bana son 1 haftadaki notlarımdan bir özet çıkar" diyebilen aktif bir asistan modülü.

## 📄 Lisans

Bu proje özel bir projedir.
