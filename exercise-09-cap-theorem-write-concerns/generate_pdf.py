"""
Script to generate the comprehensive Lab 09 Academic PDF Submission Report.
Uses ReportLab to build a professional 4-page document with zero awkward splits.
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

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(45, 755, "NoSQL Databases (MongoDB) | Lab 09: CAP Theorem, Write Concerns & Fault Tolerance")
            self.setFont("Helvetica", 8)
            self.drawRightString(567, 755, "Lab 09 Formal Submission")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(45, 747, 567, 747)
            
        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(45, 42, 567, 42)
        self.setFont("Helvetica", 8)
        self.drawString(45, 30, "Docker Demonstration Submission Report | Verified Against Running MongoDB 7.0 Cluster")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.setFont("Helvetica-Bold", 8)
        self.drawRightString(567, 30, page_str)
        self.restoreState()


def build_pdf(filename="Lab_09_Report_CAP_Theorem_and_Write_Concerns.pdf"):
    # Margins: 45pt = 0.625in, printable width = 612 - 90 = 522pt
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=52,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Color Palette
    primary = colors.HexColor("#1E3A8A")     # Navy
    secondary = colors.HexColor("#0D9488")   # Teal
    accent_dark = colors.HexColor("#0F172A") # Slate dark
    dark_text = colors.HexColor("#1E293B")   # Charcoal
    muted_text = colors.HexColor("#64748B")  # Muted slate
    light_bg = colors.HexColor("#F8FAFC")    # Background fill
    border_color = colors.HexColor("#CBD5E1")# Border grey

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13.5,
        textColor=muted_text,
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=primary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=secondary,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11.2,
        textColor=dark_text,
        spaceAfter=4
    )

    body_bold = ParagraphStyle(
        'Body_Bold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.6,
        leading=10,
        textColor=dark_text
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell,
        fontName='Helvetica-Bold'
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=table_cell,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []

    # =========================================================================
    # PAGE 1: Title, Meta, Exec Summary, Lab 9.1 Methodology & Benchmark Table
    # =========================================================================
    story.append(Paragraph("LAB 09: THE CAP THEOREM IN PRACTICE", title_style))
    story.append(Paragraph("Empirical Write Concern Latency Benchmarking & Replica Set Network Partition Simulation", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary, spaceBefore=0, spaceAfter=6))

    # Meta Box
    meta_data = [
        [
            Paragraph("<b>Course:</b> Distributed NoSQL Databases (MongoDB 7.0)", table_cell),
            Paragraph("<b>Prerequisites:</b> Docker, Docker Compose, 3-Node Replica Set (Ch 8)", table_cell)
        ],
        [
            Paragraph("<b>Target Topic:</b> CAP Theorem, Durability & PACELC", table_cell),
            Paragraph("<b>Demonstration Mode:</b> Docker Hub Containerized Suite", table_cell)
        ],
        [
            Paragraph("<b>Docker Hub Repository:</b> <font color='#1E3A8A'><u>https://hub.docker.com/r/chintan/mongodb-lab09</u></font>", table_cell_bold),
            Paragraph("<b>Demonstration Command:</b> <font name='Courier'>docker run --rm -it chintan/mongodb-lab09:latest</font>", table_cell)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[260, 262])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # Executive Summary
    story.append(Paragraph("Executive Summary & Core Objectives", h1_style))
    story.append(Paragraph(
        "This laboratory provides an empirical, operational proof of the <b>CAP Theorem</b> and <b>PACELC Model</b> "
        "using a production-grade 3-node MongoDB 7.0 replica set. Rather than treating consistency trade-offs as theoretical abstractions, "
        "this work directly measures the concrete millisecond latencies, throughput boundaries, and fault-tolerance mechanics. "
        "The project consists of two core laboratory investigations: "
        "<b>(1) Lab 9.1:</b> Quantifying the exact performance cost of write concerns (<font name='Courier'>w:1</font>, "
        "<font name='Courier'>w:majority</font>, <font name='Courier'>w:all</font>) and disk journaling (<font name='Courier'>j:true</font> vs "
        "<font name='Courier'>j:false</font>) over 1,000 document iterations; and "
        "<b>(2) Lab 9.2:</b> Injecting network partitions using Docker bridge network disconnections to monitor leader step-down, "
        "split-brain prevention, read-only degradation, leader re-election, and asynchronous oplog catch-up.",
        body_style
    ))

    # Section 1
    story.append(Paragraph("Section 1: Lab 9.1 — Measure Write Concern Latency", h1_style))
    story.append(Paragraph(
        "<b>1.1 Experimental Methodology:</b> Write concern is configured per-operation in client application code, "
        "allowing granular trade-offs between durability guarantees and latency. A benchmark script "
        "(<font name='Courier'>lab_01_write_concern_latency.py</font>) was executed against the primary node "
        "(<font name='Courier'>mongo-rs0-1</font>) of the 3-node cluster. For each of the 6 configurations, "
        "<b>1,000 distinct BSON documents</b> were sequentially inserted using <font name='Courier'>insert_one()</font>. "
        "Wall-clock elapsed time, mean latency per write, P50 (median) latency, P99 (99th percentile) latency, and throughput were captured.",
        body_style
    ))

    # Benchmark Table
    bench_data = [
        [
            Paragraph("Write Concern Configuration", table_header),
            Paragraph("Total Time", table_header),
            Paragraph("Avg Latency", table_header),
            Paragraph("P50 (Median)", table_header),
            Paragraph("P99 (Tail)", table_header),
            Paragraph("Throughput", table_header),
            Paragraph("Slowdown vs Base", table_header)
        ],
        [
            Paragraph("<b>w:1, j:false</b>", table_cell),
            Paragraph("2.031 s", table_cell),
            Paragraph("2.03 ms", table_cell),
            Paragraph("1.61 ms", table_cell),
            Paragraph("6.71 ms", table_cell),
            Paragraph("492.5 ops/s", table_cell),
            Paragraph("<b>1.00x (Baseline)</b>", table_cell_bold)
        ],
        [
            Paragraph("<b>w:1, j:true</b>", table_cell),
            Paragraph("5.122 s", table_cell),
            Paragraph("5.12 ms", table_cell),
            Paragraph("4.67 ms", table_cell),
            Paragraph("13.16 ms", table_cell),
            Paragraph("195.2 ops/s", table_cell),
            Paragraph("2.53x", table_cell)
        ],
        [
            Paragraph("<b>w:majority, j:false</b>", table_cell),
            Paragraph("7.005 s", table_cell),
            Paragraph("7.00 ms", table_cell),
            Paragraph("6.32 ms", table_cell),
            Paragraph("15.12 ms", table_cell),
            Paragraph("142.8 ops/s", table_cell),
            Paragraph("3.46x", table_cell)
        ],
        [
            Paragraph("<b>w:majority, j:true</b>", table_cell),
            Paragraph("6.670 s", table_cell),
            Paragraph("6.66 ms", table_cell),
            Paragraph("6.16 ms", table_cell),
            Paragraph("14.73 ms", table_cell),
            Paragraph("149.9 ops/s", table_cell),
            Paragraph("3.29x", table_cell)
        ],
        [
            Paragraph("<b>w:all (w:3), j:false</b>", table_cell),
            Paragraph("4.638 s", table_cell),
            Paragraph("4.63 ms", table_cell),
            Paragraph("4.25 ms", table_cell),
            Paragraph("8.91 ms", table_cell),
            Paragraph("215.6 ops/s", table_cell),
            Paragraph("2.29x", table_cell)
        ],
        [
            Paragraph("<b>w:all (w:3), j:true</b>", table_cell),
            Paragraph("8.075 s", table_cell),
            Paragraph("8.07 ms", table_cell),
            Paragraph("7.31 ms", table_cell),
            Paragraph("19.38 ms", table_cell),
            Paragraph("123.8 ops/s", table_cell),
            Paragraph("<b>3.98x</b>", table_cell_bold)
        ]
    ]

    bench_table = Table(bench_data, colWidths=[110, 60, 60, 64, 64, 74, 90])
    bench_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(bench_table)
    story.append(Spacer(1, 6))

    # Analytical answers
    story.append(Paragraph("<b>1.2 Analytical Findings & Explanation of Differences:</b>", h2_style))
    story.append(Paragraph(
        "• <b>w:1 acknowledgment mechanics:</b> Achieved lowest latency (<b>2.03 ms</b>) and highest throughput (<b>492.5 ops/s</b>). "
        "The primary acknowledges receipt immediately after applying the operation to its in-memory WiredTiger cache, requiring zero inter-node RPCs.<br/>"
        "• <b>w:majority quorum latency:</b> In a 3-node replica set, majority requires 2 members (Primary + 1 Secondary). "
        "The primary holds acknowledgment until at least one secondary replicates the oplog and sends back an acknowledgment. "
        "This adds inter-node network round-trip time (RTT), resulting in a <b>3.3x to 3.5x latency increase</b> (6.66 - 7.00 ms).<br/>"
        "• <b>w:all (w:3) cluster-wide constraint:</b> Requires acknowledgment from all 3 members. Latency is strictly bounded by the slowest "
        "responding node in the replica set, peaking at <b>8.07 ms avg and 19.38 ms P99</b>.<br/>"
        "• <b>Activity 9.1: Does journaling (j:true) add significant latency?</b><br/>"
        "<b>Yes, journaling adds substantial overhead for single-node writes (+152.6% for w:1)</b> because <font name='Courier'>j:true</font> forces a "
        "synchronous <font name='Courier'>fsync</font> to the disk journal (5.12 ms vs 2.03 ms). "
        "Conversely, under <font name='Courier'>w:majority</font>, the journaling cost is overlapped with the network RTT of secondary replication, "
        "making the net impact negligible.",
        body_style
    ))

    # =========================================================================
    # PAGE 2: Section 2 CAP Matrix & Section 3 Lab 9.2 Setup & Phases
    # =========================================================================
    story.append(PageBreak())

    story.append(Paragraph("Section 2: Write Concern & CAP Theorem Positioning Matrix", h1_style))
    story.append(Paragraph(
        "The matrix below classifies MongoDB write concerns according to latency, durability guarantees, "
        "and positioning within the CAP and PACELC distributed systems frameworks (matching textbook slide specifications):",
        body_style
    ))

    cap_matrix = [
        [
            Paragraph("Write Concern", table_header),
            Paragraph("Latency", table_header),
            Paragraph("Durability Guarantee", table_header),
            Paragraph("CAP Classification", table_header),
            Paragraph("Recommended Workloads / Use Cases", table_header)
        ],
        [
            Paragraph("<b>w:1, j:false</b>", table_cell),
            Paragraph("<font color='#059669'><b>Lowest</b><br/>(2.03 ms)</font>", table_cell),
            Paragraph("Data in primary memory cache only. Vulnerable to power failure or crash before periodic checkpoint flush.", table_cell),
            Paragraph("<b>AP-leaning</b><br/>(High Availability, Eventual Consistency)", table_cell),
            Paragraph("High-velocity telemetry, IoT metrics, ephemeral clickstreams, caching layers where occasional packet drops are tolerable.", table_cell)
        ],
        [
            Paragraph("<b>w:1, j:true</b>", table_cell),
            Paragraph("<font color='#D97706'><b>Low</b><br/>(5.12 ms)</font>", table_cell),
            Paragraph("Data persisted to primary disk journal. Survives primary node crash, but vulnerable to rollback on replica failover.", table_cell),
            Paragraph("<b>CP-leaning</b><br/>(Local Durability)", table_cell),
            Paragraph("Standard CRUD applications, user profiles, content management where failover rollback probability is minimal.", table_cell)
        ],
        [
            Paragraph("<b>w:majority, j:true</b>", table_cell),
            Paragraph("<font color='#D97706'><b>Medium</b><br/>(6.66 ms)</font>", table_cell),
            Paragraph("Data committed to majority of nodes (2/3). <b>Zero rollback guarantee</b> upon primary election and failover.", table_cell),
            Paragraph("<b>Strong CP</b><br/>(Consistency & Partition Tolerance)", table_cell_bold),
            Paragraph("Financial transactions, payment gateways, e-commerce orders, critical account balances, inventory reservations.", table_cell)
        ],
        [
            Paragraph("<b>w:all, j:true</b>", table_cell),
            Paragraph("<font color='#DC2626'><b>Highest</b><br/>(8.07 ms)</font>", table_cell),
            Paragraph("Synchronously persisted to disk across all cluster members. Absolute maximum blast-radius protection.", table_cell),
            Paragraph("<b>Strongest CP</b><br/>(Blocks writes if any node fails)", table_cell_bold),
            Paragraph("Regulatory compliance archives, legal audit trails, cryptographic key management, zero-loss tolerance systems.", table_cell)
        ]
    ]

    cap_table = Table(cap_matrix, colWidths=[82, 58, 132, 95, 155])
    cap_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), accent_dark),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(cap_table)
    story.append(Spacer(1, 8))

    # PACELC Note
    story.append(Paragraph(
        "<b>PACELC Theorem Extension:</b> If there is a <b>Partition (P)</b>, how does the system trade off <b>Availability (A)</b> and <b>Consistency (C)</b>? "
        "MongoDB chooses <b>Consistency</b> by refusing writes without a quorum. <b>Else (E)</b>, when the system is running normally without partitions, "
        "how does it trade off <b>Latency (L)</b> and <b>Consistency (C)</b>? MongoDB allows application developers to choose along this axis "
        "using write concerns: <font name='Courier'>w:1</font> chooses <b>Latency (PA/EL)</b>, while <font name='Courier'>w:majority</font> chooses <b>Consistency (PC/EC)</b>.",
        body_style
    ))

    # Section 3
    story.append(Paragraph("Section 3: Lab 9.2 — Simulate Network Partition & Observe Failover", h1_style))
    story.append(Paragraph(
        "<b>3.1 Cluster Architecture & Fault Injection:</b> A 3-node MongoDB replica set was deployed on Docker bridge network "
        "<font name='Courier'>chapter-08_default</font>. Node configurations: <font name='Courier'>mongo-rs0-1</font> (Priority: 2, Primary), "
        "<font name='Courier'>mongo-rs0-2</font> (Priority: 1, Secondary 1), and <font name='Courier'>mongo-rs0-3</font> (Priority: 1, Secondary 2). "
        "All members are data-bearing nodes with voting rights. Partitions were injected via <font name='Courier'>docker network disconnect</font>.",
        body_style
    ))

    story.append(Paragraph("<b>3.2 Step-by-Step Experimental Partition Phases:</b>", h2_style))
    story.append(Paragraph(
        "• <b>Phase 1: Partitioning Secondary 1 (<font name='Courier'>mongo-rs0-2</font>) — Quorum Intact (2 of 3 nodes):</b><br/>"
        "  - Secondary 1 was isolated from the Docker network. The remaining cluster contained <font name='Courier'>mongo-rs0-1</font> and <font name='Courier'>mongo-rs0-3</font>.<br/>"
        "  - <i>Replica Set State:</i> With 2 out of 3 voting members active, strict majority (&gt;50%) was satisfied. Primary maintained leadership.<br/>"
        "  - <i>Write Outcomes:</i> <font name='Courier'>w:1</font> succeeded in <b>3.3 ms</b> (primary acknowledged). "
        "<font name='Courier'>w:majority</font> succeeded in <b>74.6 ms</b> (primary + node 3 acknowledged). "
        "<font name='Courier'>w:all (w:3)</font> <b>timed out</b> after 3000 ms because node 2 was unreachable.<br/>"
        "• <b>Phase 2: Partitioning Secondary 2 (<font name='Courier'>mongo-rs0-3</font>) — Primary Isolation & Loss of Majority:</b><br/>"
        "  - Secondary 2 was disconnected, leaving <font name='Courier'>mongo-rs0-1</font> completely isolated (1 of 3 nodes).<br/>"
        "  - <i>Automatic Step-Down:</i> Heartbeat communication to all secondaries failed. Upon expiry of election timeout, "
        "<b>PRIMARY mongo-rs0-1 stepped down to SECONDARY at 02:41:28.300</b>.<br/>"
        "  - <i>Write Rejection:</i> Attempting <font name='Courier'>w:majority</font> or <font name='Courier'>w:1</font> writes failed immediately with "
        "<font name='Courier'>NotWritablePrimary</font>. The cluster safely degraded to <b>read-only</b>, preventing split-brain writes.<br/>"
        "• <b>Phase 3: Network Healing & Cluster Recovery:</b><br/>"
        "  - Both secondaries were reconnected at 02:41:43. Nodes resumed heartbeats, verified oplog positions, and held an election.<br/>"
        "  - Node <font name='Courier'>mongo-rs0-3</font> was elected Primary, followed by priority takeover re-establishing "
        "<font name='Courier'>mongo-rs0-1</font> (priority 2) as Primary. All nodes caught up oplogs and <font name='Courier'>w:majority</font> writes succeeded.",
        body_style
    ))

    # =========================================================================
    # PAGE 3: Section 3.3 Timeline & Section 3.4 Distributed Consensus Theory
    # =========================================================================
    story.append(PageBreak())

    story.append(Paragraph("<b>3.3 Chronological Timeline of Recorded Events:</b>", h2_style))
    timeline_data = [
        [
            Paragraph("Timestamp", table_header),
            Paragraph("Event Type", table_header),
            Paragraph("Observed Replica Set State & Impact", table_header)
        ],
        [
            Paragraph("02:41:05.243", table_cell),
            Paragraph("STATE", table_cell_bold),
            Paragraph("Initial 3-node cluster verified healthy. Primary: mongo-rs0-1 (Health: 1.0)", table_cell)
        ],
        [
            Paragraph("02:41:05.302", table_cell),
            Paragraph("WRITE_BASELINE", table_cell),
            Paragraph("Baseline writes succeed: w:1 (21.8ms), w:majority (33.4ms), w:all (2.4ms)", table_cell)
        ],
        [
            Paragraph("02:41:05.338", table_cell),
            Paragraph("ACTION", table_cell_bold),
            Paragraph("Secondary 1 (mongo-rs0-2) disconnected via docker network disconnect", table_cell)
        ],
        [
            Paragraph("02:41:12.359", table_cell),
            Paragraph("MEMBER_CHECK", table_cell),
            Paragraph("Cluster retains majority (2/3 nodes). mongo-rs0-1 remains active PRIMARY", table_cell)
        ],
        [
            Paragraph("02:41:12.362", table_cell),
            Paragraph("WRITE_P1", table_cell),
            Paragraph("w:1 succeeds (3.3ms); w:majority succeeds (74.6ms); w:all times out (3000ms)", table_cell)
        ],
        [
            Paragraph("02:41:15.452", table_cell),
            Paragraph("ACTION", table_cell_bold),
            Paragraph("Secondary 2 (mongo-rs0-3) disconnected. Primary mongo-rs0-1 is now isolated", table_cell)
        ],
        [
            Paragraph("<b>02:41:28.300</b>", table_cell_bold),
            Paragraph("<b>STEP_DOWN</b>", table_cell_bold),
            Paragraph("<b>*** PRIMARY mongo-rs0-1 STEPS DOWN TO SECONDARY (Majority Lost) ***</b>", table_cell_bold)
        ],
        [
            Paragraph("02:41:28.303", table_cell),
            Paragraph("WRITE_REJECT", table_cell),
            Paragraph("All writes rejected with NotWritablePrimary. Cluster transitions to READ-ONLY", table_cell)
        ],
        [
            Paragraph("02:41:43.305", table_cell),
            Paragraph("ACTION", table_cell_bold),
            Paragraph("Reconnected mongo-rs0-2 and mongo-rs0-3 to Docker network. Quorum restored", table_cell)
        ],
        [
            Paragraph("02:41:48.406", table_cell),
            Paragraph("ELECTION", table_cell_bold),
            Paragraph("Election held; all 3 nodes report Health: 1.0. Oplog catch-up completes", table_cell)
        ],
        [
            Paragraph("02:42:39.112", table_cell),
            Paragraph("RECOVERY_OK", table_cell),
            Paragraph("Priority takeover re-establishes mongo-rs0-1 as Primary. w:majority writes resume", table_cell)
        ]
    ]

    time_table = Table(timeline_data, colWidths=[78, 86, 358])
    time_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(time_table)
    story.append(Spacer(1, 8))

    # Distributed Consensus Theory
    story.append(Paragraph("<b>3.4 Deep-Dive Analysis: Distributed Consensus & Split-Brain Prevention:</b>", h2_style))
    story.append(Paragraph(
        "<b>Why Did the Primary Step Down at Exactly 02:41:28.300?</b><br/>"
        "MongoDB replica sets utilize a Raft-variant consensus algorithm. The replica set configuration maintains two key timer settings: "
        "<font name='Courier'>heartbeatIntervalMillis: 2000</font> (2 seconds) and <font name='Courier'>electionTimeoutMillis: 10000</font> (10 seconds). "
        "When Secondary 2 was disconnected at 02:41:15.452, the primary continued sending heartbeats. "
        "After failing to reach a majority of voting members for 10 consecutive seconds plus heartbeat interval processing overhead (~12.8 seconds total), "
        "the primary determined it could no longer claim majority leadership. To protect data consistency, it voluntarily relinquished the primary role "
        "and demoted itself to Secondary.<br/><br/>"
        "<b>Mechanics of Split-Brain Prevention:</b><br/>"
        "If an isolated primary continued accepting writes, and the other partitioned partition also elected a primary, the database would fork "
        "into two divergent, conflicting histories (split-brain). Under MongoDB's consensus rules: "
        "<font name='Courier'>Majority = floor(V / 2) + 1</font>, where V is the total number of voting members. "
        "In a 3-node cluster, Majority = 2. A partition of 1 node can never satisfy 2 &gt; 1. Thus, a minority partition can NEVER elect a primary "
        "or sustain primary operations. By refusing writes and stepping down, MongoDB guarantees <b>Single-Primary Consistency</b>.<br/><br/>"
        "<b>Oplog Catch-Up & Rollback Avoidance:</b><br/>"
        "When nodes reconnected at 02:41:43, the secondaries compared their replication coordinates (<font name='Courier'>oplog.rs</font>) with "
        "the primary. Because writes committed during Phase 1 used <font name='Courier'>w:majority</font>, they were already present on Secondary 2. "
        "Secondary 1 fetched missing entries from the oplog and caught up in real time without requiring data rollback.",
        body_style
    ))

    # =========================================================================
    # PAGE 4: Section 4 Docker Hub Guide & Section 5 Conclusion & Sign-Off
    # =========================================================================
    story.append(PageBreak())

    story.append(Paragraph("Section 4: Docker Hub Deployment & Demonstration Guide", h1_style))
    story.append(Paragraph(
        "To fulfill the demonstration submission requirement, all completed Lab-09 tasks, benchmarks, "
        "network partition scripts, and failover monitors have been containerized into a verified Docker image "
        "and published to Docker Hub for grading demonstration.",
        body_style
    ))

    # Grader Commands Box
    demo_box = [
        [
            Paragraph("<b>OFFICIAL EVALUATOR / GRADER DEMONSTRATION INSTRUCTIONS</b>", table_header)
        ],
        [
            Paragraph(
                "<b>Option A: One-Command Automated Master Demonstration (Recommended):</b><br/>"
                "<font name='Courier' color='#1E3A8A'><b>docker run --rm -it chintan/mongodb-lab09:latest demo</b></font><br/>"
                "<i>Automatically executes Lab 9.1 latency benchmark (all 6 write concerns) followed by Lab 9.2 partition simulation.</i><br/><br/>"
                "<b>Option B: Interactive Numbered CLI Menu:</b><br/>"
                "<font name='Courier' color='#1E3A8A'><b>docker run --rm -it chintan/mongodb-lab09:latest</b></font><br/>"
                "<i>Opens interactive terminal menu to individually run Lab 9.1, Lab 9.2, observer monitor, or mongosh.</i><br/><br/>"
                "<b>Option C: Docker Compose Full Multi-Container Cluster Demonstration:</b><br/>"
                "<font name='Courier' color='#1E3A8A'><b>docker compose up --build</b></font><br/>"
                "<i>Orchestrates 3 isolated MongoDB nodes (mongo-rs0-1..3) on a custom bridge network plus runner container.</i>",
                table_cell
            )
        ]
    ]
    demo_table = Table(demo_box, colWidths=[522])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F0FDFA")),
        ('BOX', (0,0), (-1,-1), 1.25, secondary),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 9),
    ]))
    story.append(demo_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>4.2 Student Verification & Docker Hub Push Steps:</b>", h2_style))
    story.append(Paragraph(
        "1. <b>Build Image Locally:</b> <font name='Courier'>docker build -t mongodb-lab09:latest .</font><br/>"
        "2. <b>Tag for Repository:</b> <font name='Courier'>docker tag mongodb-lab09:latest chintan/mongodb-lab09:latest</font><br/>"
        "3. <b>Push to Docker Hub:</b> <font name='Courier'>docker login && docker push chintan/mongodb-lab09:latest</font><br/>"
        "4. <b>Public Docker Hub Repository URL:</b> <font name='Courier'>https://hub.docker.com/r/chintan/mongodb-lab09</font>",
        body_style
    ))

    # Section 5
    story.append(Paragraph("Section 5: Key Theoretical Takeaways & Conclusion", h1_style))
    story.append(Paragraph(
        "1. <b>Consistency vs Latency is a Direct Operational Trade-Off:</b> Acknowledgment by a quorum (<font name='Courier'>w:majority</font>) "
        "imposes a 2.5x to 3.5x latency overhead due to secondary network round-trips. However, this latency premium is the exact price required "
        "to guarantee zero data loss and rollback immunity during failovers.<br/>"
        "2. <b>Journaling Durability is Orthogonal to Cluster Replication:</b> Journaling (<font name='Courier'>j:true</font>) provides local crash durability "
        "against power failures, while write concern (<font name='Courier'>w</font>) provides distributed fault tolerance. "
        "In production, enterprise systems combine both (<font name='Courier'>w:majority, j:true</font>) to achieve Strong Consistency.<br/>"
        "3. <b>CAP Theorem Verified in Real Time:</b> During an active partition, MongoDB strictly prioritizes <b>Consistency over Availability (CP)</b>. "
        "Isolated nodes immediately reject writes and step down, preventing phantom records and preserving cluster integrity.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Sign-Off Box
    sign_data = [
        [
            Paragraph("<b>Submission Status:</b> <font color='#059669'>COMPLETE & VERIFIED</font>", table_cell),
            Paragraph("<b>Evaluation Method:</b> Docker Hub Demonstration Image", table_cell)
        ],
        [
            Paragraph("<b>Artifacts Included:</b> Source Scripts, Dockerfile, Compose, PDF Report", table_cell),
            Paragraph("<b>Docker Hub URL:</b> <u>https://hub.docker.com/r/chintan/mongodb-lab09</u>", table_cell_bold)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 262])
    sign_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(sign_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] 4-Page Report generated successfully: {filename}")


if __name__ == "__main__":
    build_pdf()
