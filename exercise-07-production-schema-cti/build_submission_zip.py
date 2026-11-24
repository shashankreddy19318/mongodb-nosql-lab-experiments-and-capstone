"""
Builds the consolidated submission ZIP file for Lab 7.1 and Lab 7.2.
"""

import os
import zipfile

def create_zip():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(base_dir, "cti_platform")
    output_zip = os.path.join(base_dir, "CyberThreatIntelligence-Lab7-Project.zip")

    print(f"Creating submission zip: {output_zip} ...")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Skip __pycache__
            if "__pycache__" in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, arcname=rel_path)
                print(f"  + Added {rel_path}")

    size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    print(f"\n[SUCCESS] Consolidated ZIP created successfully: {output_zip} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    create_zip()
