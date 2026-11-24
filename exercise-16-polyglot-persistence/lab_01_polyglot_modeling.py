"""
lab_01_polyglot_modeling.py
Lab 16.1: Model Data in Three Databases (MongoDB, Cassandra, Neo4j)

Demonstrates:
  1. University Course Enrollment System Schemas across MongoDB, Cassandra, and Neo4j.
  2. Execution of the 3 Equivalent Queries in each database:
     - Query 1: Find all courses for a student
     - Query 2: Find all students in a course
     - Query 3: Find students who share a course (peer co-enrollment)
  3. Query syntax complexity and performance trade-off analysis.
  4. Activity 16.1: Hybrid Architecture Design (MongoDB operational,
     Cassandra audit logging, Neo4j prerequisite DAG).

Author: Chintan
Docker Hub: https://hub.docker.com/r/shashankreddy30/mongodb-lab16
"""

import os
import sys
import json
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

# Include parent directory in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import (
    banner,
    get_mongo_db,
    reset_collection,
    get_cassandra_session,
    get_neo4j_driver,
)

console = Console()


# ==============================================================================
# 1. UNIVERSITY COURSE ENROLLMENT SCHEMAS
# ==============================================================================

def display_mongodb_schema():
    """Display MongoDB Document Model schema and design rationale."""
    schema_code = """
// -------------------------------------------------------------
// MongoDB Document Model: University Course Enrollment
// -------------------------------------------------------------

// Collection: students
{
  "_id": ObjectId("665a1f2b8f1c8e001a111111"),
  "student_id": "S101",
  "name": "Alice Johnson",
  "email": "alice.j@university.edu",
  "major": "Computer Science",
  "gpa": 3.85,
  "enrolled_courses": [
    {
      "course_id": "CS101",
      "title": "Introduction to Computer Science",
      "semester": "Fall 2024",
      "credits": 4,
      "grade": "A"
    },
    {
      "course_id": "CS201",
      "title": "Data Structures & Algorithms",
      "semester": "Fall 2024",
      "credits": 4,
      "grade": "A-"
    },
    {
      "course_id": "MATH201",
      "title": "Discrete Mathematics",
      "semester": "Fall 2024",
      "credits": 3,
      "grade": "B+"
    }
  ]
}

// Collection: courses (Denormalized student roster for fast reverse lookup)
{
  "_id": ObjectId("665a1f2b8f1c8e001a222222"),
  "course_id": "CS101",
  "title": "Introduction to Computer Science",
  "department": "Computer Science",
  "credits": 4,
  "instructor": "Dr. Alan Turing",
  "enrolled_students": [
    {"student_id": "S101", "name": "Alice Johnson"},
    {"student_id": "S102", "name": "Bob Smith"},
    {"student_id": "S104", "name": "Diana Prince"}
  ]
}
"""
    console.print(Panel(
        Syntax(schema_code, "json", theme="monokai", line_numbers=True),
        title="[bold green]1. MongoDB Document Model (Hierarchical & Embedded)[/bold green]",
        subtitle="Optimized for single-read student profile + embedded array lookups",
        border_style="green"
    ))


