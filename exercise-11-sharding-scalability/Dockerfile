FROM mongo:7

LABEL maintainer="Student Submission - Lab 11 NoSQL (Chintan)"
LABEL description="Complete Lab 11 Demonstration Suite - Sharding, Shard Key Evaluation, Hotspot Detection & Scatter-Gather Analysis"

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
RUN pip3 install --no-cache-dir pymongo reportlab rich python-dotenv

# Copy application scripts and configuration
COPY config/ /app/config/
COPY lab_01_shard_key_eval.py /app/
COPY lab_02_shard_key_hotspot.py /app/
COPY demo_all.py /app/
COPY generate_pdf.py /app/
COPY entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh

ENV MONGO_URI="mongodb://mongos-router:27017"
ENV MONGO_DB="ecommerce_sharding"

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["demo"]
