#!/usr/bin/env bash
set -e

case "$1" in
  api|backend)
    echo "Starting Threat Intelligence FastAPI Backend on 0.0.0.0:8000..."
    exec uvicorn app.chat_api:app --host 0.0.0.0 --port 8000
    ;;
  demo)
    echo "Running Exercises 1 - 18 Master Demonstration Suite..."
    exec python demo_all_exercises.py
    ;;
  bot)
    echo "Starting Autonomous Vulnerability Scanner Bot Daemon..."
    exec python vulnerability_bot.py
    ;;
  ingest)
    echo "Ingesting Threat Intelligence Corpus..."
    exec python ingest_threat_intelligence.py
    ;;
  streamlit|frontend)
    echo "Starting Streamlit Frontend on 0.0.0.0:8501..."
    exec streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
    ;;
  test)
    echo "Running Unit and Integration Test Suite..."
    exec python test_app.py
    ;;
  pdf)
    echo "Compiling Publication-Grade PDF Report..."
    exec python generate_pdf_report.py
    ;;
  *)
    exec "$@"
    ;;
esac
