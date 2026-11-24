#!/bin/bash
# ==============================================================================
# Comprehensive Demonstration Runner for MongoDB Security Labs (Chapter 12)
# ==============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}####################################################################${NC}"
echo -e "${CYAN}#  MongoDB Chapter 12: Security, RBAC, Views & TLS Encryption      #${NC}"
echo -e "${CYAN}#           Automated Grading Demonstration Suite                  #${NC}"
echo -e "${CYAN}####################################################################${NC}"
echo "Demonstration started at: $(date)"

# Ensure default MongoDB instance is running for Lab 12.1
mkdir -p /data/db /data/db_tls /var/log
if ! mongosh --quiet --eval 'db.runCommand({ping:1})' >/dev/null 2>&1; then
    echo -e "${YELLOW}[SETUP] Starting primary mongod on port 27017...${NC}"
    mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db --bind_ip 0.0.0.0
    sleep 2
fi

# Run Lab 12.1: Authentication & RBAC
echo -e "\n${CYAN}>>> EXECUTING LAB 12.1: AUTHENTICATION AND RBAC SETUP <<<${NC}"
bash "${SCRIPT_DIR}/lab_01_rbac_setup.sh"

# Run Activity 12.1: Field-Level Redaction
echo -e "\n${CYAN}>>> EXECUTING ACTIVITY 12.1: FIELD-LEVEL REDACTION VIA VIEWS <<<${NC}"
python3 "${SCRIPT_DIR}/activity_12_1_redaction.py"

# Run Activity 12.1 mongosh verification
echo -e "\n${CYAN}>>> EXECUTING ACTIVITY 12.1: MONGOSH COMPATIBILITY VERIFICATION <<<${NC}"
bash "${SCRIPT_DIR}/activity_12_1_redaction.sh"

# Run Lab 12.2: TLS / Encryption-in-Transit
echo -e "\n${CYAN}>>> EXECUTING LAB 12.2: TLS / ENCRYPTION-IN-TRANSIT SETUP <<<${NC}"
bash "${SCRIPT_DIR}/lab_02_tls_setup.sh"

# Summary Report
echo ""
echo -e "${GREEN}====================================================================${NC}"
echo -e "${GREEN}             LAB COMPLETION SUMMARY - ALL TESTS PASSED!             ${NC}"
echo -e "${GREEN}====================================================================${NC}"
echo -e " [✓] Lab 12.1:  Admin User Created (userAdminAnyDatabase, clusterAdmin)"
echo -e " [✓] Lab 12.1:  Custom Roles Created (analyticsReader, collectionReader, collectionWriter, limitedWriter)"
echo -e " [✓] Lab 12.1:  Least-Privilege Users Enforced (app_user_read, app_user_write, analyst, app_writer, log_writer)"
echo -e " [✓] Lab 12.1:  Negative Tests: Unauthorized Writes & Cross-DB Reads Correctly Rejected"
echo -e " [✓] Act 12.1:  Field-Level Redaction View (employees_safe) masks SSN and removes salary"
echo -e " [✓] Act 12.1:  RBAC Role Separation (HR user sees raw collection, non-HR user restricted to view)"
echo -e " [✓] Lab 12.2:  OpenSSL & Cryptography Python automated CA, Server & Client cert generation"
echo -e " [✓] Lab 12.2:  Server SAN Configured (DNS:localhost, IP:127.0.0.1)"
echo -e " [✓] Lab 12.2:  requireTLS Enforced (Unencrypted connections rejected with connection/SSL error)"
echo -e " [✓] Lab 12.2:  mongosh connected over TLS successfully"
echo -e " [✓] Lab 12.2:  PyMongo connected over TLS with find_one() data verification"
echo -e "${GREEN}====================================================================${NC}"
echo "Demonstration completed at: $(date)"
