// =============================================================================
// Lab 8.2 Try It Yourself - Reconfigure Priorities and Predict Election
// =============================================================================

print("\n=== Fetching Current Replica Set Configuration ===");
let cfg = rs.conf();

print("\n=== Assigning Distinct Priority Values ===");
// Node 0: host.docker.internal:27017 -> Priority 1 (Low priority)
// Node 1: host.docker.internal:27018 -> Priority 10 (Highest priority)
// If node 2 is an arbiter or secondary, adjust accordingly
cfg.members.forEach(m => {
  if (m.host.includes("27017")) {
    m.priority = 1;
  } else if (m.host.includes("27018")) {
    m.priority = 10;
  } else if (m.host.includes("27019") && !m.arbiterOnly) {
    m.priority = 3;
  }
});

print("Applying reconfiguration with rs.reconfig()...");
try {
  let reconfigRes = rs.reconfig(cfg);
  printjson(reconfigRes);
} catch (e) {
  print("Reconfig result: " + e.message);
}

sleep(3000);

print("\n=== Configured Member Priorities ===");
rs.conf().members.forEach(m => {
  print("Member: " + m.host + " | Priority: " + m.priority + " | Arbiter: " + (m.arbiterOnly ? "YES" : "NO"));
});

print("\n=======================================================");
print("PREDICTION:");
print("Because host.docker.internal:27018 has the highest priority (10),");
print("when host.docker.internal:27017 steps down, the election MUST elect");
print("host.docker.internal:27018 as PRIMARY.");
print("=======================================================\n");
