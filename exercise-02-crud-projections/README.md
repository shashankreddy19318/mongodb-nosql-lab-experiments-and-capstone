# Exercise 02: CRUD Operations, Filtering & Field Projections

**Author:** G. Shashank Reddy (Chintan)  
**Student ID / USN:** 24BTRCL079  
**Course:** Distributed NoSQL Databases (MongoDB 7.0)  

---

## 📌 Overview

This chapter covers core database CRUD operations in MongoDB using PyMongo, contrasting relational SQL projection paradigms with document-oriented projection techniques.

### Key Learning Objectives:
1. **Activity 2.1:** Inspecting MongoDB server parameters, client drivers, build environment, and connection topologies using `buildInfo` and `serverStatus`.
2. **Activity 2.1 (Try It Yourself):** Client connection options, socket timeouts, direct connection verification, and replica set discovery.
3. **Activity 2.2:** CRUD operations on structured collections (`bookstore`), advanced filtering (`$gt`, `$in`, `$regex`), and field projection optimization (`{ title: 1, price: 1, _id: 0 }`).
4. **Activity 2.2 (Try It Yourself):** Complex nested document updates with `$set`, `$inc`, `$push`, and array element modifications.

---

## 📂 Directory Structure

```
├── Activity_2.1/
│   ├── activity_2_1.py                   # Server environment & configuration inspector
│   ├── activity_2_1_try_it_yourself.py   # Connection tuning & client parameter tests
│   ├── environment_check.json            # JSON dump of driver & host environment
│   └── server_info_comparison.json       # Server status benchmarking output
├── Activity_2.2/
│   ├── activity_2_2.py                   # Primary CRUD & Projection implementation
│   ├── activity_2_2_try_it_yourself.py   # Extended updates & array operations
│   ├── bookstore_books.json              # Sample dataset (Books collection)
│   └── bookstore_extended.json           # Extended dataset with nested reviews
├── Exercise_02_NoSQL_Submission.zip      # Archived lab artifacts
└── Exercise_2_NoSQL_Scripts_and_Outputs.docx # Official documentation report
```

---

## 🚀 How to Run

```bash
# Run Activity 2.1: Server Info & Environment
python Activity_2.1/activity_2_1.py

# Run Activity 2.2: CRUD Operations & Projections
python Activity_2.2/activity_2_2.py
```
