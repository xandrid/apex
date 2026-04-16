import time
import requests
import json
import sys

URL = "http://localhost:8000"
CLAIM = "A method for autonomous vehicle navigation comprising: receiving sensor data from a plurality of sensors; identifying an obstacle in a path of the vehicle based on the sensor data; calculating a trajectory to avoid the obstacle; and controlling a steering system of the vehicle to follow the calculated trajectory."

def wait_for_server():
    print("Waiting for server to be ready...")
    for _ in range(30):
        try:
            r = requests.get(f"{URL}/health", timeout=2)
            if r.status_code == 200:
                print("Server is ready!")
                return True
        except:
            pass
        time.sleep(2)
    print("Server failed to come online.")
    return False

def test_analyze_claim():
    print(f"\nAnalyzing claim: {CLAIM}")
    try:
        payload = {"claim_text": CLAIM, "strict_mode": True}
        start = time.time()
        r = requests.post(f"{URL}/analyze-claim", json=payload, timeout=120)
        duration = time.time() - start
        
        if r.status_code == 200:
            data = r.json()
            print(f"\nSuccess! (Took {duration:.2f}s)")
            print(json.dumps(data, indent=2))
            
            # Basic Validation
            risk = data.get("overall_risk", {})
            print(f"\nOverall Risk: Novelty={risk.get('novelty_risk')}, Obviousness={risk.get('obviousness_risk')}")
            
            elements = data.get("elements", [])
            print(f"Elements Found: {len(elements)}")
            
            analyses = data.get("prior_art_analyses", [])
            print(f"Prior Art Analyzed: {len(analyses)}")
            
        else:
            print(f"Error: {r.status_code}")
            print(r.text)
            
    except Exception as e:
        print(f"Exception during test: {e}")

if __name__ == "__main__":
    if wait_for_server():
        test_analyze_claim()
    else:
        sys.exit(1)
