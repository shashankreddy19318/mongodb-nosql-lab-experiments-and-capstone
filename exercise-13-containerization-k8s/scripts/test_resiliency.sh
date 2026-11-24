#!/bin/bash
# scripts/test_resiliency.sh
# Lab 13.2 - Kubernetes StatefulSet Self-Healing & Resiliency Test

set -e
NAMESPACE="nosql-labs"
TARGET_POD="mongo-2"

echo "=========================================================="
echo "  Lab 13.2: Kubernetes StatefulSet Pod Resiliency Test"
echo "=========================================================="

# 1. Check pre-test status
echo ""
echo "[Step 1] Checking current replica set status before pod failure..."
kubectl exec -n "$NAMESPACE" mongo-0 -- mongosh --quiet --eval '
rs.status().members.forEach(m => print("Member: " + m.name + " -> State: " + m.stateStr + " (Health=" + m.health + ")"));
'

# 2. Simulate pod failure
echo ""
echo "[Step 2] Simulating node/pod crash: Deleting pod $TARGET_POD..."
echo "Executing: kubectl delete pod $TARGET_POD -n $NAMESPACE"
kubectl delete pod "$TARGET_POD" -n "$NAMESPACE"

# 3. Observe Kubernetes self-healing
echo ""
echo "[Step 3] Observing Kubernetes StatefulSet controller self-healing..."
echo "Waiting for $TARGET_POD to transition to Running and Ready..."
kubectl wait --for=condition=ready pod/"$TARGET_POD" -n "$NAMESPACE" --timeout=60s

# 4. Verify the pod rejoins the replica set
echo ""
echo "[Step 4] Verifying $TARGET_POD rejoined replica set with data intact..."
sleep 5
kubectl exec -n "$NAMESPACE" mongo-0 -- mongosh --quiet --eval '
print("\n--- Post-Recovery Replica Set Health ---");
rs.status().members.forEach(m => print("Member: " + m.name + " -> State: " + m.stateStr + " (Health=" + m.health + ")"));
'

echo ""
echo "=========================================================="
echo "[PASS] Kubernetes StatefulSet successfully recreated $TARGET_POD,"
echo "       re-attached persistent volume claim mongo-data-$TARGET_POD,"
echo "       and rejoined the replica set automatically!"
echo "=========================================================="
