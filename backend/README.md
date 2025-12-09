# TUYGUN Backend

FastAPI tabanlı backend servisi.

## Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt
```

## Veritabanı Kurulumu

### Docker ile (Önerilen)

```bash
# Docker Compose ile tüm servisleri başlat
docker-compose up -d

# Backend otomatik olarak veritabanını initialize edecek
```

### Manuel Kurulum

```bash
# Veritabanı tablolarını oluştur ve örnek veriler ekle
python init_db.py
```

## Geliştirme

```bash
# Development server'ı başlat
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API dokümantasyonu: http://localhost:8000/docs

## Veritabanı Modelleri

### Document
- Belgeleri temsil eder
- Her belge bir Source'a bağlıdır
- Status: indexed, processing, error

### Source
- Bilgi kaynaklarını temsil eder (Obsidian, PDF, SAP Codes, etc.)
- Status: active, syncing, error, pending
- Progress: 0-100 arası senkronizasyon durumu

### Activity
- Sistem aktivitelerini loglar
- Type: document, query, embedding, source

## API Endpoints

- `GET /api/dashboard/stats` - Dashboard istatistikleri
- `GET /api/dashboard/activities` - Son aktiviteler
- `GET /api/dashboard/sources` - Dashboard kaynakları
- `GET /api/documents` - Tüm belgeler
- `GET /api/sources` - Tüm kaynaklar

## Environment Variables

- `DATABASE_URL`: PostgreSQL bağlantı string'i
- `OPENAI_API_KEY`: OpenAI API anahtarı (opsiyonel)



