FROM mongo:7

LABEL maintainer="Student Submission - Lab 09 NoSQL"
LABEL description="Complete Lab 09 Demonstration Suite - Consistency, Write Concerns & Network Partition"

# Install Python 3, pip, and docker CLI for container orchestration
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        curl \
        ca-certificates \
        docker.io \
        net-tools \
        procps && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir pymongo python-dotenv

# Copy lab source code and scripts
COPY lab_01_write_concern_latency.py /app/
COPY lab_02_simulate_partition.py /app/
COPY lab_02_failover_observer.py /app/
COPY demo_all.py /app/
COPY entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh

ENV MONGO_URI="mongodb://mongo-rs0-1:27017/?directConnection=true"
ENV DOCKER_NETWORK="mongo-net"
ENV SEC1_CONTAINER="mongo-rs0-2"
ENV SEC2_CONTAINER="mongo-rs0-3"
ENV PRIMARY_CONTAINER="mongo-rs0-1"

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["demo"]
