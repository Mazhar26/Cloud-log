import requests
import time
import sys

ANALYZER_URL = "http://localhost:8001"

def wait_for_analyzer(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(ANALYZER_URL)
            if response.status_code == 200:
                print("✅ Analyzer service is up and running!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        print("Waiting for analyzer service to start...")
        time.sleep(2)
    print("❌ Timeout waiting for analyzer service.")
    return False

def test_pipeline():
    print("Starting smoke tests...")
    
    # 1. Reset
    print("Resetting log store...")
    res = requests.post(f"{ANALYZER_URL}/reset")
    assert res.status_code == 200, "Reset request failed"
    
    # 2. Check initial stats
    stats = requests.get(f"{ANALYZER_URL}/stats").json()
    assert stats["total_logs"] == 0, f"Expected 0 logs, got {stats['total_logs']}"
    assert stats["error_count"] == 0, f"Expected 0 errors, got {stats['error_count']}"
    print("✅ Initial state is clean.")
    
    # 3. Ingest some logs (INFO and ERROR)
    logs_to_send = [
        {"level": "INFO", "message": "User login successful"},
        {"level": "INFO", "message": "Database query completed"},
        {"level": "WARNING", "message": "Disk space warning"},
        {"level": "INFO", "message": "API call completed"},
        {"level": "ERROR", "message": "Connection timeout error"}
    ]
    
    print("Sending 5 logs...")
    for log in logs_to_send:
        res = requests.post(f"{ANALYZER_URL}/ingest-log", json=log)
        assert res.status_code == 200, "Ingestion request failed"
        
    # Wait for the async queue to process the logs
    time.sleep(1)
    
    stats = requests.get(f"{ANALYZER_URL}/stats").json()
    assert stats["total_logs"] == 5, f"Expected 5 logs, got {stats['total_logs']}"
    assert stats["error_count"] == 1, f"Expected 1 error, got {stats['error_count']}"
    
    alerts = requests.get(f"{ANALYZER_URL}/alerts").json()
    assert alerts["alert"] is None, f"Expected no alert, got {alerts['alert']}"
    print("✅ Ingestion and stats check passed.")
    
    # 4. Trigger alert threshold (need 4 more errors, error_threshold = 5)
    errors_to_send = [
        {"level": "ERROR", "message": "Failed to write data"},
        {"level": "ERROR", "message": "Out of memory"},
        {"level": "ERROR", "message": "Null pointer exception"},
        {"level": "ERROR", "message": "Unauthorized access attempt"}
    ]
    
    print("Sending 4 more errors to trigger alert...")
    for err in errors_to_send:
        res = requests.post(f"{ANALYZER_URL}/ingest-log", json=err)
        assert res.status_code == 200, "Error ingestion request failed"
        
    # Wait for queue
    time.sleep(1)
    
    stats = requests.get(f"{ANALYZER_URL}/stats").json()
    assert stats["total_logs"] == 9, f"Expected 9 logs, got {stats['total_logs']}"
    assert stats["error_count"] == 5, f"Expected 5 errors, got {stats['error_count']}"
    
    alerts = requests.get(f"{ANALYZER_URL}/alerts").json()
    assert alerts["alert"] == "🚨 High error rate detected!", f"Alert trigger failed: {alerts['alert']}"
    print("✅ Anomaly detection alert triggered successfully.")
    
    print("🎉 All smoke tests passed successfully!")

if __name__ == "__main__":
    if not wait_for_analyzer():
        sys.exit(1)
    try:
        test_pipeline()
    except AssertionError as e:
        print(f"❌ Test verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    sys.exit(0)
