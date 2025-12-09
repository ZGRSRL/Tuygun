from config import settings
# from dotenv import load_dotenv  # Artık config.py içinde BaseSettings yönetiyor
# import os
# from pathlib import Path
# env_path = Path(__file__).resolve().parent.parent / '.env'
# load_dotenv(dotenv_path=env_path)

print(f"Project: {settings.PROJECT_NAME}, Version: {settings.VERSION}")
print(f"OBSIDIAN_VAULT_PATH: {settings.OBSIDIAN_VAULT_PATH}")
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

from database import get_db, engine, Base
from models import Document, Source, Activity, DocumentStatus, SourceStatus, ActivityType, SourceType, RSSFeed, Article, ArticleStatus, Category
from schemas import (
    StatItem, DocumentSchema, SourceSchema, ActivitySchema,
    RSSFeedSchema, ArticlePreviewSchema, ArticleDetailSchema,
    AddRSSFeedRequest, AddLinkRequest, SaveArticleRequest,
    ChatRequest, ChatResponse, CategorySchema, AddCategoryRequest
)
from utils import format_time_ago, format_file_size, generate_safe_filename
from services.embedding_service import generate_embedding
from services.rag_service import chat_with_data
import feedparser
import requests
from bs4 import BeautifulSoup
import uuid
import json
import time
import re
import re
from datetime import datetime, timezone
import trafilatura
from security import get_current_username

app = FastAPI(
    title="TUYGUN API", 
    version="1.0.0",
    dependencies=[Depends(get_current_username)]
)

# React (localhost:5173, 3000) Python'a erişebilsin diye CORS ayarı şart
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Uygulama başladığında çalışacak kodlar"""
    logger.info("Uygulama başlatılıyor...")
    
    # Veritabanı tablolarını oluştur (eğer yoksa) ve pgvector extension'ı aktif et
    try:
        from sqlalchemy import text
        # Retry logic for main app startup
        import time
        from sqlalchemy.exc import OperationalError
        
        max_retries = 30
        for attempt in range(max_retries):
            try:
                # Engine bağlantısını test et
                with engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                    logger.info("pgvector extension aktif edildi.")
                
                # Tabloları oluştur
                Base.metadata.create_all(bind=engine)
                logger.info("Tablolar oluşturuldu/kontrol edildi.")
                
                # Migration: category_id kolonunu ekle
                try:
                    from migrate_add_category_id import migrate_add_category_id
                    migrate_add_category_id()
                except Exception as e:
                    logger.warning(f"Migration uyarısı: {e}")
                    
                break # Başarılı olursa döngüden çık
                
            except OperationalError as e:
                logger.warning(f"DB bağlantısı bekleniyor ({attempt+1}/{max_retries})")
                time.sleep(2)
            except Exception as e:
                try:
                    logger.error(f"Beklenmeyen DB hatası: {str(e)}")
                except:
                    logger.error("DB hatası (decode edilemedi)")
                time.sleep(2)
                
    except Exception as e:
        logger.error("Startup kritik hata")

@app.get("/")
async def root():
    return {"message": "TUYGUN API is running", "version": "1.0.0"}

@app.get("/api/dashboard/stats", response_model=List[StatItem])
async def get_stats(db: Session = Depends(get_db)):
    """Dashboard'daki istatistik kartları için veri döner"""
    try:
        # Toplam belge sayısı
        total_docs = db.query(func.count(Document.id)).scalar() or 0
        
        # Toplam kaynak sayısı
        total_sources = db.query(func.count(Source.id)).scalar() or 0
        
        # Bugünkü sorgu sayısı (activities tablosundan)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_queries = db.query(func.count(Activity.id)).filter(
            Activity.type == ActivityType.query,
            Activity.created_at >= today_start
        ).scalar() or 0
        
        # Toplam embedding sayısı
        total_embeddings = db.query(func.sum(Document.embeddings_count)).scalar() or 0
        total_embeddings_k = f"{total_embeddings / 1000:.1f}K" if total_embeddings >= 1000 else str(total_embeddings)
        
        return [
            {"label": "Toplam Belge", "value": f"{total_docs:,}".replace(",", ".")},
            {"label": "Bilgi Kaynağı", "value": str(total_sources)},
            {"label": "Sorgu (Bugün)", "value": str(today_queries)},
            {"label": "Embedding", "value": total_embeddings_k}
        ]
    except Exception as e:
        # Hata durumunda fallback değerler
        return [
            {"label": "Toplam Belge", "value": "0"},
            {"label": "Bilgi Kaynağı", "value": "0"},
            {"label": "Sorgu (Bugün)", "value": "0"},
            {"label": "Embedding", "value": "0"}
        ]