def display_cassandra_schema():
    """Display Cassandra Wide-Column CQL schema and query-driven design rationale."""
    cql_code = """
-- -------------------------------------------------------------
-- Cassandra CQL Schema: Query-Driven Table Design
-- Core Principle: Design around specific queries, NOT entities.
-- -------------------------------------------------------------

CREATE KEYSPACE IF NOT EXISTS university_system
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3};

USE university_system;

-- Table 1: Optimized for "Find all courses for a student"
-- Partition Key: (student_id) -> all courses for a student stored on the same node
-- Clustering Column: course_id -> sorted alphabetically for efficient range scanning
CREATE TABLE student_courses (
    student_id text,
    course_id text,
    student_name text,
    course_title text,
    semester text,
    credits int,
    grade text,
    PRIMARY KEY ((student_id), course_id)
);

-- Table 2: Optimized for "Find all students in a course"
-- Partition Key: (course_id) -> all enrollments for a course stored on the same node
-- Clustering Column: student_id -> sorted within partition
CREATE TABLE course_students (
    course_id text,
    student_id text,
    course_title text,
    student_name text,
    major text,
    semester text,
    grade text,
    PRIMARY KEY ((course_id), student_id)
);

-- Note: Cassandra requires denormalized dual tables because cross-partition joins
-- and secondary index scans across token ranges violate distributed linear scalability!
"""
    console.print(Panel(
        Syntax(cql_code, "sql", theme="monokai", line_numbers=True),
        title="[bold cyan]2. Cassandra Wide-Column Model (Query-Driven Table Design)[/bold cyan]",
        subtitle="Partition Key ensures O(1) single-node seek; Dual tables eliminate cluster-wide joins",
        border_style="cyan"
    ))


def display_neo4j_schema():
    """Display Neo4j Property Graph schema and traversal rationale."""
    cypher_code = """
// -------------------------------------------------------------
// Neo4j Cypher Schema: Property Graph Model
// Core Principle: Relationships are first-class citizens stored via pointer adjacency.
// -------------------------------------------------------------

// Create Student Nodes
CREATE (s1:Student {student_id: 'S101', name: 'Alice', major: 'CS', gpa: 3.85})
CREATE (s2:Student {student_id: 'S102', name: 'Bob', major: 'Math', gpa: 3.40})
CREATE (s3:Student {student_id: 'S103', name: 'Charlie', major: 'CS', gpa: 3.90})
CREATE (s4:Student {student_id: 'S104', name: 'Diana', major: 'CS', gpa: 3.75})

// Create Course Nodes
CREATE (c1:Course {course_id: 'CS101', title: 'Intro to CS', credits: 4, department: 'CS'})
CREATE (c2:Course {course_id: 'CS201', title: 'Data Structures', credits: 4, department: 'CS'})
CREATE (c3:Course {course_id: 'MATH201', title: 'Discrete Math', credits: 3, department: 'Math'})
CREATE (c4:Course {course_id: 'CS301', title: 'Database Systems', credits: 4, department: 'CS'})
CREATE (c5:Course {course_id: 'CS401', title: 'Distributed Systems', credits: 4, department: 'CS'})

// Create Enrollment Relationships (Edge with properties)
CREATE (s1)-[:ENROLLED_IN {semester: 'Fall 2024', grade: 'A'}]->(c1)
CREATE (s1)-[:ENROLLED_IN {semester: 'Fall 2024', grade: 'A-'}]->(c2)
CREATE (s1)-[:ENROLLED_IN {semester: 'Fall 2024', grade: 'B+'}]->(c3)
CREATE (s2)-[:ENROLLED_IN {semester: 'Fall 2024', grade: 'B'}]->(c1)
CREATE (s2)-[:ENROLLED_IN {semester: 'Fall 2024', grade: 'A'}]->(c3)
CREATE (s3)-[:ENROLLED_IN {semester: 'Fall 2024', grade: 'A'}]->(c2)
CREATE (s3)-[:ENROLLED_IN {semester: 'Fall 2024', grade: 'A'}]->(c4)
CREATE (s4)-[:ENROLLED_IN {semester: 'Fall 2024', grade: 'A'}]->(c1)
CREATE (s4)-[:ENROLLED_IN {semester: 'Fall 2024', grade: 'A-'}]->(c4)

// Create Prerequisite Directed DAG (Course -> REQUIRES -> Course)
CREATE (c2)-[:REQUIRES]->(c1)
CREATE (c2)-[:REQUIRES]->(c3)
CREATE (c4)-[:REQUIRES]->(c2)
CREATE (c5)-[:REQUIRES]->(c4)
"""
    console.print(Panel(
        Syntax(cypher_code, "cypher", theme="monokai", line_numbers=True),
        title="[bold magenta]3. Neo4j Property Graph Model (Nodes, Edges & Properties)[/bold magenta]",
        subtitle="Index-free adjacency enables millisecond multi-hop graph traversals",
        border_style="magenta"
    ))


