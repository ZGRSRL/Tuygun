import requests
import uuid

BASE_URL = "http://localhost:8000"

def test_add_category():
    print("Testing Add Category...")
    cat_name = f"Test Category {uuid.uuid4()}"
    
    try:
        resp = requests.post(f"{BASE_URL}/api/categories", json={"name": cat_name})
        if resp.status_code == 200:
            print(f"✅ Success: Added category '{cat_name}'")
            print(resp.json())
        else:
            print(f"❌ Failed: {resp.status_code}")
            print(resp.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_add_category()
