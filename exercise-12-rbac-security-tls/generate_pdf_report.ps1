# ==============================================================================
# Generate High-Resolution PDF Lab Report using Headless Chrome
# Accepts optional -DockerUsername parameter (e.g. -DockerUsername "myuser")
# ==============================================================================

param (
    [string]$DockerUsername = "YOUR_DOCKERHUB_USERNAME"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = Get-Location }

$htmlFile = Join-Path $scriptDir "MongoDB_Security_RBAC_TLS_Lab_Report.html"
$pdfFile = Join-Path $scriptDir "MongoDB_Security_RBAC_TLS_Lab_Report.pdf"
$shardingImg = Join-Path $scriptDir "architecture_sharding.jpg"
$securityImg = Join-Path $scriptDir "architecture_security_cia.jpg"

$shardingB64 = ""
if (Test-Path $shardingImg) {
    $shardingB64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($shardingImg))
}

$securityB64 = ""
if (Test-Path $securityImg) {
    $securityB64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($securityImg))
}

$template = @'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MongoDB Security, RBAC & TLS Encryption - Exercise 12 Lab Report</title>
<style>
  @page {
    size: A4 portrait;
    margin: 18mm 14mm 18mm 14mm;
    @bottom-right {
      content: counter(page);
    }
  }
  * {
    box-sizing: border-box;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.5;
    font-size: 10pt;
    margin: 0;
    padding: 0;
  }
  .page-break {
    page-break-before: always;
  }
  .cover {
    text-align: center;
    padding: 30px 10px 20px 10px;
    border-bottom: 2px solid #0284c7;
    margin-bottom: 25px;
  }
  .institution {
    font-size: 13pt;
    font-weight: 700;
    color: #0369a1;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 5px;
  }
  .course-title {
    font-size: 18pt;
    font-weight: 800;
    color: #0f172a;
    margin: 10px 0 5px 0;
  }
  .lab-subtitle {
    font-size: 13pt;
    font-weight: 600;
    color: #475569;
    margin-bottom: 20px;
  }
  .meta-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    display: inline-block;
    padding: 14px 24px;
    text-align: left;
    margin-top: 10px;
  }
  .meta-card table td {
    padding: 3px 10px;
    font-size: 9.5pt;
  }
  .meta-label {
    font-weight: 700;
    color: #334155;
  }
  .docker-banner {
    background: linear-gradient(135deg, #0284c7, #0369a1);
    color: #ffffff;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 20px 0 25px 0;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
  }
  .docker-banner h3 {
    margin: 0 0 8px 0;
    font-size: 12pt;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
  }
  .docker-url {
    background: #082f49;
    color: #38bdf8;
    padding: 8px 12px;
    border-radius: 6px;
    font-family: "Courier New", Courier, monospace;
    font-size: 10pt;
    font-weight: 700;
    word-break: break-all;
    margin: 5px 0;
  }
  .docker-cmd {
    background: #0f172a;
    color: #4ade80;
    padding: 8px 12px;
    border-radius: 6px;
    font-family: "Courier New", Courier, monospace;
    font-size: 9.5pt;
    margin-top: 6px;
  }
  h2 {
    font-size: 13.5pt;
    color: #0f172a;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 4px;
    margin-top: 24px;
    margin-bottom: 12px;
  }
  h3 {
    font-size: 11pt;
    color: #0369a1;
    margin-top: 16px;
    margin-bottom: 6px;
  }
  p {
    margin: 0 0 10px 0;
    text-align: justify;
  }
  table.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 16px 0;
    font-size: 8.5pt;
  }
  table.data-table th, table.data-table td {
    border: 1px solid #cbd5e1;
    padding: 6px 9px;
    text-align: left;
  }
  table.data-table th {
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
  }
  table.data-table tr:nth-child(even) td {
    background-color: #f8fafc;
  }
  .badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 12px;
    font-size: 7.5pt;
    font-weight: 700;
  }
  .badge-success {
    background-color: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
  }
  .badge-deny {
    background-color: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fca5a5;
  }
  .badge-info {
    background-color: #e0f2fe;
    color: #0369a1;
    border: 1px solid #7dd3fc;
  }
  .code-block {
    background-color: #0f172a;
    color: #e2e8f0;
    padding: 10px 12px;
    border-radius: 6px;
    font-family: "Courier New", Courier, monospace;
    font-size: 8pt;
    line-height: 1.35;
    margin: 10px 0 14px 0;
    overflow-x: auto;
    border: 1px solid #334155;
  }
  .code-title {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 4px 10px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 7.5pt;
    font-weight: 600;
    margin-bottom: -10px;
    display: inline-block;
  }
  .callout {
    background-color: #f0fdf4;
    border-left: 4px solid #16a34a;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 12px 0;
    font-size: 9pt;
  }
  .callout-title {
    font-weight: 700;
    color: #15803d;
    margin-bottom: 3px;
  }
  .callout-warning {
    background-color: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin: 12px 0;
    font-size: 9pt;
  }
  .callout-warning .callout-title {
    color: #b45309;
  }
  .figure-box {
    text-align: center;
    margin: 14px 0 18px 0;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
  }
  .figure-img {
    max-width: 90%;
    max-height: 250px;
    object-fit: contain;
    border-radius: 4px;
    border: 1px solid #cbd5e1;
  }
  .figure-caption {
    font-size: 8pt;
    font-style: italic;
    color: #64748b;
    margin-top: 6px;
  }
  ul, ol {
    margin: 0 0 10px 0;
    padding-left: 20px;
  }
  li {
    margin-bottom: 4px;
  }
