# Exercise 03: Relational vs Document Modeling Paradigms

**Author:** G. Shashank Reddy (Chintan)  
**Student ID / USN:** 24BTRCL079  
**Course:** Distributed NoSQL Databases (MongoDB 7.0)  

---

## 📌 Overview

This chapter explores the architectural transition from normalized Relational (RDBMS 3NF) database models to document-oriented NoSQL paradigms in MongoDB.

### Key Learning Objectives:
1. **Activity 3.1:** Modeling One-to-One and One-to-Many relationships via document embedding to optimize read locality.
2. **Activity 3.1 (Try It Yourself):** Evaluating boundary constraints, read/write patterns, and atomic updates on nested subdocuments.
3. **Activity 3.2:** Modeling Many-to-Many relationships through referencing (`DBRef` / Object IDs) vs. array-of-references.
4. **Activity 3.2 (Try It Yourself):** Measuring query performance and preventing document fragmentation when relationship cardinality scales.

---

## 📂 Directory Structure

```
├── activity_3_1/                         # One-to-Few & Embedded document modeling
├── activity_3_1_try_it_yourself/         # Custom embedding exercises & benchmarks
├── activity_3_2/                         # Referenced Many-to-Many models
├── activity_3_2_try_it_yourself/         # Unbounded relationship isolation
├── build_submission.py                   # Automated submission builder
├── Exercise_03_NoSQL_Submission.zip      # Archived lab artifacts
└── NoSQL_Lab_Chapter_03_Submission.docx  # Official lab report
```

---

## 🚀 How to Run

```bash
# Execute Activity 3.1
python activity_3_1/activity_3_1.py

# Execute Activity 3.2
python activity_3_2/activity_3_2.py
```