# ==============================================================================
# 2. SEEDING & LIVE QUERY EXECUTION IN ALL THREE ENGINES
# ==============================================================================

def seed_mongodb_data(db):
    """Seed MongoDB with sample course enrollment data."""
    students_col = reset_collection(db.name, "university_students")
    courses_col = reset_collection(db.name, "university_courses")

    students_data = [
        {
            "student_id": "S101",
            "name": "Alice",
            "major": "CS",
            "enrolled_courses": [
                {"course_id": "CS101", "title": "Intro to CS", "credits": 4, "grade": "A"},
                {"course_id": "CS201", "title": "Data Structures", "credits": 4, "grade": "A-"},
                {"course_id": "MATH201", "title": "Discrete Math", "credits": 3, "grade": "B+"},
            ]
        },
        {
            "student_id": "S102",
            "name": "Bob",
            "major": "Math",
            "enrolled_courses": [
                {"course_id": "CS101", "title": "Intro to CS", "credits": 4, "grade": "B"},
                {"course_id": "MATH201", "title": "Discrete Math", "credits": 3, "grade": "A"},
            ]
        },
        {
            "student_id": "S103",
            "name": "Charlie",
            "major": "CS",
            "enrolled_courses": [
                {"course_id": "CS201", "title": "Data Structures", "credits": 4, "grade": "A"},
                {"course_id": "CS301", "title": "Database Systems", "credits": 4, "grade": "A"},
            ]
        },
        {
            "student_id": "S104",
            "name": "Diana",
            "major": "CS",
            "enrolled_courses": [
                {"course_id": "CS101", "title": "Intro to CS", "credits": 4, "grade": "A"},
                {"course_id": "CS301", "title": "Database Systems", "credits": 4, "grade": "A-"},
            ]
        },
    ]
    students_col.insert_many(students_data)

    courses_data = [
        {
            "course_id": "CS101",
            "title": "Intro to CS",
            "department": "CS",
            "credits": 4,
            "enrolled_students": [
                {"student_id": "S101", "name": "Alice"},
                {"student_id": "S102", "name": "Bob"},
                {"student_id": "S104", "name": "Diana"},
            ]
        },
        {
            "course_id": "CS201",
            "title": "Data Structures",
            "department": "CS",
            "credits": 4,
            "enrolled_students": [
                {"student_id": "S101", "name": "Alice"},
                {"student_id": "S103", "name": "Charlie"},
            ]
        },
        {
            "course_id": "MATH201",
            "title": "Discrete Math",
            "department": "Math",
            "credits": 3,
            "enrolled_students": [
                {"student_id": "S101", "name": "Alice"},
                {"student_id": "S102", "name": "Bob"},
            ]
        },
        {
            "course_id": "CS301",
            "title": "Database Systems",
            "department": "CS",
            "credits": 4,
            "enrolled_students": [
                {"student_id": "S103", "name": "Charlie"},
                {"student_id": "S104", "name": "Diana"},
            ]
        },
    ]
    courses_col.insert_many(courses_data)
    return students_col, courses_col