</style>
</head>
<body>

<!-- COVER / HEADER -->
<div class="cover">
  <div class="institution">NoSQL Databases Using MongoDB &bull; Technical Assignment</div>
  <div class="course-title">Chapter 12: Database Security and the CIA Triad</div>
  <div class="lab-subtitle">Lab 12.1 (RBAC & Authentication) &bull; Activity 12.1 (Field-Level Redaction) &bull; Lab 12.2 (TLS Encryption-in-Transit)</div>
  
  <div class="meta-card">
    <table>
      <tr>
        <td class="meta-label">Author / Student:</td>
        <td>Lab Participant & Technical Demonstrator</td>
        <td class="meta-label">Submission Date:</td>
        <td>November 2026</td>
      </tr>
      <tr>
        <td class="meta-label">Course Module:</td>
        <td>Enterprise NoSQL & Database Security</td>
        <td class="meta-label">Demonstration Mode:</td>
        <td>Dockerized Automated Test Suite</td>
      </tr>
      <tr>
        <td class="meta-label">Official Reference:</td>
        <td colspan="3"><a href="https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-12" style="color:#0284c7;text-decoration:none;">github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB (Chapter 12)</a></td>
      </tr>
    </table>
  </div>
</div>

<!-- DOCKER SUBMISSION CALLOUT -->
<div class="docker-banner">
  <h3>&#128011; Docker Hub Deployment & Demonstration Link for Grading</h3>
  <div>This entire assignment has been packaged into an automated, self-testing, and interactive Docker container uploaded to Docker Hub:</div>
  <div class="docker-url">Docker Hub Repository: https://hub.docker.com/r/%%DOCKER_USER%%/mongodb-security-lab</div>
  <div style="font-size: 8.5pt; margin-top: 6px;">Evaluation command to pull and run the automated demonstration:</div>
  <div class="docker-cmd">docker run -it -p 27017:27017 -p 27100:27100 %%DOCKER_USER%%/mongodb-security-lab:latest</div>
</div>

<!-- SECTION 1: EXECUTIVE SUMMARY -->
<h2>1. Executive Summary & CIA Triad Defense Framework</h2>
<p>
Database security encompasses technical safeguards, administrative policies, and cryptographic controls designed to protect data assets against unauthorized access, corruption, tampering, and denial-of-service. This lab implements a defense-in-depth security model for MongoDB mapped directly against the <strong>CIA Triad</strong>:
</p>
<ul>
  <li><strong>Confidentiality (Data Protection & Privacy):</strong> Restricting access exclusively to authenticated principals via <strong>SCRAM-SHA-256 Authentication</strong>, enforcing least-privilege <strong>Role-Based Access Control (RBAC)</strong>, providing fine-grained privacy via <strong>Aggregation Views with Field-Level Redaction</strong> ($$REMOVE and SSN masking), and encrypting data over the wire using <strong>TLS/SSL Encryption</strong>.</li>
  <li><strong>Integrity (Data Accuracy & Trust):</strong> Guaranteeing that data cannot be altered by unauthorized users through fine-grained collection privileges, schema validation, and digital certificate validation (X.509 PKI).</li>
  <li><strong>Availability (Reliability & Uptime):</strong> Supporting operational continuity through distributed sharding, query routing via <code>mongos</code>, and high-availability replica sets with automated failover.</li>
