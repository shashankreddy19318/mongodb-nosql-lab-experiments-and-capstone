// =============================================================================
// Lab 8.2 - MongoDB Failover & Election Demonstration Commands
// =============================================================================

print("\n=== Current Primary Identification ===");
let statusBefore = rs.status();
let currentPrimary = statusBefore.members.find(m => m.stateStr === "PRIMARY");
print("Current PRIMARY before stepDown: " + (currentPrimary ? currentPrimary.name : "None"));

print("\n=== Step 1: Forcing Election via rs.stepDown(60) ===");
print("Executing stepDown command on primary node (forces node to step down for 60 seconds)...");
try {
  rs.stepDown(60);
} catch (e) {
  // rs.stepDown disconnects current client session as node steps down to SECONDARY
  print("stepDown triggered (connection closed by server during role transition): " + e.message);
}

print("\n=== Step 2: Waiting for New Primary Election ===");
sleep(4000);

print("\n=== Step 3: Checking New Replica Set Status ===");
let statusAfter = rs.status();
statusAfter.members.forEach(m => {
  print("Member: " + m.name + " | Role: " + m.stateStr + " | Health: " + m.health);
});

let newPrimary = statusAfter.members.find(m => m.stateStr === "PRIMARY");
print("\n>>> NEW PRIMARY ELECTED: " + (newPrimary ? newPrimary.name : "Election still settling") + " <<<");
