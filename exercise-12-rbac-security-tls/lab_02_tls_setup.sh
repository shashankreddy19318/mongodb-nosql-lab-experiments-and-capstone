#!/bin/bash
# ==============================================================================
# Lab 12.2 - TLS / Encryption-in-Transit Setup
# Objective: Configure TLS encryption for MongoDB, enforce requireTLS,
#            verify unencrypted rejection, and test encrypted connections.
# ==============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="${SCRIPT_DIR}/tls"
TLS_PORT=27100
DB_PATH="/data/db_tls"

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}      Lab 12.2: TLS / Encryption-in-Transit Setup & Verification    ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# ------------------------------------------------------------------------------
# Step 1: Generate Certificate Chain using OpenSSL & Python
# ------------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}=== Step 1: Generate TLS Certificate Authority & Keys ===${NC}"
mkdir -p "${CERT_DIR}"

if [ ! -f "${CERT_DIR}/server.pem" ] || [ ! -f "${CERT_DIR}/ca.crt" ]; then
    echo "[INFO] Generating fresh X.509 Certificate Chain..."
    
    # 1. Root Certificate Authority (CA)
    openssl genrsa -out "${CERT_DIR}/ca.key" 4096 2>/dev/null
    openssl req -new -x509 -days 365 -key "${CERT_DIR}/ca.key" -out "${CERT_DIR}/ca.crt" \
        -subj '/CN=MongoDB-CA/O=NoSQL-Lab/C=US' 2>/dev/null
    echo -e "${GREEN}[OK] Generated CA: ${CERT_DIR}/ca.crt${NC}"

    # 2. Server Key & Certificate Signing Request (CSR)
    openssl genrsa -out "${CERT_DIR}/server.key" 4096 2>/dev/null
    openssl req -new -key "${CERT_DIR}/server.key" -out "${CERT_DIR}/server.csr" \
        -subj '/CN=localhost/O=MongoDB-Server' 2>/dev/null

    # 3. Sign Server Certificate with Subject Alternative Name (SAN)
    cat > "${CERT_DIR}/san.cnf" << 'EOF'