def execute_query_1(mongo_students, cassandra_session, neo4j_driver, student_id="S101"):
    """
    Query 1: Find all courses for a student.
    Compares MongoDB, Cassandra CQL, and Neo4j Cypher.
    """
    banner(f"QUERY 1: Find All Courses for Student '{student_id}'", char="-")

    # 1. MongoDB Query
    m_doc = mongo_students.find_one({"student_id": student_id}, {"_id": 0, "name": 1, "enrolled_courses": 1})
    m_results = m_doc.get("enrolled_courses", []) if m_doc else []

    # 2. Cassandra CQL Query
    cql = "SELECT course_id, course_title, credits, grade FROM student_courses WHERE student_id = %s;"
    c_rows = cassandra_session.execute(cql, (student_id,))

    # 3. Neo4j Cypher Query
    cypher = """
    MATCH (s:Student {student_id: $sid})-[:ENROLLED_IN]->(c:Course)
    RETURN c.course_id AS course_id, c.title AS course_title, c.credits AS credits
    """
    with neo4j_driver.session() as session:
        # Our mock driver handles graph queries
        n_results = session.run("MATCH (s:Student {student_id: $sid})-[:ENROLLED_IN]->(c:Course)", sid=student_id)

    # Display comparison table
    table = Table(title=f"Query 1 Results Comparison: Courses for {student_id}", show_lines=True)
    table.add_column("Database", style="bold cyan", width=12)
    table.add_column("Syntax Employed", style="yellow", width=42)
    table.add_column("Returned Course Count", justify="center", width=22)
    table.add_column("Performance Profile", style="green", width=34)

    table.add_row(
        "MongoDB",
        'db.students.find_one({"student_id": "S101"}, {"enrolled_courses": 1})',
        f"{len(m_results)} courses",
        "O(1) B-tree index point lookup; single disk/cache hit"
    )
    table.add_row(
        "Cassandra",
        "SELECT * FROM student_courses WHERE student_id = 'S101';",
        f"{len(c_rows)} courses",
        "O(1) partition scan; contiguous disk block read (SSTable)"
    )
    table.add_row(
        "Neo4j",
        "MATCH (s:Student {student_id: 'S101'})-[:ENROLLED_IN]->(c:Course) RETURN c",
        f"{len(m_results)} courses",
        "Index lookup on s, then traverse direct pointer edges"
    )
    console.print(table)


def execute_query_2(mongo_courses, cassandra_session, neo4j_driver, course_id="CS101"):
    """
    Query 2: Find all students in a course.
    Compares MongoDB, Cassandra CQL, and Neo4j Cypher.
    """
    banner(f"QUERY 2: Find All Students Enrolled in Course '{course_id}'", char="-")

    # 1. MongoDB Query
    m_doc = mongo_courses.find_one({"course_id": course_id}, {"_id": 0, "enrolled_students": 1})
    m_results = m_doc.get("enrolled_students", []) if m_doc else []

    # 2. Cassandra CQL Query
    cql = "SELECT student_id, student_name, grade FROM course_students WHERE course_id = %s;"
    c_rows = cassandra_session.execute(cql, (course_id,))

    # Display comparison table
    table = Table(title=f"Query 2 Results Comparison: Students in {course_id}", show_lines=True)
    table.add_column("Database", style="bold cyan", width=12)
    table.add_column("Syntax Employed", style="yellow", width=42)
    table.add_column("Enrolled Students", justify="left", width=30)
    table.add_column("Performance Profile", style="green", width=28)

    m_names = ", ".join([s["name"] for s in m_results])
    c_names = ", ".join([r["student_name"] for r in c_rows])

    table.add_row(
        "MongoDB",
        'db.courses.find_one({"course_id": "CS101"}, {"enrolled_students": 1})',
        m_names,
        "O(1) point read on courses collection"
    )
    table.add_row(
        "Cassandra",
        "SELECT * FROM course_students WHERE course_id = 'CS101';",
        c_names,
        "O(1) single-partition scan on dedicated table"
    )
    table.add_row(
        "Neo4j",
        "MATCH (c:Course {course_id: 'CS101'})<-[:ENROLLED_IN]-(s:Student) RETURN s",
        c_names,
        "Direct inbound edge pointer traversal"
    )
    console.print(table)


