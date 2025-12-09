from sqlalchemy import create_engine, text
import requests
import uuid
import os
import json
from dotenv import load_dotenv

# Config
BASE_URL = "http://localhost:8000"
load_dotenv(r"D:\Tuygun\.env")

user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5432")
db_name = os.getenv("POSTGRES_DB", "zgrwise")

DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

def test_force_save():
    print("Initializing Force Save Test...")
    
    # 1. Insert Article manually
    try:
        engine = create_engine(DATABASE_URL)
        aid = str(uuid.uuid4())
        title = "Force Save Test Article"
        url = f"http://force-save.com/{aid}"
        
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO articles (id, title, url, status, content) VALUES (:id, :title, :url, 'pending', 'Dummy Content')"
            ), {"id": aid, "title": title, "url": url})
            conn.commit()
            print(f"✅ Inserted article {aid} manually.")
            
    except Exception as e:
        print(f"❌ DB Insert failed: {e}")
        return

    # 2. Call Save API
    print(f"Attempting to save article {aid} via API...")
    try:
        payload = {
            "article_id": aid,
            "category": "Test/ForceSave"
        }
        response = requests.post(f"{BASE_URL}/api/articles/{aid}/save", json=payload)
        
        if response.status_code == 200:
            print("✅ SUCCESS: Article saved via API.")
            print(f"Response: {response.json()}")
            
            # Verify file
            obsidian_path = r"G:\Drive'ım\TUYGUN"
            expected_file = os.path.join(obsidian_path, "Test", "ForceSave", "Force Save Test Article.md")
            print(f"Checking for file: {expected_file}")
            
            if os.path.exists(expected_file):
                print("✅ VERIFIED: File exists on disk!")
            else:
                # Fallback check (clean title might differ)
                print(f"⚠️ warning: exact path match failed. Checking directory {os.path.dirname(expected_file)}")
                if os.path.exists(os.path.dirname(expected_file)):
                     print("Directory exists. Listing content:")
                     print(os.listdir(os.path.dirname(expected_file)))
                else:
                     print("❌ Directory not found.")
                     
        else:
            print(f"❌ API Save failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API call failed: {e}")

if __name__ == "__main__":
    test_force_save()
