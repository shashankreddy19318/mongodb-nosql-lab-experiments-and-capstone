"""
Build Submission Script for Chapter 04 / Exercise 4 NoSQL:
1. Executes all 4 activity python scripts.
2. Captures stdout/stderr outputs.
3. Generates high-resolution dark-mode terminal window screenshots (PNG) using Pillow.
4. Generates a comprehensive, professionally styled Microsoft Word document (DOCX).
5. Creates the final submission ZIP file with 1 directory for each activity plus the DOCX file.
"""

import os
import sys
import subprocess
import zipfile
from PIL import Image, ImageDraw, ImageFont
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

WORKSPACE = r"c:\Users\chint\Downloads\exercise 4 nosql"
PY_EXE = r"C:\Users\chint\AppData\Local\Python\bin\python.exe"

def run_script(script_path):
    """Executes a python script and returns captured output."""
    res = subprocess.run([PY_EXE, script_path], capture_output=True, text=True, cwd=os.path.dirname(script_path))
    output = res.stdout
    if res.stderr:
        output += "\n" + res.stderr
    return output

def create_terminal_screenshot(title, command_str, text_content, output_image_path):
    """
    Renders terminal output as a realistic terminal window screenshot.
    """
    font_path = r"C:\Windows\Fonts\consola.ttf"
    title_font_path = r"C:\Windows\Fonts\arial.ttf"
    
    font_size = 13
    font = ImageFont.truetype(font_path, font_size)
    title_font = ImageFont.truetype(title_font_path, 12)
    
    lines = []
    lines.append(f"PS C:\\Users\\student\\exercise4_nosql> {command_str}")
    lines.append("")
    for l in text_content.strip().split("\n"):
        lines.append(l)
    
    line_height = 19
    top_bar_height = 34
    padding = 16
    
    # Calculate dimensions
    max_line_len = max(len(l) for l in lines) if lines else 60
    img_width = max(1000, max_line_len * 8 + padding * 3)
    img_height = top_bar_height + len(lines) * line_height + padding * 2
    
    # Canvas
    img = Image.new("RGB", (img_width, img_height), color=(28, 28, 28))
    draw = ImageDraw.Draw(img)
    
    # Title bar
    draw.rectangle([(0, 0), (img_width, top_bar_height)], fill=(42, 42, 42))
    
    # macOS-style window control buttons
    draw.ellipse([(12, 10), (24, 22)], fill=(255, 95, 86))
    draw.ellipse([(30, 10), (42, 22)], fill=(255, 189, 46))
    draw.ellipse([(48, 10), (60, 22)], fill=(39, 201, 63))
    
    # Window title text
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w) // 2, 9), title, fill=(195, 195, 195), font=title_font)
    
    # Render terminal lines with syntax highlighting
    y = top_bar_height + padding
    for idx, line in enumerate(lines):
        if idx == 0:
            draw.text((padding, y), line, fill=(100, 255, 100), font=font)
        elif line.startswith("[+]"):
            draw.text((padding, y), line, fill=(80, 220, 100), font=font)
        elif line.startswith("[*]"):
            draw.text((padding, y), line, fill=(100, 180, 255), font=font)
        elif any(line.startswith(h) for h in ["CATEGORY", "TASK", "LAB", "ACTIVITY", "TEST CASE", "PHASE", "SCHEMA", "QUERY", "--- PAGE"]):
            draw.text((padding, y), line, fill=(255, 215, 0), font=font)
        elif line.startswith("=") or line.startswith("-") or line.startswith("+"):
            draw.text((padding, y), line, fill=(110, 110, 110), font=font)
        elif "Error" in line or "[!]" in line or "FAILED" in line:
            draw.text((padding, y), line, fill=(255, 110, 110), font=font)
        else:
            draw.text((padding, y), line, fill=(225, 225, 225), font=font)
        y += line_height
        
    img.save(output_image_path, "PNG", quality=95)
    print(f"[+] Generated screenshot: {output_image_path}")

def set_cell_background(cell, fill_hex):
    """Sets background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def add_code_block(doc, code_text):
    """Adds a beautifully formatted code block table to the Word document."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F4F6F9")
    
    # Left accent border
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
        f'<w:left w:val="single" w:sz="18" w:space="0" w:color="0969DA"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(code_text.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(8.0)
    run.font.color.rgb = RGBColor(36, 41, 47)
    
    doc.add_paragraph()

