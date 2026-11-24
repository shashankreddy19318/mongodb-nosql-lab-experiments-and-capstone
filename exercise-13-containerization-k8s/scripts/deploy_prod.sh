#!/bin/bash
# scripts/deploy_prod.sh
# Complete deployment and initialization script for Lab 13.1

set -e
cd "$(dirname "$0")/.."

echo "=========================================================="
echo "  Lab 13.1: Deploy Production 3-Node Replica Set"
echo "=========================================================="

# 1. Generate keyfile if not present
if [ ! -f keyfile ]; then
    echo "[Step 1] Generating keyfile..."
    bash generate-keyfile.sh keyfile
else
    echo "[Step 1] keyfile already exists."
fi

# 2. Start Docker Compose services
echo ""
echo "[Step 2] Starting MongoDB containers with Docker Compose..."
docker-compose -f docker-compose.yml up -d mongo-rs0-1 mongo-rs0-2 mongo-rs0-3

echo "Waiting 15 seconds for mongod instances to initialize..."
sleep 15

# 3. Initialize Replica Set and create users
echo ""
echo "[Step 3] Initializing Replica Set 'rs0'..."
docker exec -i prod-mongo-1 mongosh --quiet < scripts/init-replica.js

# 4. Start Prometheus Exporter & Prometheus
echo ""
echo "[Step 4] Starting Prometheus Exporter sidecar & Prometheus server..."
docker-compose -f docker-compose.yml up -d mongo-exporter prometheus

echo "Waiting 5 seconds for exporter to begin scraping..."
sleep 5

# 5. Verify Health
echo ""
echo "[Step 5] Verifying Replica Set Status..."
docker exec -i prod-mongo-1 mongosh -u admin -p AdminPass123! --authenticationDatabase admin --quiet --eval "
rs.status().members.forEach(m => print('Member [' + m.name + '] : State=' + m.stateStr + ', Health=' + m.health));
"

echo ""
echo "=========================================================="
echo "  Replica Set & Monitoring Stack Deployed Successfully!"
echo "  - Mongo Node 1 : localhost:27017"
echo "  - Mongo Node 2 : localhost:27018"
echo "  - Mongo Node 3 : localhost:27019"
echo "  - Exporter     : http://localhost:9216/metrics"
echo "  - Prometheus   : http://localhost:9090"
echo "=========================================================="