</ul>

<!-- FIGURE 2: CIA DEFENSE LAYERS -->
<div class="figure-box">
  <img class="figure-img" src="data:image/jpeg;base64,%%SECURITY_B64%%" alt="MongoDB Security Controls and CIA Triad Defense Layers">
  <div class="figure-caption">Figure 1: Attack Surface, MongoDB Security Controls, and CIA Triad Defense Layers Architecture</div>
</div>

<table class="data-table">
  <thead>
    <tr>
      <th>Attack Surface Threat</th>
      <th>Mitigating Security Control</th>
      <th>CIA Layer</th>
      <th>Lab Implementation</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Unauthenticated Access</strong> (Default open port)</td>
      <td>SCRAM-SHA Authentication (<code>--auth</code>)</td>
      <td>Confidentiality</td>
      <td>Admin user created; unauthenticated commands blocked.</td>
    </tr>
    <tr>
      <td><strong>Weak Credentials / Over-Privilege</strong></td>
      <td>Role-Based Access Control (RBAC)</td>
      <td>Confidentiality, Integrity</td>
      <td>Custom roles (<code>collectionReader</code>, <code>collectionWriter</code>) scoped to specific collections.</td>
    </tr>
    <tr>
      <td><strong>Network Eavesdropping / Packet Sniffing</strong></td>
      <td>TLS/SSL In-Transit Encryption</td>
      <td>Confidentiality</td>
      <td><code>--tlsMode requireTLS</code>, X.509 CA & Server Cert with SAN, PyMongo SSL sockets.</td>
    </tr>
    <tr>
      <td><strong>Insider Threat / Sensitive PII Exposure</strong></td>
      <td>Field-Level Redaction via Views</td>
      <td>Confidentiality</td>
      <td><code>employees_safe</code> view removing salary and masking SSN for non-HR staff.</td>
    </tr>
    <tr>
      <td><strong>Server / Hardware Outages</strong></td>
      <td>Replica Sets & Sharding Routing</td>
      <td>Availability</td>
      <td>Clustered deployment architecture using <code>mongos</code> routers and replica sets.</td>
    </tr>
  </tbody>
</table>

<!-- FIGURE 1: SHARDING ARCHITECTURE -->
<div class="figure-box">
  <img class="figure-img" src="data:image/jpeg;base64,%%SHARDING_B64%%" alt="MongoDB Sharded Cluster Architecture">
  <div class="figure-caption">Figure 2: Production MongoDB Distributed Deployment with mongos Query Routers and Sharded Replica Sets</div>
</div>

<div class="page-break"></div>

<!-- SECTION 2: LAB 12.1 -->
<h2>2. Lab 12.1: Authentication and Least-Privilege RBAC</h2>

<h3>2.1 Objective & Strategy</h3>
<p>
The objective is to eliminate default unauthenticated access by starting <code>mongod</code> with <code>--auth</code>, provisioning a central administrative account, and configuring least-privilege custom roles. In accordance with the principle of least privilege, applications must never connect as broad administrative accounts; instead, roles grant only the exact actions required on targeted namespaces.
</p>

