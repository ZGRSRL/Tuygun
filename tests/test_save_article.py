import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_save_article():
    print("Testing Article Save Flow...")
    
    # 1. Create a dummy link first (to have something to save)
    # We'll use a hypothetical URL
    test_url = f"https://example.com?t={int(time.time())}"
    
    print(f"1. Adding link: {test_url}")
    try:
        response = requests.post(f"{BASE_URL}/api/articles/link", json={
            "url": test_url,
            "category": "Test"
        })
        if response.status_code != 200:
            print(f"Failed to add link: {response.text}")
            return
        
        article = response.json()
        article_id = article['id']
        print(f"   Article Created: {article_id}")
    except Exception as e:
        print(f"   Error connecting to API: {e}")
        return

    # 2. Preview (scrape) - mocked mostly by backend if url not reachable, but required for flow
    print(f"2. Previewing article: {article_id}")
    try:
        response = requests.post(f"{BASE_URL}/api/articles/{article_id}/preview")
        if response.status_code != 200:
            print(f"Failed to preview: {response.text}")
            # Depending on logic, might fail if scrape fails. Backend has fallback.
            
        # 3. Save Article
        print(f"3. Saving article: {article_id}")
        response = requests.post(f"{BASE_URL}/api/articles/{article_id}/save", json={
            "category": "Test/Saved",
            "article_id": article_id
        })
        
        if response.status_code == 200:
            msg = f"✅ SUCCESS: Article saved successfully.\nResponse: {response.json()}"
            print(msg)
            with open("test_result.txt", "w", encoding="utf-8") as f:
                f.write(msg)
        else:
            msg = f"❌ FAILURE: Could not save article.\nStatus Code: {response.status_code}\nResponse: {response.text}"
            print(msg)
            with open("test_result.txt", "w", encoding="utf-8") as f:
                f.write(msg)
            
            # Verify file creation
            import os
            obsidian_path = r"G:\Drive'ım\TUYGUN\Test\Saved"
            expected_file = f"{obsidian_path}\\{article_id}.md"  # Note: logic in main.py uses safe_title, not ID. 
            # Actually main.py uses safe_title. Let's list the directory to see if *any* new file appeared or check the response['obsidian_path']
            
            resp_json = response.json()
            saved_path = resp_json.get('obsidian_path')
            
            if saved_path and os.path.exists(saved_path):
                 print(f"   ✅ VERIFIED: File exists at {saved_path}")
                 with open("test_result.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n✅ VERIFIED: File exists at {saved_path}")
            else:
                 print(f"   ❌ WARNING: File not found at {saved_path}")
                 with open("test_result.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n❌ WARNING: File not found at {saved_path}")

    except Exception as e:
        print(f"   Error during flow: {e}")
        with open("test_result.txt", "w", encoding="utf-8") as f:
            f.write(f"Error: {e}")

if __name__ == "__main__":
    test_save_article()
