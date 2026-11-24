// =============================================================================
// Lab 8.1 Try It Yourself - MongoDB Replica Set with Dedicated Arbiter Node
// =============================================================================

print("\n--- Initializing Replica Set with Arbiter Node (rs0) ---");
try {
  let initRes = rs.initiate({
    _id: "rs0",
    members: [
      { _id: 0, host: "host.docker.internal:27017", priority: 2 },
      { _id: 1, host: "host.docker.internal:27018", priority: 1 },
      { _id: 2, host: "host.docker.internal:27019", arbiterOnly: true }
    ]
  });
  printjson(initRes);
} catch (e) {
  print("Replica set already initiated or reconfiguring: " + e.message);
}

print("\nWaiting for replica set election to settle...");
while (true) {
  try {
    let s = rs.status();
    let hasPrimary = s.members.some(m => m.stateStr === "PRIMARY");
    let hasArbiter = s.members.some(m => m.stateStr === "ARBITER");
    if (hasPrimary && hasArbiter) {
      print("Primary and Arbiter nodes confirmed online!\n");
      break;
    }
  } catch (err) {
    // waiting
  }
  sleep(1000);
}

print("=== Replica Set Membership & Roles ===");
let status = rs.status();
status.members.forEach(m => {
  print("Node ID: " + m._id + 
        " | Host: " + m.name + 
        " | State: " + m.stateStr + 
        " | Health: " + m.health +
        " | Arbiter: " + (m.arbiterOnly ? "YES" : "NO"));
});

print("\n=== Testing Data Write on Primary ===");
db = db.getSiblingDB("arbiter_demo_db");
let res = db.orders.insertOne({
  order_id: "ORD-9901",
  customer: "Enterprise Client A",
  amount: 4500.00,
  created_at: new Date()
});
print("Inserted record with ID: " + res.insertedId);

print("\n=== Checking Arbiter Node Direct Read Behavior ===");
print("Note: Arbiters hold no data and cannot accept queries.");
print("Setup complete.");
