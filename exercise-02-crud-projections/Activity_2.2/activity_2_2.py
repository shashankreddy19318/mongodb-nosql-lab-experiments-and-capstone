"""
Activity 2.2 - Bookstore CRUD Operations
Performs Create, Read, Update (10% price increase for books before 2010), Delete
using PyMongo against a local MongoDB instance.
"""

import sys
import os
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# ─── Configuration ───────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI_LOCAL", "mongodb://localhost:27017")
DB_NAME = "bookstore"
COLLECTION_NAME = "books"

# ─── Sample Book Data ────────────────────────────────────────────
BOOKS = [
    {
        "title": "The Pragmatic Programmer",
        "author": "David Thomas & Andrew Hunt",
        "year": 2019,
        "genre": "Software Engineering",
        "price": 49.99,
        "isbn": "978-0135957059",
        "tags": ["programming", "career", "best-practices"],
        "publisher": {"name": "Addison-Wesley", "location": "Boston"}
    },
    {
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "year": 2017,
        "genre": "Databases",
        "price": 45.99,
        "isbn": "978-1449373320",
        "tags": ["databases", "distributed-systems", "architecture"],
        "publisher": {"name": "O'Reilly Media", "location": "Sebastopol"}
    },
    {
        "title": "Deep Learning",
        "author": "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
        "year": 2016,
        "genre": "Machine Learning",
        "price": 72.00,
        "isbn": "978-0262035613",
        "tags": ["AI", "neural-networks", "theory"],
        "publisher": {"name": "MIT Press", "location": "Cambridge"}
    },
    {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "year": 2008,
        "genre": "Software Engineering",
        "price": 39.99,
        "isbn": "978-0132350884",
        "tags": ["programming", "clean-code", "refactoring"],
        "publisher": {"name": "Prentice Hall", "location": "Upper Saddle River"}
    },
    {
        "title": "Hands-On Machine Learning",
        "author": "Aurelien Geron",
        "year": 2022,
        "genre": "Machine Learning",
        "price": 59.99,
        "isbn": "978-1098125974",
        "tags": ["AI", "scikit-learn", "tensorflow", "practical"],
        "publisher": {"name": "O'Reilly Media", "location": "Sebastopol"}
    },
]


def banner(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def save_to_json(collection, filename):
    """Export current collection state to a JSON file."""
    docs = list(collection.find({}, {"_id": 0}))
    with open(filename, "w") as f:
        json.dump(docs, f, indent=2, default=str)
    print(f"  [OK] Collection exported to {filename}")


def main():
    banner("Activity 2.2: Bookstore CRUD Operations")

    # Connect to MongoDB
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print(f"  [OK] Connected to MongoDB at {MONGO_URI}")
    except ConnectionFailure as e:
        print(f"  [ERROR] Cannot connect to MongoDB: {e}")
        print("  Make sure MongoDB is running:")
        print("    docker run -d -p 27017:27017 --name mongo mongo:7")
        sys.exit(1)

    db = client[DB_NAME]

    # Drop existing collection for a clean start
    db[COLLECTION_NAME].drop()
    print(f"  [OK] Reset collection '{COLLECTION_NAME}'")
    col = db[COLLECTION_NAME]

    # ─── CREATE ──────────────────────────────────────────────────
    print("\n=== CREATE: Inserting 5 books ===")
    result = col.insert_many(BOOKS)
    print(f"  [OK] Inserted {len(result.inserted_ids)} books")
    for _id in result.inserted_ids:
        print(f"    ID: {str(_id)[:8]}...")

    # ─── READ: Books published after 2020 ────────────────────────
    print("\n=== READ: Books published after 2020 ===")
    recent = list(col.find(
        {"year": {"$gt": 2020}},
        {"title": 1, "year": 1, "price": 1, "_id": 0}
    ))
    for b in recent:
        print(f"  {b['title']:<45} ({b['year']}) - ${b['price']:.2f}")

    # ─── READ: Machine Learning books ────────────────────────────
    print("\n=== READ: Machine Learning books ===")
    ml_books = col.find(
        {"genre": "Machine Learning"},
        {"title": 1, "author": 1, "_id": 0}
    )
    for b in ml_books:
        print(f"  {b['title']:<45} by {b['author']}")

    # ─── READ: Books priced $40-$60 ──────────────────────────────
    print("\n=== READ: Books priced $40-$60 ===")
    mid_range = col.find(
        {"price": {"$gte": 40, "$lte": 60}},
        {"title": 1, "price": 1, "_id": 0}
    )
    for b in mid_range:
        print(f"  {b['title']:<45} ${b['price']:.2f}")

    # ─── READ: Books tagged 'AI' ─────────────────────────────────
    print("\n=== READ: Books tagged 'AI' ===")
    ai_books = col.find(
        {"tags": "AI"},
        {"title": 1, "tags": 1, "_id": 0}
    )
    for b in ai_books:
        print(f"  {b['title']:<45} tags: {b['tags']}")

    # ─── UPDATE: 10% price increase for books published before 2010 ───
    print("\n=== UPDATE: 10% price increase for books published before 2010 ===")
    # Show prices before update
    before_update = list(col.find(
        {"year": {"$lt": 2010}},
        {"title": 1, "price": 1, "year": 1, "_id": 0}
    ))
    print("  Books published before 2010 (BEFORE update):")
    for b in before_update:
        print(f"    {b['title']:<45} ({b['year']}) - ${b['price']:.2f}")

    # Perform the update: multiply price by 1.10 for books before 2010
    update_result = col.update_many(
        {"year": {"$lt": 2010}},
        {"$mul": {"price": 1.10}}
    )
    print(f"\n  [OK] Matched: {update_result.matched_count}, Modified: {update_result.modified_count}")

    # Show prices after update
    after_update = list(col.find(
        {"year": {"$lt": 2010}},
        {"title": 1, "price": 1, "year": 1, "_id": 0}
    ))
    print("\n  Books published before 2010 (AFTER update):")
    for b in after_update:
        print(f"    {b['title']:<45} ({b['year']}) - ${b['price']:.2f}")

    # Show comparison
    print("\n  Price Comparison (Before → After):")
    for old, new in zip(before_update, after_update):
        print(f"    {old['title']:<45} ${old['price']:.2f} → ${new['price']:.2f}")

    # ─── DELETE: Remove 'Clean Code' ─────────────────────────────
    print("\n=== DELETE: Removing 'Clean Code' ===")
    del_result = col.delete_one({"title": "Clean Code"})
    print(f"  [OK] Deleted {del_result.deleted_count} document(s)")
    print(f"  Remaining books: {col.count_documents({})}")

    # ─── Final State ─────────────────────────────────────────────
    print("\n=== Final Collection State ===")
    for b in col.find({}, {"_id": 0}):
        print(f"  {b['title']:<45} ({b['year']}) - ${b['price']:.2f}")

    # Export to JSON
    save_to_json(col, "bookstore_books.json")

    # Note for Compass verification
    print("\n  ──────────────────────────────────────────────")
    print("  To verify in MongoDB Compass:")
    print("  1. Open Compass and connect to localhost:27017")
    print("  2. Navigate to bookstore → books collection")
    print("  3. Check that 'Clean Code' price was updated")
    print("     from $39.99 to $43.99 (10% increase)")
    print("  4. 'Clean Code' should no longer exist (deleted)")
    print("  ──────────────────────────────────────────────")

    banner("Activity 2.2 Complete")


if __name__ == "__main__":
    main()
