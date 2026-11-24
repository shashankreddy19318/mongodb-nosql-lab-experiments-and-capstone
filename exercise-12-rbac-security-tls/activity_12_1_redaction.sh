#!/bin/bash
# ==============================================================================
# Activity 12.1: Field-Level Redaction via Views & RBAC (mongosh shell edition)
# ==============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}   Activity 12.1: Field-Level Redaction via Views (mongosh)         ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Seed & Create View + Roles
mongosh -u "admin" -p "AdminPass123!" --authenticationDatabase "admin" --quiet --eval '
const hrDb = db.getSiblingDB("hr_db");
const adminDb = db.getSiblingDB("admin");

hrDb.employees.drop();
hrDb.employees.insertMany([
  { username: "arjun", email: "arjun@company.com", role: "admin", ssn: "111-22-3333", salary: 150000 },
  { username: "sneha", email: "sneha@company.com", role: "developer", ssn: "444-55-6666", salary: 120000 },
  { username: "rahul", email: "rahul@company.com", role: "developer", ssn: "777-88-9999", salary: 130000 }
]);
print("[OK] Seeded 3 employee records.");

try { hrDb.employees_safe.drop(); } catch(e) {}

hrDb.createView(
  "employees_safe",
  "employees",
  [
    {
      $project: {
        _id: 0,
        username: 1,
        email: 1,
        role: 1,
        ssn: { $concat: ["***-**-", { $substrCP: ["$ssn", 7, 4] }] },
        salary: "$$REMOVE"
      }
    }
  ]
);
print("[OK] Created view: employees_safe (salary excluded, ssn masked).");

// Roles
try {
  adminDb.createRole({
    role: "hr_role",
    privileges: [{ resource: { db: "hr_db", collection: "employees" }, actions: ["find", "insert", "update"] }],
    roles: []
  });
} catch(e) {}

try {
  adminDb.createRole({
    role: "non_hr_role",
    privileges: [{ resource: { db: "hr_db", collection: "employees_safe" }, actions: ["find"] }],
    roles: []
  });
} catch(e) {}

// Users
try {
  adminDb.createUser({ user: "hr_user", pwd: "HrPass123!", roles: [{ role: "hr_role", db: "admin" }] });
} catch(e) {}

try {
  adminDb.createUser({ user: "staff_user", pwd: "StaffPass123!", roles: [{ role: "non_hr_role", db: "admin" }] });
} catch(e) {}

print("[OK] Roles & users created: hr_user (HR role), staff_user (non-HR role).");
'

echo ""
echo -e "${YELLOW}=== Testing HR User Access (Direct Collection Query) ===${NC}"
mongosh -u "hr_user" -p "HrPass123!" --authenticationDatabase "admin" --quiet --eval '
const hrDb = db.getSiblingDB("hr_db");
const docs = hrDb.employees.find({}, {_id: 0}).toArray();
print("[OK] HR User can see full sensitive documents:");
docs.forEach(d => print("     " + JSON.stringify(d)));
'

echo ""
echo -e "${YELLOW}=== Testing Non-HR User Access (Querying Safe View) ===${NC}"
mongosh -u "staff_user" -p "StaffPass123!" --authenticationDatabase "admin" --quiet --eval '
const hrDb = db.getSiblingDB("hr_db");
const docs = hrDb.employees_safe.find().toArray();
print("[OK] Non-HR User querying employees_safe view (SSN masked, salary removed):");
docs.forEach(d => print("     " + JSON.stringify(d)));
'

echo ""
echo -e "${YELLOW}=== Testing Non-HR User Access Violation (Querying Raw Collection) ===${NC}"
mongosh -u "staff_user" -p "StaffPass123!" --authenticationDatabase "admin" --quiet --eval '
const hrDb = db.getSiblingDB("hr_db");
try {
  hrDb.employees.find().toArray();
  print("[ERROR] Security breach! Non-HR user queried raw employees collection!");
} catch(e) {
  print("[OK] Access correctly REJECTED by MongoDB RBAC: " + e.message.substring(0, 65));
}
'

echo -e "\n${GREEN}[PASS] Activity 12.1 mongosh verification finished successfully!${NC}"
