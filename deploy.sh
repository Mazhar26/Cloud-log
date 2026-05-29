#!/bin/bash

# Cloud Log Monitoring Pipeline Deployment & Orchestration Script

set -e

# Configuration
COMPOSE_FILE="docker-compose.yml"
SMOKE_TEST_SCRIPT="tests/smoke_test.py"

function show_help() {
    echo "============================================================"
    echo "  Cloud Log Monitoring - Container Orchestration Tool"
    echo "============================================================"
    echo "Usage: ./deploy.sh [option]"
    echo ""
    echo "Options:"
    echo "  --up          Build and start all microservices in background"
    echo "  --down        Stop all microservices and remove volumes"
    echo "  --restart     Restart all microservices"
    echo "  --status      Check the status of running containers"
    echo "  --logs        View real-time tailing logs of all containers"
    echo "  --verify      Execute health checks and smoke tests on the stack"
    echo "  --help        Show this help message"
    echo "============================================================"
}

function start_services() {
    echo "🚀 Starting all microservices..."
    docker compose -f "$COMPOSE_FILE" up --build -d
    echo "✅ Containers launched. Run './deploy.sh --status' to view state."
}

function stop_services() {
    echo "🛑 Stopping all microservices..."
    docker compose -f "$COMPOSE_FILE" down -v
    echo "✅ Cleaned up containers and volumes."
}

function restart_services() {
    echo "🔄 Restarting microservices..."
    docker compose -f "$COMPOSE_FILE" restart
    echo "✅ Services restarted."
}

function check_status() {
    echo "📊 Container Statuses:"
    docker compose -f "$COMPOSE_FILE" ps
}

function tail_logs() {
    echo "📋 Tailing logs (Press Ctrl+C to exit)..."
    docker compose -f "$COMPOSE_FILE" logs -f
}

function run_verification() {
    echo "🔍 Starting local health checks and integration tests..."
    
    # Ensure containers are running
    if ! docker compose -f "$COMPOSE_FILE" ps --format json | grep -q "running"; then
        echo "⚠️ Containers do not appear to be running. Launching them first..."
        start_services
        echo "Waiting for services to initialize..."
        sleep 5
    fi

    # Run the Python verification test
    if [ -f "$SMOKE_TEST_SCRIPT" ]; then
        echo "Running Python smoke tests..."
        python "$SMOKE_TEST_SCRIPT"
    else
        echo "❌ Smoke test script not found at $SMOKE_TEST_SCRIPT"
        exit 1
    fi
}

# Main command dispatcher
if [ -z "$1" ]; then
    show_help
    exit 0
fi

case "$1" in
    --up)
        start_services
        ;;
    --down)
        stop_services
        ;;
    --restart)
        restart_services
        ;;
    --status)
        check_status
        ;;
    --logs)
        tail_logs
        ;;
    --verify)
        run_verification
        ;;
    --help)
        show_help
        ;;
    *)
        echo "❌ Invalid option: $1"
        show_help
        exit 1
        ;;
esac

exit 0
