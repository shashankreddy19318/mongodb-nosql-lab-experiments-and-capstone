# ==============================================================================
# Dockerfile - NoSQL Databases: Chapter 16 Demonstration Image
# Self-contained container for demonstrating:
#   - Lab 16.1: Polyglot Data Modeling in MongoDB, Cassandra, and Neo4j
#   - Activity 16.1: University Hybrid Architecture (MongoDB, Cassandra, Neo4j)
#   - Lab 16.2: Hybrid Query Service with Circuit Breakers & Connection Pooling
#   - Latency Benchmarking & Unit Test Suite
# ==============================================================================

FROM mongo:7

LABEL maintainer="Chintan" \
      description="Polyglot Persistence Demonstration Environment: MongoDB 7.0, Cassandra CQL, Neo4j Graph" \
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

# 2. Setup workspace directory
WORKDIR /workspace

# 3. Copy requirements and install Python dependencies
COPY requirements.txt /workspace/
RUN pip3 install --no-cache-dir -r /workspace/requirements.txt

# 4. Copy project files into container
COPY . /workspace

# 5. Setup directories & permissions
RUN mkdir -p /workspace/logs /data/db && \
    chmod +x /workspace/entrypoint.sh \
             /workspace/*.py \
             /workspace/*.sh 2>/dev/null || true

# 6. Expose default ports
EXPOSE 27017

# 7. Default Entrypoint
ENTRYPOINT ["/workspace/entrypoint.sh"]
