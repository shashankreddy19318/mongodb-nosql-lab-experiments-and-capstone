"""
Activity 2.2 - Try It Yourself
Extended CRUD: Adds more queries, updates books before 2010 with 10% price
increase, adds a new book, updates by tag, and exports results.
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

# ─── Sample Book Data (expanded) ─────────────────────────────────
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
    {
        "title": "Introduction to Algorithms",
        "author": "Thomas H. Cormen",
        "year": 2009,
        "genre": "Computer Science",
        "price": 85.00,
        "isbn": "978-0262033848",
        "tags": ["algorithms", "data-structures", "theory"],
        "publisher": {"name": "MIT Press", "location": "Cambridge"}
    },
    {
        "title": "Design Patterns",
        "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides",
        "year": 1994,
        "genre": "Software Engineering",
        "price": 54.99,
        "isbn": "978-0201633610",
        "tags": ["programming", "design-patterns", "object-oriented"],
        "publisher": {"name": "Addison-Wesley", "location": "Boston"}
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
    banner("Activity 2.2 - Try It Yourself: Extended CRUD")

    # Connect
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print(f"  [OK] Connected to MongoDB at {MONGO_URI}")
    except ConnectionFailure as e:
        print(f"  [ERROR] Cannot connect: {e}")
        sys.exit(1)

    db = client[DB_NAME]
    db[COLLECTION_NAME].drop()
    col = db[COLLECTION_NAME]

    # ─── CREATE: Insert extended book list ───────────────────────
    print("\n=== CREATE: Inserting 7 books ===")
    result = col.insert_many(BOOKS)
    print(f"  [OK] Inserted {len(result.inserted_ids)} books")

    # ─── READ: Books by specific publisher ───────────────────────
    print("\n=== READ: Books by O'Reilly Media ===")
    oreilly = col.find(
        {"publisher.name": "O'Reilly Media"},
        {"title": 1, "publisher.name": 1, "_id": 0}
    )
    for b in oreilly:
        print(f"  {b['title']:<45} Publisher: {b['publisher']['name']}")

    # ─── READ: Books with multiple tags ──────────────────────────
    print("\n=== READ: Books tagged both 'programming' and 'best-practices' ===")
    multi_tag = col.find(
        {"tags": {"$all": ["programming", "best-practices"]}},
        {"title": 1, "tags": 1, "_id": 0}
    )
    for b in multi_tag:
        print(f"  {b['title']:<45} tags: {b['tags']}")

    # ─── READ: Books sorted by price (descending) ────────────────
    print("\n=== READ: All books sorted by price (high to low) ===")
    sorted_books = col.find(
        {},
        {"title": 1, "price": 1, "year": 1, "_id": 0}
    ).sort("price", -1)
    for b in sorted_books:
        print(f"  {b['title']:<45} ({b['year']}) - ${b['price']:.2f}")

    # ─── UPDATE: 10% price increase for books published before 2010 ───
    print("\n=== UPDATE: 10% price increase for books before 2010 ===")
    before_update = list(col.find(
        {"year": {"$lt": 2010}},
        {"title": 1, "price": 1, "year": 1, "_id": 0}
    ))
    print("  Books before 2010 (BEFORE update):")
    for b in before_update:
        print(f"    {b['title']:<45} ({b['year']}) - ${b['price']:.2f}")

    update_result = col.update_many(
        {"year": {"$lt": 2010}},
        {"$mul": {"price": 1.10}}
    )
    print(f"\n  [OK] Matched: {update_result.matched_count}, Modified: {update_result.modified_count}")

    after_update = list(col.find(
        {"year": {"$lt": 2010}},
        {"title": 1, "price": 1, "year": 1, "_id": 0}
    ))
    print("\n  Books before 2010 (AFTER update):")
    for b in after_update:
        print(f"    {b['title']:<45} ({b['year']}) - ${b['price']:.2f}")

    print("\n  Price Comparison:")
    for old, new in zip(before_update, after_update):
        increase = new['price'] - old['price']
        print(f"    {old['title']:<45} ${old['price']:.2f} → ${new['price']:.2f} (+${increase:.2f})")

    # ─── UPDATE: Add a new tag to AI books ───────────────────────
    print("\n=== UPDATE: Adding 'trending' tag to all AI books ===")
    tag_result = col.update_many(
        {"tags": "AI"},
        {"$addToSet": {"tags": "trending"}}
    )
    print(f"  [OK] Modified {tag_result.modified_count} AI books")

    # Verify
    ai_books = col.find({"tags": "AI"}, {"title": 1, "tags": 1, "_id": 0})
    for b in ai_books:
        print(f"  {b['title']:<45} tags: {b['tags']}")

    # ─── DELETE: Remove 'Design Patterns' ────────────────────────
    print("\n=== DELETE: Removing 'Design Patterns' ===")
    del_result = col.delete_one({"title": "Design Patterns"})
    print(f"  [OK] Deleted {del_result.deleted_count} document(s)")
    print(f"  Remaining books: {col.count_documents({})}")

    # ─── Final State ─────────────────────────────────────────────
    print("\n=== Final Collection State ===")
    for b in col.find({}, {"_id": 0}):
        print(f"  {b['title']:<45} ({b['year']}) - ${b['price']:.2f}")

    # Export
    save_to_json(col, "bookstore_extended.json")

    # Compass verification note
    print("\n  ──────────────────────────────────────────────")
    print("  To verify in MongoDB Compass:")
    print("  1. Connect to localhost:27017 in Compass")
    print("  2. Navigate to bookstore → books")
    print("  3. Verify 'Clean Code' price: $39.99 → $43.99")
    print("  4. Verify 'Introduction to Algorithms': $85.00 → $93.50")
    print("  5. Verify 'Design Patterns': $54.99 → $60.49 (then deleted)")
    print("  6. AI books should have 'trending' tag added")
    print("  ──────────────────────────────────────────────")

    banner("Activity 2.2 - Try It Yourself Complete")


if __name__ == "__main__":
    main()