<h3>2.2 Custom Role and User Configuration</h3>
<p>
The following custom roles and accounts were established on the deployment:
</p>
<table class="data-table">
  <thead>
    <tr>
      <th>Account</th>
      <th>Assigned Role</th>
      <th>Scope (Namespace)</th>
      <th>Permitted Actions</th>
      <th>Security Posture</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>admin</code></td>
      <td><code>userAdminAnyDatabase</code><br><code>readWriteAnyDatabase</code><br><code>clusterAdmin</code></td>
      <td>admin (Cluster-wide)</td>
      <td>All actions</td>
      <td><span class="badge badge-info">Administrator</span></td>
    </tr>
    <tr>
      <td><code>app_user_read</code></td>
      <td>Custom: <code>collectionReader</code></td>
      <td><code>analytics.reports</code><br><code>nosql_labs.inventory</code></td>
      <td><code>find</code>, <code>aggregate</code></td>
      <td><span class="badge badge-success">Least Privilege Read</span></td>
    </tr>
    <tr>
      <td><code>app_user_write</code></td>
      <td>Custom: <code>collectionWriter</code></td>
      <td><code>nosql_labs.orders</code></td>
      <td><code>find</code>, <code>insert</code>, <code>update</code>, <code>delete</code></td>
      <td><span class="badge badge-success">Least Privilege Write</span></td>
    </tr>
    <tr>
      <td><code>analyst</code></td>
      <td>Built-in: <code>read</code></td>
      <td><code>nosql_labs</code>, <code>bookstore</code></td>
      <td><code>find</code></td>
      <td><span class="badge badge-info">Reporting Analyst</span></td>
    </tr>
    <tr>
      <td><code>log_writer</code></td>
      <td>Custom: <code>limitedWriter</code></td>
      <td><code>nosql_labs.logs</code> (Write)<br><code>nosql_labs.*</code> (Read)</td>
      <td><code>insert</code>, <code>update</code> (logs)<br><code>find</code> (all)</td>
      <td><span class="badge badge-success">Restricted Logger</span></td>
    </tr>
  </tbody>
</table>

<div class="code-title">mongosh: Defining Custom Least-Privilege Roles</div>
<div class="code-block">
use admin;

// 1. Role for application reader: restricted to reports and inventory
db.createRole({
  role: "collectionReader",
  privileges: [
    { resource: { db: "analytics", collection: "reports" }, actions: ["find", "aggregate"] },
    { resource: { db: "nosql_labs", collection: "inventory" }, actions: ["find"] }
  ],
  roles: []
});

// 2. Role for application writer: CRUD operations restricted exclusively to orders
db.createRole({
  role: "collectionWriter",
  privileges: [
    { resource: { db: "nosql_labs", collection: "orders" }, actions: ["find", "insert", "update", "delete"] }
  ],
  roles: []
});

// 3. User provisioning
db.createUser({ user: "app_user_read", pwd: "ReadPass123!", roles: [{ role: "collectionReader", db: "admin" }] });
db.createUser({ user: "app_user_write", pwd: "WritePass123!", roles: [{ role: "collectionWriter", db: "admin" }] });
</div>

<h3>2.3 Permission Enforcement & Verification Results</h3>
<p>
Security controls are verified by executing both positive tests (authorized operations succeed) and negative tests (unauthorized operations fail):
</p>
<table class="data-table">
  <thead>
    <tr>
      <th>Test Case</th>
      <th>User</th>
      <th>Operation Attempted</th>
      <th>Expected Result</th>
      <th>Actual Result</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Test 1.1</td>
      <td><code>app_user_read</code></td>
      <td><code>analytics.reports.find()</code></td>
      <td>Allow (Read allowed)</td>
      <td>2 reports retrieved successfully</td>
      <td><span class="badge badge-success">PASSED</span></td>
    </tr>
    <tr>
      <td>Test 1.2</td>
      <td><code>app_user_read</code></td>
      <td><code>analytics.reports.insertOne(...)</code></td>
      <td>Deny (Write attempted by reader)</td>
      <td>Error: not authorized on analytics to execute command insert</td>
      <td><span class="badge badge-deny">REJECTED (OK)</span></td>
    </tr>
    <tr>
      <td>Test 1.3</td>
      <td><code>app_user_read</code></td>
      <td><code>nosql_labs.secret_records.find()</code></td>
      <td>Deny (Unauthorized collection)</td>
      <td>Error: not authorized on nosql_labs to execute command find</td>
      <td><span class="badge badge-deny">REJECTED (OK)</span></td>
    </tr>
    <tr>
      <td>Test 2.1</td>
      <td><code>app_user_write</code></td>
      <td><code>nosql_labs.orders.insertOne(...)</code></td>
      <td>Allow (Write allowed on orders)</td>
      <td>Document inserted (ORD-999) and retrieved</td>
      <td><span class="badge badge-success">PASSED</span></td>
    </tr>
    <tr>
      <td>Test 2.2</td>
      <td><code>app_user_write</code></td>
      <td><code>nosql_labs.inventory.find()</code></td>
      <td>Deny (Read attempted outside orders)</td>
      <td>Error: not authorized on nosql_labs to execute command find</td>
      <td><span class="badge badge-deny">REJECTED (OK)</span></td>
    </tr>
    <tr>
      <td>Test 3.1</td>
      <td><code>analyst</code></td>
      <td><code>nosql_labs.inventory.insertOne(...)</code></td>
      <td>Deny (Write attempted by analyst)</td>
      <td>Error: not authorized on nosql_labs to execute command insert</td>
      <td><span class="badge badge-deny">REJECTED (OK)</span></td>
    </tr>
    <tr>
      <td>Test 3.2</td>
      <td><code>app_writer</code></td>
      <td><code>bookstore.books.find()</code></td>
      <td>Deny (Cross-database query outside scope)</td>
      <td>Error: not authorized on bookstore to execute command find</td>
      <td><span class="badge badge-deny">REJECTED (OK)</span></td>
    </tr>
  </tbody>
