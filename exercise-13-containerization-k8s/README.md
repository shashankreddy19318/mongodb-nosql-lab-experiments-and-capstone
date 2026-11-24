# Exercise 13: Deploying MongoDB with Containers and the Cloud

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-Repository-blue?logo=docker)](https://hub.docker.com/r/chintan/mongodb-replica-k8s-lab13)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0%20ReplicaSet-green?logo=mongodb)](https://www.mongodb.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-StatefulSet-326CE5?logo=kubernetes)](https://kubernetes.io/)
[![Prometheus](https://img.shields.io/badge/Prometheus-Exporter%20Sidecar-orange?logo=prometheus)](https://prometheus.io/)
[![Terraform](https://img.shields.io/badge/Terraform-Atlas%20M0-purple?logo=terraform)](https://www.terraform.io/)

---

## 📌 Submission Information
- **Docker Hub Repository URL:** `https://hub.docker.com/r/chintan/mongodb-replica-k8s-lab13` *(or replace with your Docker Hub handle)*
- **Docker Image Tag:** `chintan/mongodb-replica-k8s-lab13:latest`
- **PDF Report:** [`Lab13_NoSQL_MongoDB_ReplicaSet_K8s_Report.pdf`](./Lab13_NoSQL_MongoDB_ReplicaSet_K8s_Report.pdf)

> **Note for Grading / Evaluation:**  
> The uploaded Docker image is fully self-contained and equipped with an interactive demonstration CLI test harness (`demo/run_demo.py`) that showcases all completed lab deliverables. Graders can run the image directly with a single command!

```bash
# Pull and run the interactive demonstration container
docker run -it --rm chintan/mongodb-replica-k8s-lab13:latest
```

---

## 🚀 Quick Start Demonstration Guide

### Option 1: Run the Pre-packaged Demonstration Container
```bash
# Automated full-suite demonstration run
docker run --rm chintan/mongodb-replica-k8s-lab13:latest --auto

# Interactive menu mode (inspect individual labs)
docker run -it --rm chintan/mongodb-replica-k8s-lab13:latest
```

### Option 2: Deploy Locally with Docker Compose (Lab 13.1 + Activity)
```bash
# 1. Generate keyfile with strict permissions
bash generate-keyfile.sh keyfile
# (On Windows PowerShell: .\generate-keyfile.ps1)

# 2. Start the 3-node cluster and Prometheus monitoring sidecar
docker-compose up -d

# 3. Initialize the replica set and provision admin/exporter users
docker exec -i prod-mongo-1 mongosh --quiet < scripts/init-replica.js

# 4. Run PyMongo continuous failover verification
python scripts/test_failover.py

# 5. Verify Prometheus Exporter metrics endpoint
python scripts/verify_metrics.py
# (View metrics in browser at http://localhost:9216/metrics or Prometheus UI at http://localhost:9090)
```

### Option 3: Deploy to Kubernetes (Lab 13.2)
```bash
# Apply Kubernetes manifests in order
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/mongo-keyfile-secret.yaml
kubectl apply -f k8s/mongo-headless-svc.yaml
kubectl apply -f k8s/mongo-statefulset.yaml

# Monitor rollout until all 3 replicas are running
kubectl rollout status statefulset/mongo -n nosql-labs

# Initialize replica set via Job
kubectl apply -f k8s/03-replicaset-init-job.yaml

# Test pod resiliency and self-healing
bash scripts/test_resiliency.sh
```

---

## 📂 Project Structure

```
.
├── README.md                                  # Comprehensive documentation & grading instructions
├── Dockerfile                                 # Multi-stage demonstration Docker image
├── docker-compose-production.yml              # Base production 3-node replica set with keyFile auth
├── docker-compose.yml                         # Production compose + Prometheus Exporter + Prometheus
├── prometheus.yml                             # Prometheus scrape configuration targeting exporter
├── generate-keyfile.sh                        # Keyfile generation script (Linux/macOS)
├── generate-keyfile.ps1                       # Keyfile generation script (Windows PowerShell)
├── keyfile                                    # 756-byte internal replica set authentication key
├── docker-build-push.sh                       # Automation script to build & push image to Docker Hub
├── docker-build-push.bat                      # Windows batch script for Docker Hub build & push
├── Lab13_NoSQL_MongoDB_ReplicaSet_K8s_Report.pdf # Formal submission PDF report
├── scripts/
│   ├── init-replica.js                        # Replica set initiation and RBAC user provisioning
│   ├── test_failover.py                       # PyMongo continuous read/write failover test
│   ├── verify_metrics.py                      # Prometheus exporter metric validator
│   ├── deploy_prod.sh                         # End-to-end Docker Compose deploy automation
│   ├── deploy_prod.ps1                        # PowerShell deployment automation
│   └── test_resiliency.sh                     # K8s pod deletion & self-healing test automation
├── k8s/
│   ├── 00-namespace.yaml                      # K8s namespace (nosql-labs)
│   ├── mongo-headless-svc.yaml                # Headless Service (clusterIP: None) for stable DNS
│   ├── mongo-statefulset.yaml                 # StatefulSet with InitContainer, emptyDir & PVCs
│   ├── mongo-keyfile-secret.yaml              # Secret containing the internal authentication key
│   ├── 03-replicaset-init-job.yaml            # Automated K8s Job for rs.initiate()
│   ├── mongo-client-pod.yaml                  # Interactive debug client pod
│   └── lab_02_k8s_statefulset.py              # Python automation script for K8s deployment
├── terraform/
│   ├── main.tf                                # Terraform Atlas free-tier cluster configuration (M0)
│   ├── variables.tf                           # Atlas variable definitions
│   └── terraform.tfvars.example               # Example variables template
└── demo/
    ├── run_demo.py                            # Interactive CLI demo harness for grader/evaluator
    └── entrypoint.sh                          # Demonstration container entrypoint
```

---

## 🧪 Detailed Lab Solutions

### Lab 13.1: Deploy a Replica Set with Docker Compose
- **KeyFile Authentication:** Internal peer authentication between `mongod` nodes is enforced using a 756-byte base64 keyfile with `chmod 400` permissions. Members verify peer legitimacy before allowing them into the cluster.
- **Node Architecture:** Three containerized nodes (`mongo-rs0-1:27017`, `mongo-rs0-2:27018`, `mongo-rs0-3:27019`) configured with `--replSet rs0 --keyFile /etc/mongodb/keyfile --auth --bind_ip_all`.
- **Healthchecks:** Native `mongosh` healthchecks ensure container orchestration responds to transient database stalls.
- **PyMongo Automatic Failover:**
  - `scripts/test_failover.py` launches concurrent write and read threads with `retryWrites=True` and `readPreference=primaryPreferred`.
  - Primary step-down (`rs.stepDown(30)`) is dispatched.
  - The driver handles transient `AutoReconnect` exceptions during the 2–3 second Raft election window.
  - Client automatically rediscovers the newly elected primary (`mongo-rs0-2`) and resumes writes without data loss.

### Activity for 13.1: Prometheus Exporter Sidecar
- Integrated `percona/mongodb_exporter:0.40.0` sidecar mapped to port `9216`.
- Provisioned dedicated `exporter` user with `clusterMonitor` role on `admin` and `read` on `local`.
- Exposes vital operational telemetry:
  - `mongodb_up`: Instance availability (1 = healthy)
  - `mongodb_mongod_replset_my_state`: Member role (1 = PRIMARY, 2 = SECONDARY)
  - `mongodb_mongod_replset_number_of_members`: Active cluster member count (3)
  - `mongodb_mongod_replset_oplog_head_timestamp`: Replication lag monitoring
  - `mongodb_connections`: Connection pool saturation
- Prometheus server scrapes metrics at 5-second intervals via `prometheus.yml`.

### Lab 13.2: Kubernetes StatefulSet for MongoDB
- **Headless Service (`mongo-headless-svc.yaml`):**
  - Configured with `clusterIP: None` and `selector: app: mongo`.
  - Disables virtual IP round-robin routing; CoreDNS creates deterministic A-records for each pod:
    - `mongo-0.mongo-headless-svc.nosql-labs.svc.cluster.local`
    - `mongo-1.mongo-headless-svc.nosql-labs.svc.cluster.local`
    - `mongo-2.mongo-headless-svc.nosql-labs.svc.cluster.local`
- **StatefulSet (`mongo-statefulset.yaml`):**
  - **InitContainer (`init-keyfile`):** Runs before `mongod`. Copies keyfile from Secret to a shared `emptyDir` volume, executes `chmod 400 /etc/mongodb/keyfile`, and sets ownership to `999:999` (mongodb UID).
  - **VolumeClaimTemplates:** Dynamically provisions dedicated `PersistentVolumeClaims` (`mongo-data-mongo-0`, `mongo-data-mongo-1`, `mongo-data-mongo-2`).
  - **Readiness Probe:** Executes `mongosh --eval 'db.runCommand({ping:1})'` every 10 seconds to ensure pod is healthy before serving traffic.
- **Resiliency & Self-Healing (`scripts/test_resiliency.sh`):**
  - Simulated failure: `kubectl delete pod mongo-2 -n nosql-labs`.
  - StatefulSet controller immediately recreates `mongo-2` with the exact same hostname and re-attaches PVC `mongo-data-mongo-2`.
  - Pod performs rapid replication catch-up from oplog and rejoins `rs0` as `SECONDARY` with zero data loss.

---

## 📊 Comparison: Docker Compose vs. Kubernetes StatefulSet

| Dimension | Docker Compose (Lab 13.1) | Kubernetes StatefulSet (Lab 13.2) |
|---|---|---|
| **Identity Management** | Host/Container names; IP addresses change on recreation | Predictable, stable network identities (`pod-0`, `pod-1`) via Headless Service |
| **Storage Persistence** | Docker named volumes mapped to local host storage | Per-pod `PersistentVolumeClaims` dynamically bound to cloud/network block storage |
| **Self-Healing** | Container restarts locally if daemon is running; no node-failover | Automated rescheduling across worker nodes upon physical node failure |
| **Secret Management** | Keyfile mounted directly from local filesystem (`./keyfile`) | Kubernetes `Secret` mounted via volume and adjusted by InitContainer |
| **Service Discovery** | Bridge network DNS (`host.docker.internal` or container name) | Headless Service CoreDNS records (`<pod>.<svc>.<ns>.svc.cluster.local`) |
| **Operational Overhead** | Extremely low; single config file, runs on developer machine | Higher complexity; requires control plane, CNI, CSI, and manifest management |
| **Production Fit** | Local development, CI/CD testing, staging sandboxes | Mission-critical enterprise production, high availability, auto-scaling |

---

## ☁️ Cloud: Terraform MongoDB Atlas Free-Tier Cluster (`main.tf`)
The Terraform configuration in `terraform/main.tf` provisions:
1. `mongodbatlas_project`: Logical project container for the lab environment.
2. `mongodbatlas_cluster`: Multi-AZ M0 Sandbox cluster in AWS Mumbai (`AP_SOUTH_1`), MongoDB 7.0.
3. `mongodbatlas_database_user`: Application user with `readWriteAnyDatabase` privileges.
4. `mongodbatlas_ip_access_list`: Network firewall IP access list.
5. Output variables exporting the production-ready `mongodb+srv://` connection string.

---

## 🚢 Building and Uploading to Docker Hub

To build and publish the demonstration image to your personal Docker Hub repository:

```bash
# 1. Login to Docker Hub
docker login

# 2. Build and push using the automation script
./docker-build-push.sh <your-dockerhub-username> latest

# Alternatively, manual build and push:
docker build -t <your-dockerhub-username>/mongodb-replica-k8s-lab13:latest .
docker push <your-dockerhub-username>/mongodb-replica-k8s-lab13:latest
```