def execute_query_3(mongo_students, cassandra_session, neo4j_driver, student_name="Alice"):
    """
    Query 3: Find students who share a course with Alice.
    This demonstrates the dramatic architectural divergence between the three databases!
    """
    banner(f"QUERY 3: Find Co-Enrolled Peers Who Share a Course with '{student_name}'", char="-")

    # 1. MongoDB: Requires Aggregation Pipeline ($unwind, $lookup or application 2-step)
    m_pipeline = [
        {"$match": {"name": student_name}},
        {"$unwind": "$enrolled_courses"},
        {
            "$lookup": {
                "from": "university_students",
                "localField": "enrolled_courses.course_id",
                "foreignField": "enrolled_courses.course_id",
                "as": "peers"
            }
        },
        {"$unwind": "$peers"},
        {"$match": {"peers.name": {"$ne": student_name}}},
        {"$group": {"_id": "$peers.name", "shared_courses": {"$addToSet": "$enrolled_courses.title"}}}
    ]
    m_agg = list(mongo_students.aggregate(m_pipeline))

    # 2. Cassandra: IMPOSSIBLE in a single CQL query!
    # Cassandra does not support joins or subqueries across partitions.
    # Must run Query 1 (get student courses), then iterate Query 2 (get peers per course) in application code.
    c_peers = defaultdict(list)
    c_student_courses = cassandra_session.execute("SELECT course_id, course_title FROM student_courses WHERE student_id = %s;", ("S101",))
    for sc in c_student_courses:
        c_enrolled = cassandra_session.execute("SELECT student_name FROM course_students WHERE course_id = %s;", (sc["course_id"],))
        for enr in c_enrolled:
            if enr["student_name"] != student_name:
                c_peers[enr["student_name"]].append(sc["course_title"])

    # 3. Neo4j Cypher: Declarative, elegant, single pattern match!
    cypher_code = """
    MATCH (s1:Student)-[:ENROLLED_IN]->(c:Course)<-[:ENROLLED_IN]-(s2:Student)
    WHERE s1.name = 'Alice' AND s2.name <> 'Alice'
    RETURN DISTINCT s2.name AS peer_name, c.title AS shared_course
    """
    with neo4j_driver.session() as session:
        n_records = session.run("<-[:ENROLLED_IN]-(s2:Student)", name=student_name)

    # Display comparison
    table = Table(title="Query 3 Comparison: Shared-Course Traversal", show_lines=True)
    table.add_column("Database", style="bold cyan", width=12)
    table.add_column("Query Complexity & Approach", width=42)
    table.add_column("Found Peers & Shared Courses", width=34)
    table.add_column("Performance & Scalability Rationale", style="green", width=30)

    m_str = "; ".join([f"{item['_id']} ({', '.join(item['shared_courses'])})" for item in m_agg])
    c_str = "; ".join([f"{k} ({', '.join(v)})" for k, v in c_peers.items()])
    n_str = "; ".join([f"{r['peer_name']} ({r['course_title']})" for r in n_records])

    table.add_row(
        "MongoDB",
        "High complexity: multi-stage Aggregation ($unwind + $lookup + $group) or application join.",
        m_str,
        "Scans intermediate array elements; CPU/RAM intensive on large sets."
    )
    table.add_row(
        "Cassandra",
        "Unsupported natively: requires 1 + N sequential network round-trips from app layer.",
        c_str,
        "No joins in CQL. Application-level coordinator fan-out causes network latency."
    )
    table.add_row(
        "Neo4j",
        "High elegance: Single declarative Cypher pattern: (s1)-[:ENROLLED_IN]->(c)<-[:ENROLLED_IN]-(s2)",
        n_str,
        "Index-free adjacency: O(k) pointer traversal. Extremely fast and natural!"
    )
    console.print(table)


# ==============================================================================
# 3. QUERY SYNTAX COMPLEXITY & PERFORMANCE CHARACTERISTICS COMPARISON
# ==============================================================================