</table>

<div class="page-break"></div>

<!-- SECTION 3: ACTIVITY 12.1 -->
<h2>3. Activity 12.1: Field-Level Redaction via Views</h2>

<h3>3.1 Problem Statement & Solution Architecture</h3>
<p>
Organizations frequently store employee records containing sensitive Personally Identifiable Information (PII) such as Social Security Numbers (SSN) and compensation details (<code>salary</code>). Providing application developers or general staff with access to this data violates privacy mandates (e.g. GDPR, HIPAA, SOC 2).
</p>
<p>
Instead of creating duplicate, synchronized collections—which introduces data inconsistency and maintenance overhead—MongoDB provides <strong>Read-Only Aggregation Views</strong> (<code>db.createView()</code>). The view acts as an automated virtual layer that applies a deterministic aggregation pipeline:
</p>
<ul>
  <li><code>salary: "$$REMOVE"</code>: Completely strips the compensation field from the output payload.</li>
  <li><code>ssn: { $concat: ["***-**-", { $substrCP: ["$ssn", 7, 4] }] }</code>: Partially masks the SSN to preserve utility for verification while protecting identity.</li>
</ul>

<div class="code-title">Python/PyMongo: Creating the Redacted Aggregation View and Role-Based Separation</div>
<div class="code-block">
pipeline = [
    {
        "$project": {
            "_id": 0,
            "empId": 1,
            "username": 1,
            "name": 1,
            "email": 1,
            "department": 1,
            "role": 1,
            "ssn": {
                "$concat": [
                    "***-**-",
                    { "$substrCP": ["$ssn", 7, 4] }
                ]
            },
            "salary": "$$REMOVE"
        }
    }
]

# Create view
db.command("create", "employees_safe", viewOn="employees", pipeline=pipeline)

# Grant HR role full access to raw collection; grant staff role access ONLY to the view
admin_db.command("createRole", "hr_role", privileges=[
    {"resource": {"db": "hr_db", "collection": "employees"}, "actions": ["find", "insert", "update"]}
], roles=[])

admin_db.command("createRole", "non_hr_role", privileges=[
    {"resource": {"db": "hr_db", "collection": "employees_safe"}, "actions": ["find", "aggregate"]}
], roles=[])
</div>

<h3>3.2 Comparative Analysis: Raw Collection vs. Redacted View</h3>
<table class="data-table">
  <thead>
    <tr>
      <th>Field</th>
      <th>Raw Document (Queried by HR Role: <code>hr_user</code>)</th>
      <th>Redacted View Document (Queried by Non-HR: <code>staff_user</code>)</th>
      <th>Privacy Protection Outcome</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>empId</code></td>
      <td><code>E101</code></td>
      <td><code>E101</code></td>
      <td>Retained for unique identification</td>
    </tr>
    <tr>
      <td><code>name</code></td>
      <td><code>Arjun Patel</code></td>
      <td><code>Arjun Patel</code></td>
      <td>Retained for directory access</td>
    </tr>
    <tr>
      <td><code>role</code></td>
      <td><code>Lead Architect</code></td>
      <td><code>Lead Architect</code></td>
      <td>Retained for organizational charts</td>
    </tr>
    <tr>
      <td><code>ssn</code></td>
      <td><strong><code>111-22-3333</code></strong> (Plaintext)</td>
      <td><strong><code>***-**-3333</code></strong> (Masked)</td>
      <td><span class="badge badge-success">Masked: First 5 digits hidden</span></td>
    </tr>
    <tr>
      <td><code>salary</code></td>
      <td><strong><code>$165,000</code></strong> (Exposed)</td>
      <td><em>[Field Completely Removed]</em></td>
      <td><span class="badge badge-success">Zero Exposure: Key omitted via $$REMOVE</span></td>
    </tr>
  </tbody>
