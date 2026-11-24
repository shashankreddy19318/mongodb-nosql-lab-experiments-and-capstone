# ==============================================================================
# Dockerfile: MongoDB Security, RBAC, Views & TLS Lab Environment
# Author: Sujeet Jagtap / Lab 12 Security Demonstrator
# ==============================================================================

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install essential dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    openssl \
    python3 \
    python3-pip \
    procps \
    nano \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Add MongoDB Official GPG Key and Repository (MongoDB 7.0)
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor && \
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
    tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install MongoDB Server, mongosh shell, and tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    mongodb-org \
    mongodb-mongosh \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages required for the labs
RUN pip3 install --no-cache-dir \
    pymongo \
    cryptography

# Create MongoDB data and log directories
RUN mkdir -p /data/db /data/db_tls /var/log /app/tls

WORKDIR /app

# Copy all lab scripts, source files, and utilities
COPY . /app/

# Set executable permissions on scripts
RUN chmod +x /app/*.sh /app/*.py /app/entrypoint.sh

# Pre-generate TLS certificates so the environment is ready out-of-the-box
RUN python3 /app/generate_certs.py /app/tls

# Expose MongoDB ports
# 27017: MongoDB with SCRAM-SHA Authentication & RBAC (Lab 12.1)
# 27100: MongoDB with requireTLS (Lab 12.2)
EXPOSE 27017 27100

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["demo"]
