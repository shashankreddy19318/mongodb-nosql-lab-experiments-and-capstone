#!/bin/bash
# Generate 756-byte base64 keyfile for MongoDB internal replica set authentication
# MongoDB requires keyfile permissions to be 400 or 600 (owner read-only)

set -e

KEYFILE_PATH="${1:-keyfile}"

echo "Generating MongoDB replica set keyfile at: $KEYFILE_PATH"

# Generate 756 bytes of random base64 data
openssl rand -base64 756 > "$KEYFILE_PATH"

# Set strict permissions (MongoDB requires chmod 400 or 600)
chmod 400 "$KEYFILE_PATH"

echo "[OK] Generated keyfile ($(wc -c < "$KEYFILE_PATH") bytes) with mode 400."
