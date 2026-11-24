"""
Lab 3.1 - Try It Yourself:
Design Decision & Implementation: Tracking Prerequisites Between Courses
Comparison: Embedded vs. Referenced Relationships

Decision: REFERENCED RELATIONSHIPS (Storing array of prerequisite Course Codes/IDs)
Justification:
1. Many-to-Many Nature: A course can be a prerequisite for many courses, and a course 
   can have multiple prerequisites. Embedding would lead to massive data duplication.
2. Update Consistency: If a course's name, syllabus, credits, or instructor changes, 
   a referenced design updates only one document. An embedded design would require 
   updating every dependent course across the entire catalog.
3. Arbitrary Depth & Recursion: Prerequisite dependency graphs (CS101 -> CS201 -> CS301 -> CS401)
   are directed acyclic graphs (DAGs). Embedding creates unbounded nesting depth.
4. Independent Document Lifecycle: Courses exist independently in the curriculum, 
   regardless of whether another course lists them as a prerequisite.
"""

import sys
import os
import json
from bson import json_util
from pymongo import MongoClient

def get_database():
    """Connect to local MongoDB instance or fallback to mongomock."""
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        print("[*] Successfully connected to live MongoDB server at localhost:27017")
        return client, client["university_db"], False
    except Exception:
        import mongomock
        print("[*] Local MongoDB server offline. Running with mongomock in-memory database.")
        client = mongomock.MongoClient()
        return client, client["university_db"], True

