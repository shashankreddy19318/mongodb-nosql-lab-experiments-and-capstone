# Exercise 05: Advanced Query Operators & Aggregation Framework

**Author:** G. Shashank Reddy (Chintan)  
**Student ID / USN:** 24BTRCL079  
**Course:** Distributed NoSQL Databases (MongoDB 7.0)  

---

## 📌 Overview

This chapter covers advanced querying techniques and multi-stage aggregation pipelines in MongoDB.

### Key Learning Objectives:
1. **Activity 5.1:** Advanced query operators including `$elemMatch` for precise nested array matching, `$expr` for comparing fields within the same document, and `$regex` for pattern filtering.
2. **Activity 5.1 (Try It Yourself):** Complex compound queries combining logical operators (`$and`, `$or`, `$nor`) with projection slicing.
3. **Activity 5.2:** Multi-stage Aggregation Pipeline construction using `$match`, `$group`, `$project`, `$sort`, and `$facet` for faceted search and statistical summaries.
4. **Activity 5.2 (Try It Yourself):** Calculating rolling averages, percentile distributions, and document reshaping with `$unwind` and `$lookup`.

---

## 📂 Directory Structure

```
├── activity_5_1/                         # $elemMatch, $expr & array operators
├── activity_5_1_try_it_yourself/         # Custom complex query implementations
├── activity_5_2/                         # Aggregation pipelines ($group, $facet)
├── activity_5_2_try_it_yourself/         # Statistical aggregation & faceted reporting
├── build_submission.py                   # Automated submission builder
├── Exercise_05_NoSQL_Submission.zip      # Archived submission artifacts
└── NoSQL_Lab_Chapter_05_Submission.docx  # Official lab report
```

---

## 🚀 How to Run

```bash
# Execute Activity 5.1
python activity_5_1/activity_5_1.py

# Execute Activity 5.2
python activity_5_2/activity_5_2.py
```
