# ==============================================================================
# Dockerfile - NoSQL Databases: Chapter 15 Multi-Tenant SaaS Demonstration Image
# Self-contained container for demonstrating:
#   - Lab 15.1: Multi-Tenant REST API with FastAPI & MongoDB (Tenant Isolation & Rate Limiting)
#   - Activity 15.1: Role-Based Access Control (Admin vs Regular User)
#   - Lab 15.2: Data Migration Between Tenant Isolation Strategies
#   - Workload Benchmarks & Academic Report Generation
# ==============================================================================

FROM mongo:7

LABEL maintainer="Chintan" \
      description="Multi-Tenant SaaS Demonstration Environment: MongoDB 7.0, FastAPI, JWT RBAC, Rate Limiting & Tenant Migration" \
      version="1.5.0"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    WORKSPACE_DIR=/workspace \
    MONGO_URI="mongodb://127.0.0.1:27017/saas_app?directConnection=true" \
    MONGO_DB="saas_app"

# 1. Install Python and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    procps \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Setup workspace directory
WORKDIR /workspace

# 3. Copy requirements and install Python dependencies
COPY requirements.txt /workspace/
RUN pip3 install --no-cache-dir --break-system-packages -r /workspace/requirements.txt || \
    pip3 install --no-cache-dir -r /workspace/requirements.txt

# 4. Copy project files into container
COPY . /workspace

# 5. Setup directories & permissions
RUN mkdir -p /workspace/logs /data/db && \
    chmod +x /workspace/entrypoint.sh \
             /workspace/*.py \
             /workspace/*.sh 2>/dev/null || true

# 6. Expose default ports (MongoDB: 27017, FastAPI: 8000)
EXPOSE 27017 8000

# 7. Default Entrypoint
ENTRYPOINT ["/workspace/entrypoint.sh"]
