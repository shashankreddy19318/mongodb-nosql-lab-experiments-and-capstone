from pymongo import MongoClient
from pymongo.errors import ValidationError

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

db = client["college_db"]

# Drop collection if it already exists
if "courses" in db.list_collection_names():
    db.courses.drop()

# JSON Schema validator
course_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "course_name",
            "instructor",
            "schedule",
            "enrolled_students"
        ],
        "properties": {
            "course_name": {
                "bsonType": "string"
            },
            "instructor": {
                "bsonType": "string"
            },
            "schedule": {
                "bsonType": "object",
                "required": ["days", "time"],
                "properties": {
                    "days": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "string"
                        }
                    },
                    "time": {
                        "bsonType": "string"
                    }
                }
            },
            "enrolled_students": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["name", "email", "grade"],
                    "properties": {
                        "name": {
                            "bsonType": "string"
                        },
                        "email": {
                            "bsonType": "string"
                        },
                        "grade": {
                            "bsonType": "string"
                        }
                    }
                }
            }
        }
    }
}

# Create collection with validator
db.create_collection(
    "courses",
    validator=course_validator,
    validationLevel="strict",
    validationAction="error"
)

courses = db.courses

# Insert sample courses
course_data = [
    {
        "course_name": "MongoDB Basics",
        "instructor": "Dr. Kumar",
        "schedule": {
            "days": ["Monday", "Wednesday"],
            "time": "10:00 AM"
        },
        "enrolled_students": [
            {
                "name": "Rahul",
                "email": "rahul@gmail.com",
                "grade": "A"
            },
            {
                "name": "Priya",
                "email": "priya@gmail.com",
                "grade": "B"
            }
        ]
    },
    {
        "course_name": "Python Programming",
        "instructor": "Dr. Sharma",
        "schedule": {
            "days": ["Tuesday", "Thursday"],
            "time": "11:00 AM"
        },
        "enrolled_students": [
            {
                "name": "Arun",
                "email": "arun@gmail.com",
                "grade": "A"
            },
            {
                "name": "Rahul",
                "email": "rahul@gmail.com",
                "grade": "B"
            }
        ]
    },
    {
        "course_name": "Web Development",
        "instructor": "Dr. Kumar",
        "schedule": {
            "days": ["Monday", "Friday"],
            "time": "2:00 PM"
        },
        "enrolled_students": [
            {
                "name": "Sneha",
                "email": "sneha@gmail.com",
                "grade": "A"
            },
            {
                "name": "Vijay",
                "email": "vijay@gmail.com",
                "grade": "B"
            }
        ]
    }
]

courses.insert_many(course_data)

print("\n--- All Courses ---")
for course in courses.find():
    print(course)


# 1. Courses meeting on Monday
print("\n--- Courses Meeting on Monday ---")

for course in courses.find({"schedule.days": "Monday"}):
    print(course["course_name"])


# 2. Courses taught by Dr. Kumar and roster size
print("\n--- Courses Taught by Dr. Kumar ---")

for course in courses.find({"instructor": "Dr. Kumar"}):
    print(
        course["course_name"],
        "- Students:",
        len(course["enrolled_students"])
    )


# 3. Add a new student using $push
print("\n--- Adding New Student ---")

new_student = {
    "name": "Anjali",
    "email": "anjali@gmail.com",
    "grade": "A"
}

result = courses.update_one(
    {"course_name": "MongoDB Basics"},
    {"$push": {"enrolled_students": new_student}}
)

print("Students added:", result.modified_count)


# Display updated course
updated_course = courses.find_one(
    {"course_name": "MongoDB Basics"}
)

print(updated_course)


# 4. Find every course Rahul is enrolled in
print("\n--- Courses Where Rahul Is Enrolled ---")

for course in courses.find(
    {"enrolled_students.email": "rahul@gmail.com"}
):
    print(course["course_name"])


# 5. Test JSON Schema validation
print("\n--- Testing Schema Validation ---")

invalid_course = {
    "course_name": "Invalid Course"
}

try:
    courses.insert_one(invalid_course)
    print("[ERROR] Validation should have failed!")
except Exception as e:
    print("[OK] Validation caught error:", e)


print("\nActivity 1 completed successfully.")

client.close()