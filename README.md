# Cloud Log Monitoring System

Real-time log monitoring pipeline built with Python microservices. Three Docker containers work together — one generates logs, one analyzes them for anomalies, and one displays everything on a live dashboard. Logs are persisted to disk so nothing gets lost on restarts.

**Tech stack:** Python · FastAPI · Streamlit · Docker Compose · GitHub Actions

---

## How It Works

The system follows a simple producer-analyzer-dashboard flow:

```
Producer (generates logs) ──HTTP POST──> Analyzer (processes + stores) <──polls── Dashboard (displays)
```

- The **Producer** sends simulated log events (INFO, WARNING, ERROR) to the Analyzer every second.
- The **Analyzer** receives them, pushes each log into an async queue, and a background worker handles the rest — writing to a `.jsonl` file on disk, tracking error counts, and triggering alerts if errors pile up.
- The **Dashboard** polls the Analyzer's API every 2 seconds and renders everything in a Streamlit web app.

All three services are containerized and wired together through Docker Compose.

---

## Getting Started

### What you need
- Docker Desktop (v20.10+)
- Git
- Python 3.10+ (only if you want to run tests outside Docker)

### Clone and run

```bash
git clone https://github.com/Mazhar26/Cloud-log.git
cd Cloud-log
docker compose up --build -d
```

That's it. Open [http://localhost:8501](http://localhost:8501) for the dashboard, or hit [http://localhost:8001](http://localhost:8001) to check the analyzer API directly.

To bring everything down:

```bash
docker compose down -v
```

---

## Project Structure

```
Cloud-Log/
├── producer/
│   ├── main.py              # Log event generator (1 event/sec)
│   ├── Dockerfile
│   └── requirements.txt
├── analyzer/
│   ├── main.py              # FastAPI backend with async processing
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py               # Streamlit dashboard (8 panels)
│   ├── Dockerfile
│   └── requirements.txt
├── tests/
│   └── smoke_test.py        # Integration tests
├── docker-compose.yml
├── deploy.sh                # Orchestration helper script
└── README.md
```

---

## The Three Services

### Producer

Lives in `producer/main.py`. A simple FastAPI app that spawns a background thread on startup. The thread runs in an infinite loop — every second it picks a random log level (INFO, WARNING, or ERROR), builds a JSON payload, and POSTs it to the analyzer's `/ingest-log` endpoint. Nothing fancy, but it gives you a steady stream of events to work with.

**Throughput:** ~60 log events per minute.

### Analyzer

Lives in `analyzer/main.py`. This is the core of the system.

When a log comes in through `/ingest-log`, it doesn't get processed right there in the request handler. Instead, it goes into an `asyncio.Queue`. A background coroutine (`async_anomaly_detector`) picks up items from that queue and does three things:

1. Appends the log to an in-memory list (for fast reads)
2. Writes it to `logs.jsonl` inside a Docker volume (for persistence)
3. Checks if the cumulative error count has crossed the threshold (currently set to 5)

On startup, the analyzer reads back the existing `logs.jsonl` file to restore state — so if the container restarts, your metrics and alert status pick up where they left off.

**API endpoints:**

| Method | Route | What it does |
|--------|-------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/ingest-log` | Accept a log event (`{"level": "...", "message": "..."}`) |
| `GET` | `/logs` | Return the last 50 log entries |
| `GET` | `/stats` | Return `total_logs` and `error_count` |
| `GET` | `/alerts` | Return active alert message (or null) |
| `POST` | `/reset` | Wipe all logs from memory and disk |

### Dashboard

Lives in `frontend/app.py`. A Streamlit app that polls the analyzer every 2 seconds and renders 8 panels:

1. **System status banner** — green when things are fine, red when an alert is active
2. **Total logs ingested** — running count
3. **Error count + rate** — shows both the raw number and the percentage
4. **Alert details** — shows the active alert message if one exists
5. **Log level distribution** — bar chart breaking down INFO vs WARNING vs ERROR
6. **Ingestion timeline** — line chart showing log volume over time
7. **Search and filter controls** — sidebar with text search and level dropdown
8. **Log stream table** — sortable table with the raw log records, newest first

The sidebar also has a "Clear & Reset" button that hits the analyzer's `/reset` endpoint.

---

## Deploy Script

There's a `deploy.sh` in the root that wraps common Docker Compose operations. On Mac/Linux, make it executable first:

```bash
chmod +x deploy.sh
```

Then use it like:

```bash
./deploy.sh --up        # Build and start everything
./deploy.sh --down      # Stop and remove volumes
./deploy.sh --restart   # Restart all services
./deploy.sh --status    # Check container states
./deploy.sh --logs      # Tail logs from all containers
./deploy.sh --verify    # Run health checks + smoke tests
```

---

## CI Pipeline

GitHub Actions runs on every push and PR to `main`. The workflow (`.github/workflows/ci.yml`) does the following:

1. Spins up the full Docker Compose stack on an Ubuntu runner
2. Installs Python and the `requests` library
3. Runs `tests/smoke_test.py`, which:
   - Resets the analyzer state
   - Sends 5 mixed log events and verifies the counts are accurate
   - Sends 4 more ERROR logs to cross the threshold (5 total errors)
   - Confirms the alert actually triggered
4. Hits the Streamlit container with `curl` to make sure it's responding
5. Tears everything down

If any step fails, the pipeline fails. The teardown runs regardless so containers don't linger.

---

## Persistent Logging

Logs are written to `/app/logs/logs.jsonl` inside the analyzer container. That path is backed by a named Docker volume (`analyzer-logs`), so the data survives container restarts.

Each line in the file is a JSON object:

```json
{"level": "ERROR", "message": "Connection timeout error", "timestamp": "14:32:07"}
```

On startup, the analyzer reads this file line by line to rebuild its in-memory state.

---

## Troubleshooting

**Port already in use** — If 8001 or 8501 is taken, stop whatever's using it or change the port mapping in `docker-compose.yml`.

**Dashboard says "Connecting to Analyzer..."** — The frontend can't reach the backend. Run `docker compose ps` to check if the analyzer container is actually running.

**Logs don't persist after restart** — Make sure the Docker volume is set up properly. Run `docker volume inspect cloud-log_analyzer-logs` to verify.

---

## What's Next

Some things I'd like to add down the line:
- Elasticsearch integration for proper log indexing and search
- Slack/email notifications when alerts trigger
- Auth layer on the ingestion endpoints
- Prometheus metrics exporter for external monitoring

---

## License

MIT