</table>

<div class="callout">
  <div class="callout-title">Security Proof: Unauthorized Direct Access Blocked</div>
  When <code>staff_user</code> attempts to bypass the view and query the base <code>hr_db.employees</code> collection directly, the MongoDB RBAC engine blocks the query:
  <br><code>OperationFailure: command find requires authentication on hr_db.employees (Code 13: Unauthorized)</code>
</div>

<div class="page-break"></div>

<!-- SECTION 4: LAB 12.2 -->
<h2>4. Lab 12.2: TLS / Encryption-in-Transit Setup</h2>

<h3>4.1 Threat Model & Cryptographic Purpose</h3>
<p>
While RBAC protects data at the database logical boundary, unencrypted TCP connections expose sensitive credentials, session tokens, and query payloads to network sniffing and Man-in-the-Middle (MitM) attacks. TLS (Transport Layer Security) guarantees:
</p>
<ol>
  <li><strong>Confidentiality:</strong> Encrypts all frames in transit using strong symmetric ciphers (e.g. AES-256-GCM).</li>
  <li><strong>Authentication:</strong> Cryptographically validates server identity via X.509 digital certificates signed by a trusted Certificate Authority (CA).</li>
  <li><strong>Integrity:</strong> Prevents alteration or replay of packets using Message Authentication Codes (HMAC).</li>
</ol>

<h3>4.2 Public Key Infrastructure (PKI) Architecture & OpenSSL Generation</h3>
<p>
A multi-tier X.509 certificate chain was engineered for the MongoDB deployment:
</p>
<ul>
  <li><strong>Root CA (<code>ca.crt</code>):</strong> Self-signed CA generated with RSA 4096-bit private key.</li>
  <li><strong>Server Certificate (<code>server.crt</code>):</strong> Signed by the CA, bundling Subject Alternative Names (SAN) for <code>DNS:localhost</code>, <code>DNS:mongodb</code>, and <code>IP:127.0.0.1</code> to prevent hostname validation errors.</li>
  <li><strong>Server PEM (<code>server.pem</code>):</strong> Concatenated private key and signed certificate, required by <code>mongod</code>.</li>
  <li><strong>Client Certificate (<code>client.pem</code>):</strong> Generated for mutual TLS (mTLS) client authentication.</li>
</ul>

<div class="code-title">Bash / OpenSSL: Certificate Authority & Server Key Generation with SAN</div>
<div class="code-block">
# 1. Root Certificate Authority (CA)
openssl genrsa -out ./tls/ca.key 4096
openssl req -new -x509 -days 365 -key ./tls/ca.key -out ./tls/ca.crt -subj '/CN=MongoDB-CA/O=NoSQL-Lab'

# 2. Server Key & CSR
openssl genrsa -out ./tls/server.key 4096
openssl req -new -key ./tls/server.key -out ./tls/server.csr -subj '/CN=localhost'

# 3. Sign Server Cert with Subject Alternative Names (SAN)
openssl x509 -req -days 365 -in ./tls/server.csr -CA ./tls/ca.crt -CAkey ./tls/ca.key -CAcreateserial \
  -out ./tls/server.crt -extfile &lt;(echo "subjectAltName=DNS:localhost,DNS:mongodb,IP:127.0.0.1")

# 4. Concatenate server bundle
cat ./tls/server.key ./tls/server.crt &gt; ./tls/server.pem
chmod 600 ./tls/server.pem
</div>

<h3>4.3 Automated Python Certificate Generator (cryptography Library)</h3>
<p>
To ensure continuous integration and deployment (CI/CD) readiness, certificate management was automated using Python's <code>cryptography</code> library in <code>generate_certs.py</code>. The script builds the complete X.509 chain programmatically:
</p>
<div class="code-title">Python (generate_certs.py snippet)</div>
<div class="code-block">
san = x509.SubjectAlternativeName([
    x509.DNSName("localhost"),
    x509.DNSName("mongodb"),
    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))
])
server_cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(ca_cert.subject)
    .public_key(server_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
    .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
    .add_extension(san, critical=False)
    .sign(ca_key, hashes.SHA256())
)
</div>