def main():
    client, db, is_mock = get_database()

    print("=" * 70)
    print("Lab 3.1 - Try It Yourself: Course Prerequisites (Referenced Design)")
    print("=" * 70)

    db.drop_collection("courses_with_prereqs")
    courses = db["courses_with_prereqs"]

    # ============================================================
    # Course Catalog with Referenced Prerequisites
    # 'prerequisites' stores an array of referenced course codes
    # ============================================================
    course_catalog = [
        {
            "code": "CS101",
            "title": "Introduction to Computer Science",
            "credits": 3,
            "instructor": "Dr. Adams",
            "prerequisites": [],  # Entry-level foundational course
            "schedule": {
                "days": ["Monday", "Wednesday", "Friday"],
                "time": "09:00 AM - 10:00 AM",
                "room": "Hall 101"
            },
            "students": [
                {"name": "Alice Johnson", "student_id": "S101", "grade": "A"},
                {"name": "Bob Williams", "student_id": "S102", "grade": "B+"}
            ]
        },
        {
            "code": "CS201",
            "title": "Data Structures and Algorithms",
            "credits": 4,
            "instructor": "Dr. Baker",
            "prerequisites": ["CS101"],  # References CS101
            "schedule": {
                "days": ["Tuesday", "Thursday"],
                "time": "10:00 AM - 11:30 AM",
                "room": "Hall 202"
            },
            "students": [
                {"name": "Charlie Davis", "student_id": "S103", "grade": "A-"},
                {"name": "Diana Ross", "student_id": "S104", "grade": "B"}
            ]
        },
        {
            "code": "CS301",
            "title": "Algorithms and Complexity",
            "credits": 4,
            "instructor": "Dr. Chen",
            "prerequisites": ["CS101", "CS201"],  # Multiple prerequisites
            "schedule": {
                "days": ["Monday", "Wednesday"],
                "time": "01:00 PM - 02:30 PM",
                "room": "Hall 305"
            },
            "students": [
                {"name": "Evan Wright", "student_id": "S105", "grade": "A"},
                {"name": "Frank Miller", "student_id": "S106", "grade": "B+"}
            ]
        },
        {
            "code": "CS401",
            "title": "Advanced Database Systems",
            "credits": 3,
            "instructor": "Dr. Smith",
            "prerequisites": ["CS201", "CS301"],  # Requires Data Structures & Algorithms
            "schedule": {
                "days": ["Tuesday", "Thursday", "Friday"],
                "time": "02:00 PM - 03:30 PM",
                "room": "Hall 410"
            },
            "students": [
                {"name": "Grace Hopper", "student_id": "S107", "grade": "A+"},
                {"name": "Henry Ford", "student_id": "S108", "grade": "A-"}
            ]
        },
        {
            "code": "CS502",
            "title": "Deep Learning & Artificial Intelligence",
            "credits": 4,
            "instructor": "Dr. Patel",
            "prerequisites": ["CS301", "CS401"],  # Advanced capstone
            "schedule": {
                "days": ["Monday", "Wednesday"],
                "time": "03:00 PM - 04:30 PM",
                "room": "Lab 501"
            },
            "students": [
                {"name": "Alice Johnson", "student_id": "S101", "grade": "A"},
                {"name": "Evan Wright", "student_id": "S105", "grade": "A-"}
            ]
        }
    ]

    result = courses.insert_many(course_catalog)
    print(f"[+] Inserted {len(result.inserted_ids)} courses with referenced prerequisite structure.\n")

    # ============================================================
    # Query 1: Direct prerequisite lookup for a specific course
    # ============================================================
    target_code = "CS401"
    print("-" * 70)
    print(f"QUERY 1: Retrieve Direct Prerequisites for '{target_code}'")
    print("-" * 70)
    target_course = courses.find_one({"code": target_code})
    print(f"  Target Course: {target_course['title']} ({target_course['code']})")
    print(f"  Direct Prerequisite Codes: {target_course['prerequisites']}")

    # Resolve details of prerequisite courses
    resolved_prereqs = list(courses.find({"code": {"$in": target_course['prerequisites']}}))
    for p in resolved_prereqs:
        print(f"    -> [{p['code']}] {p['title']} (Instructor: {p['instructor']}, Credits: {p['credits']})")
    print()

    # ============================================================
    # Query 2: Aggregation ($lookup) to resolve prerequisite details
    # ============================================================
    print("-" * 70)
    print("QUERY 2: Course Catalog with Resolved Prerequisite Details ($lookup)")
    print("-" * 70)

    pipeline = [
        {
            "$lookup": {
                "from": "courses_with_prereqs",
                "localField": "prerequisites",
                "foreignField": "code",
                "as": "prereq_details"
            }
        },
        {
            "$project": {
                "code": 1,
                "title": 1,
                "credits": 1,
                "prerequisites": 1,
                "prereq_details.code": 1,
                "prereq_details.title": 1,
                "prereq_details.credits": 1,
                "_id": 0
            }
        },
        {"$sort": {"code": 1}}
    ]

    resolved_catalog = list(courses.aggregate(pipeline))
    for item in resolved_catalog:
        prereqs = [f"{p['title']} ({p['code']})" for p in item.get('prereq_details', [])]
        prereq_display = ", ".join(prereqs) if prereqs else "None (Introductory Course)"
        print(f"  Course: [{item['code']}] {item['title']} ({item['credits']} credits)")
        print(f"    Prerequisites: {prereq_display}")
    print()

    # ============================================================
    # Query 3: Recursive Dependency Graph Traversal (Transitive Prereqs)
    # ============================================================
    print("-" * 70)
    print("QUERY 3: Full Dependency Chain for Capstone Course 'CS502'")
    print("-" * 70)

    def find_all_prerequisites(collection, course_code, visited=None):
        if visited is None:
            visited = set()
        c = collection.find_one({"code": course_code})
        if not c or not c.get("prerequisites"):
            return []
        
        full_list = []
        for req_code in c["prerequisites"]:
            if req_code not in visited:
                visited.add(req_code)
                req_course = collection.find_one({"code": req_code})
                if req_course:
                    full_list.append(req_course)
                    full_list.extend(find_all_prerequisites(collection, req_code, visited))
        return full_list

    capstone_code = "CS502"
    chain = find_all_prerequisites(courses, capstone_code)
    print(f"  Capstone: CS502 - Deep Learning & Artificial Intelligence")
    print(f"  Complete Prerequisite Chain (Direct + Transitive):")
    for idx, req in enumerate(chain, 1):
        print(f"    {idx}. [{req['code']}] {req['title']} (Instructor: {req['instructor']})")
    print()

    # ============================================================
    # Architectural Justification Summary
    # ============================================================
    print("-" * 70)
    print("ARCHITECTURAL JUSTIFICATION: REFERENCED VS. EMBEDDED")
    print("-" * 70)
    print("""
  1. ELIMINATES DATA DUPLICATION:
     CS201 is required by both CS301 and CS401. Referencing by code ('CS201')
     stores the course definition once, avoiding repetitive nested copies.

  2. PRESERVES ATOMICITY & SINGLE SOURCE OF TRUTH:
     If CS201 changes credits or room, only a single course document is modified.

  3. PREVENTS UNBOUNDED NESTING DEPTH:
     Curriculums form hierarchical trees. Embedding transitive prerequisites
     would cause deeply nested objects that are difficult to index and maintain.

  4. QUERY FLEXIBILITY:
     A referenced model allows bidirectional queries:
     a) "What are the prerequisites for Course X?" ($in / $lookup)
     b) "What downstream courses require Course X as a prerequisite?" 
        (e.g., db.courses.find({'prerequisites': 'CS101'}))
""")

    # ============================================================
    # Export collection to JSON file
    # ============================================================
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "activity_3_1_try_it_yourself.json")
    all_courses_export = list(courses.find())
    json_export = json.loads(json_util.dumps(all_courses_export))

    with open(json_path, "w") as f:
        json.dump(json_export, f, indent=2)

    print("-" * 70)
    print(f"[+] Output JSON saved to: {json_path}")
    print("=" * 70)

    client.close()

if __name__ == "__main__":
    main()