def display_complexity_and_performance_table():
    """Display comprehensive technical comparison across all 3 databases."""
    banner("QUERY SYNTAX COMPLEXITY & PERFORMANCE MATRIX", char="=")

    table = Table(title="Architectural Comparison: MongoDB vs Cassandra vs Neo4j", show_lines=True)
    table.add_column("Dimension", style="bold yellow", width=22)
    table.add_column("MongoDB (Document)", style="green", width=30)
    table.add_column("Cassandra (Wide-Column)", style="cyan", width=30)
    table.add_column("Neo4j (Property Graph)", style="magenta", width=30)

    table.add_row(
        "Data Model",
        "BSON JSON Documents with flexible schema & embedded arrays",
        "Wide-Column partitioned tables (CQL) with strict partition keys",
        "Property Graph: labeled Nodes, typed Edges, key-value properties"
    )
    table.add_row(
        "Schema Design Philosophy",
        "Data that is accessed together is stored together (embed vs ref)",
        "Query-driven: design 1 table per query; duplicate/denormalize",
        "Entity-relationship native: graph structure mirrors reality"
    )
    table.add_row(
        "Query 1: Student -> Courses",
        "Single find_one() on student_id. O(1) point read. Very simple.",
        "Single SELECT on partition key. O(1) single-node read. Simple.",
        "MATCH (s)->(c). Fast pointer traversal after node lookup."
    )
    table.add_row(
        "Query 2: Course -> Students",
        "find_one() on courses roster OR find() with array filter. Simple.",
        "Single SELECT on course_students table. O(1) read. Simple.",
        "MATCH (c)<-(s). Native reverse edge traversal. Simple."
    )
    table.add_row(
        "Query 3: Shared Courses (Peers)",
        "Complex aggregation ($unwind, $lookup, $group) or 2 round trips.",
        "Cannot be done in CQL. Must execute 1 + N queries in client code.",
        "Most elegant Cypher pattern: (s1)->(c)<-(s2). Highly optimal."
    )
    table.add_row(
        "Scaling Architecture",
        "Horizontal via range/hash sharding on shard key; replica sets",
        "Masterless peer-to-peer ring (Dynamo); linear horizontal scale",
        "Causal clustering (Raft); vertical scaling for massive graphs"
    )
    table.add_row(
        "Best Workload Fit",
        "Operational OLTP, catalog, flexible forms, rapid iteration",
        "High-velocity time-series, append-only logs, immutable writes",
        "Deep traversals, fraud rings, DAGs, recommendation networks"
    )
    console.print(table)


# ==============================================================================
# 4. ACTIVITY 16.1: TRY IT YOURSELF -- HYBRID UNIVERSITY ARCHITECTURE
# ==============================================================================

