"""
generate_final_submission_pdf.py
Publication-Grade Academic Laboratory Project Report.
Matches the official Jain University CTI MongoDB Project format:
- Institution: JGi JAIN (Deemed-to-be University), Faculty of Engineering and Technology, CSE Department
- Project: CTI MongoDB Project - A Comprehensive Study of NoSQL Databases, Distributed Systems, and Cyber Threat Intelligence
- Submitted by: G. SHASHANK REDDY (USN: 24BTRCL079), B.Tech CSE (AIML), Section B / V Semester
- Submitted to: Prof. Sujeet S Jagtap, Faculty, NoSQL Databases using MongoDB
- Consolidated GitHub: https://github.com/shashankreddy19318/threat-intelligence-platform
- Complete 15-page academic syllabus covering Labs 1-19, Polyglot Persistence, RAG & Autonomous Mitigation Bot
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Group

class AcademicCanvas(canvas.Canvas):
    """
    Two-pass canvas for Jain University CTI MongoDB Laboratory report.
    - Suppresses headers and footers on the cover page (physical page 1).
    - Physical page 2 is labeled 'Page 1' (Index), physical page 3 is 'Page 2', etc.
    - Header: 'CTI MongoDB Laboratory | G. Shashank Reddy (24BTRCL079)'
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_academic_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_academic_decorations(self, total_pages):
        self.saveState()
        # Cover page has NO headers or footers
        if self._pageNumber > 1:
            content_page_num = self._pageNumber - 1

            # Running Header
            self.setFont("Times-Roman", 9)
            self.setFillColor(colors.HexColor("#333333"))
            self.drawCentredString(306, 755, "CTI MongoDB Laboratory | G. Shashank Reddy (24BTRCL079)")
            self.setStrokeColor(colors.HexColor("#777777"))
            self.setLineWidth(0.5)
            self.line(54, 748, 558, 748)

            # Running Footer
            self.setFont("Times-Roman", 9)
            self.setFillColor(colors.HexColor("#333333"))
            self.drawCentredString(306, 36, f"Page {content_page_num}")

        self.restoreState()

