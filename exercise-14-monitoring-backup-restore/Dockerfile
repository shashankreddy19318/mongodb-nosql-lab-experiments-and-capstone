# ==============================================================================
# Dockerfile - NoSQL Databases Using MongoDB: Lab 14 Demonstration Image
# Self-contained container for demonstrating:
#   - Lab 14.1: Operational Monitoring Dashboard & Threshold-Based Alerting
#   - Activity 14.1: Webhook Alert Integration (Slack/Discord/REST)
#   - Lab 14.2: Automated Backup, Point-in-Time Restore Verification & Retention
#   - Lab 14.2: Performance Benchmarking (1K, 10K, 100K docs) & RPO/RTO Analysis
# ==============================================================================

FROM mongo:7

LABEL maintainer="Chintan" \
      description="Demonstration container for MongoDB Production Monitoring, Backup, Restore Verification & RPO/RTO Benchmarks" \
      version="1.0"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    WORKSPACE_DIR=/workspace \
    MONGO_URI="mongodb://127.0.0.1:27017/?directConnection=true"

# 1. Install Python and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    procps \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python dependencies
RUN pip3 install --no-cache-dir \
    pymongo>=4.6.0 \
    requests>=2.31.0 \
    rich>=13.7.0 \
    tabulate>=0.9.0 \
    schedule>=1.2.0 \
    reportlab>=4.1.0

# 3. Setup workspace directory
WORKDIR /workspace

# 4. Copy project files into container
COPY . /workspace

# 5. Setup directories & permissions
RUN mkdir -p /workspace/logs /workspace/backups /data/db && \
    chmod +x /workspace/entrypoint.sh \
             /workspace/*.py \
             /workspace/*.sh 2>/dev/null || true

EXPOSE 27017 9099

ENTRYPOINT ["/workspace/entrypoint.sh"]
CMD ["demo"]
