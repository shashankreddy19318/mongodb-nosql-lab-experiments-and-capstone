// =============================================================================
// Lab 8.1 - MongoDB Replica Set Initialization & Verification Script
// =============================================================================

print("\n--- Initializing 3-Node Replica Set (rs0) ---");
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "host.docker.internal:27017" },
    { _id: 1, host: "host.docker.internal:27018" },
    { _id: 2, host: "host.docker.internal:27019" }
  ]
});

print("Replica set initiate command executed. Waiting for primary election...");
while (true) {
  try {
    let status = rs.status();
    let hasPrimary = status.members.some(m => m.stateStr === "PRIMARY");
    if (hasPrimary) {
      print("Primary elected successfully!\n");
      break;
    }
  } catch (err) {
    // waiting
  }
  sleep(1000);
}

print("=== Current Replica Set Status ===");
let status = rs.status();
status.members.forEach(m => {
  print("Member ID: " + m._id + " | Host: " + m.name + " | Role: " + m.stateStr + " | Health: " + m.health);
});

print("\n=== Inserting Sample Document on Primary ===");
db = db.getSiblingDB("inventory_db");
let insertResult = db.products.insertOne({
  item: "Industrial Sensor Node",
  sku: "SN-90210",
  qty: 250,
  status: "ACTIVE",
  replicated_at: new Date()
});
print("Inserted document ID: " + insertResult.insertedId);

print("\n=== Verifying Replication on Primary ===");
printjson(db.products.findOne({ sku: "SN-90210" }));
print("\nReplication script complete. Verify on secondaries using rs.secondaryOk() or db.setReadPref('secondary').");
