# syntax=docker/dockerfile:1
FROM python:3.11-slim

LABEL maintainer="Chintan <shashankreddy19318>"
LABEL description="Threat Intelligence LLM/SLM Platform with Autonomous Mitigation Bot & Exercises 1-18"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Default environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MONGO_URI=mongodb://mongo:27017/?directConnection=true \
    MONGO_DB=threat_intelligence_db \
    LLM_BACKEND=local_slm \
    BACKEND_URL=http://backend:8000

# Entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["api"]
