"""
Migration: rss_feeds tablosuna category_id kolonu ekle
"""
from database import engine, SessionLocal
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def migrate_add_category_id():
    """rss_feeds tablosuna category_id kolonu ekle"""
    db = SessionLocal()
    try:
        # Önce categories tablosunu oluştur (yoksa)
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS categories (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        db.commit()
        logger.info("categories tablosu oluşturuldu/kontrol edildi.")
        
        # category_id kolonunu ekle (yoksa)
        # PostgreSQL'de IF NOT EXISTS yok, önce kontrol et
        try:
            # Kolon var mı kontrol et
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='rss_feeds' AND column_name='category_id';
            """))
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                db.execute(text("""
                    ALTER TABLE rss_feeds 
                    ADD COLUMN category_id VARCHAR;
                """))
                db.commit()
                logger.info("category_id kolonu eklendi.")
                
                # Foreign key constraint ekle
                try:
                    db.execute(text("""
                        ALTER TABLE rss_feeds 
                        ADD CONSTRAINT fk_rss_feeds_category 
                        FOREIGN KEY (category_id) REFERENCES categories(id);
                    """))
                    db.commit()
                    logger.info("Foreign key constraint eklendi.")
                except Exception as fk_error:
                    logger.warning(f"Foreign key eklenirken uyarı: {fk_error}")
                    db.rollback()
            else:
                logger.info("category_id kolonu zaten mevcut.")
        except Exception as e:
            logger.error(f"category_id kolonu eklenirken hata: {e}")
            db.rollback()
        
        # Index ekle
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rss_feeds_category_id 
                ON rss_feeds(category_id);
            """))
            db.commit()
            logger.info("category_id index'i eklendi.")
        except Exception as e:
            logger.warning(f"Index eklenirken uyarı: {e}")
            db.rollback()
        
        logger.info("Migration tamamlandı!")
        
    except Exception as e:
        logger.error(f"Migration hatası: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_category_id()