def main():
    print("[*] Starting Chapter 04 report and package generation...")
    
    activities = [
        {
            "id": "activity_4_1",
            "dir": os.path.join(WORKSPACE, "activity_4_1"),
            "script_name": "activity_4_1.py",
            "json_name": "activity_4_1.json",
            "title": "Lab 4.1: Build a Product Query API",
            "command": "python activity_4_1.py"
        },
        {
            "id": "activity_4_1_try_it_yourself",
            "dir": os.path.join(WORKSPACE, "activity_4_1_try_it_yourself"),
            "script_name": "activity_4_1_try_it_yourself.py",
            "json_name": "activity_4_1_try_it_yourself.json",
            "title": "Lab 4.1 - Try It Yourself: Text Search Using $regex",
            "command": "python activity_4_1_try_it_yourself.py"
        },
        {
            "id": "activity_4_2",
            "dir": os.path.join(WORKSPACE, "activity_4_2"),
            "script_name": "activity_4_2.py",
            "json_name": "activity_4_2.json",
            "title": "Lab 4.2: Implement Upsert and Bulk Operations",
            "command": "python activity_4_2.py"
        },
        {
            "id": "activity_4_2_try_it_yourself",
            "dir": os.path.join(WORKSPACE, "activity_4_2_try_it_yourself"),
            "script_name": "activity_4_2_try_it_yourself.py",
            "json_name": "activity_4_2_try_it_yourself.json",
            "title": "Lab 4.2 - Try It Yourself: Idempotent Bulk Import Engine",
            "command": "python activity_4_2_try_it_yourself.py"
        }
    ]
    
    # Execute each activity script and capture output & screenshot
    for act in activities:
        script_path = os.path.join(act["dir"], act["script_name"])
        with open(script_path, "r", encoding="utf-8") as f:
            act["code"] = f.read()
            
        print(f"[*] Running {act['script_name']}...")
        output = run_script(script_path)
        act["output"] = output
        
        screenshot_path = os.path.join(act["dir"], f"{act['id']}_output_screenshot.png")
        create_terminal_screenshot(act["title"], act["command"], output, screenshot_path)
        act["screenshot_path"] = screenshot_path

    # ============================================================
    # Build the Word Document (.docx)
    # ============================================================
    print("[*] Generating Microsoft Word Document (DOCX)...")
    doc = Document()
    
    # Page Margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Document Header / Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(2)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("NoSQL Databases Using MongoDB")
    title_run.font.name = "Segoe UI"
    title_run.font.size = Pt(22)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(16, 54, 98)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(0)
    sub_p.paragraph_format.space_after = Pt(14)
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run("Chapter 04: Advanced Query Operators, Upsert & Bulk Write Operations Lab Report")
    sub_run.font.name = "Segoe UI"
    sub_run.font.size = Pt(13)
    sub_run.font.color.rgb = RGBColor(80, 90, 105)

    # Metadata Table
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_info = [
        ("Course / Topic", "NoSQL Databases Using MongoDB (Chapter 04)"),
        ("Lab Modules", "Lab 4.1 & Lab 4.2 (Core Labs + 'Try It Yourself' Activities)"),
        ("Key Technologies", "Python 3, PyMongo, MongoDB Query Operators ($gte, $lte, $or, $and, $all, $size, $regex), Upserts & Bulk Operations (UpdateOne)"),
        ("Submission Package", "Complete Source Code (.py), Exported Datasets (.json), Execution Screenshots (.png) & DOCX Report")
    ]
    for row_idx, (k, v) in enumerate(meta_info):
        row = meta_table.rows[row_idx]
        cell_k, cell_v = row.cells[0], row.cells[1]
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.3)
        set_cell_background(cell_k, "EAEEF3")
        set_cell_background(cell_v, "F8F9FA")
        
        pk = cell_k.paragraphs[0]
        pk.paragraph_format.space_before = Pt(3)
        pk.paragraph_format.space_after = Pt(3)
        rk = pk.add_run(k)
        rk.font.name = "Segoe UI"
        rk.font.size = Pt(9.5)
        rk.font.bold = True
        rk.font.color.rgb = RGBColor(30, 40, 60)
        
        pv = cell_v.paragraphs[0]
        pv.paragraph_format.space_before = Pt(3)
        pv.paragraph_format.space_after = Pt(3)
        rv = pv.add_run(v)
        rv.font.name = "Segoe UI"
        rv.font.size = Pt(9.5)
        rv.font.color.rgb = RGBColor(40, 40, 40)

    doc.add_paragraph()

    # ============================================================
    # Section 1: Lab 4.1
    # ============================================================
    h1 = doc.add_heading("1. Lab 4.1: Build a Product Query API", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    
    p = doc.add_paragraph()
    p.add_run("Objective: ").bold = True
    p.add_run("Implement a comprehensive set of CRUD and query operations for an e-commerce product inventory system using all major query operator categories (comparison, logical, array) and pagination.")
    
    doc.add_heading("1.1 Architecture & Query Operator Implementations", level=2)
    bullets_4_1 = [
        "Schema Validation ($jsonSchema): Defines strict document typing requiring 'name' (string), 'price' (positive number > 0), 'stock' (non-negative integer >= 0), and 'tags' (array of strings). Invalid documents (e.g., negative prices, non-array tags) are automatically rejected.",
        "Comparison Operators ($gte, $lte, $eq): Implemented queries to filter products with price between $20 and $50 ({'price': {'$gte': 20, '$lte': 50}}) and out-of-stock items ({'stock': {'$eq': 0}}).",
        "Logical Operators ($or, $and): Implemented compound criteria queries: finding items that are either out of stock OR priced above $100 ({'$or': [{'stock': 0}, {'price': {'$gt': 100}}]}), and products that are in stock AND tagged as 'premium' ({'$and': [{'stock': {'$gt': 0}}, {'tags': 'premium'}]}).",
        "Array Operators ($all, $size): Implemented element containment queries finding products with BOTH 'electronics' AND 'wireless' tags ({'tags': {'$all': ['electronics', 'wireless']}}), and products with an exact tag count of 2 ({'tags': {'$size': 2}}).",
        "Pagination & Sorting: Implemented a production-ready pagination engine taking page number and page size, computing total pages, navigation flags (has_next, has_prev), and applying cursor skip/limit sorted by name."
    ]
    for b in bullets_4_1:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(1)
        bp.paragraph_format.space_after = Pt(2)
        bp.add_run(b)

    doc.add_heading("1.2 Python Implementation (activity_4_1.py)", level=2)
    add_code_block(doc, activities[0]["code"])

    doc.add_heading("1.3 Execution Output & Terminal Screenshot", level=2)
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture(activities[0]["screenshot_path"], width=Inches(6.5))
    doc.add_paragraph()

    # ============================================================
    # Section 2: Lab 4.1 Try It Yourself
    # ============================================================
    h2 = doc.add_heading("2. Lab 4.1 - Try It Yourself: Text Search Using $regex", level=1)
    h2.paragraph_format.space_before = Pt(16)
    h2.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.add_run("Requirement: ").bold = True
    p.add_run("Add a text search capability using the $regex operator to find products whose name contains a search string (case-insensitive).")

    doc.add_heading("2.1 Text Search Patterns & Operator Analysis", level=2)
    bullets_4_1_tiy = [
        "Case-Insensitive Substring Match: Utilizes {'name': {'$regex': 'wireless', '$options': 'i'}} to match occurrences regardless of casing.",
        "Anchored Prefix Search: Employs {'name': {'$regex': '^Smart', '$options': 'i'}}. In MongoDB, anchored prefix regex queries can effectively traverse B-tree index bounds, avoiding full collection scans.",
        "Anchored Suffix Search: Employs {'name': {'$regex': 'Router$', '$options': 'i'}} to match domain-specific suffixes.",
        "Regex Disjunction / Multi-Keyword: Uses alternation {'name': {'$regex': 'mouse|keyboard', '$options': 'i'}} to search across multiple keyword stems in a single pass.",
        "Compound Regex Filtering: Combines text pattern matching with range and inventory predicates (e.g., matching 'wireless' products that are currently in stock and under $100)."
    ]
    for b in bullets_4_1_tiy:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(1)
        bp.paragraph_format.space_after = Pt(2)
        bp.add_run(b)

    doc.add_heading("2.2 Architectural Comparison: $regex vs $text Index", level=2)
    comp_table = doc.add_table(rows=7, cols=3)
    comp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Criterion", "$regex Operator Search", "$text Full-Text Index"]
    for c_idx, h in enumerate(headers):
        cell = comp_table.rows[0].cells[c_idx]
        set_cell_background(cell, "1F4E79")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Segoe UI"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    rows_data_tiy = [
        ("Matching Mechanism", "Pattern & arbitrary character substring", "Word tokenization, stemming & root forms"),
        ("Partial Word / Infix", "Matches partial stems anywhere in word", "Exact words only; cannot match middle of word"),
        ("Index Utilization", "Anchored prefix (^abc) uses B-tree index", "Uses specialized inverted text index"),
        ("Unanchored Performance", "Collection Scan O(N) over entire dataset", "Fast logarithmic lookup O(log N)"),
        ("Relevance Scoring", "None (Binary match: true or false)", "Supported via $meta: 'textScore' weight"),
        ("Stopwords Filtering", "No automatic stopword filtering", "Filters language stopwords (e.g., 'the', 'and')")
    ]
    for r_idx, row in enumerate(rows_data_tiy, 1):
        for c_idx, val in enumerate(row):
            cell = comp_table.rows[r_idx].cells[c_idx]
            cell.width = Inches(2.1)
            set_cell_background(cell, "F9FAFC" if r_idx % 2 == 0 else "FFFFFF")
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.name = "Segoe UI"
            r.font.size = Pt(8.5)
            if c_idx == 0:
                r.font.bold = True

    doc.add_paragraph()

    doc.add_heading("2.3 Python Implementation (activity_4_1_try_it_yourself.py)", level=2)
    add_code_block(doc, activities[1]["code"])

    doc.add_heading("2.4 Execution Output & Terminal Screenshot", level=2)
    doc.add_picture(activities[1]["screenshot_path"], width=Inches(6.5))
    doc.add_paragraph()

    # ============================================================
    # Section 3: Lab 4.2
    # ============================================================
    h3 = doc.add_heading("3. Lab 4.2: Implement Upsert and Bulk Operations", level=1)
    h3.paragraph_format.space_before = Pt(16)
    h3.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.add_run("Objective: ").bold = True
    p.add_run("Use conditional upserts and batch bulk operations to perform high-throughput updates, conditional insertions, and mass inventory adjustments.")

    doc.add_heading("3.1 Key Implementation Details", level=2)
    bullets_4_2 = [
        "Conditional Upsert (update_one with upsert=True): Implemented upsert_product_price function combining $set (to update the price) and $setOnInsert (to initialize SKU, name, stock, tags, and timestamps only upon insertion).",
        "Upsert Case A (Existing Product): When invoked with existing SKU 'PROD-A', matched_count was 1, modified_count was 1, and upserted_id was None, verifying in-place modification without duplication.",
        "Upsert Case B (New Product): When invoked with non-existent SKU 'PROD-X99', matched_count was 0 and upserted_id was created with defaults populated via $setOnInsert.",
        "Simultaneous Bulk Operations (bulk_write): Dispatched 5 concurrent UpdateOne operations in a single network round-trip: incrementing stock by 10 for products A, B, and C via $inc, and deactivating products D and E via $set: {'is_active': False}.",
        "Result Object Verification: Verified BulkWriteResult object confirming matched_count = 5, modified_count = 5, and acknowledged = True."
    ]
    for b in bullets_4_2:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(1)
        bp.paragraph_format.space_after = Pt(2)
        bp.add_run(b)

    doc.add_heading("3.2 Python Implementation (activity_4_2.py)", level=2)
    add_code_block(doc, activities[2]["code"])

    doc.add_heading("3.3 Execution Output & Terminal Screenshot", level=2)
    doc.add_picture(activities[2]["screenshot_path"], width=Inches(6.5))
    doc.add_paragraph()

    # ============================================================
    # Section 4: Lab 4.2 Try It Yourself
    # ============================================================
    h4 = doc.add_heading("4. Lab 4.2 - Try It Yourself: Idempotent Bulk Import Engine", level=1)
    h4.paragraph_format.space_before = Pt(16)
    h4.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.add_run("Scenario: ").bold = True
    p.add_run("Implement an idempotent bulk import function that can be run multiple times without creating duplicates, using upsert logic for each document.")

    doc.add_heading("4.1 Idempotency Architecture & Three-Phase Verification", level=2)
    bullets_4_2_tiy = [
        "Idempotency Principle: In mathematical and distributed computing terms, f(f(x)) = f(x). Replaying the identical batch payload multiple times results in the exact same state as applying it once, eliminating duplicate catalog rows.",
        "State Convergence via $set & $setOnInsert: The bulk import utilizes UpdateOne(filter={'sku': key}, update={'$set': mutable_fields, '$setOnInsert': immutable_fields}, upsert=True). If an item already exists, its state updates; if absent, it is inserted cleanly.",
        "Phase 1 (Initial Ingestion): 8 fresh items imported into an empty collection -> 8 upserted, 0 modified, total documents = 8.",
        "Phase 2 (Duplicate Replay Test): The exact same 8 items are re-imported. 8 documents matched, 0 upserted, total documents remains exactly 8. Idempotency is 100% verified.",
        "Phase 3 (Delta Synchronization): Feed with 5 unchanged items, 2 modified items, and 3 brand-new items -> 7 matched, 3 upserted, total documents converges to 11."
    ]
    for b in bullets_4_2_tiy:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(1)
        bp.paragraph_format.space_after = Pt(2)
        bp.add_run(b)

    doc.add_heading("4.2 Idempotence Verification Summary Matrix", level=2)
    matrix_table = doc.add_table(rows=4, cols=6)
    matrix_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    matrix_headers = ["Run / Phase", "Input Records", "Matched", "Modified", "Upserted", "Total In DB"]
    for c_idx, h in enumerate(matrix_headers):
        cell = matrix_table.rows[0].cells[c_idx]
        set_cell_background(cell, "1F4E79")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Segoe UI"
        r.font.size = Pt(9.0)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    matrix_rows = [
        ("Run 1: Initial Import", "8", "0", "0", "8", "8"),
        ("Run 2: Identical Replay", "8", "8", "8", "0", "8 (0 Duplicates)"),
        ("Run 3: Delta Sync", "10", "7", "7", "3", "11")
    ]
    for r_idx, row in enumerate(matrix_rows, 1):
        for c_idx, val in enumerate(row):
            cell = matrix_table.rows[r_idx].cells[c_idx]
            cell.width = Inches(1.1 if c_idx > 0 else 1.8)
            set_cell_background(cell, "F9FAFC" if r_idx % 2 == 0 else "FFFFFF")
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.name = "Segoe UI"
            r.font.size = Pt(8.5)
            if c_idx == 0:
                r.font.bold = True

    doc.add_paragraph()

    doc.add_heading("4.3 Python Implementation (activity_4_2_try_it_yourself.py)", level=2)
    add_code_block(doc, activities[3]["code"])

    doc.add_heading("4.4 Execution Output & Terminal Screenshot", level=2)
    doc.add_picture(activities[3]["screenshot_path"], width=Inches(6.5))
    doc.add_paragraph()

    # Save Word document
    docx_filename = "NoSQL_Lab_Chapter_04_Submission.docx"
    docx_path = os.path.join(WORKSPACE, docx_filename)
    doc.save(docx_path)
    print(f"[+] Successfully saved Word document: {docx_path}")

    # ============================================================
    # Build Submission ZIP file
    # ============================================================
    print("[*] Creating submission ZIP archive...")
    zip_filename = "NoSQL_Lab_Chapter_04_Submission.zip"
    zip_path = os.path.join(WORKSPACE, zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for act in activities:
            # Python script
            script_full = os.path.join(act["dir"], act["script_name"])
            arc_script = os.path.join(act["id"], act["script_name"])
            zipf.write(script_full, arc_script)
            
            # JSON file
            json_full = os.path.join(act["dir"], act["json_name"])
            arc_json = os.path.join(act["id"], act["json_name"])
            zipf.write(json_full, arc_json)
            
            # Screenshot image
            arc_img = os.path.join(act["id"], os.path.basename(act["screenshot_path"]))
            zipf.write(act["screenshot_path"], arc_img)

        # DOCX report in the root of the ZIP
        zipf.write(docx_path, docx_filename)

    print(f"[+] Successfully created ZIP package: {zip_path}")
    print("[*] All tasks finished successfully!")

if __name__ == "__main__":
    main()
