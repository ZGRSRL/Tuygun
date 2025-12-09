import requests
import json

def test_preview():
    url = "http://localhost:8002/api/rss/preview"
    # Use a real technical article URL to test AI summarization
    payload = {
        "url": "https://techcrunch.com/2023/12/01/openai-agrees-to-buy-chip-startup-rain-neuromorphics-for-51m/"
    }
    
    try:
        print(f"Testing {url}...")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS!")
            print(f"Title: {data.get('title')}")
            print(f"Summary: {data.get('ai_summary')[:100]}...")
            print(f"Tags: {data.get('ai_tags')}")
        else:
            print(f"FAILED: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_preview()
