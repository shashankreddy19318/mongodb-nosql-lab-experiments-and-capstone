"""
Lab 3.2 - Try It Yourself:
Scenario Analysis: Handling 10,000 Comments on a Single Blog Post
Embedding Bottlenecks & Production-Ready Alternative Architectures
(Subset Pattern & Referenced Pattern with Keyset/Offset Pagination)
"""

import sys
import os
import json
from datetime import datetime, timedelta
from bson import json_util, ObjectId
from pymongo import MongoClient

def get_database():
    """Connect to local MongoDB instance or fallback to mongomock."""
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        print("[*] Successfully connected to live MongoDB server at localhost:27017")
        return client, client["blog_scale_db"], False
    except Exception:
        import mongomock
        print("[*] Local MongoDB server offline. Running with mongomock in-memory database.")
        client = mongomock.MongoClient()
        return client, client["blog_scale_db"], True

def main():
    client, db, is_mock = get_database()

    print("=" * 80)
    print("Lab 3.2 - Try It Yourself: 10,000 Comments Scenario Analysis & Solutions")
    print("=" * 80)

    # ============================================================
    # SECTION 1: Detailed Technical Analysis of the 10,000 Comments Problem
    # ============================================================
    print("""
[1] WHY EMBEDDING 10,000 COMMENTS IS HIGHLY PROBLEMATIC IN MONGODB:
--------------------------------------------------------------------------------
1. 16MB BSON Document Size Limit:
   MongoDB enforces an immutable 16 megabyte maximum limit on any single document.
   If each comment averages 1.2 KB (text, author ID, timestamps, upvotes, replies),
   10,000 comments consume ~12-16 MB, pushing the document directly to or beyond 
   the 16MB hard threshold and throwing 'DocumentTooLarge' errors on insertion.

2. Severe Network & Bandwidth Inefficiencies:
   When a user navigates to a blog post, fetching an embedded document forces the 
   server to transfer the entire 15MB payload across the network, even if the user 
   only intended to read the 500-word post article or the top 5 comments.

3. Working Set & WiredTiger Cache Degradation:
   MongoDB caches hot documents in RAM. Large 16MB documents rapidly consume cache 
   space, evicting index nodes and other critical collections, causing aggressive 
   cache evictions, elevated page faults, and high disk I/O.

4. Document Resizing and Memory Fragmentation:
   Each newly appended comment causes dynamic array reallocation. In WiredTiger, 
   frequent document growth leads to storage fragmentation and rewrite latency.

5. Extreme Write Lock Contention:
   On viral posts where hundreds of users submit comments concurrently, all writes 
   target a single document record, triggering high concurrency contention.
""")

    # ============================================================
    # SECTION 2: Implementation of the Recommended Architecture
    # Pattern: Subset Pattern (Hybrid Design) + Referenced Collection with Pagination
    # ============================================================
    print("-" * 80)
    print("[2] IMPLEMENTING ALTERNATIVE DESIGNS")
    print("-" * 80)

    db.drop_collection("scale_posts")
    db.drop_collection("scale_comments")

    posts_col = db["scale_posts"]
    comments_col = db["scale_comments"]

    # Index for high-performance referenced lookups and chronological pagination
    try:
        comments_col.create_index([("post_id", 1), ("created_at", -1)])
        print("[+] Created compound index on scale_comments: (post_id: 1, created_at: -1)")
    except Exception:
        pass

    target_post_id = ObjectId("660000000000000000000001")
    base_timestamp = datetime(2026, 2, 1, 10, 0, 0)

    # Generate sample comments demonstrating referenced pagination
    sample_comments = []
    for i in range(1, 31):  # 30 representative comments
        comment_item = {
            "_id": ObjectId(),
            "post_id": target_post_id,
            "comment_index": i,
            "author": f"User_{i:03d}",
            "comment_text": f"Insightful analysis on MongoDB schema patterns #{i}!",
            "created_at": base_timestamp + timedelta(minutes=i * 3),
            "upvotes": (i * 11) % 45
        }
        sample_comments.append(comment_item)

    comments_col.insert_many(sample_comments)
    print(f"[+] Inserted {len(sample_comments)} comments into referenced 'scale_comments' collection.")

    # Create Post document using the SUBSET PATTERN:
    # Stores post content + total comment count + top 3 most recent preview comments
    top_recent = sorted(sample_comments, key=lambda c: c["created_at"], reverse=True)[:3]
    subset_preview = [
        {
            "comment_id": c["_id"],
            "author": c["author"],
            "comment_text": c["comment_text"],
            "created_at": c["created_at"]
        }
        for c in top_recent
    ]

    post_record = {
        "_id": target_post_id,
        "title": "Architecting Scalable MongoDB Systems for Viral Comments",
        "author": "Dr. Sarah Connor",
        "content": "Designing document schemas requires analyzing cardinality and access patterns...",
        "tags": ["mongodb", "scalability", "schema-design", "big-data"],
        "total_comments_count": 10000,  # Demonstrating total count tracking
        "latest_comments_preview": subset_preview,  # Subset pattern preview
        "published_at": base_timestamp
    }
    posts_col.insert_one(post_record)
    print(f"[+] Created post record using the SUBSET PATTERN with {len(subset_preview)} preview comments embedded.\n")

    # ============================================================
    # SECTION 3: Query Demonstration
    # ============================================================
    print("-" * 80)
    print("[3] QUERY WORKFLOW DEMONSTRATION")
    print("-" * 80)

    # Workflow 1: Instant First Page Load (Zero Joins, Minimal Data Transfer)
    print("Workflow 1: Initial Page Render using Subset Pattern (1 query, 0 joins)")
    loaded_post = posts_col.find_one({"_id": target_post_id})
    print(f"  Title           : {loaded_post['title']}")
    print(f"  Total Comments  : {loaded_post['total_comments_count']}")
    print(f"  Instant Preview : Showing latest {len(loaded_post['latest_comments_preview'])} comments directly from post document:")
    for c in loaded_post['latest_comments_preview']:
        print(f"    * [{c['author']}]: \"{c['comment_text']}\"")
    print()

    # Workflow 2: On-Demand Paginated Loading of Comments
    print("Workflow 2: User Scrolls to Read Comments (Paginated from Referenced Collection)")
    page_size = 5
    page_number = 1
    skip_offset = (page_number - 1) * page_size

    paginated_comments = list(
        comments_col.find({"post_id": target_post_id})
        .sort("created_at", -1)
        .skip(skip_offset)
        .limit(page_size)
    )

    print(f"  Page {page_number} Output (Top {page_size} comments by date descending):")
    for c in paginated_comments:
        print(f"    * #{c['comment_index']} [{c['author']}] (Upvotes: {c['upvotes']}): {c['comment_text']}")
    print()

    # ============================================================
    # SECTION 4: Architecture Comparison Matrix
    # ============================================================
    print("-" * 80)
    print("[4] ARCHITECTURAL OPTIONS COMPARISON MATRIX")
    print("-" * 80)
    print("""
+-------------------------+-----------------------------------+-----------------------------------------+
| ARCHITECTURAL PATTERN   | MECHANISM                         | TRADE-OFFS & ASSESSMENT                 |
+-------------------------+-----------------------------------+-----------------------------------------+
| 1. Pure Embedded        | All 10,000 comments in array      | CRITICAL FAILURE: Exceeds 16MB limit,   |
|    (Anti-Pattern here)  | inside the post document.         | high network waste, write contention.   |
|                         |                                   |                                         |
| 2. Pure Referenced      | Separate 'comments' collection;   | SAFE: No 16MB limit. Clean indexing     |
|    with Pagination      | query with post_id & pagination.  | and pagination. Requires 2 queries      |
|                         |                                   | on initial page render.                 |
|                         |                                   |                                         |
| 3. Subset Pattern       | Post embeds top 3-5 latest        | OPTIMAL (BEST PRACTICE): 1 query loads  |
|    (Recommended)        | comments for immediate UI render. | post & preview comments instantly. Full |
|                         | Full history in referenced col.   | comment archive paginated as needed.    |
|                         |                                   |                                         |
| 4. The Bucket Pattern   | Groups comments into buckets of   | EXCELLENT FOR ANALYTICS: Reduces total  |
|                         | 50-100 per bucket document.       | documents in collection by factor of 50.|
+-------------------------+-----------------------------------+-----------------------------------------+
""")

    # ============================================================
    # Export collection to JSON file
    # ============================================================
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "activity_3_2_try_it_yourself.json")

    export_payload = {
        "post_subset_pattern": json.loads(json_util.dumps(posts_col.find_one({"_id": target_post_id}))),
        "referenced_comments_sample": json.loads(json_util.dumps(list(comments_col.find().limit(10)))),
        "technical_analysis": {
            "scenario": "Post receiving 10,000 comments",
            "why_embedding_fails": [
                "Exceeds MongoDB 16MB BSON document limit (10,000 x 1.5KB = ~15-20MB)",
                "Massive network bandwidth waste transferring megabytes of unused comments",
                "Working set RAM pollution evicting critical database cache",
                "Document resizing causing WiredTiger storage fragmentation",
                "High concurrency write lock contention on a single document"
            ],
            "recommended_solution": "Hybrid Subset Pattern combined with Indexed Referenced Collection",
            "key_benefits": [
                "Post document remains lightweight (<2KB)",
                "Instant first-page render without joins or secondary round-trips",
                "Infinite comment scalability via compound index (post_id, created_at)",
                "Zero risk of hitting 16MB limit"
            ]
        }
    }

    with open(json_path, "w") as f:
        json.dump(export_payload, f, indent=2)

    print("-" * 80)
    print(f"[+] Output JSON saved to: {json_path}")
    print("=" * 80)

    client.close()

if __name__ == "__main__":
    main()