def build_pdf(filename="CTI_MongoDB_Project_Report_24BTRCL079.pdf"):
    pdf_path = os.path.abspath(filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # --- Typography Styles ---
    # Cover Page Styles
    jgi_style = ParagraphStyle(
        "JGiHeader",
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=30,
        alignment=1, # Center
        textColor=colors.HexColor("#0f4c81")
    )
    jain_sub = ParagraphStyle(
        "JainSub",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#0f4c81"),
        spaceAfter=4
    )
    dept_style = ParagraphStyle(
        "DeptHeader",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=3
    )
    subdept_style = ParagraphStyle(
        "SubDeptHeader",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=120
    )
    title_style = ParagraphStyle(
        "ReportMainTitle",
        fontName="Times-Bold",
        fontSize=24,
        leading=28,
        alignment=1,
        textColor=colors.HexColor("#0f2a4a"),
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        fontName="Times-Bold",
        fontSize=11.5,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#2d3748"),
        spaceAfter=130
    )

    # Body & Academic Heading Styles
    h1_style = ParagraphStyle(
        "AcademicH1",
        fontName="Times-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#111827"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        "AcademicH2",
        fontName="Times-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=7,
        spaceAfter=2,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        "AcademicBody",
        fontName="Times-Roman",
        fontSize=9.5,
        leading=13.2,
        textColor=colors.HexColor("#1f2937"),
        alignment=4, # Justified
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        "AcademicBullet",
        fontName="Times-Roman",
        fontSize=9.5,
        leading=13,
        leftIndent=12,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=3
    )
    index_item = ParagraphStyle(
        "IndexItem",
        fontName="Times-Roman",
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor("#1f2937")
    )
    index_bold = ParagraphStyle(
        "IndexBold",
        fontName="Times-Bold",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#111827")
    )
    meta_box_p = ParagraphStyle(
        "MetaBoxP",
        fontName="Times-Roman",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#1f2937")
    )

    story = []

    # =========================================================================
    # PAGE 1: COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 40))
    # Logo text header
    story.append(Paragraph("<b>JGi</b> &nbsp;&nbsp;&nbsp;&nbsp; <b>JAIN</b>", jgi_style))
    story.append(Paragraph("DEEMED-TO-BE UNIVERSITY", jain_sub))
    story.append(Paragraph("FACULTY OF ENGINEERING AND TECHNOLOGY", dept_style))
    story.append(Paragraph("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", subdept_style))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0284c7"), spaceAfter=70))

    story.append(Paragraph("CTI MongoDB Project", title_style))
    story.append(Paragraph("A Comprehensive Study of NoSQL Databases, Distributed<br/>Systems, and Cyber Threat Intelligence", subtitle_style))

    # Box at bottom
    sub_data = [
        [
            Paragraph("<b>SUBMITTED BY:</b><br/><br/>"
                      "<b>Name:</b> G. SHASHANK REDDY<br/>"
                      "<b>USN:</b> 24BTRCL079<br/>"
                      "<b>Programme:</b> B.Tech in CSE (AIML)<br/>"
                      "<b>Section / Semester:</b> Section B / V Semester", meta_box_p),
            Paragraph("<b>SUBMITTED TO:</b><br/><br/>"
                      "<b>Prof. Sujeet S Jagtap</b><br/>"
                      "Faculty, NoSQL Databases using MongoDB<br/>"
                      "Department of Computer Science & Engineering<br/>"
                      "Faculty of Engineering and Technology", meta_box_p)
        ],
        [
            Paragraph("<b>Consolidated GitHub:</b> <font color='#0284c7'>https://github.com/shashankreddy19318/threat-intelligence-platform</font>", meta_box_p),
            ""
        ]
    ]
    sub_table = Table(sub_data, colWidths=[252, 252])
    sub_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#4a5568")),
        ("LINEBELOW", (0, 0), (1, 0), 0.5, colors.HexColor("#cbd5e1")),
        ("SPAN", (0, 1), (1, 1)),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sub_table)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: INDEX (CONTENT PAGE 1)
    # =========================================================================
    story.append(Paragraph("<u><b>Index</b></u>", ParagraphStyle("IndexTitle", fontName="Times-Bold", fontSize=13, spaceAfter=14)))

    index_rows_p1 = [
        [Paragraph("<b>I Introduction</b>", index_bold), Paragraph("<b>4</b>", index_bold)],
        [Paragraph("<b>II Background and Related Technologies</b>", index_bold), Paragraph("<b>4</b>", index_bold)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;A NoSQL Database Systems ............................................................................................", index_item), Paragraph("4", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;B MongoDB .....................................................................................................................", index_item), Paragraph("4", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;C Cassandra ....................................................................................................................", index_item), Paragraph("4", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;D Neo4j .........................................................................................................................", index_item), Paragraph("4", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;E Docker and Kubernetes ...............................................................................................", index_item), Paragraph("4", index_item)],
        [Paragraph("<b>III Project Objectives</b>", index_bold), Paragraph("<b>5</b>", index_bold)],
        [Paragraph("<b>IV MongoDB Architecture and Document Modeling</b>", index_bold), Paragraph("<b>5</b>", index_bold)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;A Document Modeling ....................................................................................................", index_item), Paragraph("5", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;B Document Size Analysis ...............................................................................................", index_item), Paragraph("5", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;C Working Set and Cache Management .......................................................................", index_item), Paragraph("5", index_item)],
        [Paragraph("<b>V System Architecture</b>", index_bold), Paragraph("<b>6</b>", index_bold)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;A Architectural Components ...........................................................................................", index_item), Paragraph("6", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;B System Architecture Illustration ..................................................................................", index_item), Paragraph("6", index_item)],
        [Paragraph("<b>VI Laboratory Modules</b>", index_bold), Paragraph("<b>7</b>", index_bold)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;A Overview of Laboratory Experiments 1–19 .............................................................", index_item), Paragraph("7", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;B Labs 1–12: MongoDB Fundamentals ........................................................................", index_item), Paragraph("8", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;C Lab 13: Deployment and High Availability ..............................................................", index_item), Paragraph("8", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;D Lab 14: Monitoring, Backup and Recovery ..............................................................", index_item), Paragraph("8", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;E Lab 15: Multi-Tenant SaaS Architecture ....................................................................", index_item), Paragraph("9", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;F Lab 16: Polyglot Persistence and Fraud Detection ...................................................", index_item), Paragraph("9", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;G Lab 17: Advanced Database and Intelligence .............................................................", index_item), Paragraph("9", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;H Lab 18: Threat Intelligence False-Positive Analysis ...............................................", index_item), Paragraph("10", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;I Lab 19: AI-Powered Threat Intelligence Assistant ...................................................", index_item), Paragraph("10", index_item)],
        [Paragraph("<b>VII Distributed Database Deployment</b>", index_bold), Paragraph("<b>10</b>", index_bold)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;A MongoDB Replica Sets ...............................................................................................", index_item), Paragraph("10", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;B Containerization ...........................................................................................................", index_item), Paragraph("10", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;C Kubernetes Orchestration ...........................................................................................", index_item), Paragraph("11", index_item)]
    ]
    t_idx1 = Table(index_rows_p1, colWidths=[460, 44])
    t_idx1.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
    ]))
    story.append(t_idx1)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: INDEX CONTINUED (CONTENT PAGE 2)
    # =========================================================================
    index_rows_p2 = [
        [Paragraph("<b>VIII Monitoring and Performance Evaluation</b>", index_bold), Paragraph("<b>11</b>", index_bold)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;A WiredTiger Cache .......................................................................................................", index_item), Paragraph("11", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;B Query Performance ....................................................................................................", index_item), Paragraph("11", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;C Performance Metrics .................................................................................................", index_item), Paragraph("11", index_item)],
        [Paragraph("<b>IX Polyglot Persistence and Data Engineering</b>", index_bold), Paragraph("<b>11</b>", index_bold)],
        [Paragraph("<b>X Cyber Threat Intelligence Analysis</b>", index_bold), Paragraph("<b>12</b>", index_bold)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;A Threat Event Analysis ...............................................................................................", index_item), Paragraph("12", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;B Graph-Based Investigation .........................................................................................", index_item), Paragraph("12", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;C False-Positive Evaluation ............................................................................................", index_item), Paragraph("12", index_item)],
        [Paragraph("<b>XI AI-Assisted Threat Intelligence</b>", index_bold), Paragraph("<b>12</b>", index_bold)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;A Assistant Capabilities .................................................................................................", index_item), Paragraph("13", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;B Local AI Integration ....................................................................................................", index_item), Paragraph("13", index_item)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;C Practical Significance .................................................................................................", index_item), Paragraph("13", index_item)],
        [Paragraph("<b>XII Security Considerations</b>", index_bold), Paragraph("<b>13</b>", index_bold)],
        [Paragraph("<b>XIII Results and Discussion</b>", index_bold), Paragraph("<b>13</b>", index_bold)],
        [Paragraph("<b>XIV Limitations and Future Scope</b>", index_bold), Paragraph("<b>14</b>", index_bold)],
        [Paragraph("<b>XV Conclusion</b>", index_bold), Paragraph("<b>14</b>", index_bold)],
        [Paragraph("<b>References</b>", index_bold), Paragraph("<b>14</b>", index_bold)]
    ]
    t_idx2 = Table(index_rows_p2, colWidths=[460, 44])
    t_idx2.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_idx2)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: ABSTRACT & INDEX TERMS (CONTENT PAGE 3)
    # =========================================================================
    story.append(Paragraph("<u><b>Abstract</b></u>", ParagraphStyle("AbstractTitle", fontName="Times-Bold", fontSize=13, spaceAfter=14)))
    p_abstract = (
        "The increasing demand for scalable data management, distributed computing, and intelligent cybersecurity solutions has "
        "encouraged the adoption of modern NoSQL database technologies. This report presents the CTI MongoDB Laboratory, a "
        "comprehensive practical project designed to explore MongoDB architecture, distributed database systems, data "
        "engineering, and Cyber Threat Intelligence (CTI).<br/><br/>"
        "The project consists of nineteen laboratory exercises covering fundamental database operations, document modeling, "
        "indexing, query optimization, transactions, replication, containerization, orchestration, monitoring, backup and recovery, "
        "multi-tenant architecture, and polyglot persistence.<br/><br/>"
        "The system integrates MongoDB with Cassandra and Neo4j to demonstrate different approaches to structured event "
        "storage and relationship analysis. It also incorporates threat intelligence analysis, fraud detection, and an AI-powered "
        "assistant using a locally hosted language model through Ollama.<br/><br/>"
        "The laboratory provides an integrated learning environment for understanding how modern database technologies can "
        "support scalable applications, distributed data processing, and cybersecurity investigation workflows."
    )
    story.append(Paragraph(p_abstract, body_style))
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>Index Terms</b>", h1_style))
    story.append(Paragraph(
        "MongoDB, NoSQL, Distributed Systems, Cyber Threat Intelligence, Cassandra, Neo4j, Docker, Kubernetes, Database "
        "Monitoring, Fraud Detection, Artificial Intelligence.", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: I. INTRODUCTION & II. BACKGROUND (CONTENT PAGE 4)
    # =========================================================================
    story.append(Paragraph("<b><u>I. Introduction</u></b>", h1_style))
    story.append(Paragraph(
        "Modern applications generate enormous amounts of data through user interactions, transactions, network activities, and "
        "digital services. Traditional relational database systems may face limitations when handling rapidly changing data "
        "structures, distributed workloads, and large-scale information processing requirements.<br/><br/>"
        "NoSQL databases provide alternative data management approaches that support flexible data models, horizontal "
        "scalability, and distributed storage.<br/><br/>"
        "MongoDB is a document-oriented NoSQL database that stores information in BSON documents. Its flexible schema and "
        "indexing capabilities make it suitable for applications that require dynamic data structures and scalable storage.<br/><br/>"
        "The CTI MongoDB Laboratory was developed as a comprehensive educational project to demonstrate different database "
        "technologies and their practical applications.<br/><br/>"
        "The project combines database engineering with cybersecurity analysis through nineteen laboratory exercises. These "
        "exercises progress from basic MongoDB operations to distributed deployment, database monitoring, graph analytics, threat "
        "intelligence, and AI-assisted cybersecurity applications.<br/><br/>"
        "The main purpose is to provide practical understanding of how different database systems work together in modern "
        "software architectures.", body_style
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b><u>II. Background and Related Technologies</u></b>", h1_style))
    story.append(Paragraph("<b>A. NoSQL Database Systems</b>", h2_style))
    story.append(Paragraph(
        "NoSQL databases are designed to manage data using models other than traditional relational tables. Common categories "
        "include document, key-value, column-family, and graph databases. These systems provide flexibility in data modeling "
        "and support different scalability requirements.", body_style
    ))
    story.append(Paragraph("<b>B. MongoDB</b>", h2_style))
    story.append(Paragraph(
        "MongoDB is a document-oriented database that stores data as BSON documents. It supports collections, flexible document "
        "structures, indexing, aggregation, transactions, and replica sets. MongoDB is the primary database technology used throughout this laboratory.", body_style
    ))
    story.append(Paragraph("<b>C. Cassandra</b>", h2_style))
    story.append(Paragraph(
        "Apache Cassandra is a distributed wide-column database designed for high availability and large-scale data storage. Within "
        "this project, Cassandra is used to demonstrate distributed event storage and event-oriented data management.", body_style
    ))
    story.append(Paragraph("<b>D. Neo4j</b>", h2_style))
    story.append(Paragraph(
        "Neo4j is a graph database that represents information using nodes, relationships, and properties. It is particularly "
        "useful for investigating connections between entities, identifying suspicious relationships, and performing graph-based analysis.", body_style
    ))
    story.append(Paragraph("<b>E. Docker and Kubernetes</b>", h2_style))
    story.append(Paragraph(
        "Docker provides containerization for application deployment, while Kubernetes supports container orchestration and "
        "persistent storage management. Both technologies are explored to demonstrate production-oriented database deployment concepts.", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: III. PROJECT OBJECTIVES & IV. MONGODB ARCHITECTURE (CONTENT PAGE 5)
    # =========================================================================
    story.append(Paragraph("<b><u>III. Project Objectives</u></b>", h1_style))
    story.append(Paragraph("The major objectives of the CTI MongoDB Laboratory are as follows:", body_style))
    objectives = [
        "To understand the architecture and operation of MongoDB.",
        "To study document-oriented data modeling, embedding, and referencing.",
        "To evaluate database indexing and query performance.",
        "To understand transactions and concurrent database operations.",
        "To explore replica sets and high availability.",
        "To demonstrate containerized database deployment using Docker.",
        "To understand Kubernetes StatefulSets and persistent storage.",
        "To implement database monitoring and backup management concepts.",
        "To explore multi-tenant application architecture.",
        "To understand polyglot persistence using multiple database technologies.",
        "To investigate fraud detection and cyber threat intelligence analysis.",
        "To demonstrate AI-assisted cybersecurity interaction through a locally hosted language model."
    ]
    for obj in objectives:
        story.append(Paragraph(f"• {obj}", bullet_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b><u>IV. MongoDB Architecture and Document Modeling</u></b>", h1_style))
    story.append(Paragraph(
        "MongoDB follows a document-oriented data architecture. Instead of organizing information into conventional relational "
        "rows, it stores data in collections containing BSON documents.<br/><br/>"
        "Each document can contain multiple fields, nested objects, and arrays. This structure allows applications to represent "
        "complex information in a flexible manner.", body_style
    ))
    story.append(Paragraph("<b>A. Document Modeling</b>", h2_style))
    story.append(Paragraph(
        "The laboratory explores two important document modeling approaches:<br/>"
        "<b>Embedded Documents:</b> Related information is stored within a parent document. This approach can reduce the number of "
        "database operations required to retrieve associated information.<br/>"
        "<b>Referenced Documents:</b> Related information is stored separately and connected through references. This approach can "
        "reduce unnecessary duplication and support relationships between independent records.", body_style
    ))
    story.append(Paragraph("<b>B. Document Size Analysis</b>", h2_style))
    story.append(Paragraph(
        "The laboratory examines BSON document sizes using MongoDB’s document size measurement capabilities.<br/>"
        "MongoDB imposes a maximum BSON document size of 16 MB. Understanding this restriction is important when "
        "designing document structures and deciding which information should be embedded or referenced.", body_style
    ))
    story.append(Paragraph("<b>C. Working Set and Cache Management</b>", h2_style))
    story.append(Paragraph(
        "A working set represents the portion of database information frequently accessed by an application.<br/>"
        "The laboratory investigates the relationship between working-set size, available memory, and WiredTiger cache "
        "utilization. This analysis helps explain how memory management can influence database performance.", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 7: V. SYSTEM ARCHITECTURE & DIAGRAM (CONTENT PAGE 6)
    # =========================================================================
    story.append(Paragraph("<b><u>V. System Architecture</u></b>", h1_style))
    story.append(Paragraph(
        "The CTI MongoDB Laboratory follows a multi-component architecture in which different services perform specialized functions.<br/><br/>"
        "The Flask/FastAPI application acts as the primary user interface and connects users to the laboratory modules.<br/><br/>"
        "MongoDB provides the main application database, while Cassandra and Neo4j support distributed event storage and "
        "graph-based relationship analysis.<br/><br/>"
        "FastAPI provides an independent service for multi-tenant operations, and Ollama supports local AI-assisted interaction.", body_style
    ))
    story.append(Paragraph("<b>A. Architectural Components</b>", h2_style))
    story.append(Paragraph(
        "The major architectural components are:<br/>"
        "• <b>Flask / FastAPI Application:</b> Provides the primary web interface and laboratory navigation.<br/>"
        "• <b>MongoDB:</b> Stores application information and supports document-oriented database operations.<br/>"
        "• <b>Cassandra:</b> Supports distributed event storage.<br/>"
        "• <b>Neo4j:</b> Supports relationship analysis and graph-based fraud investigation.<br/>"
        "• <b>FastAPI:</b> Provides the separate multi-tenant application service.<br/>"
        "• <b>Ollama:</b> Provides locally hosted AI model interaction.<br/>"
        "• <b>Docker and Kubernetes:</b> Support containerized deployment and orchestration.", body_style
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>B. System Architecture Illustration</b>", h2_style))
    story.append(Paragraph(
        "The architecture demonstrates the interaction between the web application, supporting services, databases, and intelligence analysis components.", body_style
    ))
    story.append(Spacer(1, 10))

    # Architecture Box Diagram using Flowable Table
    arch_box_data = [
        ["", Paragraph("<para align='center'><b>User</b></para>", ParagraphStyle("D1", fontName="Times-Bold", fontSize=9)), ""],
        ["", Paragraph("<para align='center'>↓</para>", ParagraphStyle("Darr", fontName="Times-Bold", fontSize=12, alignment=1)), ""],
        ["", Paragraph("<para align='center'><b>Web Application / Frontend</b><br/><font size='7.5'>FastAPI / Flask Dashboard (Port 8000 / 5000)</font></para>", ParagraphStyle("D2", fontName="Times-Roman", fontSize=8.5, alignment=1)), ""],
        ["", Paragraph("<para align='center'>↓</para>", ParagraphStyle("Darr2", fontName="Times-Bold", fontSize=12, alignment=1)), ""],
        [
            Paragraph("<b>Application Services</b><br/>• FastAPI Service (8001)<br/>• Ollama AI Assistant (11434)<br/>• Autonomous SecOps Bot", ParagraphStyle("D3", fontName="Times-Roman", fontSize=8)),
            Paragraph("<b>Databases Core</b><br/>• MongoDB (Replica Set rs0)<br/>• Cassandra (Event Storage)<br/>• Neo4j (Graph Database)", ParagraphStyle("D4", fontName="Times-Roman", fontSize=8)),
            Paragraph("<b>Data Analysis</b><br/>• Monitoring & WiredTiger<br/>• Community Detection<br/>• RAG Vector Retrieval", ParagraphStyle("D5", fontName="Times-Roman", fontSize=8))
        ]
    ]
    arch_table = Table(arch_box_data, colWidths=[168, 168, 168])
    arch_table.setStyle(TableStyle([
        ("BOX", (1, 0), (1, 0), 0.75, colors.HexColor("#1e3a8a")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f0fdf4")),
        ("BOX", (1, 2), (1, 2), 1, colors.HexColor("#1e3a8a")),
        ("BACKGROUND", (1, 2), (1, 2), colors.HexColor("#eff6ff")),
        ("BOX", (0, 4), (0, 4), 0.75, colors.HexColor("#475569")),
        ("BACKGROUND", (0, 4), (0, 4), colors.HexColor("#f8fafc")),
        ("BOX", (1, 4), (1, 4), 0.75, colors.HexColor("#475569")),
        ("BACKGROUND", (1, 4), (1, 4), colors.HexColor("#f8fafc")),
        ("BOX", (2, 4), (2, 4), 0.75, colors.HexColor("#475569")),
        ("BACKGROUND", (2, 4), (2, 4), colors.HexColor("#f8fafc")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph("<para align='center'><font size='8'>Figure 1: Overall architecture of the CTI MongoDB Laboratory.</font></para>", ParagraphStyle("FigCap", fontName="Times-Italic", fontSize=8, alignment=1)))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 8: VI. LABORATORY MODULES (TABLE 1: LABS 1-17) (CONTENT PAGE 7)
    # =========================================================================
    story.append(Paragraph("<b><u>VI. Laboratory Modules</u></b>", h1_style))
    story.append(Paragraph(
        "The project consists of nineteen laboratory exercises organized around database fundamentals, advanced deployment, data "
        "engineering, and cybersecurity.", body_style
    ))
    story.append(Paragraph("<b>A. Overview of Laboratory Experiments 1–19</b>", h2_style))
    story.append(Paragraph(
        "Table 1 summarises what each experiment does. The details of each group follow in the subsections below.", body_style
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<para align='center'><font size='8.5'><b>Table 1: Summary of laboratory experiments 1–19.</b></font></para>", ParagraphStyle("TblCap", fontName="Times-Bold", fontSize=8.5, alignment=1, spaceAfter=4)))

    t1_data_p1 = [
        ["Lab", "Title", "What the experiment does"],
        ["1", "Database and Collection Management*", "Creates and manages databases and collections, the starting point for all later labs."],
        ["2", "CRUD Operations*", "Inserts, retrieves, updates and deletes documents in MongoDB."],
        ["3", "BSON Document Structure*", "Studies how documents with multiple fields, nested objects and arrays are represented as BSON."],
        ["4", "Embedded and Referenced Modeling*", "Compares storing related data inside a parent document with storing it separately and linking by reference."],
        ["5", "Schema Design and Relationships*", "Designs schemas and the relationships between entities, applying the embedding-versus-referencing decision."],
        ["6", "Document Size Measurement*", "Measures document size with $bsonSize and relates it to MongoDB’s 16 MB document limit."],
        ["7", "Working-Set Analysis*", "Relates the size of frequently accessed data to available memory and WiredTiger cache use."],
        ["8", "Index Creation and Optimization*", "Creates indexes to reduce the amount of data examined and weighs their storage and maintenance cost."],
        ["9", "Query Execution*", "Runs queries and inspects how they execute against collections."],
        ["10", "Transactions and Concurrency*", "Applies transactions and manages concurrent database operations."],
        ["11", "WiredTiger Cache Utilization*", "Analyses how the WiredTiger cache is used under different workloads."],
        ["12", "Query Performance Evaluation*", "Evaluates query performance and how design decisions influence it."],
        ["13", "Deployment and High Availability", "Docker: a three-node replica set (one primary, two secondaries) with health monitoring and node stop/restart. Kubernetes: a MongoDB StatefulSet with Persistent Volume Claims, secrets and replica set initialization in the nosql-labs namespace."],
        ["14", "Monitoring, Backup and Recovery", "14.1: monitors connection health and WiredTiger cache metrics (capacity, usage, dirty cache, pages read and evicted) on a live dashboard. 14.2: timestamped, scheduled backups with seven-day retention, SHA-256 integrity checks, restore into a separate recovery collection, backup benchmarking and RPO/RTO reporting."],
        ["15", "Multi-Tenant SaaS Architecture", "Builds a FastAPI and MongoDB service on a shared database with tenant separation and tenant-specific operations; benchmarks migration, query performance and analytics."],
        ["16", "Polyglot Persistence and Fraud Detection", "Uses MongoDB for application and tenant data, Cassandra for distributed event storage and querying, and Neo4j for relationships and fraud investigation."],
        ["17", "Advanced Database and Intelligence", "Connects database engineering concepts with analytical and intelligence-oriented processing, as a foundation for advanced analysis."]
    ]
    t1_table_p1 = Table(t1_data_p1, colWidths=[24, 150, 330])
    t1_table_p1.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#111827")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#111827")),
        ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#111827")),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6.8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t1_table_p1)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 9: VI. LABS 18-19 CONTINUATION & LABS 1-14 (CONTENT PAGE 8)
    # =========================================================================
    t1_data_p2 = [
        ["Lab", "Title", "What the experiment does"],
        ["18", "Threat Intelligence False-Positive Analysis", "Generates 100,000 events deterministically from a seed, analyses suspicious relationships and communities in Neo4j, and evaluates false positives through comparative reports."],
        ["19", "AI-Powered Threat Intelligence Assistant", "Adds a locally hosted Ollama/SLM chat assistant (Qwen 2.5 3B) to the application for threat explanations, CVE discussion, classification guidance and mitigation advice, with conversation history and response validation."]
    ]
    t1_table_p2 = Table(t1_data_p2, colWidths=[24, 150, 330])
    t1_table_p2.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#111827")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#111827")),
        ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#111827")),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t1_table_p2)
    story.append(Spacer(1, 4))
    story.append(Paragraph("<font size='7'><i>* The project description covers Labs 1–12 as one group and lists their topics without numbering each lab. Titles for Labs 1–12 follow the order of that topic list and are provisional; adjust them to your actual lab numbering.</i></font>", ParagraphStyle("TblNote", fontName="Times-Italic", fontSize=7, spaceAfter=8)))

    story.append(Paragraph("<b>B. Labs 1–12: MongoDB Fundamentals</b>", h2_style))
    story.append(Paragraph(
        "The first twelve laboratory exercises establish the foundation of MongoDB development and database engineering. These exercises cover:<br/>"
        "• Database and collection management.<br/>"
        "• Document insertion, retrieval, updating, and deletion.<br/>"
        "• BSON document structure.<br/>"
        "• Embedded and referenced document modeling.<br/>"
        "• Schema design and relationships.<br/>"
        "• Document size measurement.<br/>"
        "• Working-set analysis.<br/>"
        "• Index creation and optimization.<br/>"
        "• Query execution and performance evaluation.<br/>"
        "• Transactions and concurrency management.<br/>"
        "These exercises help learners understand how MongoDB manages information and how database design decisions influence application performance.", body_style
    ))
    story.append(Paragraph("<b>C. Lab 13: Deployment and High Availability</b>", h2_style))
    story.append(Paragraph(
        "Lab 13 focuses on MongoDB deployment using Docker and Kubernetes.<br/>"
        "The Docker-based deployment demonstrates a three-node MongoDB replica set consisting of one primary node and two secondary nodes.<br/>"
        "The laboratory explores node health, primary and secondary roles, container management, and replica set availability.<br/>"
        "The Kubernetes deployment introduces StatefulSets, Persistent Volume Claims, namespace management, secrets, and replica set initialization.<br/>"
        "These exercises demonstrate important concepts related to database reliability and infrastructure management.", body_style
    ))
    story.append(Paragraph("<b>D. Lab 14: Monitoring, Backup and Recovery</b>", h2_style))
    story.append(Paragraph(
        "Lab 14 is divided into two major components.<br/>"
        "<b>Monitoring:</b> The monitoring component examines MongoDB connection health and WiredTiger cache metrics. Important measurements include:", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 10: LABS 14-17 DETAILS (CONTENT PAGE 9)
    # =========================================================================
    story.append(Paragraph(
        "• Maximum cache capacity.<br/>"
        "• Current cache utilization.<br/>"
        "• Dirty cache information.<br/>"
        "• Pages read into cache.<br/>"
        "• Pages evicted from cache.<br/>"
        "The monitoring dashboard helps visualize database behavior and resource utilization.<br/><br/>"
        "<b>Backup and Recovery:</b> The backup component demonstrates timestamped backups, automated scheduling, retention policies, and integrity verification. SHA-256 checksums are used to support backup integrity validation. The recovery process restores backup information into a separate recovery collection.<br/>"
        "The laboratory also examines backup performance and two important recovery measurements:<br/>"
        "<b>Recovery Point Objective (RPO):</b> Represents the maximum acceptable amount of data loss measured in time.<br/>"
        "<b>Recovery Time Objective (RTO):</b> Represents the target time required to restore a service after a failure.", body_style
    ))
    story.append(Paragraph("<b>E. Lab 15: Multi-Tenant SaaS Architecture</b>", h2_style))
    story.append(Paragraph(
        "Lab 15 demonstrates a multi-tenant Software as a Service architecture using FastAPI and MongoDB.<br/>"
        "A multi-tenant application allows multiple organizations or customers to use the same application infrastructure while "
        "maintaining logical separation of their information.<br/>"
        "The laboratory investigates:<br/>"
        "• Shared database architecture.<br/>"
        "• Tenant-specific data operations.<br/>"
        "• Tenant separation.<br/>"
        "• Migration benchmarking.<br/>"
        "• Query performance comparison.<br/>"
        "• Analytics performance evaluation.<br/>"
        "This module introduces important concepts used in cloud-based business applications.", body_style
    ))
    story.append(Paragraph("<b>F. Lab 16: Polyglot Persistence and Fraud Detection</b>", h2_style))
    story.append(Paragraph(
        "Lab 16 demonstrates polyglot persistence, an architectural approach in which an application uses multiple database "
        "technologies according to their individual strengths.<br/>"
        "MongoDB manages application and tenant data. Cassandra supports distributed event storage and querying. Neo4j "
        "represents relationships between entities and supports graph-based investigation.<br/>"
        "The combination demonstrates how different database technologies can cooperate within one application architecture.", body_style
    ))
    story.append(Paragraph("<b>G. Lab 17: Advanced Database and Intelligence</b>", h2_style))
    story.append(Paragraph(
        "Lab 17 extends the advanced database and intelligence workflow of the project.<br/>"
        "It focuses on connecting database engineering concepts with analytical operations and intelligence-oriented processing.<br/>"
        "The laboratory provides a foundation for understanding how stored information can be used in more advanced analysis workflows.", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 11: LABS 18-19 & VII. DISTRIBUTED DATABASE DEPLOYMENT (CONTENT PAGE 10)
    # =========================================================================
    story.append(Paragraph("<b>H. Lab 18: Threat Intelligence False-Positive Analysis</b>", h2_style))
    story.append(Paragraph(
        "Lab 18 explores threat intelligence analysis using a reproducible dataset of 100,000 events.<br/>"
        "The laboratory uses deterministic, seed-based event generation to support repeatable experiments.<br/>"
        "It investigates suspicious relationships and applies graph-based analysis through Neo4j. Community detection is used to "
        "examine groups of related entities and identify potentially suspicious patterns.<br/>"
        "An important objective is the evaluation of false positives. A false positive occurs when a system incorrectly classifies "
        "legitimate activity as suspicious.<br/>"
        "Comparative analysis helps explain why reliable threat detection requires more than simply identifying unusual connections.", body_style
    ))
    story.append(Paragraph("<b>I. Lab 19: AI-Powered Threat Intelligence Assistant</b>", h2_style))
    story.append(Paragraph(
        "Lab 19 introduces a locally hosted AI assistant through Ollama. The current integration uses the Qwen 2.5 3B / Local SLM language model.<br/>"
        "The assistant is designed to support users in understanding cybersecurity concepts and threat intelligence information. Its major capabilities include:<br/>"
        "• Threat intelligence explanations.<br/>"
        "• Cybersecurity concept assistance.<br/>"
        "• CVE and vulnerability discussions.<br/>"
        "• Threat classification guidance.<br/>"
        "• Mitigation recommendations.<br/>"
        "• Conversation history support.<br/>"
        "• Response validation and error handling.<br/>"
        "The local model integration demonstrates how AI can be incorporated into an existing database-oriented application.<br/>"
        "The assistant is intended to support analysis and learning rather than replace professional security investigation.", body_style
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b><u>VII. Distributed Database Deployment</u></b>", h1_style))
    story.append(Paragraph(
        "Distributed deployment is an important part of modern database infrastructure. The project explores replica sets and "
        "container orchestration to demonstrate availability and scalability concepts.", body_style
    ))
    story.append(Paragraph("<b>A. MongoDB Replica Sets</b>", h2_style))
    story.append(Paragraph(
        "A MongoDB replica set maintains multiple copies of the same dataset across different database nodes.<br/>"
        "The primary node handles write operations, while secondary nodes maintain replicated information. If the primary node "
        "becomes unavailable, the replica set can elect another eligible member as primary.<br/>"
        "This approach improves database availability and fault tolerance.", body_style
    ))
    story.append(Paragraph("<b>B. Containerization</b>", h2_style))
    story.append(Paragraph(
        "Docker is used to package application services and database components into isolated containers. Containerization "
        "simplifies deployment, environment management, and service separation.", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 12: K8S, VIII. MONITORING & IX. POLYGLOT PERSISTENCE (CONTENT PAGE 11)
    # =========================================================================
    story.append(Paragraph("<b>C. Kubernetes Orchestration</b>", h2_style))
    story.append(Paragraph(
        "Kubernetes extends container management through orchestration capabilities.<br/>"
        "StatefulSets provide stable identities and persistent storage associations for stateful applications. Persistent Volume Claims "
        "allow database containers to use persistent storage.<br/>"
        "These concepts are important when deploying database services in managed environments.", body_style
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b><u>VIII. Monitoring and Performance Evaluation</u></b>", h1_style))
    story.append(Paragraph(
        "Database monitoring helps administrators understand system behavior and identify potential performance problems.<br/>"
        "The laboratory focuses on the relationship between memory utilization, database workload, and query performance.", body_style
    ))
    story.append(Paragraph("<b>A. WiredTiger Cache</b>", h2_style))
    story.append(Paragraph(
        "WiredTiger is MongoDB’s default storage engine. Its cache maintains frequently accessed database information in memory.<br/>"
        "Cache utilization, dirty data, page reads, and page eviction metrics provide useful information about database activity.", body_style
    ))
    story.append(Paragraph("<b>B. Query Performance</b>", h2_style))
    story.append(Paragraph(
        "Indexes improve the efficiency of database queries by reducing the amount of information that must be examined.<br/>"
        "However, indexes also require additional storage and maintenance operations.<br/>"
        "The laboratory explores query performance and the importance of selecting appropriate indexes for different workloads.", body_style
    ))
    story.append(Paragraph("<b>C. Performance Metrics</b>", h2_style))
    story.append(Paragraph(
        "The main performance measurements include:<br/>"
        "• Database response time.<br/>"
        "• Query execution performance.<br/>"
        "• Cache utilization.<br/>"
        "• Page read activity.<br/>"
        "• Page eviction activity.<br/>"
        "• Backup duration.<br/>"
        "• Recovery performance.<br/>"
        "The purpose of these measurements is to develop an understanding of database performance characteristics.", body_style
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b><u>IX. Polyglot Persistence and Data Engineering</u></b>", h1_style))
    story.append(Paragraph(
        "Polyglot persistence refers to the use of multiple database systems within a single application architecture. Different "
        "databases are selected according to the requirements of individual workloads.<br/>"
        "The CTI MongoDB Laboratory demonstrates three major database technologies, summarised in Table 2.", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 13: TABLE 2, X. CYBER THREAT INTEL & XI. AI-ASSISTED INTEL (CONTENT PAGE 12)
    # =========================================================================
    story.append(Paragraph("<para align='center'><font size='8.5'><b>Table 2: Database responsibilities.</b></font></para>", ParagraphStyle("TblCap2", fontName="Times-Bold", fontSize=8.5, alignment=1, spaceAfter=4)))
    t2_data = [
        ["Database", "Primary Responsibility"],
        ["MongoDB", "Application information, tenant data, and document-oriented storage."],
        ["Cassandra", "Distributed event storage and event-oriented data management."],
        ["Neo4j", "Entity relationships, graph investigation, and fraud analysis."]
    ]
    t2_table = Table(t2_data, colWidths=[120, 384])
    t2_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#111827")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#111827")),
        ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#111827")),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t2_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "This architecture demonstrates that a single database may not be the optimal choice for every application requirement. By "
        "combining specialized databases, the application can demonstrate different approaches to data storage, querying, and analysis.", body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b><u>X. Cyber Threat Intelligence Analysis</u></b>", h1_style))
    story.append(Paragraph(
        "Cyber Threat Intelligence involves collecting, processing, and analyzing information about potential cyber threats. It helps "
        "organizations understand suspicious activities, identify attack patterns, and develop appropriate defensive strategies.<br/>"
        "The CTI MongoDB Laboratory incorporates threat-oriented analysis through its advanced laboratory modules.", body_style
    ))
    story.append(Paragraph("<b>A. Threat Event Analysis</b>", h2_style))
    story.append(Paragraph(
        "The project uses a reproducible collection of generated events to demonstrate threat analysis concepts.<br/>"
        "Event relationships can provide useful context about the behavior of users, systems, and other entities.", body_style
    ))
    story.append(Paragraph("<b>B. Graph-Based Investigation</b>", h2_style))
    story.append(Paragraph(
        "Neo4j provides a graph-based representation of relationships between entities.<br/>"
        "Graph analysis allows investigators to examine connected entities and identify suspicious relationship patterns.<br/>"
        "Community detection helps identify groups of interconnected entities that may require additional investigation.", body_style
    ))
    story.append(Paragraph("<b>C. False-Positive Evaluation</b>", h2_style))
    story.append(Paragraph(
        "False-positive analysis is important because incorrect threat classification can result in unnecessary alerts and investigation effort.<br/>"
        "The laboratory evaluates suspicious relationships and compares analysis outcomes to understand the limitations of detection approaches.", body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b><u>XI. AI-Assisted Threat Intelligence</u></b>", h1_style))
    story.append(Paragraph(
        "Artificial intelligence has become an important technology in cybersecurity research and information analysis.<br/>"
        "The project integrates an AI-powered assistant using Ollama and the Qwen 2.5 3B model (or built-in Threat SLM). Unlike cloud-dependent AI "
        "services, a locally hosted language model can process user interactions within the local environment, subject to the "
        "configured system resources and model capabilities.", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 14: XI-A..C, XII. SECURITY & XIII. RESULTS (CONTENT PAGE 13)
    # =========================================================================
    story.append(Paragraph("<b>A. Assistant Capabilities</b>", h2_style))
    story.append(Paragraph(
        "The assistant supports several educational and analytical activities. These include cybersecurity explanations, vulnerability "
        "discussions, threat classification guidance, and mitigation recommendations.", body_style
    ))
    story.append(Paragraph("<b>B. Local AI Integration</b>", h2_style))
    story.append(Paragraph(
        "Ollama provides the local model-serving environment. The Flask / FastAPI application communicates with the locally hosted AI "
        "service and presents the responses through a chat interface.<br/>"
        "Conversation history and response validation are additional features of the integration.", body_style
    ))
    story.append(Paragraph("<b>C. Practical Significance</b>", h2_style))
    story.append(Paragraph(
        "The AI assistant demonstrates how language models can support cybersecurity education and information interpretation.<br/>"
        "However, AI-generated recommendations must be reviewed and verified before they are used in real security environments.", body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b><u>XII. Security Considerations</u></b>", h1_style))
    story.append(Paragraph(
        "Security is essential when developing applications that manage sensitive data and connect multiple services. The project "
        "identifies several important security considerations:<br/>"
        "• Database credentials should be protected using environment-based configuration.<br/>"
        "• API keys and authentication secrets should never be exposed publicly.<br/>"
        "• Database authentication should be enabled.<br/>"
        "• Database ports should be restricted to trusted networks.<br/>"
        "• JWT secrets should be securely managed.<br/>"
        "• Frontend access should be restricted through appropriate CORS policies.<br/>"
        "• AI-generated security recommendations should be independently verified.<br/>"
        "• Administrative access should follow the principle of least privilege.<br/>"
        "The laboratory is intended for educational and experimental purposes. Additional security hardening is necessary before "
        "production deployment.", body_style
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b><u>XIII. Results and Discussion</u></b>", h1_style))
    story.append(Paragraph(
        "The CTI MongoDB Laboratory provides an integrated environment for demonstrating database engineering and "
        "cybersecurity concepts.<br/><br/>"
        "Its nineteen laboratory exercises cover multiple stages of modern application development, beginning with fundamental "
        "database operations and progressing toward distributed infrastructure and AI-assisted analysis.<br/><br/>"
        "The project demonstrates the different responsibilities of document, distributed event, and graph database systems. It also "
        "provides practical exposure to replication, containerization, monitoring, backup verification, and recovery planning.<br/><br/>"
        "The multi-tenant architecture introduces important concepts related to shared application infrastructure and data isolation.<br/><br/>"
        "The threat intelligence modules extend the database learning environment into cybersecurity analysis through event "
        "relationships and graph-based investigation.", body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 15: XIII CONTINUED, XIV, XV & REFERENCES (CONTENT PAGE 14)
    # =========================================================================
    story.append(Paragraph(
        "The AI integration further demonstrates how locally hosted language models can support an interactive cybersecurity "
        "learning environment.<br/><br/>"
        "The project is primarily a practical demonstration platform. Quantitative performance improvements and detection "
        "accuracy should be established through measured experimental results rather than assumed values.", body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b><u>XIV. Limitations and Future Scope</u></b>", h1_style))
    story.append(Paragraph(
        "Although the project covers several advanced database and cybersecurity concepts, there are opportunities for further "
        "development. Future improvements may include:<br/>"
        "• Advanced database benchmarking under larger workloads.<br/>"
        "• Improved authentication and role-based access control.<br/>"
        "• Enhanced tenant isolation mechanisms.<br/>"
        "• Integration with additional threat intelligence sources.<br/>"
        "• Advanced graph-based threat correlation.<br/>"
        "• Improved AI response evaluation and validation.<br/>"
        "• More comprehensive monitoring and alerting mechanisms.<br/>"
        "• Deployment within a secured cloud infrastructure.<br/>"
        "• Automated security testing and vulnerability assessment.<br/>"
        "These improvements could extend the laboratory into a more comprehensive database engineering and cybersecurity "
        "research platform.", body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b><u>XV. Conclusion</u></b>", h1_style))
    story.append(Paragraph(
        "The CTI MongoDB Laboratory presents a comprehensive practical study of modern NoSQL databases, distributed "
        "systems, data engineering, and Cyber Threat Intelligence.<br/><br/>"
        "Through nineteen laboratory exercises, the project explores MongoDB fundamentals, document modeling, indexing, "
        "performance optimization, replication, containerization, monitoring, backup and recovery.<br/><br/>"
        "It further demonstrates multi-tenant application architecture and polyglot persistence through the integration of MongoDB, "
        "Cassandra, and Neo4j.<br/><br/>"
        "The advanced intelligence modules introduce graph-based relationship analysis, fraud investigation, false-positive "
        "evaluation, and AI-assisted cybersecurity interaction.<br/><br/>"
        "The integration of Flask, FastAPI, Docker, Kubernetes, and Ollama demonstrates how multiple technologies can work "
        "together within a modern software environment.<br/><br/>"
        "Overall, the project provides a practical learning foundation for understanding database architecture, distributed "
        "application development, and intelligent cybersecurity systems.", body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b><u>References</u></b>", h1_style))
    story.append(Paragraph("[1] MongoDB Inc., “MongoDB Documentation.” [Online]. Available: https://www.mongodb.com/docs/", body_style))
    story.append(Paragraph("[2] MongoDB Inc., “PyMongo Documentation.” [Online]. Available: https://www.mongodb.com/docs/languages/python/pymongo-driver/", body_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 16: REFERENCES CONTINUED (CONTENT PAGE 15)
    # =========================================================================
    refs = [
        "[3] Apache Software Foundation, “Apache Cassandra Documentation.” [Online]. Available: https://cassandra.apache.org/doc/",
        "[4] Neo4j, Inc., “Neo4j Documentation.” [Online]. Available: https://neo4j.com/docs/",
        "[5] Docker Inc., “Docker Documentation.” [Online]. Available: https://docs.docker.com/",
        "[6] The Kubernetes Authors, “Kubernetes Documentation.” [Online]. Available: https://kubernetes.io/docs/",
        "[7] Pallets Projects, “Flask Documentation.” [Online]. Available: https://flask.palletsprojects.com/",
        "[8] FastAPI, “FastAPI Documentation.” [Online]. Available: https://fastapi.tiangolo.com/",
        "[9] Prometheus Authors, “Prometheus Documentation.” [Online]. Available: https://prometheus.io/docs/",
        "[10] Ollama, “Ollama Documentation.” [Online]. Available: https://docs.ollama.com/",
        "[11] MITRE Corporation, “MITRE ATT&CK Framework.” [Online]. Available: https://attack.mitre.org/",
        "[12] OWASP Foundation, “OWASP Top Ten.” [Online]. Available: https://owasp.org/www-project-top-ten"
    ]
    for r in refs:
        story.append(Paragraph(r, body_style))
        story.append(Spacer(1, 4))

    doc.build(story, canvasmaker=AcademicCanvas)
    print(f"[OK] Master academic report successfully compiled at: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    build_pdf()
