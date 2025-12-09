from pydantic import BaseModel
from typing import List, Optional, Literal

# Dashboard'daki 'Stats' kartları için
class StatItem(BaseModel):
    label: str
    value: str
    trend: Optional[str] = None

# KnowledgeBase.tsx'deki 'Document' interface'i
class DocumentSchema(BaseModel):
    id: str
    title: str
    type: str      # PDF, Markdown, DOCX...
    source: str    # Obsidian, Drive...
    size: str
    embeddings_count: int
    last_updated: str
    status: Literal['indexed', 'processing', 'error']

# Dashboard ve KnowledgeBase için 'Source' interface'i
class SourceSchema(BaseModel):
    id: str
    name: str
    type: str
    doc_count: int
    status: Literal['active', 'syncing', 'error', 'pending']
    progress: int  # 0-100 arası
    embeddings: Optional[int] = None
    last_sync: Optional[str] = None

# Dashboard için Recent Activity
class ActivitySchema(BaseModel):
    type: str  # document, query, embedding, source
    title: str
    time: str

# RSS Feed Schema
class RSSFeedSchema(BaseModel):
    id: str
    name: str
    url: str
    category: Optional[str] = None
    is_active: bool = True
    last_fetched_at: Optional[str] = None

# Article Schema (Radar listesi için)
class ArticlePreviewSchema(BaseModel):
    id: str
    feed_id: Optional[str] = None
    feed_name: Optional[str] = None
    title: str
    url: str
    author: Optional[str] = None
    published_at: Optional[str] = None
    status: Literal['pending', 'previewed', 'saved', 'skipped']

# Article Detail Schema (AI özet ile)
class ArticleDetailSchema(BaseModel):
    id: str
    feed_id: Optional[str] = None
    feed_name: Optional[str] = None
    title: str
    url: str
    content: Optional[str] = None  # Orijinal içerik
    summary: Optional[str] = None  # AI özeti
    author: Optional[str] = None
    published_at: Optional[str] = None
    status: Literal['pending', 'previewed', 'saved', 'skipped']
    category: Optional[str] = None

# RSS Feed Ekleme Request
class AddRSSFeedRequest(BaseModel):
    name: str
    url: str
    category: Optional[str] = None

# Link Ekleme Request
class AddLinkRequest(BaseModel):
    url: str
    category: Optional[str] = None

# Article Kaydetme Request
class SaveArticleRequest(BaseModel):
    article_id: str
    category: str  # Inbox/AI, Inbox/Sağlık, etc.

# Category Schema
class CategorySchema(BaseModel):
    id: str
    name: str

class AddCategoryRequest(BaseModel):
    name: str

# RAG Chat Modelleri
class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []  # Önceki konuşmalar (Opsiyonel, Context için)

class SourceDoc(BaseModel):
    title: str
    url: Optional[str] = None
    similarity: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDoc]  # Cevabın dayandığı kaynaklar



