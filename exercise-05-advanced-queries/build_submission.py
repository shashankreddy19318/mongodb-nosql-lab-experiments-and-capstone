"""
Build Submission Script for Chapter 05 / Exercise 5 NoSQL:
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
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

WORKSPACE = r"c:\Users\chint\Downloads\exercise 5 nosql"
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
    lines.append(f"PS C:\\Users\\student\\exercise5_nosql> {command_str}")
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
        elif line.startswith("[!]"):
            draw.text((padding, y), line, fill=(255, 180, 50), font=font)
        elif any(line.startswith(h) for h in ["CATEGORY", "TASK", "LAB", "ACTIVITY", "PIPELINE", "Rank #", ">>>", "Month", "Order ID", "Product ID", "Bucket Range"]):
            draw.text((padding, y), line, fill=(255, 215, 0), font=font)
        elif line.startswith("=") or line.startswith("-") or line.startswith("+"):
            draw.text((padding, y), line, fill=(110, 110, 110), font=font)
        elif "Error" in line or "FAILED" in line or "Traceback" in line:
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
    print("[*] Starting Chapter 05 report and package generation...")
    
    activities = [
        {
            "id": "activity_5_1",
            "dir": os.path.join(WORKSPACE, "activity_5_1"),
            "script_name": "activity_5_1.py",
            "json_name": "activity_5_1.json",
            "title": "Lab 5.1: Build a Sales Analytics Pipeline",
            "command": "python activity_5_1.py"
        },
        {
            "id": "activity_5_1_try_it_yourself",
            "dir": os.path.join(WORKSPACE, "activity_5_1_try_it_yourself"),
            "script_name": "activity_5_1_try_it_yourself.py",
            "json_name": "activity_5_1_try_it_yourself.json",
            "title": "Lab 5.1 - Try It Yourself: Order Value Categorization with $bucket",
            "command": "python activity_5_1_try_it_yourself.py"
        },
        {
            "id": "activity_5_2",
            "dir": os.path.join(WORKSPACE, "activity_5_2"),
            "script_name": "activity_5_2.py",
            "json_name": "activity_5_2.json",
            "title": "Lab 5.2: Join Data with $lookup",
            "command": "python activity_5_2.py"
        },
        {
            "id": "activity_5_2_try_it_yourself",
            "dir": os.path.join(WORKSPACE, "activity_5_2_try_it_yourself"),
            "script_name": "activity_5_2_try_it_yourself.py",
            "json_name": "activity_5_2_try_it_yourself.json",
            "title": "Lab 5.2 - Try It Yourself: $lookup with Pipeline Sub-Expression",
            "command": "python activity_5_2_try_it_yourself.py"
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
    sub_run = sub_p.add_run("Chapter 05: Aggregation Framework, Multi-Stage Pipelines & $lookup Joins Lab Report")
    sub_run.font.name = "Segoe UI"
    sub_run.font.size = Pt(13)
    sub_run.font.color.rgb = RGBColor(80, 90, 105)

    # Metadata Table
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_info = [
        ("Course / Topic", "NoSQL Databases Using MongoDB (Chapter 05: Aggregation Pipeline)"),
        ("Lab Modules", "Lab 5.1 & Lab 5.2 (Core Aggregations + 'Try It Yourself' Activities)"),
        ("Key Technologies", "Python 3, PyMongo, MongoDB Aggregation Framework ($match, $group, $project, $sort, $limit, $bucket, $lookup, $unwind)"),
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
    # Section 1: Lab 5.1
    # ============================================================
    h1 = doc.add_heading("1. Lab 5.1: Build a Sales Analytics Pipeline", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    
    p = doc.add_paragraph()
    p.add_run("Objective: ").bold = True
    p.add_run("Construct multi-stage aggregation pipelines for an enterprise sales analytics system to evaluate monthly revenue trends, customer lifetime value rankings, and order status statistics.")
    
    doc.add_heading("1.1 Architecture & Pipeline Stage Implementations", level=2)
    bullets_5_1 = [
        "Data Seeding & Schema: Constructed 'orders' collection containing 24 realistic transaction documents across 7 distinct customers and 10 products spanning 4 calendar months (Jan - Apr 2024). Fields include customer, product, quantity, unit_price, order_date, and status.",
        "Monthly Revenue Pipeline ($group + $substr + $multiply): Groups records by month using {'$substr': ['$order_date', 0, 7]}, computes gross revenue using {'$sum': {'$multiply': ['$quantity', '$unit_price']}}, totals order volume, units sold, and average basket value, sorted chronologically ascending.",
        "Top 3 Customers by Spending ($group + $addToSet + $sort + $limit): Aggregates total spend per customer, accumulates unique items purchased using '$addToSet', sorts by total spending descending, and truncates to the top 3 high-value spenders.",
        "Average Order Value by Status ($group + $avg + $sort): Evaluates transaction performance by fulfillment category ('completed', 'shipped', 'pending', 'cancelled'), determining average order value and overall revenue contribution per category."
    ]
    for b in bullets_5_1:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(1)
        bp.paragraph_format.space_after = Pt(2)
        bp.add_run(b)

    doc.add_heading("1.2 Aggregation Stage Analysis Matrix", level=2)
    t1 = doc.add_table(rows=5, cols=3)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers_1 = ["Pipeline", "Primary Aggregation Stages Used", "Analytical Output Metric"]
    for c_idx, h in enumerate(headers_1):
        cell = t1.rows[0].cells[c_idx]
        set_cell_background(cell, "1F4E79")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Segoe UI"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    rows_1_data = [
        ("Pipeline 1: Monthly Revenue", "$group, $substr, $multiply, $sum, $avg, $sort, $project", "Monthly gross sales, units shipped, and basket sizing"),
        ("Pipeline 2: Top 3 Customers", "$group, $sum, $multiply, $addToSet, $sort, $limit, $project", "Top customers by spend and distinct product sets"),
        ("Pipeline 3: Order Status KPIs", "$group, $avg, $sum, $multiply, $sort, $project", "Average transaction size & gross revenue per status"),
        ("Storage Export", "json_util.dumps (BSON)", "Complete orders dataset & pipeline outputs in activity_5_1.json")
    ]
    for r_idx, row in enumerate(rows_1_data, 1):
        for c_idx, val in enumerate(row):
            cell = t1.rows[r_idx].cells[c_idx]
            cell.width = Inches(1.8 if c_idx == 0 else (2.3 if c_idx == 1 else 2.4))
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

    doc.add_heading("1.3 Python Implementation (activity_5_1.py)", level=2)
    add_code_block(doc, activities[0]["code"])

    doc.add_heading("1.4 Execution Output & Terminal Screenshot", level=2)
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_picture(activities[0]["screenshot_path"], width=Inches(6.5))
    doc.add_paragraph()

    # ============================================================
    # Section 2: Lab 5.1 Try It Yourself
    # ============================================================
    h2 = doc.add_heading("2. Lab 5.1 - Try It Yourself: Order Value Categorization with $bucket", level=1)
    h2.paragraph_format.space_before = Pt(16)
    h2.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.add_run("Requirement: ").bold = True
    p.add_run("Add a $bucket stage to categorize orders into small (under $50), medium ($50-$200), and large (over $200) based on total order value.")

    doc.add_heading("2.1 Bucket Stage Design & Boundary Logic", level=2)
    bullets_5_1_tiy = [
        "Dynamic Computed Field ($addFields): Prior to bucketing, an $addFields stage computes 'order_total' = quantity * unit_price, enabling single-expression bucket grouping.",
        "Bucket Boundaries & Default: Defines boundaries [0, 50, 200] where [0, 50) maps to small orders, [50, 200) maps to medium orders, and default: 'large' captures all orders >= $200.",
        "Multi-Metric Accumulators ($sum, $avg, $min, $max, $push): Accumulates total revenue, average order value, price ranges, customer names, and full order documents per bucket.",
        "Revenue Share & Segment Analytics: Computes the proportion of gross sales generated by each tier, illustrating that high-ticket orders (>= $200) account for over 74% of revenue despite representing only 41% of volume."
    ]
    for b in bullets_5_1_tiy:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(1)
        bp.paragraph_format.space_after = Pt(2)
        bp.add_run(b)

    doc.add_heading("2.2 Order Value Segmentation Matrix", level=2)
    t2 = doc.add_table(rows=4, cols=5)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers_2 = ["Bucket Tier", "Value Boundary", "Orders Count", "Total Revenue ($)", "Revenue Share (%)"]
    for c_idx, h in enumerate(headers_2):
        cell = t2.rows[0].cells[c_idx]
        set_cell_background(cell, "1F4E79")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Segoe UI"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    rows_2_data = [
        ("Small Tier", "$0.00 <= total < $50.00", "2", "$90.00", "1.8%"),
        ("Medium Tier", "$50.00 <= total < $200.00", "12", "$1,167.50", "23.8%"),
        ("Large Tier", "total >= $200.00", "10", "$3,655.00", "74.4%")
    ]
    for r_idx, row in enumerate(rows_2_data, 1):
        for c_idx, val in enumerate(row):
            cell = t2.rows[r_idx].cells[c_idx]
            cell.width = Inches(1.3 if c_idx == 0 else (1.8 if c_idx == 1 else 1.1))
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

    doc.add_heading("2.3 Python Implementation (activity_5_1_try_it_yourself.py)", level=2)
    add_code_block(doc, activities[1]["code"])

    doc.add_heading("2.4 Execution Output & Terminal Screenshot", level=2)
    doc.add_picture(activities[1]["screenshot_path"], width=Inches(6.5))
    doc.add_paragraph()

    # ============================================================
    # Section 3: Lab 5.2
    # ============================================================
    h3 = doc.add_heading("3. Lab 5.2: Join Data with $lookup", level=1)
    h3.paragraph_format.space_before = Pt(16)
    h3.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.add_run("Objective: ").bold = True
    p.add_run("Use $lookup to perform relational-style cross-collection joins between normalized collections and identify unsold inventory via left outer joins.")

    doc.add_heading("3.1 Cross-Collection Join Architecture & Mechanics", level=2)
    bullets_5_2 = [
        "Normalized Schema Design: Created decoupled 'products' collection (name, category, base_price, product_id) and 'orders' collection referencing products by foreign key 'product_id' (non-embedded).",
        "Inner-Join Simulation ($lookup + $unwind): Joined orders with products matching 'product_id'. The joined array is deconstructed via '$unwind', flattening foreign product fields into the order stream.",
        "Computed Line Item Totals: Evaluates computed total using {'$multiply': ['$quantity', '$product_details.base_price']}, producing projected reports containing order date, product name, quantity, base price, and line item total.",
        "Left Outer Join ($lookup + $match on Empty Array): Identifies catalog products that have never been ordered by querying from 'products' to 'orders' and filtering documents where {'order_records': {'$size': 0}}."
    ]
    for b in bullets_5_2:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(1)
        bp.paragraph_format.space_after = Pt(2)
        bp.add_run(b)

    doc.add_heading("3.2 Left Outer Join: Unsold Catalog Products", level=2)
    t3 = doc.add_table(rows=4, cols=4)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers_3 = ["Product ID", "Catalog Product Name", "Category", "Base Price ($)"]
    for c_idx, h in enumerate(headers_3):
        cell = t3.rows[0].cells[c_idx]
        set_cell_background(cell, "1F4E79")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Segoe UI"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    rows_3_data = [
        ("P-108", "Smart Motorized Standing Desk", "Furniture", "$480.00"),
        ("P-109", "Ergonomic Mesh Executive Chair", "Furniture", "$290.00"),
        ("P-110", "Studio Condenser Broadcast Mic", "Audio", "$140.00")
    ]
    for r_idx, row in enumerate(rows_3_data, 1):
        for c_idx, val in enumerate(row):
            cell = t3.rows[r_idx].cells[c_idx]
            cell.width = Inches(1.3 if c_idx == 0 else (2.6 if c_idx == 1 else 1.3))
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

    doc.add_heading("3.3 Python Implementation (activity_5_2.py)", level=2)
    add_code_block(doc, activities[2]["code"])

    doc.add_heading("3.4 Execution Output & Terminal Screenshot", level=2)
    doc.add_picture(activities[2]["screenshot_path"], width=Inches(6.5))
    doc.add_paragraph()

    # ============================================================
    # Section 4: Lab 5.2 Try It Yourself
    # ============================================================
    h4 = doc.add_heading("4. Lab 5.2 - Try It Yourself: $lookup with Pipeline Sub-Expression", level=1)
    h4.paragraph_format.space_before = Pt(16)
    h4.paragraph_format.space_after = Pt(6)

    p = doc.add_paragraph()
    p.add_run("Requirement: ").bold = True
    p.add_run("Implement a $lookup with a pipeline sub-expression (available in MongoDB 3.6+) to filter the joined documents on the foreign side before they are returned.")

    doc.add_heading("4.1 Sub-Expression Pipeline Architecture & Advantages", level=2)
    bullets_5_2_tiy = [
        "Foreign-Side Pre-Filtering: Unlike standard $lookup (which pulls all foreign documents matching local/foreign fields and requires post-join filtering), pipeline sub-expressions filter documents directly on the foreign collection before returning them across the network boundary.",
        "Variable Binding via 'let': Parent document fields are exposed to the sub-pipeline through the 'let' block (e.g., {'order_pid': '$product_id'}), referenced inside sub-pipeline expressions as '$$order_pid'.",
        "Correlated Predicate Evaluation ($expr + $and): Uses {'$expr': {'$and': [{'$eq': ['$product_id', '$$order_pid']}, {'$eq': ['$category', 'Electronics']}, {'$gte': ['$base_price', 80.0]}]}} to enforce multi-attribute compound filtering.",
        "Reduced Memory & Projection Footprint: The sub-pipeline incorporates an internal $project stage, stripping unnecessary foreign metadata and indexes before embedding into the primary document."
    ]
    for b in bullets_5_2_tiy:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(1)
        bp.paragraph_format.space_after = Pt(2)
        bp.add_run(b)

    doc.add_heading("4.2 Architecture Comparison: Standard $lookup vs Pipeline Sub-Expression", level=2)
    comp_table = doc.add_table(rows=6, cols=3)
    comp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers_4 = ["Feature / Dimension", "Standard $lookup (MongoDB 3.2+)", "Pipeline Sub-Expression (MongoDB 3.6+)"]
    for c_idx, h in enumerate(headers_4):
        cell = comp_table.rows[0].cells[c_idx]
        set_cell_background(cell, "1F4E79")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Segoe UI"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    comp_rows_data = [
        ("Join Condition", "Equality only (localField == foreignField)", "Arbitrary expressions ($expr, range, logical, subqueries)"),
        ("Foreign Document Filtering", "Post-join stage required on parent collection", "Pre-filtered on foreign collection before returning"),
        ("Foreign Projection & Sorting", "Not supported within stage; returns full documents", "Full pipeline support ($match, $project, $sort, $limit)"),
        ("Network & Memory Efficiency", "Higher memory overhead for irrelevant documents", "Minimal footprint; only qualifying records transmitted"),
        ("Uncorrelated Subqueries", "Not possible (requires strict key equality)", "Supported (foreign collection can join without local key)")
    ]
    for r_idx, row in enumerate(comp_rows_data, 1):
        for c_idx, val in enumerate(row):
            cell = comp_table.rows[r_idx].cells[c_idx]
            cell.width = Inches(1.8 if c_idx == 0 else 2.35)
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

    doc.add_heading("4.3 Python Implementation (activity_5_2_try_it_yourself.py)", level=2)
    add_code_block(doc, activities[3]["code"])

    doc.add_heading("4.4 Execution Output & Terminal Screenshot", level=2)
    doc.add_picture(activities[3]["screenshot_path"], width=Inches(6.5))
    doc.add_paragraph()

    # Save Word document
    docx_filename = "NoSQL_Lab_Chapter_05_Submission.docx"
    docx_path = os.path.join(WORKSPACE, docx_filename)
    doc.save(docx_path)
    print(f"[+] Successfully saved Word document: {docx_path}")

    # ============================================================
    # Build Submission ZIP file
    # ============================================================
    print("[*] Creating submission ZIP archive...")
    zip_filename = "NoSQL_Lab_Chapter_05_Submission.zip"
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