@app.get("/api/dashboard/activities", response_model=List[ActivitySchema])
async def get_activities(db: Session = Depends(get_db)):
    """Dashboard'daki son aktiviteler için veri döner"""
    try:
        activities = db.query(Activity).order_by(desc(Activity.created_at)).limit(10).all()
        
        result = []
        for activity in activities:
            result.append({
                "type": activity.type.value,
                "title": activity.title,
                "time": format_time_ago(activity.created_at)
            })
        
        return result
    except Exception as e:
        print(f"Error fetching activities: {e}")
        return []

@app.get("/api/dashboard/sources", response_model=List[SourceSchema])
async def get_dashboard_sources(db: Session = Depends(get_db)):
    """Dashboard'daki bilgi kaynakları için veri döner"""
    try:
        sources = db.query(Source).all()
        
        result = []
        for source in sources:
            # Her kaynak için belge sayısını hesapla
            doc_count = db.query(func.count(Document.id)).filter(
                Document.source_id == source.id
            ).scalar() or 0
            
            result.append({
                "id": source.id,
                "name": source.name,
                "type": source.type,
                "doc_count": doc_count,
                "status": source.status.value,
                "progress": source.progress
            })
        
        return result
    except Exception as e:
        print(f"Error fetching dashboard sources: {e}")
        return []

@app.get("/api/documents", response_model=List[DocumentSchema])
async def get_documents(db: Session = Depends(get_db)):
    """KnowledgeBase sayfasındaki belgeler için veri döner"""
    try:
        documents = db.query(Document).order_by(desc(Document.updated_at)).all()
        
        result = []
        for doc in documents:
            # Source bilgisini al
            source = db.query(Source).filter(Source.id == doc.source_id).first()
            source_name = source.name if source else "Bilinmeyen"
            
            # Size formatını kontrol et, yoksa size_bytes'tan hesapla
            size = doc.size if doc.size else format_file_size(doc.size_bytes)
            
            result.append({
                "id": doc.id,
                "title": doc.title,
                "type": doc.type,
                "source": source_name,
                "size": size,
                "embeddings_count": doc.embeddings_count or 0,
                "last_updated": format_time_ago(doc.updated_at),
                "status": doc.status.value
            })
        
        return result
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return []

@app.get("/api/sources", response_model=List[SourceSchema])
async def get_sources(db: Session = Depends(get_db)):
    """KnowledgeBase sayfasındaki kaynaklar için veri döner"""
    try:
        sources = db.query(Source).all()
        
        result = []
        for source in sources:
            # Her kaynak için belge sayısını hesapla
            doc_count = db.query(func.count(Document.id)).filter(
                Document.source_id == source.id
            ).scalar() or 0
            
            result.append({
                "id": source.id,
                "name": source.name,
                "type": source.type,
                "doc_count": doc_count,
                "status": source.status.value,
                "progress": source.progress,
                "embeddings": source.total_embeddings,
                "last_sync": format_time_ago(source.last_sync_at) if source.last_sync_at else None
            })
        
        return result
    except Exception as e:
        print(f"Error fetching sources: {e}")
        return []

# ==================== THE CURATION FLOW ENDPOINTS ====================

@app.post("/api/rss/feeds", response_model=RSSFeedSchema)
async def add_rss_feed(feed_data: AddRSSFeedRequest, db: Session = Depends(get_db)):
    """RSS feed ekle"""
    try:
        # Name kontrolü
        if not feed_data.name or not feed_data.name.strip():
            raise HTTPException(status_code=400, detail="Feed adı gerekli")
        
        # URL kontrolü
        if not feed_data.url or not feed_data.url.strip():
            raise HTTPException(status_code=400, detail="Feed URL gerekli")
        
        # Feed'i parse et ve doğrula
        try:
            parsed = feedparser.parse(feed_data.url)
            if parsed.bozo:
                logger.warning(f"RSS feed parse uyarısı: {feed_data.url}")
                # Bozo olsa bile devam et, bazı feed'ler bozo olabilir ama çalışır
        except Exception as parse_error:
            logger.error(f"RSS feed parse hatası: {parse_error}")
            raise HTTPException(status_code=400, detail=f"RSS feed parse edilemedi: {str(parse_error)}")
        
        # Zaten var mı kontrol et (URL normalize et)
        normalized_url = feed_data.url.strip().rstrip('/')
        existing = db.query(RSSFeed).filter(
            (RSSFeed.url == normalized_url) | 
            (RSSFeed.url == feed_data.url.strip())
        ).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Bu RSS feed zaten ekli: {existing.name}"
            )
        
        # Kategoriyi bul veya oluştur
        category_id = None
        if feed_data.category:
            category = db.query(Category).filter(Category.name == feed_data.category.strip()).first()
            if not category:
                category = Category(
                    id=str(uuid.uuid4()),
                    name=feed_data.category.strip()
                )
                db.add(category)
                db.commit()
                db.refresh(category)
            category_id = category.id
        
        feed = RSSFeed(
            id=str(uuid.uuid4()),
            name=feed_data.name.strip(),
            url=normalized_url,
            category=feed_data.category.strip() if feed_data.category else None,  # Backward compatibility
            category_id=category_id,
            is_active="true"
        )
        db.add(feed)
        db.commit()
        db.refresh(feed)
        
        return {
            "id": feed.id,
            "name": feed.name,
            "url": feed.url,
            "category": feed.category_obj.name if feed.category_obj else feed.category,
            "is_active": feed.is_active == "true",
            "last_fetched_at": feed.last_fetched_at.isoformat() if feed.last_fetched_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"RSS feed ekleme hatası: {e}")
        raise HTTPException(status_code=500, detail=f"RSS feed eklenirken hata: {str(e)}")