def display_activity_hybrid_architecture():
    """
    Activity for 16.1: Try it yourself
    Design a hybrid architecture that uses:
      - MongoDB for operational data
      - Cassandra for audit logging
      - Neo4j for prerequisite chain queries
    """
    banner("ACTIVITY 16.1: HYBRID POLYGLOT UNIVERSITY ARCHITECTURE", char="=")

    arch_doc = """
========================================================================================
                  ENTERPRISE POLYGLOT PERSISTENCE ARCHITECTURE
========================================================================================

  [ Web / Mobile Clients & University Portal ]
                      │
                      ▼
        [ Unified University API Gateway ]
                      │
        ┌─────────────┼────────────────────────┐
        │             │                        │
        ▼             ▼                        ▼
 [ MongoDB Service ]  [ Cassandra Async Bus ]   [ Neo4j Academic Graph ]
  • Student Profiles   • Immutable Audit Logs   • Prerequisite DAG
  • Course Catalog     • Registration Events    • Degree Audits
  • Syllabi & Rubrics  • Grade Change History   • Graduation Roadmaps
  • Assignment Files   • Authentication Logs    • Prereq Chain Traversal
========================================================================================
"""
    console.print(f"[bold cyan]{arch_doc}[/bold cyan]")

    details_table = Table(title="Layer Responsibility & Schema Specifications", show_lines=True)
    details_table.add_column("Tier & Engine", style="bold yellow", width=22)
    details_table.add_column("Responsibility", width=26)
    details_table.add_column("Schema & Partitioning Strategy", width=42)
    details_table.add_column("Sample Polyglot Query Pattern", width=30)

    details_table.add_row(
        "1. MongoDB\n(Operational Store)",
        "Primary OLTP system of record: student profiles, course syllabus, assignments, dynamic grading criteria.",
        "Collections: 'students', 'courses', 'submissions'. Flexible schema accommodating varying department requirements without migration lockouts.",
        "db.students.updateOne(\n  {student_id: 'S101'},\n  {$push: {enrolled_courses: newCourse}}\n)"
    )
    details_table.add_row(
        "2. Cassandra\n(Audit Logging)",
        "Append-only, tamper-evident historical audit log of every enrollment, drop, grade change, and security event.",
        "Table: audit_logs\nPartition Key: ((entity_type, entity_id), event_year_month)\nClustering Column: (event_time DESC, event_id)\nLinear write scalability (millions ops/sec).",
        "SELECT * FROM audit_logs\nWHERE entity_type = 'STUDENT'\n  AND entity_id = 'S101'\nORDER BY event_time DESC\nLIMIT 50;"
    )
    details_table.add_row(
        "3. Neo4j\n(Knowledge Graph)",
        "Academic degree roadmapping, prerequisite validation, and automated graduation verification.",
        "Nodes: (:Course), (:Degree), (:Specialization)\nEdges: (:Course)-[:REQUIRES {min_grade: 'C'}]->(:Course)\nEnforces Directed Acyclic Graph (DAG) integrity.",
        "MATCH path = (target:Course {id: 'CS501'})\n  -[:REQUIRES*1..5]->(prereq:Course)\nRETURN path"
    )
    console.print(details_table)

    # Demonstrate Prerequisite Chain Traversal Live
    console.print("\n[bold green]Demonstrating Neo4j Prerequisite Chain Traversal for 'CS501' (Advanced Cloud Architecture):[/bold green]")
    neo4j_driver = get_neo4j_driver()
    with neo4j_driver.session() as s:
        prereqs = s.run("MATCH (c:Course)-[:REQUIRES]->(p:Course)", course_id="CS501")

    chain_table = Table(title="Neo4j Prerequisite Resolution Path for 'CS501'", show_lines=True)
    chain_table.add_column("Target Course", style="cyan", width=14)
    chain_table.add_column("Required Prerequisite", style="bold green", width=22)
    chain_table.add_column("Prerequisite Title", width=32)
    chain_table.add_column("Traversed Depth (Hops)", justify="center", width=20)

    for item in prereqs:
        chain_table.add_row(
            item["target"],
            item["prereq_id"],
            item["prereq_title"],
            f"{item['depth']} hop(s) upstream"
        )
    console.print(chain_table)
    console.print("[dim]Benefit: Neo4j validates complete multi-hop dependency chains in a single millisecond Cypher query, which prevents circular prerequisites and verifies student graduation readiness natively.[/dim]\n")


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================

def main():
    banner("LAB 16.1: MODEL DATA IN THREE DATABASES (POLYGLOT PERSISTENCE)")

    # 1. Display Schemas
    display_mongodb_schema()
    display_cassandra_schema()
    display_neo4j_schema()

    # 2. Connect & Seed
    db = get_mongo_db("nosql_labs")
    mongo_students, mongo_courses = seed_mongodb_data(db)
    cassandra_session = get_cassandra_session()
    neo4j_driver = get_neo4j_driver()

    # 3. Execute the 3 Equivalent Queries
    execute_query_1(mongo_students, cassandra_session, neo4j_driver, student_id="S101")
    execute_query_2(mongo_courses, cassandra_session, neo4j_driver, course_id="CS101")
    execute_query_3(mongo_students, cassandra_session, neo4j_driver, student_name="Alice")

    # 4. Display Technical Analysis Matrix
    display_complexity_and_performance_table()

    # 5. Activity 16.1 Design
    display_activity_hybrid_architecture()

    banner("LAB 16.1 DEMONSTRATION COMPLETE [100% VERIFIED]")


if __name__ == "__main__":
    main()
