from fastapi import FastAPI
import requests
import random
import time
import threading

app = FastAPI()

ANALYZER_URL = "http://analyzer:8001/ingest-log"

LOG_LEVELS = ["INFO", "WARNING", "ERROR"]


def generate_logs():
    while True:
        log = {
            "level": random.choice(LOG_LEVELS),
            "message": "Simulated log event"
        }

        try:
            requests.post(ANALYZER_URL, json=log)
            print(f"Sent log: {log}")
        except:
            print("Analyzer not reachable")

        time.sleep(1)  # 1 log per second


@app.on_event("startup")
def start_log_generator():
    thread = threading.Thread(target=generate_logs)
    thread.daemon = True
    thread.start()


@app.get("/")
def home():
    return {"message": "Producer running 🚀"}