[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = mongodb
IP.1 = 127.0.0.1
EOF

    openssl x509 -req -days 365 -in "${CERT_DIR}/server.csr" \
        -CA "${CERT_DIR}/ca.crt" -CAkey "${CERT_DIR}/ca.key" -CAcreateserial \
        -out "${CERT_DIR}/server.crt" -extfile "${CERT_DIR}/san.cnf" -extensions v3_req 2>/dev/null

    # Concatenate private key and certificate into single PEM bundle for mongod
    cat "${CERT_DIR}/server.key" "${CERT_DIR}/server.crt" > "${CERT_DIR}/server.pem"
    cp "${CERT_DIR}/server.pem" "${CERT_DIR}/mongodb.pem"
    chmod 600 "${CERT_DIR}/server.pem" "${CERT_DIR}/mongodb.pem"
    echo -e "${GREEN}[OK] Generated Server PEM Bundle: ${CERT_DIR}/server.pem${NC}"

    # 4. Client Certificate (for mutual TLS / PyMongo)
    openssl genrsa -out "${CERT_DIR}/client.key" 4096 2>/dev/null
    openssl req -new -key "${CERT_DIR}/client.key" -out "${CERT_DIR}/client.csr" \
        -subj '/CN=client/O=PyMongo-Client' 2>/dev/null
    openssl x509 -req -days 365 -in "${CERT_DIR}/client.csr" \
        -CA "${CERT_DIR}/ca.crt" -CAkey "${CERT_DIR}/ca.key" -CAcreateserial \
        -out "${CERT_DIR}/client.crt" 2>/dev/null
    cat "${CERT_DIR}/client.key" "${CERT_DIR}/client.crt" > "${CERT_DIR}/client.pem"
    chmod 600 "${CERT_DIR}/client.pem"
    echo -e "${GREEN}[OK] Generated Client PEM Bundle: ${CERT_DIR}/client.pem${NC}"
else
    echo -e "${GREEN}[OK] Valid TLS certificates already exist in ${CERT_DIR}.${NC}"
fi

# Print certificate details
echo ""
echo -e "${BLUE}--- Certificate Authority Details ---${NC}"
openssl x509 -in "${CERT_DIR}/ca.crt" -noout -issuer -subject -dates
echo -e "${BLUE}--- Server Certificate Subject Alternative Names (SAN) ---${NC}"
openssl x509 -in "${CERT_DIR}/server.crt" -noout -text | grep -A 2 "Subject Alternative Name" || true

# ------------------------------------------------------------------------------
# Step 2: Start MongoDB Instance with requireTLS
# ------------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}=== Step 2: Launch MongoDB with --tlsMode requireTLS ===${NC}"
mkdir -p "${DB_PATH}"

# Check if port 27100 is already in use
if mongosh --quiet --port "${TLS_PORT}" --eval 'db.runCommand({ping:1})' >/dev/null 2>&1; then
    echo "[INFO] A process is running on port ${TLS_PORT}. Stopping it..."
    mongosh --quiet --port "${TLS_PORT}" --eval 'db.getSiblingDB("admin").shutdownServer()' >/dev/null 2>&1 || true
    sleep 2
fi

echo "[INFO] Starting mongod with flags:"
echo "       --port ${TLS_PORT}"
echo "       --tlsMode requireTLS"
echo "       --tlsCertificateKeyFile ${CERT_DIR}/server.pem"
echo "       --tlsCAFile ${CERT_DIR}/ca.crt"

mongod --fork --logpath /var/log/mongodb_tls.log --dbpath "${DB_PATH}" \
    --port "${TLS_PORT}" --bind_ip 0.0.0.0 \
    --tlsMode requireTLS \
    --tlsCertificateKeyFile "${CERT_DIR}/server.pem" \
    --tlsCAFile "${CERT_DIR}/ca.crt"

sleep 3
echo -e "${GREEN}[OK] mongod started on port ${TLS_PORT} with requireTLS enforced.${NC}"

# ------------------------------------------------------------------------------
# Step 3: Negative Test - Confirm Plain Unencrypted Connection is REJECTED
# ------------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}=== Step 3: Negative Test - Attempt Unencrypted Connection (No TLS) ===${NC}"
echo "[ACTION] Attempting unencrypted ping command: mongosh --port ${TLS_PORT}..."

if mongosh --quiet --port "${TLS_PORT}" --eval 'db.runCommand({ping:1})' > /tmp/tls_notls.log 2>&1; then
    echo -e "${RED}[ERROR] CRITICAL SECURITY FAILURE! Unencrypted connection SUCCEEDED when requireTLS was set!${NC}"
    cat /tmp/tls_notls.log
    exit 1
else
    echo -e "${GREEN}[OK] Negative Test PASSED! Unencrypted plaintext connection was REJECTED.${NC}"
    echo -e "     Observed rejection: $(head -n 2 /tmp/tls_notls.log)"
fi

# ------------------------------------------------------------------------------
# Step 4: Positive Test 1 - Connect with TLS via mongosh
# ------------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}=== Step 4: Positive Test - Connect with TLS via mongosh ===${NC}"
echo "[ACTION] Connecting with: mongosh --port ${TLS_PORT} --tls --tlsCAFile ${CERT_DIR}/ca.crt..."

mongosh --quiet --port "${TLS_PORT}" \
    --tls \
    --tlsCAFile "${CERT_DIR}/ca.crt" \
    --tlsAllowInvalidHostnames \
    --eval '
const ping = db.runCommand({ping: 1});
print("[OK] mongosh successfully established TLS connection!");
print("[OK] Server response: " + JSON.stringify(ping));
'

# ------------------------------------------------------------------------------
# Step 5: Positive Test 2 - Connect with TLS via PyMongo and perform find_one()
# ------------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}=== Step 5: Positive Test - PyMongo Encrypted find_one() Test ===${NC}"
python3 "${SCRIPT_DIR}/test_tls_pymongo.py" \
    --port "${TLS_PORT}" \
    --ca-file "${CERT_DIR}/ca.crt" \
    --cert-file "${CERT_DIR}/client.pem"

echo ""
echo -e "${GREEN}====================================================================${NC}"
echo -e "${GREEN}   [PASS] Lab 12.2 TLS / Encryption-in-Transit Verified Successfully!${NC}"
echo -e "${GREEN}====================================================================${NC}"