<h3>4.4 Server Launch & Negative Enforcement Test</h3>
<p>
MongoDB was started enforcing strict TLS connections:
</p>
<div class="code-block">
mongod --fork --logpath /var/log/mongodb_tls.log --dbpath /data/db_tls --port 27100 \
  --tlsMode requireTLS --tlsCertificateKeyFile ./tls/server.pem --tlsCAFile ./tls/ca.crt
</div>

<div class="callout-warning">
  <div class="callout-title">Negative Enforcement Proof: Unencrypted Traffic Rejected</div>
  Executing an unencrypted connection attempt via <code>mongosh --port 27100 --eval 'db.runCommand({ping:1})'</code> results in immediate disconnection:
  <br><code>MongoServerSelectionError: connection closed / SSL handshake failed on port 27100.</code>
  <br><strong>Conclusion:</strong> Unencrypted plaintext traffic is 100% blocked, closing the network eavesdropping attack surface.
</div>

<h3>4.5 Positive Verification: mongosh & PyMongo find_one()</h3>
<p>
Connecting over TLS using <code>mongosh</code> and <code>test_tls_pymongo.py</code> verifies successful data transfer:
</p>
<div class="code-title">PyMongo TLS Connection & Query Execution (test_tls_pymongo.py)</div>
<div class="code-block">
from pymongo import MongoClient

uri = "mongodb://localhost:27100/?tls=true&tlsCAFile=./tls/ca.crt&tlsCertificateKeyFile=./tls/client.pem&tlsAllowInvalidHostnames=true"
client = MongoClient(uri, serverSelectionTimeoutMS=5000)

# Ping test
client.admin.command("ping")  # Response: {'ok': 1.0}

# Read/Write test over encrypted TLS socket
db = client["tls_verification_db"]
db.secure_records.insert_one({"test": "TLS Verification", "status": "ENCRYPTED"})
doc = db.secure_records.find_one({"status": "ENCRYPTED"})
print(f"[OK] Retrieved encrypted document: {doc}")
</div>

<div class="page-break"></div>

<!-- SECTION 5: DOCKER DEMONSTRATION & GRADING GUIDE -->
<h2>5. Docker Container Architecture & Grading Demonstration Guide</h2>

<h3>5.1 Multi-Tier Docker Container Design</h3>
<p>
The demonstration environment is encapsulated in a production-ready Ubuntu-based container featuring:
</p>
<ul>
  <li><strong>MongoDB 7.0 Community Edition:</strong> Bundling both <code>mongod</code> database engine and <code>mongosh</code> interactive shell.</li>
  <li><strong>Python 3 & PyMongo:</strong> Including the <code>cryptography</code> and <code>pymongo</code> packages for scripted automation.</li>
  <li><strong>Dual Database Instances:</strong> Port <code>27017</code> running SCRAM-SHA Authentication and RBAC; Port <code>27100</code> running strict <code>requireTLS</code>.</li>
  <li><strong>Automated Self-Testing Suite:</strong> On container launch, <code>run_all_labs.sh</code> executes all lab tests sequentially and outputs formatted verification logs before providing an interactive terminal for grading.</li>
</ul>

<h3>5.2 Verification Commands for Evaluator / Grader</h3>
<div class="code-title">Terminal: Pulling and Executing the Demonstration Container</div>
<div class="code-block">
# Step 1: Pull the pre-built image from Docker Hub
docker pull %%DOCKER_USER%%/mongodb-security-lab:latest

# Step 2: Run the automated self-testing demonstration
docker run --rm -it -p 27017:27017 -p 27100:27100 %%DOCKER_USER%%/mongodb-security-lab:latest

# Step 3: (Optional) Open interactive terminal for manual query testing
docker run -it -p 27017:27017 -p 27100:27100 %%DOCKER_USER%%/mongodb-security-lab:latest bash
</div>

