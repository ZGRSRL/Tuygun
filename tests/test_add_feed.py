import requests
import uuid

BASE_URL = "http://localhost:8000"

def test_add_feed():
    print("Testing Add RSS Feed...")
    feed_url = f"https://rss.nytimes.com/services/xml/rss/nyt/Technology_{uuid.uuid4()}.xml"
    feed_name = "Test Tech Feed"
    
    try:
        resp = requests.post(f"{BASE_URL}/api/rss/feeds", json={
            "name": feed_name,
            "url": feed_url,
            "category": "Technology"
        })
        if resp.status_code == 200:
            print(f"✅ Success: Added feed '{feed_name}'")
            print(resp.json())
        else:
            print(f"❌ Failed: {resp.status_code}")
            print(resp.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_add_feed()
