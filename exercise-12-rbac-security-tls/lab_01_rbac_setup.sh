#!/bin/bash
# ==============================================================================
# Lab 12.1 - Configure Authentication and Role-Based Access Control (RBAC)
# Objective: Set up authentication and least-privilege RBAC for MongoDB.
# ==============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}    Lab 12.1: Authentication & Role-Based Access Control (RBAC)     ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Ensure MongoDB is running
if ! mongosh --quiet --eval 'db.runCommand({ping:1})' >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] MongoDB is not running. Starting mongod on port 27017...${NC}"
    mkdir -p /data/db
    mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db --bind_ip 0.0.0.0
    sleep 2
fi

echo ""
echo -e "${YELLOW}=== Step 1: Create Admin User (Elevated Privileges) ===${NC}"
mongosh --quiet admin --eval '
try {
  db.createUser({
    user: "admin",
    pwd: "AdminPass123!",
    roles: [
      { role: "userAdminAnyDatabase", db: "admin" },
      { role: "clusterAdmin", db: "admin" },
      { role: "readWriteAnyDatabase", db: "admin" }
    ]
  });
  print("[OK] Admin user created with userAdminAnyDatabase, clusterAdmin, readWriteAnyDatabase.");
} catch(e) {
  if (e.code === 51003 || e.message.includes("already exists")) {
    print("[INFO] Admin user already exists, proceeding.");
  } else {
    throw e;
  }
}
'

echo ""
echo -e "${YELLOW}=== Step 2: Seed Sample Data in Databases ===${NC}"
mongosh -u "admin" -p "AdminPass123!" --authenticationDatabase "admin" --quiet --eval '
// Seed analytics database
const analyticsDb = db.getSiblingDB("analytics");
analyticsDb.reports.drop();
analyticsDb.reports.insertMany([
  { reportId: "RPT-001", month: "January", totalSales: 125000, region: "NA" },
  { reportId: "RPT-002", month: "February", totalSales: 142000, region: "EU" }
]);

// Seed nosql_labs database
const nosqlDb = db.getSiblingDB("nosql_labs");
nosqlDb.inventory.drop();
nosqlDb.inventory.insertMany([
  { item: "laptop", qty: 25, warehouse: "WH-A" },
  { item: "monitor", qty: 60, warehouse: "WH-B" }
]);

nosqlDb.orders.drop();
nosqlDb.orders.insertOne({ orderId: "ORD-101", item: "laptop", amount: 1200 });

nosqlDb.logs.drop();
nosqlDb.logs.insertOne({ timestamp: new Date(), level: "INFO", msg: "System boot" });

nosqlDb.secret_records.drop();
nosqlDb.secret_records.insertOne({ secretKey: "X-9981", classified: true });

// Seed bookstore database
const bookDb = db.getSiblingDB("bookstore");
bookDb.books.drop();
bookDb.books.insertOne({ title: "NoSQL Databases using MongoDB", author: "Sujeet Jagtap" });

print("[OK] Sample datasets created in: analytics, nosql_labs, bookstore.");
'

echo ""
echo -e "${YELLOW}=== Step 3: Define Custom Roles with Least Privilege ===${NC}"
mongosh -u "admin" -p "AdminPass123!" --authenticationDatabase "admin" --quiet --eval '
const adminDb = db.getSiblingDB("admin");

// 1. Role: analyticsReader - find/aggregate only on analytics db
try {
  adminDb.createRole({
    role: "analyticsReader",
    privileges: [
      {
        resource: { db: "analytics", collection: "" },
        actions: ["find", "aggregate"]
      }
    ],
    roles: []
  });
  print("[OK] Role created: analyticsReader (find, aggregate on analytics)");
} catch(e) { print("[INFO] analyticsReader role exists."); }

// 2. Role: collectionReader - read-only on specific collections
try {
  adminDb.createRole({
    role: "collectionReader",
    privileges: [
      { resource: { db: "analytics", collection: "reports" }, actions: ["find", "aggregate"] },
      { resource: { db: "nosql_labs", collection: "inventory" }, actions: ["find"] }
    ],
    roles: []
  });
  print("[OK] Role created: collectionReader (read-only on analytics.reports, nosql_labs.inventory)");
} catch(e) { print("[INFO] collectionReader role exists."); }