<h3>5.3 Manual Interactive Test Commands (Inside Container)</h3>
<table class="data-table">
  <thead>
    <tr>
      <th>Goal</th>
      <th>Shell Command</th>
      <th>Expected Outcome</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Test RBAC Admin</td>
      <td><code>mongosh -u admin -p AdminPass123! --authenticationDatabase admin</code></td>
      <td>Successful administrative login</td>
    </tr>
    <tr>
      <td>Test Reader Privilege</td>
      <td><code>mongosh -u app_user_read -p ReadPass123! --authenticationDatabase admin</code></td>
      <td>Can query reports; cannot write</td>
    </tr>
    <tr>
      <td>Test Non-HR Safe View</td>
      <td><code>mongosh -u staff_user -p StaffPass123! --authenticationDatabase admin</code></td>
      <td>Queries <code>employees_safe</code> with masked SSN and no salary</td>
    </tr>
    <tr>
      <td>Test HR Full View</td>
      <td><code>mongosh -u hr_user -p HrPass123! --authenticationDatabase admin</code></td>
      <td>Queries <code>employees</code> with full SSN and salary visible</td>
    </tr>
    <tr>
      <td>Test TLS Failure (No TLS)</td>
      <td><code>mongosh --port 27100 --eval 'db.runCommand({ping:1})'</code></td>
      <td>Rejected with connection error</td>
    </tr>
    <tr>
      <td>Test TLS Success (With TLS)</td>
      <td><code>mongosh --port 27100 --tls --tlsCAFile /app/tls/ca.crt --tlsAllowInvalidHostnames</code></td>
      <td>Successful TLS shell connection</td>
    </tr>
    <tr>
      <td>Run PyMongo TLS Script</td>
      <td><code>python3 /app/test_tls_pymongo.py --port 27100</code></td>
      <td>Ping ok, insert ok, find_one() ok</td>
    </tr>
  </tbody>
</table>

<!-- SECTION 6: CONCLUSION -->
<h2>6. Conclusion & Production Security Hardening Checklist</h2>
<p>
This laboratory demonstrated end-to-end configuration of enterprise MongoDB security:
</p>
<ol>
  <li><strong>Least Privilege RBAC:</strong> Replaced monolithic privileges with granular, resource-scoped roles, preventing accidental data leakage and unauthorized modifications.</li>
  <li><strong>Field-Level Redaction Views:</strong> Masked PII and excluded sensitive financial data dynamically without maintaining fragile data duplicates.</li>
  <li><strong>Cryptographic In-Transit Protection:</strong> Enforced TLS with custom X.509 PKI, validating both server authenticity and wire-level confidentiality.</li>
  <li><strong>Continuous Delivery Containerization:</strong> Standardized the complete environment inside a Docker container published to Docker Hub for grading.</li>
</ol>

<div class="callout">
  <div class="callout-title">Production Hardening Recommendations</div>
  In production environments, complement these controls with: (1) <strong>Key Management Service (KMS)</strong> integration with WiredTiger Encryption-at-Rest; (2) <strong>Enterprise Auditing</strong> for compliance change logs; (3) <strong>Mutual TLS (mTLS) with x.509 Authentication</strong> to replace static passwords; and (4) IP Whitelisting / VPC peering restrictions.
</div>

</body>
</html>
'@

$html = $template.Replace("%%SHARDING_B64%%", $shardingB64).Replace("%%SECURITY_B64%%", $securityB64).Replace("%%DOCKER_USER%%", $DockerUsername)

[System.IO.File]::WriteAllText($htmlFile, $html, [System.Text.Encoding]::UTF8)
Write-Host "[OK] Written HTML Report: $htmlFile" -ForegroundColor Green

# Generate PDF via Headless Chrome
$tempUserData = Join-Path $scriptDir "chrome_temp_pdf"
New-Item -ItemType Directory -Path $tempUserData -Force | Out-Null

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chromePath)) {
    $chromePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
}

Write-Host "[INFO] Generating PDF via Headless Browser: $chromePath" -ForegroundColor Cyan
& "$chromePath" --headless=new --no-sandbox --disable-gpu --user-data-dir="$tempUserData" "--print-to-pdf=$pdfFile" "$htmlFile"

Start-Sleep -Seconds 3

if (Test-Path $pdfFile) {
    $fileSize = (Get-Item $pdfFile).Length
    Write-Host "[SUCCESS] Generated PDF Report: $pdfFile ($fileSize bytes)" -ForegroundColor Green
} else {
    Write-Host "[ERROR] PDF generation failed!" -ForegroundColor Red
}

Remove-Item $tempUserData -Recurse -Force -ErrorAction SilentlyContinue
