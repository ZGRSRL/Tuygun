
import requests
import json
import os

URL = "http://127.0.0.1:8002/api/rss/save"

payload = {
    "title": "Test AI Article Save",
    "content": "This is a test content from the reproduction script.",
    "url": "http://example.com/test-article-save",
    "category": "Genel",
    "ai_summary": "This is an AI summary.",
    "ai_tags": ["test", "ai"],
    "rss_tags": ["rss", "feed"]
}

try:
    print(f"Sending POST to {URL}...")
    response = requests.post(URL, json=payload)
    
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

    if response.status_code == 200:
        print("\n✅ Success!")
    else:
        print("\n❌ Failed!")

except Exception as e:
    print(f"\n❌ Error: {e}")
