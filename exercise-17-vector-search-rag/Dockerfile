# ==============================================================================
# Dockerfile - NoSQL Databases: Chapter 17 Demonstration Image
# Self-contained container for demonstrating:
#   - Lab 17.1: Build a Simple RAG Pipeline with Threat Intelligence
#   - Activity 17.1: Multi-Turn Conversation Memory in MongoDB
#   - Lab 17.2: Compare HNSW and IVF Vector Search Index Types in MongoDB Atlas
#   - Latency-Recall Trade-off Benchmarking & Curve Plotting
# ==============================================================================

FROM mongo:7

LABEL maintainer="Chintan" \
      description="Chapter 17: AI-Native MongoDB, Vector Search, and RAG Pipeline" \
      version="1.0"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    WORKSPACE_DIR=/workspace \
    MONGO_URI="mongodb://127.0.0.1:27017/?directConnection=true"

# 1. Install Python, build dependencies, and system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    procps \
    ca-certificates \
    libfreetype6-dev \
    libpng-dev \
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

# 6. Expose default MongoDB port
EXPOSE 27017

# 7. Default Entrypoint
ENTRYPOINT ["/workspace/entrypoint.sh"]
