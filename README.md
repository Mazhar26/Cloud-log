# ☁️ Cloud Log Monitoring System

[![CI](https://github.com/Mazhar26/Cloud-log/actions/workflows/ci.yml/badge.svg)](https://github.com/Mazhar26/Cloud-log/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45%2B-FF4B4B?logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

A containerized real-time log monitoring pipeline that ingests, processes, and visualizes production-level observability logs. Built with **FastAPI** + **Streamlit**, featuring async anomaly detection and persistent structured logging.

---

## 🧩 System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DOCKER COMPOSE                                │
│                                                                      │
│  ┌─────────────────────┐         ┌──────────────────────────────┐   │
│  │  Streamlit (8501)   │  HTTP   │      FastAPI (8001)          │   │
│  │                     │────────▶│                              │   │
│  │  ┌───────────────┐  │         │  ┌────────────────────────┐ │   │
│  │  │   app.py      │  │  polls  │  │    Analyzer Engine     │ │   │
│  │  ├───────────────┤  │ /stats  │  │                        │ │   │
│  │  │ Status Banner │  │ /logs   │  │  /ingest-log  (async)  │ │   │
│  │  │ Metric Cards  │  │ /alerts │  │  /stats      /logs     │ │   │
│  │  │ Bar Chart     │  │ /reset  │  │  /alerts     /reset    │ │   │
│  │  │ Line Chart    │  │         │  └──────────┬─────────────┘ │   │
│  │  │ Filter Panel  │  │         │             │               │   │
│  │  │ Log Table     │  │         │             ▼               │   │
│  │  └───────────────┘  │         │  ┌────────────────────────┐ │   │
│  └─────────────────────┘         │  │  asyncio.Queue Worker  │ │   │
│                                  │  │                        │ │   │
│  ┌─────────────────────┐         │  │  1. In-memory append   │ │   │
│  │  Producer (internal)│  POST   │  │  2. JSONL file write   │ │   │
│  │                     │────────▶│  │  3. Error threshold    │ │   │
│  │  main.py            │/ingest  │  │     check (≥5 → alert) │ │   │
│  │  1 log/sec loop     │ -log   │  └──────────┬─────────────┘ │   │
│  └─────────────────────┘         │             │               │   │
│                                  │             ▼               │   │
│                                  │  ┌────────────────────────┐ │   │
│                                  │  │  logs/logs.jsonl       │ │   │
│                                  │  │  (persistent volume)   │ │   │
│                                  │  └────────────────────────┘ │   │
│                                  └──────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────┐
  │ GitHub CI    │
  │ (smoke test  │
  │  + health    │
  │  checks)     │
  └──────────────┘
```

**Data Flow:**
```
Producer ──POST──▶ /ingest-log ──▶ asyncio.Queue
                                       │
                                       ▼
                              ┌─── In-Memory List ────────┐
                              ├─── logs.jsonl (disk) ─────┤──▶ Persistent Storage
                              └─── Error Counter ─────────┘
                                       │
                                       ▼
                              Threshold ≥ 5 errors? ──▶ Alert Triggered
                                       │
                                       ▼
Dashboard ◀──polls── /stats + /logs + /alerts ──▶ 8-Panel Streamlit UI
```

---

## 🏗️ Project Structure

```
Cloud-Log/
├── analyzer/
│   ├── main.py              # FastAPI backend (6 endpoints, async queue)
│   ├── Dockerfile
│   └── requirements.txt
├── producer/
│   ├── main.py              # Log event generator (1 event/sec)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py               # Streamlit dashboard (8 panels)
│   ├── Dockerfile
│   └── requirements.txt
├── tests/
│   └── smoke_test.py        # Integration smoke test (7 checks)
├── .github/workflows/
│   └── ci.yml               # GitHub Actions CI pipeline
├── docker-compose.yml        # Multi-service orchestration
├── deploy.sh                 # Bash orchestration helper
└── README.md
```

---

## 🚀 Quick Start with Docker

The fastest way to get running — no manual setup needed:

```bash
docker compose up --build -d
```

Then open **http://localhost:8501** for the dashboard, and **http://localhost:8001** to check the analyzer API.

To stop:

```bash
docker compose down -v
```

---

## 🚀 Getting Started (Manual)

### 1. Clone & Install

```bash
git clone https://github.com/Mazhar26/Cloud-log.git
cd Cloud-log
pip install fastapi uvicorn pydantic requests streamlit pandas
```

### 2. Start the Analyzer

```bash
cd analyzer
python -m uvicorn main:app --port 8001
```

### 3. Start the Producer (separate terminal)

```bash
cd producer
python -m uvicorn main:app --port 8002
```

### 4. Start the Dashboard (separate terminal)

```bash
cd frontend
streamlit run app.py
```

### 5. Open in Browser

Navigate to **http://localhost:8501**

---

## 🔌 API Endpoints

All endpoints are served by the Analyzer on port `8001`:

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/ingest-log` | POST | Ingest a log event (`{"level": "...", "message": "..."}`) |
| `/logs` | GET | Return last 50 log entries |
| `/stats` | GET | Total log count and error count |
| `/alerts` | GET | Current active alert (or null) |
| `/reset` | POST | Clear all logs from memory and disk |

---

## 🔍 How It Works

1. **Log Generation** — The Producer runs a background thread that fires off one log event per second. Each event gets a random severity level (`INFO`, `WARNING`, or `ERROR`) and is POSTed to the Analyzer's `/ingest-log` endpoint.

2. **Async Ingestion** — The Analyzer doesn't process logs inline with the request. Instead, each log gets pushed onto an `asyncio.Queue`. The HTTP response returns immediately while a background coroutine handles the heavy lifting.

3. **Anomaly Detection** — The background worker pulls logs off the queue one by one. It appends each entry to an in-memory list, writes it to a `.jsonl` file on disk, and increments the error counter. Once errors hit the threshold (≥5), an alert gets flagged system-wide.

4. **Persistent Storage** — Logs are written as structured JSON Lines to `logs/logs.jsonl`, backed by a Docker volume. On startup, the Analyzer reads this file to restore previous state — so metrics and alerts survive container restarts.

5. **Dashboard Polling** — The Streamlit frontend polls `/stats`, `/logs`, and `/alerts` every 2 seconds. It renders 8 panels: system status, ingestion volume, error rate, active alerts, level distribution chart, ingestion timeline, search/filter controls, and a live log table.

---

## 🧪 Testing

Run the smoke test against a running Analyzer instance:

```bash
python tests/smoke_test.py
```

Expected output:
```
✅ Analyzer service is up and running!
Starting smoke tests...
Resetting log store...
✅ Initial state is clean.
Sending 5 logs...
✅ Ingestion and stats check passed.
Sending 4 more errors to trigger alert...
✅ Anomaly detection alert triggered successfully.
🎉 All smoke tests passed successfully!
```

The smoke test covers:
- Service availability and health check
- State reset and clean initial stats
- Log ingestion with mixed severity levels
- Stats counter accuracy after async processing
- Alert threshold triggering (5 errors)
- Alert message content verification

---

## 🛠️ Deploy Script

A Bash helper script (`deploy.sh`) wraps common Docker Compose commands:

```bash
chmod +x deploy.sh    # make executable (Mac/Linux)
```

| Command | What it does |
|---|---|
| `./deploy.sh --up` | Build and start all services |
| `./deploy.sh --down` | Stop services, remove volumes |
| `./deploy.sh --restart` | Restart the stack |
| `./deploy.sh --status` | Check container states |
| `./deploy.sh --logs` | Tail logs from all containers |
| `./deploy.sh --verify` | Run health checks + smoke tests |

---

## 🤖 CI/CD Pipeline

GitHub Actions runs on every push and PR to `main` (`.github/workflows/ci.yml`):

1. Spins up the full Docker Compose stack on Ubuntu
2. Installs Python 3.11 and the `requests` library
3. Runs `tests/smoke_test.py` — verifies ingestion, stats, and alert triggering
4. Hits the Streamlit container with `curl` to confirm it's responding
5. Tears down everything (runs even if earlier steps fail)

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Uvicorn, Pydantic
- **Frontend:** Streamlit, Pandas
- **Async Engine:** Python asyncio (Queue + background worker)
- **Storage:** JSON Lines (.jsonl) on Docker persistent volume
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions (smoke tests + health checks)
- **Scripting:** Bash (deploy.sh orchestration)

---

## 📄 License

This project is licensed under the MIT License.
