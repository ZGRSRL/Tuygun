from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load env directly to be sure
load_dotenv(r"D:\Tuygun\.env")

user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5432")
db_name = os.getenv("POSTGRES_DB", "zgrwise")

DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
print(f"Connecting to: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Successfully connected!")
        
        # Test SET commands
        print("Testing SET commands...")
        conn.execute(text("SET client_encoding = 'UTF8'"))
        conn.execute(text("SET lc_messages = 'C'"))
        print("SET commands success.")
        
        result = conn.execute(text("SELECT 1"))
        print(f"Test Query Result: {result.fetchone()}")
        
        # Test encoding
        try:
            conn.execute(text("SELECT 'test'"))
            print("Select string success")
        except Exception as e:
            print(f"Select string failed: {e}")

        # Check tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result]
        print(f"Tables: {tables}")
        
        if 'articles' in tables:
            print("Articles table exists.")
            # Try simple insert
            try:
                import uuid
                aid = str(uuid.uuid4())
                conn.execute(text(
                    "INSERT INTO articles (id, title, url, status) VALUES (:id, 'Test Title', :url, 'pending')"
                ), {"id": aid, "url": f"http://test.com/{aid}"})
                conn.commit()
                print("Insert article success")
            except Exception as e:
                print(f"Insert article failed: {e}")
            # Try to read all articles to check for bad encoding
            print("Reading all articles...")
            rows = conn.execute(text("SELECT * FROM articles")).fetchall()
            print(f"Read {len(rows)} articles successfully.")
            
            # Replicate add_link logic
            print("Testing requests + insert...")
            import requests
            from bs4 import BeautifulSoup
            
            url = "https://example.com"
            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.find('title')
            title_text = title.get_text() if title else "No Title"
            print(f"Fetched title: {title_text}")
            
            # Test ORM
            print("Testing ORM insert...")
            from sqlalchemy.orm import sessionmaker, declarative_base
            from sqlalchemy import Column, String, Text
            
            Base = declarative_base()
            class ArticleModel(Base):
                __tablename__ = "articles"
                id = Column(String, primary_key=True)
                title = Column(String)
                url = Column(String)
                status = Column(String)
                
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                aid3 = str(uuid.uuid4())
                art = ArticleModel(id=aid3, title="ORM Title", url=f"http://test-orm.com/{aid3}", status="pending")
                session.add(art)
                session.commit()
                print(f"ORM insert success. ID: {aid3}")
            except Exception as e:
                print(f"ORM insert failed: {e}")
                session.rollback()
            finally:
                session.close()

        else:
            print("Articles table MISSING!")

except Exception as e:
    print(f"Connection failed: {e}")
    import traceback
    traceback.print_exc()
