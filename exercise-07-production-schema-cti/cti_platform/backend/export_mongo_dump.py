"""
Exports the production MongoDB database into JSON dump files
matching standard mongodump / mongoexport formats for Lab 7.1.
"""

import json
import os
from bson import json_util
from database import db_manager
from seed_data import seed_database

def export_dumps():
    db = db_manager.get_db()
    
    # Ensure database is seeded
    if db.threat_reports.count_documents({}) == 0:
        seed_database()

    dumps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dumps"))
    os.makedirs(dumps_dir, exist_ok=True)

    consolidated_dump = {}

    for col_name in ["sources", "threat_actors", "cves", "threat_reports", "sources_embedded_threats"]:
        cursor = db[col_name].find()
        docs = list(cursor)
        
        # Save individual collection dump
        col_file = os.path.join(dumps_dir, f"{col_name}.json")
        with open(col_file, "w", encoding="utf-8") as f:
            f.write(json_util.dumps(docs, indent=2))
        
        consolidated_dump[col_name] = docs
        print(f"[Dump] Exported {len(docs)} documents to {col_file}")

    # Save master dump file
    master_file = os.path.join(dumps_dir, "cti_digest_dump.json")
    with open(master_file, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(consolidated_dump, indent=2))
    print(f"[Dump] Master CTI Digest MongoDB dump written to {master_file}")

if __name__ == "__main__":
    export_dumps()
