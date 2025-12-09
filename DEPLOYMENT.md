# 🚀 Oracle Cloud Deployment Guide

Bu rehber, TUYGUN projesini Oracle Cloud (veya herhangi bir VPS) üzerinde yayına almak için gerekli adımları içerir.

## 1. Sunucuya Bağlanma
Sunucunuza SSH ile bağlanın:
```bash
ssh ubuntu@<SUNUCU_IP_ADRESI>
```

## 2. Projeyi İndirme
GitHub üzerindeki güncel kodu sunucuya çekin:
```bash
git clone https://github.com/ZGRSRL/Tuygun.git
cd Tuygun
```

## 3. Ortam Değişkenlerini Ayarlama (.env)
Github'a güvenlik gereği gönderilmeyen şifreleri sunucuda tanımlamanız gerekir.
`.env` dosyasını oluşturun:
```bash
nano .env
```

Aşağıdaki şablonu kopyalayıp, **kendi şifrelerinizi belirleyerek** yapıştırın:

```ini
# Database
POSTGRES_USER=tuygun_user
POSTGRES_PASSWORD=cok_gizli_sifre_belirle
POSTGRES_DB=tuygun_db

# Security (Arayüz Girişi)
SECURITY_USER=admin
SECURITY_PASSWORD=guclu_bir_admin_sifresi

# Paths & API
OBSIDIAN_VAULT_PATH=/app/data/vault
VITE_API_URL=/api
```
*(Kaydetmek için: `CTRL+X`, sonra `Y`, sonra `Enter`)*

## 4. Vault Klasörünü Hazırlama
Docker volume hatası almamak için veri klasörünü oluşturun:
```bash
mkdir -p data/vault
```

## 5. Başlatma (Deploy) 🚀
Production modunda (Gunicorn + Caddy + Auto-Restart) başlatmak için:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

---

Artık sisteminiz çalışıyor olmalı! Tarayıcıdan sunucu IP adresine (veya ayarladıysanız domain adresine) giderek erişebilirsiniz.
