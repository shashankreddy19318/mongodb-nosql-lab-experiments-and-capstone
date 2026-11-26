# Exercise 04: Advanced Schema Design & Denormalization Patterns

**Author:** G. Shashank Reddy (Chintan)  
**Student ID / USN:** 24BTRCL079  
**Course:** Distributed NoSQL Databases (MongoDB 7.0)  

---

## 📌 Overview

This chapter covers production schema design patterns in MongoDB to optimize working set memory fit and query throughput.

### Key Learning Objectives:
1. **Activity 4.1:** Implementing the **Subset Pattern** for high-frequency queries, keeping recent/frequently accessed data embedded while offloading extended data to referenced collections.
2. **Activity 4.1 (Try It Yourself):** Measuring RAM cache utilization and disk I/O differences when applying the Subset pattern.
3. **Activity 4.2:** Implementing the **Bucket Pattern** for time-series and streaming data, grouping discrete readings into composite documents to reduce index overhead.
4. **Activity 4.2 (Try It Yourself):** Dynamic pre-allocation, bounded arrays with `$slice`, and aggregation over time-bucketed documents.

---

## 📂 Directory Structure

```
├── activity_4_1/                         # Subset Pattern implementation
├── activity_4_1_try_it_yourself/         # Custom subset pattern benchmarking
├── activity_4_2/                         # Bucket Pattern for streaming metrics
├── activity_4_2_try_it_yourself/         # Time-series aggregation over buckets
├── build_submission.py                   # Automated submission generator
├── Exercise_04_NoSQL_Submission.zip      # Archived submission artifacts
└── NoSQL_Lab_Chapter_04_Submission.docx  # Official lab report
```

---

## 🚀 How to Run

```bash
# Execute Activity 4.1
python activity_4_1/activity_4_1.py

# Execute Activity 4.2
python activity_4_2/activity_4_2.py
```