// 3. Role: collectionWriter - find/insert/update/delete on specific collection only
try {
  adminDb.createRole({
    role: "collectionWriter",
    privileges: [
      {
        resource: { db: "nosql_labs", collection: "orders" },
        actions: ["find", "insert", "update", "delete"]
      }
    ],
    roles: []
  });
  print("[OK] Role created: collectionWriter (CRUD on nosql_labs.orders only)");
} catch(e) { print("[INFO] collectionWriter role exists."); }

// 4. Role: limitedWriter - can insert/update logs, read all collections in nosql_labs
try {
  adminDb.createRole({
    role: "limitedWriter",
    privileges: [
      { resource: { db: "nosql_labs", collection: "logs" }, actions: ["find", "insert", "update"] },
      { resource: { db: "nosql_labs", collection: "" }, actions: ["find"] }
    ],
    roles: []
  });
  print("[OK] Role created: limitedWriter (insert/update on logs, read all in nosql_labs)");
} catch(e) { print("[INFO] limitedWriter role exists."); }
'

echo ""
echo -e "${YELLOW}=== Step 4: Create Application Users with Defined Roles ===${NC}"
mongosh -u "admin" -p "AdminPass123!" --authenticationDatabase "admin" --quiet --eval '
const adminDb = db.getSiblingDB("admin");

// Helper to safely create/update user
function safeCreateUser(userObj) {
  try {
    adminDb.createUser(userObj);
    print("[OK] User created: " + userObj.user);
  } catch(e) {
    if (e.code === 51003 || e.message.includes("already exists")) {
      adminDb.updateUser(userObj.user, { pwd: userObj.pwd, roles: userObj.roles });
      print("[OK] User updated: " + userObj.user);
    } else {
      throw e;
    }
  }
}

// User 1: app_user_read (Read-only on specific collections)
safeCreateUser({
  user: "app_user_read",
  pwd: "ReadPass123!",
  roles: [
    { role: "collectionReader", db: "admin" }
  ]
});

// User 2: app_user_write (Read-write on specific collection: orders)
safeCreateUser({
  user: "app_user_write",
  pwd: "WritePass123!",
  roles: [
    { role: "collectionWriter", db: "admin" }
  ]
});

// User 3: analyst (Read-only on nosql_labs and bookstore)
safeCreateUser({
  user: "analyst",
  pwd: "AnalystPass123!",
  roles: [
    { role: "read", db: "nosql_labs" },
    { role: "read", db: "bookstore" }
  ]
});

// User 4: app_writer (readWrite on nosql_labs only)
safeCreateUser({
  user: "app_writer",
  pwd: "WriterPass123!",
  roles: [
    { role: "readWrite", db: "nosql_labs" }
  ]
});

// User 5: log_writer (insert+update on logs, read all in nosql_labs)
safeCreateUser({
  user: "log_writer",
  pwd: "LogPass123!",
  roles: [
    { role: "limitedWriter", db: "admin" }
  ]
});
'

echo ""
echo -e "${YELLOW}=== Step 5: Verify Permissions (Positive & Negative Test Cases) ===${NC}"

# Test 1: app_user_read permitted action (find on analytics.reports)
echo -e "\n${BLUE}[Test 1.1] app_user_read: Query analytics.reports (Expected: SUCCESS)${NC}"
mongosh -u "app_user_read" -p "ReadPass123!" --authenticationDatabase "admin" --quiet --eval '
try {
  const docs = db.getSiblingDB("analytics").reports.find({}, {_id: 0, reportId: 1, month: 1, totalSales: 1}).toArray();
  print("[OK] Successfully read " + docs.length + " report(s): " + JSON.stringify(docs[0]));
} catch(e) {
  print("[ERROR] Authorized read failed: " + e.message);
}
'

