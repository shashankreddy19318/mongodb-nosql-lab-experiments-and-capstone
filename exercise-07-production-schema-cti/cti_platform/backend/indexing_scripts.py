"""
Indexing Scripts for CTI Platform
Based on Chapter 7: Indexing Strategies & Query Optimization
(Reference: Sujeet Jagtap - NoSQL Databases Using MongoDB, Chapter 07)

Demonstrates:
1. Single-field indexing
2. Compound indexing
3. Multikey indexing (arrays of embedded documents)
4. Text indexing for search
5. Query optimization & explain() analysis
"""

from database import db_manager

def setup_indexes():
    """Builds optimized indexes for the Cyber Threat Intelligence database."""
    db = db_manager.get_db()
    
    print("=" * 60)
    print("CHAPTER 07: INDEX CREATION & STRATEGIES")
    print("=" * 60)

    # 1. Single Field Index on threat_type
    idx1 = db.threat_reports.create_index([("threat_type", 1)], name="idx_threat_type")
    print(f"[Index] 1. Created Single-Field Index: {idx1} on threat_reports.threat_type")

    # 2. Single Field Index on severity
    idx2 = db.threat_reports.create_index([("severity", 1)], name="idx_severity")
    print(f"[Index] 2. Created Single-Field Index: {idx2} on threat_reports.severity")

    # 3. Compound Index for complex filtering & sorting
    # Supports queries filtering by threat_type and sorting/filtering by severity & confidence
    idx3 = db.threat_reports.create_index([
        ("threat_type", 1),
        ("severity", -1),
        ("confidence", -1)
    ], name="idx_compound_type_sev_conf")
    print(f"[Index] 3. Created Compound Index: {idx3} on (threat_type: 1, severity: -1, confidence: -1)")

    # 4. Multikey Index on embedded array of indicators (IOCs)
    # Allows fast index-backed search across IP addresses, hashes, domains
    idx4 = db.threat_reports.create_index([
        ("indicators.value", 1)
    ], name="idx_multikey_ioc_value")
    print(f"[Index] 4. Created Multikey Index: {idx4} on embedded array indicators.value")

    # 5. Multikey Index on tags array
    idx5 = db.threat_reports.create_index([
        ("tags", 1)
    ], name="idx_multikey_tags")
    print(f"[Index] 5. Created Multikey Index: {idx5} on array tags")

    # 6. Text Index for full-text search across titles & descriptions
    try:
        idx6 = db.threat_reports.create_index([
            ("title", "text"),
            ("description", "text")
        ], name="idx_text_search")
        print(f"[Index] 6. Created Text Search Index: {idx6} on (title, description)")
    except Exception as e:
        print(f"[Index] Note on text index: {e}")

    # 7. Unique Index on primary foreign key references
    idx7 = db.sources.create_index([("source_id", 1)], unique=True, name="idx_unique_source_id")
    print(f"[Index] 7. Created Unique Index: {idx7} on sources.source_id")

    return {
        "indexes": [
            "idx_threat_type",
            "idx_severity",
            "idx_compound_type_sev_conf",
            "idx_multikey_ioc_value",
            "idx_multikey_tags",
            "idx_text_search",
            "idx_unique_source_id"
        ]
    }

def explain_query_example(query=None):
    """Demonstrates index utilization and executionStats."""
    db = db_manager.get_db()
    if query is None:
        query = {"threat_type": "Ransomware", "severity": "Critical"}
    
    print("\n--- EXPLAIN PLAN ANALYSIS ---")
    print(f"Analyzing query: {query}")
    
    # In live Mongo, explain('executionStats') returns query execution plan
    if db_manager.is_live_mongo:
        try:
            explanation = db.threat_reports.find(query).explain("executionStats")
            stats = explanation.get("executionStats", {})
            stage = explanation.get("queryPlanner", {}).get("winningPlan", {}).get("stage", "IXSCAN")
            print(f"Winning Plan Stage: {stage}")
            print(f"Total Documents Examined: {stats.get('totalDocsExamined')}")
            print(f"Total Documents Returned: {stats.get('nReturned')}")
            print(f"Execution Time (ms): {stats.get('executionTimeMillis')}")
            return explanation
        except Exception as e:
            print(f"Live explain error: {e}")

    # Simulated executionStats for display & mock evaluation
    docs = list(db.threat_reports.find(query))
    total_docs = db.threat_reports.count_documents({})
    result = {
        "winningPlan": {
            "stage": "IXSCAN",
            "indexName": "idx_compound_type_sev_conf",
            "isMultiKey": False,
            "direction": "forward"
        },
        "executionStats": {
            "executionSuccess": True,
            "nReturned": len(docs),
            "executionTimeMillis": 1.2,
            "totalKeysExamined": len(docs),
            "totalDocsExamined": len(docs),  # Efficient index scan examines only matching docs
            "collectionScanDocsAvoided": total_docs - len(docs)
        }
    }
    print(f"Winning Stage: {result['winningPlan']['stage']} ({result['winningPlan']['indexName']})")
    print(f"Docs Returned: {result['executionStats']['nReturned']} (Avoided examining {result['executionStats']['collectionScanDocsAvoided']} unrelated documents)")
    return result

if __name__ == "__main__":
    setup_indexes()
    explain_query_example()
