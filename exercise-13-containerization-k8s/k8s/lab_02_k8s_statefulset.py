"""Lab 13.2 - Kubernetes StatefulSet for MongoDB

Deploys a 3-member MongoDB replica set on Kubernetes as a StatefulSet.
Unlike Docker Compose (Lab 13.1), Kubernetes gives each pod a stable
network identity (mongo-0, mongo-1, mongo-2), a headless Service for
peer discovery, and per-pod persistent storage via volumeClaimTemplates
that survives pod restarts and rescheduling.
"""

import sys, os, subprocess, shutil, time

NAMESPACE = "nosql-labs"
STATEFULSET_NAME = "mongo"
HEADLESS_SVC_NAME = "mongo-headless-svc"
REPLICAS = 3
MANIFEST_DIR = os.path.dirname(os.path.abspath(__file__))


def kubectl_available() -> bool:
    """Check whether kubectl is installed and can reach a cluster."""
    if shutil.which("kubectl") is None:
        return False
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def apply_manifests():
    """Apply manifests in order and wait for the StatefulSet to be ready."""
    order = [
        "00-namespace.yaml",
        "mongo-keyfile-secret.yaml",
        "mongo-headless-svc.yaml",
        "mongo-statefulset.yaml",
        "03-replicaset-init-job.yaml"
    ]
    for filename in order:
        path = os.path.join(MANIFEST_DIR, filename)
        if not os.path.exists(path):
            continue
        print(f"\n  Applying {filename} ...")
        result = subprocess.run(
            ["kubectl", "apply", "-f", path], capture_output=True, text=True
        )
        print(f"  {result.stdout.strip() or result.stderr.strip()}")
        if result.returncode != 0:
            print(f"  [ERROR] kubectl apply failed for {filename}")
            return False

        if filename == "mongo-statefulset.yaml":
            print(f"\n  Waiting for StatefulSet/{STATEFULSET_NAME} rollout (up to 180s)...")
            wait = subprocess.run(
                [
                    "kubectl", "rollout", "status",
                    f"statefulset/{STATEFULSET_NAME}",
                    "-n", NAMESPACE, "--timeout=180s",
                ],
                capture_output=True, text=True,
            )
            print(f"  {wait.stdout.strip() or wait.stderr.strip()}")
    return True


def verify_cluster():
    """Confirm the replica set formed correctly by checking rs.status() inside pod 0."""
    print("\n  Verifying replica set status from mongo-0 ...")
    result = subprocess.run(
        [
            "kubectl", "exec", "-n", NAMESPACE, f"{STATEFULSET_NAME}-0", "--",
            "mongosh", "--quiet", "--eval",
            "rs.status().members.forEach(m => print(m.name, m.stateStr))",
        ],
        capture_output=True, text=True,
    )
    print(result.stdout or result.stderr)


def print_manual_instructions():
    print("\n  [INFO] No live Kubernetes cluster detected.")
    print("  Manifests generated in folder:")
    print(f"    {MANIFEST_DIR}/")
    print("\n  To deploy against any live Kubernetes cluster (Minikube, KIND, EKS, GKE, AKS):")
    print(f"    kubectl apply -f {MANIFEST_DIR}/00-namespace.yaml")
    print(f"    kubectl apply -f {MANIFEST_DIR}/mongo-keyfile-secret.yaml")
    print(f"    kubectl apply -f {MANIFEST_DIR}/mongo-headless-svc.yaml")
    print(f"    kubectl apply -f {MANIFEST_DIR}/mongo-statefulset.yaml")
    print(f"    kubectl rollout status statefulset/{STATEFULSET_NAME} -n {NAMESPACE}")
    print(f"    kubectl apply -f {MANIFEST_DIR}/03-replicaset-init-job.yaml")
    print(f"    kubectl exec -n {NAMESPACE} -it {STATEFULSET_NAME}-0 -- mongosh --eval 'rs.status()'")


def main():
    print("=" * 60)
    print("  Lab 13.2: Kubernetes StatefulSet for MongoDB")
    print("=" * 60)
    print(f"Manifest Directory: {MANIFEST_DIR}")

    if kubectl_available():
        print("  [OK] kubectl is connected to active cluster.")
        if apply_manifests():
            verify_cluster()
    else:
        print_manual_instructions()


if __name__ == "__main__":
    main()
