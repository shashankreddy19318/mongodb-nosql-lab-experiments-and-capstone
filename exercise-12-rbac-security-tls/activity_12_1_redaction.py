#!/usr/bin/env python3
"""
Activity 12.1: Field-Level Redaction via Views & Role-Based Access Control
=============================================================================
Demonstrates:
1. Creating a collection 'employees' with sensitive fields (ssn, salary).
2. Creating an aggregation view 'employees_safe' using $project:
   - Excludes 'salary' completely ($$REMOVE or omitting it).
   - Masks 'ssn' to '***-**-XXXX' using $concat and $substr.
3. Establishing RBAC roles:
   - hr_role: Full access to the raw 'employees' collection.
   - non_hr_role: Access ONLY to the 'employees_safe' view.
4. Verifying access:
   - HR user sees full salary and unmasked SSN.
   - Non-HR user through the view sees no salary and masked SSN.
   - Non-HR user attempting to access raw collection is REJECTED (Unauthorized).
"""

import sys
import json
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError

ADMIN_URI = "mongodb://admin:AdminPass123!@localhost:27017/admin?authSource=admin"
HR_URI = "mongodb://hr_user:HrPass123!@localhost:27017/hr_db?authSource=admin"
STAFF_URI = "mongodb://staff_user:StaffPass123!@localhost:27017/hr_db?authSource=admin"

EMPLOYEES_DATA = [
    {
        "empId": "E101",
        "username": "arjun",
        "name": "Arjun Patel",
        "email": "arjun@company.com",
        "department": "Engineering",
        "role": "Lead Architect",
        "ssn": "111-22-3333",
        "salary": 165000
    },
    {
        "empId": "E102",
        "username": "sneha",
        "name": "Sneha Sharma",
        "email": "sneha@company.com",
        "department": "Finance",
        "role": "Financial Analyst",
        "ssn": "444-55-6666",
        "salary": 125000
    },
    {
        "empId": "E103",
        "username": "rahul",
        "name": "Rahul Verma",
        "email": "rahul@company.com",
        "department": "Security",
        "role": "SecOps Engineer",
        "ssn": "777-88-9999",
        "salary": 140000
    }
]

