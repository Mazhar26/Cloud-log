from fastapi import FastAPI
from pydantic import BaseModel
import time
import os
import json
import asyncio

app = FastAPI()

LOG_DIR = os.getenv("LOG_DIR", "./logs")
LOG_FILE = os.path.join(LOG_DIR, "logs.jsonl")
os.makedirs(LOG_DIR, exist_ok=True)

# In-memory storage
logs = []
error_count = 0
alert_message = None

ERROR_THRESHOLD = 5

log_queue = asyncio.Queue()

class Log(BaseModel):
    level: str
    message: str

async def async_anomaly_detector():
    global error_count, alert_message
    while True:
        log_entry = await log_queue.get()
        try:
            # 1. Append to in-memory list
            logs.append(log_entry)

            # 2. Write to persistent JSONL file
            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

            # 3. Anomaly detection logic
            if log_entry["level"].upper() == "ERROR":
                error_count += 1
                if error_count >= ERROR_THRESHOLD:
                    alert_message = "🚨 High error rate detected!"
        except Exception as e:
            print(f"Error in background task: {e}")
        finally:
            log_queue.task_done()

@app.on_event("startup")
async def startup_event():
    global error_count, alert_message
    # Start the async background task
    asyncio.create_task(async_anomaly_detector())

    # Load historical logs from persistent file
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                for line in f:
                    if line.strip():
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                        if log_entry.get("level", "").upper() == "ERROR":
                            error_count += 1
            if error_count >= ERROR_THRESHOLD:
                alert_message = "🚨 High error rate detected!"
        except Exception as e:
            print(f"Error loading historical logs: {e}")

@app.get("/")
def home():
    return {"message": "Analyzer Service Running 🚀"}

@app.post("/ingest-log")
async def ingest_log(log: Log):
    log_entry = {
        "level": log.level,
        "message": log.message,
        "timestamp": time.strftime("%H:%M:%S")
    }
    await log_queue.put(log_entry)
    return {"status": "log received"}

@app.get("/logs")
def get_logs():
    return {"logs": logs[-50:]}  # return last 50 logs for better dashboard visibility

@app.get("/stats")
def get_stats():
    return {
        "total_logs": len(logs),
        "error_count": error_count
    }

@app.get("/alerts")
def get_alert():
    return {"alert": alert_message}

@app.post("/reset")
def reset_logs():
    global error_count, alert_message, logs
    logs = []
    error_count = 0
    alert_message = None
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except Exception as e:
            print(f"Error resetting log file: {e}")
    return {"status": "reset successful"}