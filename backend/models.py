from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime

# pgvector için Vector tipi
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    # pgvector yoksa fallback (development için)
    VECTOR_AVAILABLE = False
    Vector = None

# Enum'lar
class DocumentStatus(str, enum.Enum):
    indexed = "indexed"
    processing = "processing"
    error = "error"

class SourceStatus(str, enum.Enum):
    active = "active"
    syncing = "syncing"
    error = "error"
    pending = "pending"

class ActivityType(str, enum.Enum):
    document = "document"
    query = "query"
    embedding = "embedding"
    source = "source"

class SourceType(str, enum.Enum):
    RSS_WEB = "RSS/Web"
    MANUAL = "Manual"

class ArticleStatus(str, enum.Enum):
    pending = "pending"  # Henüz özetlenmedi
    previewed = "previewed"  # Özet oluşturuldu, karar bekleniyor
    saved = "saved"  # Kaydedildi
    skipped = "skipped"  # Pas geçildi

# Document Model
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)  # PDF, Markdown, DOCX, SQL, etc.
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    size = Column(String, nullable=False)  # "2.4 MB", "156 KB", etc.
    size_bytes = Column(Integer, nullable=True)  # Gerçek byte değeri
    content = Column(Text, nullable=True)  # RAG için içerik (yeni eklendi)
    embeddings_count = Column(Integer, default=0)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.processing)
    file_path = Column(String, nullable=True)  # Dosyanın fiziksel yolu
    content_hash = Column(String, nullable=True)  # Dosya hash'i (duplicate kontrolü için)
    doc_metadata = Column(Text, nullable=True)  # JSON metadata (metadata reserved olduğu için doc_metadata)
    
    # Vector embedding (384 boyutlu - all-MiniLM-L6-v2 için)
    embedding = Column(Vector(384), nullable=True) if VECTOR_AVAILABLE else Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    source = relationship("Source", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title}, status={self.status})>"

# Source Model
class Source(Base):
    __tablename__ = "sources"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    type = Column(String, nullable=False)  # Markdown, PDF, Code, Script, Email, etc.
    status = Column(SQLEnum(SourceStatus), default=SourceStatus.pending)
    progress = Column(Integer, default=0)  # 0-100 arası
    total_embeddings = Column(Integer, default=0)
    source_config = Column(Text, nullable=True)  # JSON config (API keys, paths, etc.) (config reserved olabilir)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Source(id={self.id}, name={self.name}, status={self.status})>"

# Activity Model (Log tablosu)
class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(String, primary_key=True, index=True)
    type = Column(SQLEnum(ActivityType), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    activity_metadata = Column(Text, nullable=True)  # JSON metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<Activity(id={self.id}, type={self.type}, title={self.title})>"

# Category Model (RSS Feed kategorileri için)
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    feeds = relationship("RSSFeed", back_populates="category_obj", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"

# RSS Feed Model
class RSSFeed(Base):
    __tablename__ = "rss_feeds"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True, index=True)
    category = Column(String, nullable=True)  # Teknoloji, İş, Bilim, etc. (backward compatibility)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)  # Yeni kategori referansı
    is_active = Column(String, default="true")  # Boolean yerine string (SQLite uyumluluğu için)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    articles = relationship("Article", back_populates="feed", cascade="all, delete-orphan")
    category_obj = relationship("Category", back_populates="feeds")
    
    def __repr__(self):
        return f"<RSSFeed(id={self.id}, name={self.name}, url={self.url})>"

# Article Model (RSS/Web makaleleri için)
class Article(Base):
    __tablename__ = "articles"
    
    id = Column(String, primary_key=True, index=True)
    feed_id = Column(String, ForeignKey("rss_feeds.id"), nullable=True)  # RSS feed'den geliyorsa
    title = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False, unique=True, index=True)
    content = Column(Text, nullable=True)  # Orijinal içerik (scraped)
    summary = Column(Text, nullable=True)  # AI özeti (3 cümle)
    author = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    scraped_at = Column(DateTime(timezone=True), nullable=True)  # Ne zaman scrape edildi
    status = Column(SQLEnum(ArticleStatus), default=ArticleStatus.pending)
    category = Column(String, nullable=True)  # Kullanıcının seçtiği kategori (Inbox/AI, Inbox/Sağlık, etc.)
    obsidian_path = Column(String, nullable=True)  # Obsidian'a kaydedildiğinde dosya yolu
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    feed = relationship("RSSFeed", back_populates="articles")
    
    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title}, status={self.status})>"