@app.get("/api/rss/feeds", response_model=List[RSSFeedSchema])
async def get_rss_feeds(db: Session = Depends(get_db)):
    """Tüm RSS feed'leri listele"""
    try:
        from sqlalchemy.orm import joinedload
        feeds = db.query(RSSFeed).options(
            joinedload(RSSFeed.category_obj)
        ).filter(RSSFeed.is_active == "true").all()
        
        return [
            {
                "id": feed.id,
                "name": feed.name,
                "url": feed.url,
                "category": feed.category_obj.name if feed.category_obj else (feed.category or None),
                "is_active": feed.is_active == "true",
                "last_fetched_at": feed.last_fetched_at.isoformat() if feed.last_fetched_at else None
            }
            for feed in feeds
        ]
    except Exception as e:
        logger.error(f"Error fetching RSS feeds: {e}")
        return []

# ==================== CATEGORY ENDPOINTS ====================

@app.get("/api/categories", response_model=List[CategorySchema])
async def get_categories(db: Session = Depends(get_db)):
    """Tüm kategorileri listele"""
    try:
        categories = db.query(Category).order_by(Category.name).all()
        return [{"id": cat.id, "name": cat.name} for cat in categories]
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return []

@app.post("/api/categories", response_model=CategorySchema)
async def add_category(category_data: AddCategoryRequest, db: Session = Depends(get_db)):
    """Yeni kategori ekle"""
    try:
        if not category_data.name or not category_data.name.strip():
            raise HTTPException(status_code=400, detail="Kategori adı gerekli")
        
        # Aynı isimde kategori var mı kontrol et
        existing = db.query(Category).filter(
            Category.name.ilike(category_data.name.strip())
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bu isimde bir kategori zaten var")
        
        category = Category(
            id=str(uuid.uuid4()),
            name=category_data.name.strip()
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return {"id": category.id, "name": category.name}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding category: {e}")
        raise HTTPException(status_code=500, detail=f"Kategori eklenirken hata: {str(e)}")

@app.delete("/api/categories/{category_id}")
async def delete_category(category_id: str, db: Session = Depends(get_db)):
    """Kategori sil"""
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Kategori bulunamadı")
        
        # Kategoride feed var mı kontrol et
        feed_count = db.query(RSSFeed).filter(RSSFeed.category_id == category_id).count()
        if feed_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Bu kategoride {feed_count} feed var. Önce feed'leri silin veya başka kategoriye taşıyın."
            )
        
        db.delete(category)
        db.commit()
        
        return {"message": "Kategori silindi"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting category: {e}")
        raise HTTPException(status_code=500, detail=f"Kategori silinirken hata: {str(e)}")

@app.post("/api/rss/feeds/{feed_id}/fetch", response_model=List[ArticlePreviewSchema])
async def fetch_rss_feed(feed_id: str, db: Session = Depends(get_db)):
    """RSS feed'den başlıkları çek (henüz kaydetme!)"""
    try:
        feed = db.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
        if not feed:
            raise HTTPException(status_code=404, detail="RSS feed bulunamadı")
        
        # Feed'i parse et
        parsed = feedparser.parse(feed.url)
        if parsed.bozo:
            raise HTTPException(status_code=400, detail="RSS feed parse edilemedi")
        
        articles = []
        for entry in parsed.entries[:50]:  # İlk 50 makale
            # Zaten var mı kontrol et
            existing = db.query(Article).filter(Article.url == entry.link).first()
            if existing:
                continue
            
            # Yeni article oluştur (henüz scrape edilmedi, sadece başlık)
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except:
                    pass
            
            article = Article(
                id=str(uuid.uuid4()),
                feed_id=feed_id,
                title=entry.title,
                url=entry.link,
                author=getattr(entry, 'author', None),
                published_at=published_at,
                status=ArticleStatus.pending
            )
            db.add(article)
            articles.append(article)
        
        db.commit()
        
        # Feed'in last_fetched_at'ini güncelle
        feed.last_fetched_at = datetime.now(timezone.utc)
        db.commit()
        
        return [
            {
                "id": article.id,
                "feed_id": article.feed_id,
                "feed_name": feed.name,
                "title": article.title,
                "url": article.url,
                "author": article.author,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "status": article.status.value
            }
            for article in articles
        ]
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"RSS feed çekilirken hata: {str(e)}")

@app.post("/api/articles/{article_id}/preview", response_model=ArticleDetailSchema)
async def preview_article(article_id: str, db: Session = Depends(get_db)):
    """Makaleyi scrape et ve AI ile özetle (Süzgeç adımı)"""
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="Makale bulunamadı")
        
        # Eğer zaten scrape edildiyse, mevcut özeti döndür
        if article.content and article.summary:
            feed = db.query(RSSFeed).filter(RSSFeed.id == article.feed_id).first() if article.feed_id else None
            return {
                "id": article.id,
                "feed_id": article.feed_id,
                "feed_name": feed.name if feed else None,
                "title": article.title,
                "url": article.url,
                "content": article.content,
                "summary": article.summary,
                "author": article.author,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "status": article.status.value,
                "category": article.category
            }
        
        # 1. Link'i scrape et (Trafilatura ile)
        downloaded = trafilatura.fetch_url(article.url)
        if downloaded:
            content_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        
        # Fallback: Trafilatura başarısız olursa requests + bs4 (veya sadece hata mesajı)
        if not downloaded or not content_text:
             # Basic fallback
            try:
                response = requests.get(article.url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                # Basit p tag extraction
                content_text = ' '.join([p.get_text() for p in soup.find_all('p')])
            except Exception as e:
                logger.warning(f"Fallback scraping failed: {e}")
                content_text = "İçerik çekilemedi. Lütfen orijinal linki kontrol edin."

        # İlk 5000 karakteri al (Ollama için)
        content_text = content_text[:5000] if content_text else ""
        
        # 2. Ollama ile özetle
        try:
            import ollama
            # Wikilink'leri teşvik eden prompt (Nöro-Mimari)
            prompt = f"""Sen bir Bilgi Mimarı'sın. Bu metni analiz et ve "İkinci Beyin" için hazırla.

1. Makaleyi 3-4 cümlede Türkçe olarak özetle.
2. Önemli kavramları [[Kavram]] formatında parantez içine al (Wikilink).
3. En uygun 3 etiketi belirle (#etiket).
4. İlişkili 3 ana disiplini belirle ([[Disiplin]]).

Yanıtını TAM OLARAK şu formatta ver:
ÖZET: [Özet ve wikilinkler]
ETİKETLER: #etiket1 #etiket2
KONULAR: [[Konu 1]], [[Konu 2]]

Makale:
{content_text}"""
            
            ollama_response = ollama.generate(
                model='llama3',
                prompt=prompt
            )
            response_text = ollama_response.get('response', '').strip()
            
            # Parser
            summary = ""
            topics = []
            
            lines = response_text.split('\n')
            for line in lines:
                if line.startswith("ÖZET:"):
                    summary = line.replace("ÖZET:", "").strip()
                elif line.startswith("KONULAR:"):
                    topics_part = line.replace("KONULAR:", "").strip()
                    topics = [t.strip() for t in topics_part.split(',')]
            
            # Çok satırlı özet
            if "ÖZET:" in response_text and "KONULAR:" in response_text:
                start = response_text.find("ÖZET:") + 5
                end = response_text.find("ETİKETLER:") if "ETİKETLER:" in response_text else response_text.find("KONULAR:")
                summary = response_text[start:end].strip()
            
            if not summary:
                summary = response_text[:200] + "..." if content_text else "Özet oluşturulamadı."
        except Exception as ollama_error:
            # Ollama yoksa basit özet (ilk 200 karakter)
            summary = content_text[:200] + "..." if content_text else "Özet oluşturulamadı."
        
        # 3. Veritabanına kaydet
        article.content = content_text
        article.summary = summary
        article.status = ArticleStatus.previewed
        article.scraped_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(article)
        
        feed = db.query(RSSFeed).filter(RSSFeed.id == article.feed_id).first() if article.feed_id else None
        
        return {
            "id": article.id,
            "feed_id": article.feed_id,
            "feed_name": feed.name if feed else None,
            "title": article.title,
            "url": article.url,
            "content": article.content,
            "summary": article.summary,
            "author": article.author,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "status": article.status.value,
            "category": article.category
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Makale önizlenirken hata: {str(e)}")

@app.post("/api/articles/{article_id}/save")
async def save_article(article_id: str, save_data: SaveArticleRequest, db: Session = Depends(get_db)):
    """Makaleyi kaydet (Postgres + Obsidian) - Çifte Kayıt"""
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="Makale bulunamadı")
        
        if not article.content:
            raise HTTPException(status_code=400, detail="Makale henüz scrape edilmemiş")
        
        # 1. Postgres'e kaydet (Document olarak)
        # Önce "RSS/Web" source'unu bul veya oluştur
        rss_source = db.query(Source).filter(Source.name == SourceType.RSS_WEB.value).first()
        if not rss_source:
            rss_source = Source(
                id=str(uuid.uuid4()),
                name=SourceType.RSS_WEB.value,
                type="RSS",
                status=SourceStatus.active,
                progress=100
            )
            db.add(rss_source)
            db.commit()
        
        # Document oluştur
        document = Document(
            id=str(uuid.uuid4()),
            title=article.title,
            type="Web Article",
            source_id=rss_source.id,
            size=f"{len(article.content)} chars",
            size_bytes=len(article.content.encode('utf-8')),
            embeddings_count=0,  # Embedding henüz oluşturulmadı
            status=DocumentStatus.processing,
            doc_metadata=json.dumps({
                "url": article.url,
                "author": article.author,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "category": save_data.category
            })
        )
        db.add(document)
        
        # 2. Article'ı güncelle
        article.status = ArticleStatus.saved
        article.category = save_data.category
        
        # Obsidian vault path
        obsidian_vault_path = settings.OBSIDIAN_VAULT_PATH
        
        # Dosya adını temizle
        safe_title = generate_safe_filename(article.title)
        
        # Klasör Yapısı: Eğer kategori "Genel" ise "00_Inbox" yap
        target_category = save_data.category
        if not target_category or target_category == "Genel":
            target_category = "00_Inbox"
            
        obsidian_file_path = f"{obsidian_vault_path}/{target_category}/{safe_title}.md"
        
        # Klasörü oluştur
        os.makedirs(os.path.dirname(obsidian_file_path), exist_ok=True)
        
        # Konuları (topics) al - şimdilik manuel kayıtta topics verisi gelmeyebilir, boş geçiyoruz veya özetten çekiyoruz
        # (Gerçek senaryoda save_article request modeline topics eklenmeli, şimdilik empty list)
        topics_yaml = "[]" 

        # Frontmatter Standartları (Nöro-Mimari)
        frontmatter = f"""---
uuid: {datetime.now().strftime('%Y%m%d%H%M')}
type: source/article
status: 📥
url: "{article.url}"
author: {article.author or 'Unknown'}
publish_date: {datetime.now().strftime('%Y-%m-%d')}
topics: {topics_yaml}
tags: [tuygun, imported, {save_data.category.split('/')[-1] if '/' in save_data.category else save_data.category}]
---"""

        markdown_content = f"""{frontmatter}

# {article.title}

## 🦅 TUYGUN Özeti
> {article.summary}

## İçerik

{article.content}

---
*Created by TUYGUN at {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        
        # Dosyayı kaydet
        try:
            with open(obsidian_file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            logger.info(f"✅ Obsidian'a kaydedildi (Manuel): {obsidian_file_path}")
        except Exception as obsidian_error:
            logger.error(f"❌ Obsidian kayıt hatası (Manuel): {obsidian_error}")
            # Hata olsa bile devam et

        # Dosyayı kaydet (şimdilik sadece path'i kaydet)
        article.obsidian_path = obsidian_file_path
        
        db.commit()
        
        # Activity log
        activity = Activity(
            id=str(uuid.uuid4()),
            type=ActivityType.document,
            title=f"'{article.title}' makalesi kaydedildi",
            description=f"Kategori: {save_data.category}",
            activity_metadata=json.dumps({"article_id": article_id, "category": save_data.category})
        )
        db.add(activity)
        db.commit()
        
        return {"message": "Makale başarıyla kaydedildi", "article_id": article_id, "document_id": document.id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        try:
            error_msg = str(e)
        except:
             # ...
            try:
                error_msg = str(e).encode('utf-8', 'ignore').decode('utf-8')
            except:
                error_msg = "Bilinmeyen veritabanı hatası"
        raise HTTPException(status_code=500, detail=f"Makale kaydedilirken hata: {error_msg}")

@app.post("/api/articles/{article_id}/skip")
async def skip_article(article_id: str, db: Session = Depends(get_db)):
    """Makaleyi pas geç (RAM'den sil)"""
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="Makale bulunamadı")
        
        article.status = ArticleStatus.skipped
        db.commit()
        
        return {"message": "Makale pas geçildi", "article_id": article_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Makale pas geçilirken hata: {str(e)}")

@app.post("/api/articles/link", response_model=ArticleDetailSchema)
async def add_link(link_data: AddLinkRequest, db: Session = Depends(get_db)):
    """Tekil bir link ekle (RSS feed değil)"""
    try:
        # Zaten var mı kontrol et
        existing = db.query(Article).filter(Article.url == link_data.url).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bu link zaten ekli")
        
        # Link'ten başlığı çek
        response = requests.get(link_data.url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title')
        title_text = title.get_text() if title else "Başlıksız Makale"
        
        article = Article(
            id=str(uuid.uuid4()),
            feed_id=None,
            title=title_text,
            url=link_data.url,
            category=link_data.category,
            status=ArticleStatus.pending
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        
        return {
            "id": article.id,
            "feed_id": None,
            "feed_name": None,
            "title": article.title,
            "url": article.url,
            "content": None,
            "summary": None,
            "author": None,
            "published_at": None,
            "status": article.status.value,
            "category": article.category
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        try:
            error_msg = str(e)
        except:
            try:
                error_msg = str(e).encode('utf-8', 'ignore').decode('utf-8')
            except:
                error_msg = "Bilinmeyen veritabanı hatası"
        raise HTTPException(status_code=500, detail=f"Link eklenirken hata: {error_msg}")

@app.get("/api/articles/pending", response_model=List[ArticlePreviewSchema])
async def get_pending_articles(db: Session = Depends(get_db)):
    """Bekleyen makaleleri listele (Radar listesi)"""
    try:
        articles = db.query(Article).filter(
            Article.status.in_([ArticleStatus.pending, ArticleStatus.previewed])
        ).order_by(Article.created_at.desc()).limit(100).all()
        
        result = []
        for article in articles:
            feed = db.query(RSSFeed).filter(RSSFeed.id == article.feed_id).first() if article.feed_id else None
            result.append({
                "id": article.id,
                "feed_id": article.feed_id,
                "feed_name": feed.name if feed else None,
                "title": article.title,
                "url": article.url,
                "author": article.author,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "status": article.status.value
            })
        
        return result
    except Exception as e:
        print(f"Error fetching pending articles: {e}")
        return []

# ==================== BASİT CURATION FLOW ENDPOINTS (Direkt RSS URL) ====================

@app.post("/api/rss/fetch")
async def fetch_rss_direct(request: dict):
    """RSS URL'den direkt başlıkları çek (veritabanına kaydetmeden)"""
    try:
        url = request.get('url')
        if not url:
            raise HTTPException(status_code=400, detail="URL gerekli")
        
        # Feed'i parse et
        parsed = feedparser.parse(url)
        if parsed.bozo:
            raise HTTPException(status_code=400, detail="RSS feed parse edilemedi")
        
        items = []
        for entry in parsed.entries[:50]:  # İlk 50 makale
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                except:
                    published = datetime.now(timezone.utc).isoformat()
            else:
                published = datetime.now(timezone.utc).isoformat()
            
            # RSS'ten gelen etiketleri çek (varsa)
            rss_tags = []
            if hasattr(entry, 'tags') and entry.tags:
                rss_tags = [tag.term for tag in entry.tags[:5]]  # En fazla 5 etiket
            
            items.append({
                "title": entry.title,
                "link": entry.link,
                "published": published,
                "summary": entry.get('summary', '')[:200] + '...' if entry.get('summary') else '',
                "tags": rss_tags  # RSS'ten gelen etiketler
            })
        
        return items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RSS feed çekilirken hata: {str(e)}")

@app.post("/api/rss/preview")
async def preview_rss_article(request: dict):
    """Makaleyi scrape et ve AI ile özetle"""
    try:
        print("DEBUG: PREVIEW FUNCTION CALLED - NEW CODE ACTIVE")
        url = request.get('url')
        if not url:
            raise HTTPException(status_code=400, detail="URL gerekli")
        
        # 1. Link'i scrape et (Trafilatura ile)
        downloaded = trafilatura.fetch_url(url)
        content_text = ""
        title = "Başlıksız Makale"
        
        if downloaded:
            content_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            t = trafilatura.bare_extraction(downloaded)
            if t and t.get('title'):
                title = t['title']
            
        if not content_text:
            # Fallback
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                content_text = ' '.join([p.get_text() for p in soup.find_all('p')])
                if soup.title:
                    title = soup.title.string
            except Exception:
                content_text = ""
        
        # İlk 5000 karakteri al (Ollama için)
        content_text = content_text[:5000] if content_text else ""
        
        # 2. Ollama ile özetle ve etiketle
        ai_summary = ""
        ai_tags = []
        
        try:
            import ollama
            # Özet ve etiketleri tek seferde iste
            # Özet ve etiketleri tek seferde iste
            prompt = f"""Sen bir Bilgi Mimarı'sın (Information Architect). Görevin bu metni analiz edip Obsidian "İkinci Beyin" sistemine uygun hale getirmek.

Lütfen şunları yap:
1. Makaleyi 3-4 cümlede Türkçe olarak özetle.
2. Özetin içinde geçen TEKNİK TERİMLERİ, ÖNEMLİ KİŞİLERİ ve ANA KONSEPTLERİ mutlaka [[Kavram]] formatında parantez içine al (Wikilink).
3. Makalenin içeriğine göre en uygun 3 etiketi belirle (Türkçe, # formatında, örn: #yapayzeka).
4. Makalenin ilişkili olduğu 3 ana disiplini belirle (Örn: [[Yapay Zeka]], [[Makine Öğrenmesi]]).

Yanıtını TAM OLARAK şu formatta ver (başka bir şey yazma):
ÖZET: [Özet ve wikilinkler buraya]
ETİKETLER: #etiket1 #etiket2 #etiket3
KONULAR: [[Konu 1]], [[Konu 2]], [[Konu 3]]

Makale:
{content_text}"""
            
            ollama_response = ollama.generate(
                model='llama3',
                prompt=prompt
            )
            response_text = ollama_response.get('response', '').strip()
            
            # Parse response
            ai_summary = ""
            ai_tags = []
            ai_topics = []

            # Basit parser
            lines = response_text.split('\n')
            for line in lines:
                if line.startswith("ÖZET:"):
                    ai_summary = line.replace("ÖZET:", "").strip()
                elif line.startswith("ETİKETLER:"):
                    tags_part = line.replace("ETİKETLER:", "").strip()
                    ai_tags = [t.strip() for t in tags_part.split(' ') if t.strip().startswith('#')]
                elif line.startswith("KONULAR:"):
                    topics_part = line.replace("KONULAR:", "").strip()
                    # [[Konu 1]], [[Konu 2]] formatını parse et
                    ai_topics = [t.strip() for t in topics_part.split(',')]

            # Çok satırlı özet durumunda devamını yakala (ÖZET satırından sonraki satırlar, ETİKETLER'e kadar)
            if "ÖZET:" in response_text and "ETİKETLER:" in response_text:
                start = response_text.find("ÖZET:") + 5
                end = response_text.find("ETİKETLER:")
                ai_summary = response_text[start:end].strip()

        except Exception as ollama_error:
            # Ollama yoksa basit özet (ilk 200 karakter)
            ai_summary = content_text[:200] + "..."
            ai_tags = []
            ai_topics = []
        
        return {
            "title": title,
            "content": content_text,
            "ai_summary": ai_summary,
            "ai_tags": ai_tags,
            "ai_topics": ai_topics
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Makale önizlenirken hata: {str(e)}")

@app.post("/api/rss/save")
async def save_rss_article(request: dict, db: Session = Depends(get_db)):
    """Makaleyi kaydet (Postgres + Obsidian) - Çifte Kayıt"""
    try:
        title = request.get('title')
        content = request.get('content')
        url = request.get('url')
        category = request.get('category', 'Genel')
        ai_summary = request.get('ai_summary', '')
        ai_tags = request.get('ai_tags', [])  # AI'dan gelen etiketler
        ai_topics = request.get('ai_topics', []) # AI'dan gelen konular (wikilinks)
        rss_tags = request.get('rss_tags', [])  # RSS'ten gelen etiketler
        
        # Tüm etiketleri birleştir (tekrarları kaldır, # işaretlerini temizle)
        all_tags_raw = []
        for tag in ai_tags + rss_tags:
            # # işaretini kaldır ve temizle
            clean_tag = tag.replace('#', '').strip() if isinstance(tag, str) else str(tag).replace('#', '').strip()
            if clean_tag:
                all_tags_raw.append(clean_tag)
        
        # Tekrarları kaldır (sırayı koruyarak)
        all_tags = list(dict.fromkeys(all_tags_raw))
        
        if not title or not content or not url:
            raise HTTPException(status_code=400, detail="title, content ve url gerekli")
        
        # 1. Postgres'e kaydet (Document olarak)
        # Önce "RSS/Web" source'unu bul veya oluştur
        rss_source = db.query(Source).filter(Source.name == "RSS/Web").first()
        if not rss_source:
            rss_source = Source(
                id=str(uuid.uuid4()),
                name="RSS/Web",
                type="RSS",
                status=SourceStatus.active,
                progress=100
            )
            db.add(rss_source)
            db.commit()
        
        # 3. Vektör oluştur (RAG için)
        embedding_vector = None
        try:
            # İçeriği vektörleştir (özet + içerik birleşimi daha iyi sonuç verir)
            text_for_embedding = f"{title}\n\n{ai_summary}\n\n{content[:2000]}"  # İlk 2000 karakter
            embedding_vector = generate_embedding(text_for_embedding)
            if embedding_vector:
                logger.info(f"Embedding oluşturuldu: {len(embedding_vector)} boyutlu")
        except Exception as e:
            logger.warning(f"Embedding oluşturulamadı (devam ediliyor): {e}")
        
        # Document oluştur
        document = Document(
            id=str(uuid.uuid4()),
            title=title,
            type="Web Article",
            source_id=rss_source.id,
            size=f"{len(content)} chars",
            size_bytes=len(content.encode('utf-8')),
            content=content,  # RAG için içerik
            embeddings_count=1 if embedding_vector else 0,
            status=DocumentStatus.indexed if embedding_vector else DocumentStatus.processing,
            embedding=embedding_vector,  # Vektörü kaydet
            doc_metadata=json.dumps({
                "url": url,
                "category": category,
                "ai_summary": ai_summary,
                "ai_tags": ai_tags,
                "ai_topics": ai_topics,
                "rss_tags": rss_tags,
                "all_tags": all_tags
            })
        )
        db.add(document)
        
        # 2. Obsidian'a kaydet (dosya sistemi)
        import os
        # Obsidian vault path'i environment variable'dan al
        obsidian_vault_path = os.getenv('OBSIDIAN_VAULT_PATH', '/app/obsidian_vault')
        
        # Klasör Yapısı (00_Inbox Default)
        # Eğer kategori "Genel" ise veya boşsa otomatik "00_Inbox" yap
        target_folder = category
        if not target_folder or target_folder == "Genel":
            target_folder = "00_Inbox"
        
        category_path = target_folder.replace('/', os.sep)
        obsidian_dir = os.path.join(obsidian_vault_path, category_path)
        
        # Klasörü oluştur
        os.makedirs(obsidian_dir, exist_ok=True)
        
        # Dosya adını temizle (geçersiz karakterleri kaldır)
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:100]
        obsidian_file_path = os.path.join(obsidian_dir, f"{safe_title}.md")
        
        # YAML formatında konular (wikilinks)
        topics_yaml = f"[{', '.join(ai_topics)}]" if ai_topics else "[]"
        tags_yaml = "\n".join([f"  - {tag}" for tag in all_tags]) if all_tags else "  - imported"
        
        # Frontmatter Standartları (Nöro-Mimari)
        markdown_content = f"""---
uuid: {datetime.now().strftime('%Y%m%d%H%M')}
type: source/article
status: 📥
url: "{url}"
author: Unknown
publish_date: {datetime.now().strftime('%Y-%m-%d')}
topics: {topics_yaml}
tags:
{tags_yaml}
---

# {title}

## 🦅 TUYGUN Özeti

> {ai_summary}

---

## Orjinal İçerik

{content}

---
*Created by TUYGUN at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # Dosyayı kaydet
        try:
            with open(obsidian_file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            logger.info(f"✅ Obsidian'a kaydedildi: {obsidian_file_path}")
        except Exception as obsidian_error:
            logger.error(f"❌ Obsidian kayıt hatası: {obsidian_error}")
            logger.error(f"   Vault path: {obsidian_vault_path}")
            logger.error(f"   Klasör: {obsidian_dir}")
            logger.error(f"   Dosya: {obsidian_file_path}")
            # Obsidian hatası olsa bile Postgres'e kaydedildi, devam et
        
        # Activity log
        activity = Activity(
            id=str(uuid.uuid4()),
            type=ActivityType.document,
            title=f"'{title}' makalesi kaydedildi",
            description=f"Kategori: {category}",
            activity_metadata=json.dumps({"url": url, "category": category})
        )
        db.add(activity)
        db.commit()
        
        return {
            "message": "Makale başarıyla kaydedildi",
            "document_id": document.id,
            "obsidian_path": obsidian_file_path
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        try:
            error_msg = str(e)
        except:
            try:
                error_msg = str(e).encode('utf-8', 'ignore').decode('utf-8')
            except:
                error_msg = "Bilinmeyen veritabanı hatası"
        raise HTTPException(status_code=500, detail=f"Makale kaydedilirken hata: {error_msg}")

# ==================== RAG CHAT ENDPOINT ====================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    RAG (Retrieval-Augmented Generation) Chat Endpoint
    Kullanıcı sorusunu alır, veritabanında semantic search yapar,
    bulunan kaynakları LLM'e gönderir ve cevap döner.
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Mesaj boş olamaz")
        
        # RAG servisini çağır
        response = await chat_with_data(db, request.message.strip())
        
        # Activity log ekle
        try:
            activity = Activity(
                id=str(uuid.uuid4()),
                type=ActivityType.query,
                title=f"Soru: {request.message[:50]}...",
                description=response.get('answer', '')[:200]
            )
            db.add(activity)
            db.commit()
        except Exception as log_error:
            logger.warning(f"Activity log hatası: {log_error}")
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Sohbet hatası: {str(e)}")