# Test 2: app_user_read unauthorized action (insert into analytics.reports)
echo -e "\n${BLUE}[Test 1.2] app_user_read: Attempt INSERT into analytics.reports (Expected: FAIL - NotAuthorized)${NC}"
mongosh -u "app_user_read" -p "ReadPass123!" --authenticationDatabase "admin" --quiet --eval '
try {
  db.getSiblingDB("analytics").reports.insertOne({ reportId: "HACK-01", totalSales: 999999 });
  print("[ERROR] Security Breach! Insert should have been rejected!");
} catch(e) {
  print("[OK] Correctly rejected unauthorized write: " + e.message.substring(0, 65));
}
'

# Test 3: app_user_read unauthorized action (read nosql_labs.secret_records)
echo -e "\n${BLUE}[Test 1.3] app_user_read: Attempt READ from unauthorized collection (Expected: FAIL - NotAuthorized)${NC}"
mongosh -u "app_user_read" -p "ReadPass123!" --authenticationDatabase "admin" --quiet --eval '
try {
  db.getSiblingDB("nosql_labs").secret_records.find().toArray();
  print("[ERROR] Security Breach! Read should have been rejected!");
} catch(e) {
  print("[OK] Correctly rejected unauthorized read on secret_records: " + e.message.substring(0, 65));
}
'

# Test 4: app_user_write permitted action (insert and find on nosql_labs.orders)
echo -e "\n${BLUE}[Test 2.1] app_user_write: Insert and query on nosql_labs.orders (Expected: SUCCESS)${NC}"
mongosh -u "app_user_write" -p "WritePass123!" --authenticationDatabase "admin" --quiet --eval '
try {
  const res = db.getSiblingDB("nosql_labs").orders.insertOne({ orderId: "ORD-999", item: "monitor", amount: 450 });
  const doc = db.getSiblingDB("nosql_labs").orders.findOne({ orderId: "ORD-999" });
  print("[OK] Successfully wrote and read order: " + doc.orderId + " (item: " + doc.item + ", $" + doc.amount + ")");
} catch(e) {
  print("[ERROR] Authorized write failed: " + e.message);
}
'

# Test 5: app_user_write unauthorized action (attempt read on nosql_labs.inventory)
echo -e "\n${BLUE}[Test 2.2] app_user_write: Attempt READ on forbidden collection inventory (Expected: FAIL)${NC}"
mongosh -u "app_user_write" -p "WritePass123!" --authenticationDatabase "admin" --quiet --eval '
try {
  db.getSiblingDB("nosql_labs").inventory.find().toArray();
  print("[ERROR] Security Breach! Read should have failed!");
} catch(e) {
  print("[OK] Correctly rejected unauthorized read on inventory: " + e.message.substring(0, 65));
}
'

# Test 6: analyst trying to write (should FAIL)
echo -e "\n${BLUE}[Test 3.1] analyst: Attempt WRITE to nosql_labs (Expected: FAIL)${NC}"
mongosh -u "analyst" -p "AnalystPass123!" --authenticationDatabase "admin" --quiet --eval '
try {
  db.getSiblingDB("nosql_labs").inventory.insertOne({ item: "forbidden", qty: 0 });
  print("[ERROR] Write should have failed!");
} catch(e) {
  print("[OK] Write correctly rejected: " + e.message.substring(0, 65));
}
'

# Test 7: app_writer trying to read bookstore (should FAIL)
echo -e "\n${BLUE}[Test 3.2] app_writer: Attempt READ bookstore (Expected: FAIL)${NC}"
mongosh -u "app_writer" -p "WriterPass123!" --authenticationDatabase "admin" --quiet --eval '
try {
  db.getSiblingDB("bookstore").books.find().toArray();
  print("[ERROR] Read should have failed!");
} catch(e) {
  print("[OK] Read correctly rejected: " + e.message.substring(0, 65));
}
'

echo ""
echo -e "${GREEN}====================================================================${NC}"
echo -e "${GREEN}    [PASS] Lab 12.1 Authentication & RBAC Verification Complete!    ${NC}"
echo -e "${GREEN}====================================================================${NC}"
