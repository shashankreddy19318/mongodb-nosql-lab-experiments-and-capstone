# ==============================================================================
# Dockerfile - NoSQL Databases Using MongoDB: Lab 13 Demonstration Image
# Fully self-contained environment for grading & demonstrating:
#   - Lab 13.1: 3-Node MongoDB Replica Set with KeyFile Auth & PyMongo Failover
#   - Activity 13.1: Prometheus MongoDB Exporter Sidecar & Metrics Scrape
#   - Lab 13.2: Kubernetes StatefulSet Manifests & Resiliency Test
#   - Cloud: Terraform MongoDB Atlas Free-Tier Cluster Configuration
# ==============================================================================

FROM python:3.11-slim

LABEL maintainer="Student Submission - Exercise 13 NoSQL" \
      description="Demonstration container for MongoDB Replica Sets, Docker Compose, Prometheus Monitoring, and K8s StatefulSets" \
      version="1.0"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    WORKSPACE_DIR=/workspace

# 1. Install system utilities and prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    openssl \
    git \
    procps \
    jq \
    nano \
    && rm -rf /var/lib/apt/lists/*

# 2. Install MongoDB Shell (mongosh)
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg && \
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    apt-get update && apt-get install -y --no-install-recommends mongodb-mongosh && \
    rm -rf /var/lib/apt/lists/*

# 3. Install kubectl CLI
RUN curl -fsSL -o /usr/local/bin/kubectl "https://dl.k8s.io/release/v1.30.0/bin/linux/amd64/kubectl" && \
    chmod +x /usr/local/bin/kubectl

# 4. Install Python dependencies
RUN pip install --no-cache-dir \
    pymongo>=4.6.0 \
    requests>=2.31.0 \
    prometheus-client>=0.20.0

# 5. Set up workspace
WORKDIR /workspace

# Copy project files
COPY . /workspace

# Set executable permissions on scripts
RUN chmod +x /workspace/generate-keyfile.sh \
             /workspace/scripts/*.sh \
             /workspace/scripts/*.py \
             /workspace/demo/*.py \
             /workspace/demo/*.sh

# Ensure keyfile permissions
RUN chmod 400 /workspace/keyfile 2>/dev/null || true

# Expose ports for MongoDB, Exporter, and Prometheus
EXPOSE 27017 27018 27019 9216 9090

ENTRYPOINT ["/workspace/demo/entrypoint.sh"]
CMD ["--auto"]
