import httpx
import time
import sys

BASE_URL = "http://localhost:8001"
REPO_URL = "https://github.com/tiangolo/typer"  # A reliably parsing repo

def test_analysis():
    print(f"Starting analysis for {REPO_URL}...")
    try:
        # Start Job
        response = httpx.post(f"{BASE_URL}/analyze", json={"repo_url": REPO_URL}, timeout=10.0)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"Job started: {job_id}")
        
        # Poll
        while True:
            status_res = httpx.get(f"{BASE_URL}/jobs/{job_id}", timeout=10.0)
            status_res.raise_for_status()
            status_data = status_res.json()
            status = status_data["status"]
            print(f"Status: {status}")
            
            if status == "completed":
                print("Analysis SUCCESS!")
                return True
            elif status == "failed":
                print(f"Analysis FAILED: {status_data.get('error')}")
                return False
            
            time.sleep(2)
            
    except Exception as e:
        print(f"Test Error: {e}")
        return False

if __name__ == "__main__":
    success = test_analysis()
    sys.exit(0 if success else 1)
