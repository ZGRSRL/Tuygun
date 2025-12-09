from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# SQLAlchemy engine oluştur
engine = create_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=True,  # Bağlantı koparsa otomatik yeniden bağlan
    pool_size=10,
    max_overflow=20,
    connect_args={"options": "-c client_encoding=utf8 -c lc_messages=C"}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency: Her request için yeni bir DB session oluştur
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

