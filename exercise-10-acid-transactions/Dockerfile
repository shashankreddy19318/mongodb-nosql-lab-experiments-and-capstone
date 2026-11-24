FROM mongo:7

LABEL maintainer="Student Submission - Lab 10 NoSQL (chintan)"
LABEL description="Complete Lab 10 Demonstration Suite - Multi-Document Transactions, Deadlocks & Concurrency"

# Install Python 3, pip, and system utilities
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        curl \
        ca-certificates \
        procps && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir pymongo reportlab matplotlib

# Copy application scripts
COPY lab_01_bank_transfer.py /app/
COPY lab_02_inventory_reservation.py /app/
COPY demo_all.py /app/
COPY generate_pdf.py /app/
COPY entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh

ENV MONGO_URI="mongodb://mongo-rs0-1:27017,mongo-rs0-2:27018,mongo-rs0-3:27019/?replicaSet=rs0"

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["demo"]