def print_banner(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def setup_data_and_views():
    print_banner("1. Setting up Data, Views, and RBAC via Admin")
    client = MongoClient(ADMIN_URI, serverSelectionTimeoutMS=5000)
    db = client["hr_db"]
    admin_db = client["admin"]

    # 1. Reset base collection
    db["employees"].drop()
    db["employees"].insert_many(EMPLOYEES_DATA)
    print(f"[OK] Seeded {len(EMPLOYEES_DATA)} records into 'hr_db.employees'.")

    # 2. Create or recreate redacted view 'employees_safe'
    # Dropping existing view if exists
    try:
        db["employees_safe"].drop()
    except Exception:
        pass

    pipeline = [
        {
            "$project": {
                "_id": 0,
                "empId": 1,
                "username": 1,
                "name": 1,
                "email": 1,
                "department": 1,
                "role": 1,
                # Mask SSN: keep only last 4 digits
                "ssn": {
                    "$concat": [
                        "***-**-",
                        {"$substrCP": ["$ssn", 7, 4]}
                    ]
                },
                # Redact salary completely using $$REMOVE
                "salary": "$$REMOVE"
            }
        }
    ]

    db.command({
        "create": "employees_safe",
        "viewOn": "employees",
        "pipeline": pipeline
    })
    print("[OK] Created aggregation view 'employees_safe' with field-level redaction:")
    print("     - 'salary' field: completely excluded ($$REMOVE)")
    print("     - 'ssn' field: masked with '***-**-XXXX' ($concat + $substrCP)")

    # 3. Create Custom Roles:
    # - hr_role: Read/Write on employees collection
    try:
        admin_db.command({
            "createRole": "hr_role",
            "privileges": [
                {
                    "resource": {"db": "hr_db", "collection": "employees"},
                    "actions": ["find", "insert", "update", "delete"]
                },
                {
                    "resource": {"db": "hr_db", "collection": "employees_safe"},
                    "actions": ["find"]
                }
            ],
            "roles": []
        })
        print("[OK] Role created: hr_role (Full access to 'employees' and view)")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("[INFO] Role hr_role already exists.")
        else:
            raise

    # - non_hr_role: Access ONLY to view 'employees_safe', NEVER raw collection!
    try:
        admin_db.command({
            "createRole": "non_hr_role",
            "privileges": [
                {
                    "resource": {"db": "hr_db", "collection": "employees_safe"},
                    "actions": ["find", "aggregate"]
                }
            ],
            "roles": []
        })
        print("[OK] Role created: non_hr_role (Least-privilege access ONLY to view 'employees_safe')")
    except OperationFailure as e:
        if "already exists" in str(e):
            print("[INFO] Role non_hr_role already exists.")
        else:
            raise

    # 4. Create Users:
    # - hr_user
    try:
        admin_db.command({
            "createUser": "hr_user",
            "pwd": "HrPass123!",
            "roles": [{"role": "hr_role", "db": "admin"}]
        })
        print("[OK] User created: hr_user (HR Officer)")
    except OperationFailure as e:
        if "already exists" in str(e):
            admin_db.command("updateUser", "hr_user", pwd="HrPass123!", roles=[{"role": "hr_role", "db": "admin"}])
            print("[OK] User updated: hr_user")

    # - staff_user
    try:
        admin_db.command({
            "createUser": "staff_user",
            "pwd": "StaffPass123!",
            "roles": [{"role": "non_hr_role", "db": "admin"}]
        })
        print("[OK] User created: staff_user (Regular Staff Member)")
    except OperationFailure as e:
        if "already exists" in str(e):
            admin_db.command("updateUser", "staff_user", pwd="StaffPass123!", roles=[{"role": "non_hr_role", "db": "admin"}])
            print("[OK] User updated: staff_user")

    client.close()

def test_hr_user_access():
    print_banner("2. Testing HR User Access (Authorized to View Raw Sensitive Data)")
    client = MongoClient(HR_URI, serverSelectionTimeoutMS=5000)
    db = client["hr_db"]

    try:
        docs = list(db["employees"].find({}, {"_id": 0}))
        print(f"[OK] HR User queried 'employees' collection directly ({len(docs)} documents):")
        for doc in docs:
            print(f"     [HR Record] Name: {doc['name']:<15} Role: {doc['role']:<18} SSN: {doc['ssn']}  Salary: ${doc['salary']:,}")
        
        # Verify sensitive fields exist
        assert all("salary" in d and "ssn" in d for d in docs)
        print("\n[VERIFIED] HR user successfully accessed unredacted sensitive fields.")
    except Exception as e:
        print(f"[ERROR] HR query failed: {e}")
        raise
    finally:
        client.close()

def test_non_hr_user_access():
    print_banner("3. Testing Non-HR User Access (Enforcing Field-Level Redaction & Least Privilege)")
    client = MongoClient(STAFF_URI, serverSelectionTimeoutMS=5000)
    db = client["hr_db"]

    # Test 3.1: Querying the authorized view
    print("[Test 3.1] Non-HR user querying authorized view 'employees_safe'...")
    try:
        safe_docs = list(db["employees_safe"].find({}, {"_id": 0}))
        print(f"[OK] Retrieved {len(safe_docs)} records from 'employees_safe':")
        for doc in safe_docs:
            has_salary = "salary" in doc
            print(f"     [Redacted] Name: {doc['name']:<15} Role: {doc['role']:<18} SSN: {doc['ssn']}  Salary: {'EXPOSED!' if has_salary else '[REDACTED]'}")
            if has_salary:
                raise ValueError("Security violation: 'salary' field was exposed in redacted view!")
            if not doc['ssn'].startswith("***-**-"):
                raise ValueError(f"Security violation: SSN was not masked properly: {doc['ssn']}")

        print("\n[VERIFIED] Redacted view correctly masked SSN and completely excluded salary.")
    except Exception as e:
        print(f"[ERROR] View query failed: {e}")
        raise

    # Test 3.2: Attempting to query the raw collection directly (Must FAIL)
    print("\n[Test 3.2] Non-HR user attempting to bypass view and query raw 'employees' collection...")
    try:
        raw_docs = list(db["employees"].find({}, {"_id": 0}))
        print("[ERROR] SECURITY BREACH! Non-HR user was able to query raw 'employees' collection!")
        print(raw_docs)
        sys.exit(1)
    except OperationFailure as e:
        print(f"[OK] Unauthorized access correctly REJECTED by MongoDB RBAC engine:")
        print(f"     Error Code: {e.code}")
        print(f"     Message:    {e.details.get('errmsg', str(e))}")
    finally:
        client.close()

def main():
    print_banner("Activity 12.1: Field-Level Redaction via Views & RBAC Enforcement")
    try:
        setup_data_and_views()
        test_hr_user_access()
        test_non_hr_user_access()
        print_banner("[PASS] Activity 12.1 Completed Successfully!")
    except Exception as e:
        print(f"\n[FAIL] Activity 12.1 encountered an error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
