from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI()

# In-memory storage
logs = []
error_count = 0
alert_message = None

ERROR_THRESHOLD = 5


class Log(BaseModel):
    level: str
    message: str


@app.get("/")
def home():
    return {"message": "Analyzer Service Running 🚀"}


@app.post("/ingest-log")
def ingest_log(log: Log):
    global error_count, alert_message

    log_entry = {
        "level": log.level,
        "message": log.message,
        "timestamp": time.strftime("%H:%M:%S")
    }

    logs.append(log_entry)

    # Count errors
    if log.level.upper() == "ERROR":
        error_count += 1

    # Trigger alert
    if error_count >= ERROR_THRESHOLD:
        alert_message = "🚨 High error rate detected!"

    return {"status": "log received"}


@app.get("/logs")
def get_logs():
    return {"logs": logs[-20:]}  # last 20 logs


@app.get("/stats")
def get_stats():
    return {
        "total_logs": len(logs),
        "error_count": error_count
    }


@app.get("/alerts")
def get_alert():
    return {"alert": alert_message}