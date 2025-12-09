"""
zgrwise veritabanına tabloları oluşturur ve örnek veriler ekler
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Document, Source, Activity, DocumentStatus, SourceStatus, ActivityType
from datetime import datetime, timedelta, timezone
import uuid

# zgrwise veritabanına bağlan
# Eğer mergenlite-db-1 container'ı kullanıyorsak, localhost:5432 üzerinden erişebiliriz
DATABASE_URL = os.getenv(
    "ZGRWISE_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/zgrwise"
)

print(f"Connecting to database: {DATABASE_URL}")

# SQLAlchemy engine oluştur
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Tabloları oluştur"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

def seed_database():
    """Örnek veriler ekle"""
    db = SessionLocal()
    try:
        # Eğer zaten veri varsa, seed yapma
        from sqlalchemy import func
        source_count = db.query(func.count(Source.id)).scalar() or 0
        if source_count > 0:
            print(f"Database already has {source_count} sources, skipping seed...")
            return
        
        print("Seeding database with sample data...")
        
        # Sources oluştur
        sources_data = [
            {
                "id": str(uuid.uuid4()),
                "name": "Obsidian Notes",
                "type": "Markdown",
                "status": SourceStatus.active,
                "progress": 100,
                "total_embeddings": 15678,
                "last_sync_at": datetime.now(timezone.utc) - timedelta(minutes=10)
            },
            {
                "id": str(uuid.uuid4()),
                "name": "PDF Documents",
                "type": "PDF",
                "status": SourceStatus.active,
                "progress": 100,
                "total_embeddings": 8934,
                "last_sync_at": datetime.now(timezone.utc) - timedelta(hours=1)
            },
            {
                "id": str(uuid.uuid4()),
                "name": "SAP Codes",
                "type": "Code",
                "status": SourceStatus.syncing,
                "progress": 67,
                "total_embeddings": 12456,
                "last_sync_at": datetime.now(timezone.utc) - timedelta(hours=2)
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Qlik Scripts",
                "type": "Script",
                "status": SourceStatus.active,
                "progress": 100,
                "total_embeddings": 6789,
                "last_sync_at": datetime.now(timezone.utc) - timedelta(hours=5)
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Email Archive",
                "type": "Email",
                "status": SourceStatus.pending,
                "progress": 0,
                "total_embeddings": 0,
                "last_sync_at": None
            }
        ]
        
        sources = []
        for source_data in sources_data:
            source = Source(**source_data)
            db.add(source)
            sources.append(source)
        
        db.commit()
        print(f"Created {len(sources)} sources")
        
        # Documents oluştur
        documents_data = [
            {
                "id": str(uuid.uuid4()),
                "title": "SAP_ABAP_Functions.pdf",
                "type": "PDF",
                "source_id": sources[1].id,  # PDF Documents
                "size": "2.4 MB",
                "size_bytes": 2516582,
                "embeddings_count": 1248,
                "status": DocumentStatus.indexed,
                "updated_at": datetime.now(timezone.utc) - timedelta(hours=2)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Qlik_Script_Guide.md",
                "type": "Markdown",
                "source_id": sources[0].id,  # Obsidian Notes
                "size": "156 KB",
                "size_bytes": 159744,
                "embeddings_count": 342,
                "status": DocumentStatus.indexed,
                "updated_at": datetime.now(timezone.utc) - timedelta(hours=5)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "KPI_Definitions_2024.docx",
                "type": "DOCX",
                "source_id": sources[4].id,  # Email Archive
                "size": "892 KB",
                "size_bytes": 913408,
                "embeddings_count": 567,
                "status": DocumentStatus.processing,
                "updated_at": datetime.now(timezone.utc) - timedelta(days=1)
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Database_Schema.sql",
                "type": "SQL",
                "source_id": sources[2].id,  # SAP Codes
                "size": "48 KB",
                "size_bytes": 49152,
                "embeddings_count": 89,
                "status": DocumentStatus.indexed,
                "updated_at": datetime.now(timezone.utc) - timedelta(days=3)
            }
        ]
        
        for doc_data in documents_data:
            doc = Document(**doc_data)
            db.add(doc)
        
        db.commit()
        print(f"Created {len(documents_data)} documents")
        
        # Activities oluştur
        activities_data = [
            {
                "id": str(uuid.uuid4()),
                "type": ActivityType.document,
                "title": "SAP_Documentation.pdf yüklendi",
                "created_at": datetime.now(timezone.utc) - timedelta(minutes=5)
            },
            {
                "id": str(uuid.uuid4()),
                "type": ActivityType.query,
                "title": "KPI hesaplama fonksiyonu sorgulandı",
                "created_at": datetime.now(timezone.utc) - timedelta(minutes=12)
            },
            {
                "id": str(uuid.uuid4()),
                "type": ActivityType.embedding,
                "title": "45 yeni belge vektörleştirildi",
                "created_at": datetime.now(timezone.utc) - timedelta(hours=1)
            },
            {
                "id": str(uuid.uuid4()),
                "type": ActivityType.source,
                "title": "Obsidian senkronizasyonu tamamlandı",
                "created_at": datetime.now(timezone.utc) - timedelta(hours=2)
            }
        ]
        
        for activity_data in activities_data:
            activity = Activity(**activity_data)
            db.add(activity)
        
        db.commit()
        print(f"Created {len(activities_data)} activities")
        
        print("Database seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    if init_database():
        seed_database()
    else:
        print("Failed to initialize database")

