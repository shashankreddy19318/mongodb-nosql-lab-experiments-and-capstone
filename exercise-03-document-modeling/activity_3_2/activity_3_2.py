"""
Lab 3.2: Migrate from Referenced to Embedded Design
Objective: Convert a referenced design to an embedded design and compare performance characteristics.

Tasks:
1. Create a blog system with separate collections for posts and comments (referenced design).
   Insert 5 posts and 10 comments.
2. Write a query using $lookup to retrieve a post with its comments in a single query.
3. Redesign the system using embedding (comments as an array within the post document).
   Migrate data from referenced to embedded design using aggregation pipeline / Python script.
4. Compare the number of database queries required to display a post with its comments in both designs.
"""

import sys
import os
import json
from datetime import datetime
from bson import json_util, ObjectId
from pymongo import MongoClient

def get_database():
    """Connect to local MongoDB instance or fallback to mongomock."""
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        print("[*] Successfully connected to live MongoDB server at localhost:27017")
        return client, client["blog_db"], False
    except Exception:
        import mongomock
        print("[*] Local MongoDB server offline. Running with mongomock in-memory database.")
        client = mongomock.MongoClient()
        return client, client["blog_db"], True

def main():
    client, db, is_mock = get_database()

    print("=" * 75)
    print("Lab 3.2: Referenced to Embedded Migration & Query Comparison")
    print("=" * 75)

    # Clean previous collections
    db.drop_collection("posts")
    db.drop_collection("comments")
    db.drop_collection("posts_embedded")

    posts_col = db["posts"]
    comments_col = db["comments"]

    # ============================================================
    # Task 1: Referenced Design - Separate Posts & Comments
    # ============================================================
    post_docs = [
        {
            "_id": ObjectId("650000000000000000000001"),
            "title": "Introduction to NoSQL Databases",
            "author": "Alice Johnson",
            "content": "NoSQL databases provide horizontal scaling and flexible schema models...",
            "tags": ["nosql", "mongodb", "database"],
            "published_at": datetime(2026, 1, 10, 10, 0, 0)
        },
        {
            "_id": ObjectId("650000000000000000000002"),
            "title": "Mastering the MongoDB Aggregation Pipeline",
            "author": "Bob Smith",
            "content": "Aggregation pipelines allow developers to transform, filter, and join documents...",
            "tags": ["mongodb", "aggregation", "tutorial"],
            "published_at": datetime(2026, 1, 12, 14, 30, 0)
        },
        {
            "_id": ObjectId("650000000000000000000003"),
            "title": "Embedded vs Referenced Schema Design",
            "author": "Charlie Davis",
            "content": "Choosing between embedding and referencing is the most critical decision in MongoDB...",
            "tags": ["data modeling", "design patterns", "architecture"],
            "published_at": datetime(2026, 1, 15, 9, 15, 0)
        },
        {
            "_id": ObjectId("650000000000000000000004"),
            "title": "Indexing Strategies in MongoDB",
            "author": "Diana Prince",
            "content": "Proper indexes dramatically reduce query latency and memory consumption...",
            "tags": ["indexing", "performance", "optimization"],
            "published_at": datetime(2026, 1, 18, 16, 45, 0)
        },
        {
            "_id": ObjectId("650000000000000000000005"),
            "title": "Building RESTful APIs with Python and PyMongo",
            "author": "Evan Wright",
            "content": "FastAPI and Flask pair seamlessly with PyMongo for high-throughput microservices...",
            "tags": ["python", "api", "pymongo"],
            "published_at": datetime(2026, 1, 20, 11, 20, 0)
        }
    ]
    posts_col.insert_many(post_docs)
    print(f"[+] Inserted {len(post_docs)} posts into 'posts' collection (Referenced Design).")

    comment_docs = [
        {
            "_id": ObjectId("650000000000000000000011"),
            "post_id": ObjectId("650000000000000000000001"),
            "author": "Reader101",
            "comment_text": "Great introduction to NoSQL fundamentals!",
            "created_at": datetime(2026, 1, 10, 11, 0, 0)
        },
        {
            "_id": ObjectId("650000000000000000000012"),
            "post_id": ObjectId("650000000000000000000001"),
            "author": "TechEnthusiast",
            "comment_text": "How does document storage compare with key-value stores?",
            "created_at": datetime(2026, 1, 10, 12, 30, 0)
        },
        {
            "_id": ObjectId("650000000000000000000013"),
            "post_id": ObjectId("650000000000000000000002"),
            "author": "DataGeek",
            "comment_text": "The $lookup operator makes joining collections straightforward.",
            "created_at": datetime(2026, 1, 12, 15, 0, 0)
        },
        {
            "_id": ObjectId("650000000000000000000014"),
            "post_id": ObjectId("650000000000000000000002"),
            "author": "DevGuru",
            "comment_text": "Can you also explain the performance cost of multiple $lookup stages?",
            "created_at": datetime(2026, 1, 12, 16, 10, 0)
        },
        {
            "_id": ObjectId("650000000000000000000015"),
            "post_id": ObjectId("650000000000000000000002"),
            "author": "PyCoder",
            "comment_text": "Pipelines in PyMongo are very readable.",
            "created_at": datetime(2026, 1, 13, 9, 0, 0)
        },
        {
            "_id": ObjectId("650000000000000000000016"),
            "post_id": ObjectId("650000000000000000000003"),
            "author": "ArchLead",
            "comment_text": "Rule of thumb: embed 1-to-few, reference 1-to-squillions.",
            "created_at": datetime(2026, 1, 15, 10, 0, 0)
        },
        {
            "_id": ObjectId("650000000000000000000017"),
            "post_id": ObjectId("650000000000000000000003"),
            "author": "CloudNinja",
            "comment_text": "Always watch out for the 16MB document boundary!",
            "created_at": datetime(2026, 1, 15, 11, 45, 0)
        },
        {
            "_id": ObjectId("650000000000000000000018"),
            "post_id": ObjectId("650000000000000000000004"),
            "author": "DBA_Sam",
            "comment_text": "Ensure ESR (Equality, Sort, Range) rule is followed on compound keys.",
            "created_at": datetime(2026, 1, 18, 17, 0, 0)
        },
        {
            "_id": ObjectId("650000000000000000000019"),
            "post_id": ObjectId("650000000000000000000005"),
            "author": "Pythonista",
            "comment_text": "Great tutorial on PyMongo driver integration.",
            "created_at": datetime(2026, 1, 20, 12, 10, 0)
        },
        {
            "_id": ObjectId("650000000000000000000020"),
            "post_id": ObjectId("650000000000000000000005"),
            "author": "StudentDev",
            "comment_text": "Applied this in our university course project today!",
            "created_at": datetime(2026, 1, 20, 13, 0, 0)
        }
    ]
    comments_col.insert_many(comment_docs)
    print(f"[+] Inserted {len(comment_docs)} comments into 'comments' collection referencing posts.\n")

    # ============================================================
    # Task 2: $lookup Query to retrieve a post with its comments
    # ============================================================
    target_post_id = ObjectId("650000000000000000000001")
    print("-" * 75)
    print("TASK 2: Retrieve Post with its Comments in a Single Query ($lookup)")
    print("-" * 75)

    lookup_pipeline = [
        {"$match": {"_id": target_post_id}},
        {
            "$lookup": {
                "from": "comments",
                "localField": "_id",
                "foreignField": "post_id",
                "as": "comments"
            }
        }
    ]

    referenced_post = list(posts_col.aggregate(lookup_pipeline))[0]
    print(f"Post Title     : {referenced_post['title']}")
    print(f"Author         : {referenced_post['author']}")
    print(f"Total Comments : {len(referenced_post['comments'])}")
    for idx, c in enumerate(referenced_post['comments'], 1):
        print(f"  [{idx}] {c['author']}: \"{c['comment_text']}\" ({c['created_at'].strftime('%Y-%m-%d %H:%M')})")
    print()

    # ============================================================
    # Task 3: Redesign using Embedding & Migrate Data
    # ============================================================
    print("-" * 75)
    print("TASK 3: Migrate Data from Referenced Design to Embedded Design")
    print("-" * 75)

    embedded_col = db["posts_embedded"]

    if not is_mock:
        # Method A: Production MongoDB Aggregation Pipeline with $out
        print("[*] Executing MongoDB Aggregation Pipeline ($lookup -> $project -> $out)...")
        pipeline_out = [
            {
                "$lookup": {
                    "from": "comments",
                    "localField": "_id",
                    "foreignField": "post_id",
                    "as": "comments"
                }
            },
            {"$out": "posts_embedded"}
        ]
        posts_col.aggregate(pipeline_out)
    else:
        # Method B: Python Migration Script
        print("[*] Executing Python Data Migration Script...")
        all_posts = list(posts_col.find())
        embedded_docs = []
        for p in all_posts:
            # Query related comments
            post_comments = list(comments_col.find({"post_id": p["_id"]}))
            embedded_p = {
                "_id": p["_id"],
                "title": p["title"],
                "author": p["author"],
                "content": p["content"],
                "tags": p["tags"],
                "published_at": p["published_at"],
                "comments": [
                    {
                        "comment_id": c["_id"],
                        "author": c["author"],
                        "comment_text": c["comment_text"],
                        "created_at": c["created_at"]
                    }
                    for c in post_comments
                ]
            }
            embedded_docs.append(embedded_p)
        embedded_col.insert_many(embedded_docs)

    count_migrated = embedded_col.count_documents({})
    print(f"[+] Migration complete: {count_migrated} posts created in 'posts_embedded' collection.")
    
    # Verify migrated embedded document
    sample_embedded = embedded_col.find_one({"_id": target_post_id})
    print(f"Sample Embedded Document Title : {sample_embedded['title']}")
    print(f"Embedded Comments In Document  : {len(sample_embedded['comments'])} comments\n")

    # ============================================================
    # Task 4: Compare Database Queries Required to Display Post & Comments
    # ============================================================
    print("-" * 75)
    print("TASK 4: Query Count & Performance Comparison")
    print("-" * 75)

    # 1. Referenced Design without $lookup:
    print("Approach 1: Referenced Design (Application-Level Join)")
    print("  -> Query 1: posts.find_one({'_id': target_id})")
    q1 = posts_col.find_one({"_id": target_post_id})
    print("  -> Query 2: comments.find({'post_id': target_id})")
    q2 = list(comments_col.find({"post_id": target_post_id}))
    print("  Total database round-trips: 2 queries.")
    print()

    # 2. Referenced Design with $lookup:
    print("Approach 2: Referenced Design (Server-side $lookup Aggregation)")
    print("  -> Query: posts.aggregate([{'$match': ...}, {'$lookup': ...}])")
    q_lookup = list(posts_col.aggregate(lookup_pipeline))
    print("  Total database round-trips: 1 query (server joins 2 collections).")
    print()

    # 3. Embedded Design:
    print("Approach 3: Embedded Design (Single Direct Document Fetch)")
    print("  -> Query 1: posts_embedded.find_one({'_id': target_id})")
    q_embedded = embedded_col.find_one({"_id": target_post_id})
    print("  Total database round-trips: 1 simple query (Zero joins, single BSON read).")
    print()

    # Comparison Table
    print("=" * 80)
    print("SUMMARY COMPARISON TABLE: REFERENCED VS. EMBEDDED DESIGN")
    print("=" * 80)
    print(f"{'METRIC / CRITERIA':<25} | {'REFERENCED DESIGN':<26} | {'EMBEDDED DESIGN':<25}")
    print("-" * 80)
    print(f"{'Number of Queries':<25} | {'2 queries (or 1 $lookup)':<26} | {'1 query (direct fetch)':<25}")
    print(f"{'Database CPU & Joins':<25} | {'High (Index joins/lookup)':<26} | {'None (Pre-joined structure)':<25}")
    print(f"{'Read Latency':<25} | {'Higher (Multi-collection)':<26} | {'Lowest (Single disk block)':<25}")
    print(f"{'Write Performance':<25} | {'Fast (append comment row)':<26} | {'May resize document array':<25}")
    print(f"{'16MB BSON Limit':<25} | {'Not an issue (unbounded)':<26} | {'Risk if comments explode':<25}")
    print(f"{'Data Redundancy':<25} | {'Normalized (zero dupes)':<26} | {'Self-contained document':<25}")
    print(f"{'Ideal Scenario':<25} | {'Unbounded 1-to-N (>1,000)':<26} | {'1-to-Few (tens/hundreds)':<25}")
    print("=" * 80)
    print()

    # ============================================================
    # Export collection to JSON file
    # ============================================================
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "activity_3_2.json")
    all_embedded = list(embedded_col.find())
    json_export = json.loads(json_util.dumps(all_embedded))

    with open(json_path, "w") as f:
        json.dump(json_export, f, indent=2)

    print("-" * 75)
    print(f"[+] Output JSON saved to: {json_path}")
    print("=" * 75)

    client.close()

if __name__ == "__main__":
    main()
