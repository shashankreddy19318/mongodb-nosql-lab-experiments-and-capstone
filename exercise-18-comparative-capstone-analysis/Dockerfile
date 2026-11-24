# ==============================================================================
# Dockerfile - NoSQL Databases: Chapter 18 Demonstration Image
# Self-contained container for demonstrating:
#   - Lab 18.1: Build Comparative System (MongoDB, Cassandra, Neo4j)
#   - 4-Query Benchmarking Suite (100,000 Threats Dataset, 10 Runs Median Latency)
#   - Activity 18.1: Graph-based Community Detection & False-Positive Isolation
#   - Lab 18.2: Comparative Analysis Report & Publication-Grade PDF Generator
# ==============================================================================

FROM chintan/mongodb-lab17:latest

LABEL maintainer="Chintan" \
      description="Chapter 18: Comparative Capstone - Threat Intelligence False-Positive System" \
      version="1.0"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    WORKSPACE_DIR=/workspace \
    MONGO_URI="mongodb://127.0.0.1:27017/?directConnection=true"

WORKDIR /workspace

# Copy project files into container
COPY . /workspace

# Setup directories & permissions
RUN mkdir -p /workspace/logs /workspace/reports /data/db && \
    chmod +x /workspace/entrypoint.sh \
             /workspace/*.py \
             /workspace/*.sh 2>/dev/null || true

EXPOSE 27017

ENTRYPOINT ["/workspace/entrypoint.sh"]
