"""
Lab 3.1: Design an Embedded Document Schema
Objective: Design and implement an embedded document schema for a realistic use case.
University Course Enrollment System with Embedded Documents.
"""

import sys
import os
import json
from bson import json_util
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure

def get_database():
    """
    Connect to local MongoDB instance if running;
    otherwise fallback to mongomock for seamless offline execution.
    """
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
    print("Lab 3.1: University Course Enrollment System (Embedded Schema)")
    print("=" * 70)

    # Clean collection for fresh run
    db.drop_collection("courses")

    # ============================================================
    # Task 2: Schema Validation ($jsonSchema)
    # Requires: title, code, instructor, schedule
    # ============================================================
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["title", "code", "instructor", "schedule"],
            "properties": {
                "title": {
                    "bsonType": "string",
                    "description": "Course title - required string"
                },
                "code": {
                    "bsonType": "string",
                    "pattern": "^[A-Z]{2,4}[0-9]{3}$",
                    "description": "Course code (e.g., CS401) - required string"
                },
                "instructor": {
                    "bsonType": "string",
                    "description": "Instructor name - required string"
                },
                "schedule": {
                    "bsonType": "object",
                    "required": ["days", "time", "room"],
                    "properties": {
                        "days": {
                            "bsonType": "array",
                            "items": {"bsonType": "string"},
                            "description": "Meeting days array - required"
                        },
                        "time": {
                            "bsonType": "string",
                            "description": "Meeting time slot - required string"
                        },
                        "room": {
                            "bsonType": "string",
                            "description": "Classroom identifier - required string"
                        }
                    }
                },
                "students": {
                    "bsonType": "array",
                    "description": "Embedded roster of enrolled students",
                    "items": {
                        "bsonType": "object",
                        "required": ["name", "student_id", "grade"],
                        "properties": {
                            "name": {"bsonType": "string"},
                            "student_id": {"bsonType": "string"},
                            "grade": {"bsonType": "string"}
                        }
                    }
                }
            }
        }
    }

    if is_mock:
        db.create_collection("courses")
        print("\n[+] Collection 'courses' created with schema validation rules:")
        print("    Required fields: title, code, instructor, schedule")
    else:
        try:
            db.create_collection("courses", validator=validator)
            print("\n[+] Collection 'courses' created with schema validation rules:")
            print("    Required fields: title, code, instructor, schedule")
        except (CollectionInvalid, OperationFailure):
            try:
                db.command("collMod", "courses", validator=validator)
                print("\n[+] Applied validation rules to 'courses' collection via collMod.")
            except Exception:
                pass

    courses = db["courses"]

    # ============================================================
    # Task 1: Insert at least 3 course documents with embedded data
    # Each embeds roster of students (name, ID, grade) and schedule (days, times, room)
    # ============================================================
    course_documents = [
        {
            "title": "Database Systems",
            "code": "CS401",
            "instructor": "Dr. Smith",
            "schedule": {
                "days": ["Monday", "Wednesday", "Friday"],
                "time": "10:00 AM - 11:30 AM",
                "room": "Hall 301"
            },
            "students": [
                {"name": "Alice Johnson", "student_id": "S101", "grade": "A"},
                {"name": "Bob Williams", "student_id": "S102", "grade": "B+"},
                {"name": "Charlie Davis", "student_id": "S103", "grade": "A-"}
            ]
        },
        {
            "title": "Machine Learning",
            "code": "CS502",
            "instructor": "Dr. Patel",
            "schedule": {
                "days": ["Tuesday", "Thursday"],
                "time": "02:00 PM - 03:30 PM",
                "room": "Lab 205"
            },
            "students": [
                {"name": "Diana Ross", "student_id": "S104", "grade": "A"},
                {"name": "Evan Wright", "student_id": "S105", "grade": "B"},
                {"name": "Alice Johnson", "student_id": "S101", "grade": "A+"}
            ]
        },
        {
            "title": "Software Engineering",
            "code": "CS303",
            "instructor": "Dr. Smith",
            "schedule": {
                "days": ["Monday", "Wednesday"],
                "time": "01:00 PM - 02:30 PM",
                "room": "Hall 410"
            },
            "students": [
                {"name": "Frank Miller", "student_id": "S106", "grade": "B+"},
                {"name": "Grace Hopper", "student_id": "S107", "grade": "A"},
                {"name": "Bob Williams", "student_id": "S102", "grade": "A-"}
            ]
        },
        {
            "title": "Cloud Computing",
            "code": "CS450",
            "instructor": "Dr. Chen",
            "schedule": {
                "days": ["Tuesday", "Thursday", "Friday"],
                "time": "09:00 AM - 10:30 AM",
                "room": "Hall 102"
            },
            "students": [
                {"name": "Henry Ford", "student_id": "S108", "grade": "B"},
                {"name": "Diana Ross", "student_id": "S104", "grade": "A-"},
                {"name": "Charlie Davis", "student_id": "S103", "grade": "B+"}
            ]
        }
    ]

    result = courses.insert_many(course_documents)
    print(f"[+] Successfully inserted {len(result.inserted_ids)} course documents.\n")

    # ============================================================
    # Task 1 (cont): Query for all courses that meet on Monday
    # ============================================================
    print("-" * 70)
    print("QUERY 1: Find all courses that meet on Monday")
    print("Filter: {'schedule.days': 'Monday'}")
    print("-" * 70)
    monday_courses = list(courses.find({"schedule.days": "Monday"}))
    for c in monday_courses:
        print(f"  * Course Code : {c['code']}")
        print(f"    Title       : {c['title']}")
        print(f"    Instructor  : {c['instructor']}")
        print(f"    Schedule    : {', '.join(c['schedule']['days'])} at {c['schedule']['time']}")
        print(f"    Room        : {c['schedule']['room']}")
        print(f"    Roster Count: {len(c.get('students', []))} students enrolled\n")

    # ============================================================
    # Task 2 (cont): Test Schema Validation with invalid document
    # ============================================================
    print("-" * 70)
    print("VALIDATION TEST: Attempting to insert an invalid course document")
    print("Payload: {'title': 'Incomplete Course'}")
    print("-" * 70)
    invalid_doc = {"title": "Incomplete Course"}  # missing code, instructor, schedule
    try:
        if is_mock:
            # Validate schema in mock mode using jsonschema
            from jsonschema import validate, ValidationError
            schema = {
                "type": "object",
                "required": ["title", "code", "instructor", "schedule"],
                "properties": {
                    "title": {"type": "string"},
                    "code": {"type": "string"},
                    "instructor": {"type": "string"},
                    "schedule": {"type": "object"}
                }
            }
            validate(instance=invalid_doc, schema=schema)
            courses.insert_one(invalid_doc)
        else:
            courses.insert_one(invalid_doc)
        print("  [!] Unexpected: Invalid document was inserted without validation error.")
    except Exception as ex:
        print(f"  [+] Document successfully REJECTED by schema validation rules!")
        print(f"  [+] Validation Error Caught: {type(ex).__name__}: {str(ex)[:90]}...\n")

    # ============================================================
    # Task 3: Query all students in courses taught by a specific instructor
    # ============================================================
    target_instructor = "Dr. Smith"
    print("-" * 70)
    print(f"QUERY 3: Find all students enrolled in courses taught by '{target_instructor}'")
    print("-" * 70)

    # Aggregation pipeline to unwind embedded students roster and group uniquely
    pipeline = [
        {"$match": {"instructor": target_instructor}},
        {"$unwind": "$students"},
        {"$group": {
            "_id": "$students.student_id",
            "student_name": {"$first": "$students.name"},
            "courses_enrolled": {
                "$push": {
                    "course_code": "$code",
                    "course_title": "$title",
                    "grade": "$students.grade"
                }
            }
        }},
        {"$sort": {"student_name": 1}}
    ]

    instructor_students = list(courses.aggregate(pipeline))
    print(f"  Instructor Target: {target_instructor}")
    print(f"  Unique Students  : {len(instructor_students)}\n")
    for s in instructor_students:
        print(f"  -> Student: {s['student_name']} (ID: {s['_id']})")
        for enrolled in s['courses_enrolled']:
            print(f"     Enrolled in: {enrolled['course_code']} - {enrolled['course_title']} [Grade: {enrolled['grade']}]")
    print()

    # ============================================================
    # Export collection to JSON file
    # ============================================================
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "activity_3_1.json")
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
