/**
 * init-replica.js
 * Initializes replica set 'rs0' with 3 nodes and provisions administrative & monitoring accounts.
 */

// Step 1: Initialize replica set
try {
  const status = rs.status();
  if (status.ok === 1) {
    print("[INFO] Replica set rs0 is already initiated.");
  }
} catch (e) {
  print("[INFO] Initiating replica set rs0...");
  const initResult = rs.initiate({
    _id: "rs0",
    members: [
      { _id: 0, host: "mongo-rs0-1:27017", priority: 2 },
      { _id: 1, host: "mongo-rs0-2:27017", priority: 1 },
      { _id: 2, host: "mongo-rs0-3:27017", priority: 1 }
    ]
  });
  print("[OK] rs.initiate() result: " + JSON.stringify(initResult));
}

// Wait for this node to become primary
print("[INFO] Waiting for primary election...");
while (!db.isMaster().ismaster) {
  sleep(1000);
}
print("[OK] Primary elected: " + db.isMaster().primary);

// Step 2: Create Admin User on primary
const adminDb = db.getSiblingDB("admin");
if (adminDb.getUser("admin") === null) {
  adminDb.createUser({
    user: "admin",
    pwd: "AdminPass123!",
    roles: [
      { role: "userAdminAnyDatabase", db: "admin" },
      { role: "clusterAdmin", db: "admin" },
      { role: "readWriteAnyDatabase", db: "admin" }
    ]
  });
  print("[OK] Admin user 'admin' created.");
} else {
  print("[INFO] Admin user 'admin' already exists.");
}

// Step 3: Create Prometheus Exporter User with clusterMonitor role
if (adminDb.getUser("exporter") === null) {
  adminDb.createUser({
    user: "exporter",
    pwd: "ExporterPass123!",
    roles: [
      { role: "clusterMonitor", db: "admin" },
      { role: "read", db: "local" }
    ]
  });
  print("[OK] Exporter user 'exporter' created.");
} else {
  print("[INFO] Exporter user 'exporter' already exists.");
}

// Step 4: Print replica set status summary
print("\n=== Current Replica Set Status ===");
const currentStatus = rs.status();
currentStatus.members.forEach(m => {
  print(`Node [${m.name}]: State=${m.stateStr}, Health=${m.health}, Uptime=${m.uptime}s`);
});
