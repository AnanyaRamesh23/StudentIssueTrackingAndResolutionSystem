# DBMS Concepts & Viva Demonstration Guide
## Student Issue Tracking and Resolution System

This guide outlines how to demonstrate all core Relational Database Management System (DBMS) concepts implemented in the **Student Issue Tracking and Resolution System** during a laboratory presentation or viva examination.

---

## 1. Quick Access to the Live Demonstration Page

A dedicated interactive showcase is built directly into the web application:
* **URL:** `http://127.0.0.1:5000/admin/dbms-demo`
* **Navigation Path:**
  1. Open `http://127.0.0.1:5000`.
  2. On the sign-in page, click the quick profile **Campus Administrator** (or log in with `admin@college.edu` / `admin123`).
  3. In the navigation bar or top banner, click **"DBMS Concepts & Viva Showcase"**.

---

## 2. Concept-by-Concept Demonstration Breakdown

### Concept 1: Relational Normalization (Up to 3NF)
* **Where to Show:** Section 6 of `/admin/dbms-demo` and file `database/schema.sql`.
* **Talking Points:**
  1. **First Normal Form (1NF):**
     * All columns contain atomic, indivisible scalar values.
     * Multi-valued attributes (such as issue progress notes and staff reassignment logs) are not stored in concatenated strings; they are decomposed into separate tables (`ACTION`, `REASSIGNMENT_LOG`).
     * Every entity has an explicit primary key.
  2. **Second Normal Form (2NF):**
     * Satisfies 1NF.
     * No non-prime attribute depends on a proper subset of any candidate key (no partial dependencies).
     * Every table uses a single-column surrogate primary key (`Student_ID`, `Staff_ID`, `Category_ID`, `Status_ID`, `Issue_ID`, etc.), which mathematically eliminates partial dependency.
  3. **Third Normal Form (3NF):**
     * Satisfies 2NF.
     * Strictly **zero transitive functional dependencies** ($X \rightarrow Y \rightarrow Z$ where $Z$ is non-key).
     * Category SLA durations are isolated in `CATEGORY`, not repeated inside `ISSUE`.
     * Student names, departments, and semesters reside solely in `STUDENT`.
     * Staff designations reside solely in `STAFF`.
     * The `ISSUE` table holds only foreign key references (`Student_ID`, `Staff_ID`, `Category_ID`, `Status_ID`).

---

### Concept 2: Multi-Table Joins (INNER JOIN & LEFT OUTER JOIN)
* **Where to Show:** Section 1 of `/admin/dbms-demo` (Live query result table).
* **SQL Query Executed:**
  ```sql
  SELECT 
      i.Issue_ID,
      s.Name AS Student_Name,
      c.Category_Name,
      COALESCE(sf.Name, 'Unassigned') AS Staff_Name,
      st.Status_Name,
      i.Priority,
      i.Due_Date
  FROM ISSUE i
  JOIN STUDENT s ON i.Student_ID = s.Student_ID
  JOIN CATEGORY c ON i.Category_ID = c.Category_ID
  JOIN STATUS st ON i.Status_ID = st.Status_ID
  LEFT JOIN STAFF sf ON i.Staff_ID = sf.Staff_ID
  ORDER BY i.Issue_ID ASC;
  ```
* **Examiner Question & Answer:**
  * **Question:** Why use `LEFT JOIN` instead of `INNER JOIN` for `STAFF`?
  * **Answer:** When a student files a grievance, it begins in the `Submitted` state with `Staff_ID = NULL`. An `INNER JOIN` would drop newly filed, unassigned tickets from search results. A `LEFT OUTER JOIN` preserves all issue rows and returns `Unassigned` when no staff member has been assigned yet.

---

### Concept 3: Database Views (Query Abstraction & Encapsulation)
* **Where to Show:** Section 3 of `/admin/dbms-demo` and the Admin Workload Table on `/admin/dashboard`.
* **SQL View Definition:**
  ```sql
  CREATE VIEW v_staff_workload AS
  SELECT 
      sf.Staff_ID,
      sf.Name AS Staff_Name,
      sf.Department,
      sf.Role,
      COUNT(i.Issue_ID) AS Total_Assigned,
      SUM(CASE WHEN st.Status_Name = 'In Progress' THEN 1 ELSE 0 END) AS In_Progress_Count,
      SUM(CASE WHEN st.Status_Name = 'Resolved' THEN 1 ELSE 0 END) AS Resolved_Count,
      SUM(CASE WHEN st.Status_Name = 'Closed' THEN 1 ELSE 0 END) AS Closed_Count,
      SUM(CASE WHEN i.Due_Date < CURDATE() AND st.Status_Name NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS Overdue_Count
  FROM STAFF sf
  LEFT JOIN ISSUE i ON sf.Staff_ID = i.Staff_ID
  LEFT JOIN STATUS st ON i.Status_ID = st.Status_ID
  GROUP BY sf.Staff_ID, sf.Name, sf.Department, sf.Role;
  ```
* **Examiner Question & Answer:**
  * **Question:** What is the operational benefit of creating this view?
  * **Answer:** A database view acts as a virtual table. Instead of writing a complex 3-table join with multiple conditional aggregations across multiple application routes, backend queries simply call `SELECT * FROM v_staff_workload;`. This enforces query consistency and simplifies maintenance.

---

### Concept 4: Aggregation with `GROUP BY` and `HAVING`
* **Where to Show:** Section 2 of `/admin/dbms-demo`.
* **SQL Query Executed:**
  ```sql
  SELECT 
      sf.Staff_ID,
      sf.Name AS Staff_Name,
      sf.Department,
      sf.Role,
      COUNT(i.Issue_ID) AS Issue_Count,
      ROUND(AVG(f.Rating), 2) AS Avg_Rating
  FROM STAFF sf
  JOIN ISSUE i ON sf.Staff_ID = i.Staff_ID
  LEFT JOIN FEEDBACK f ON i.Issue_ID = f.Issue_ID
  GROUP BY sf.Staff_ID, sf.Name, sf.Department, sf.Role
  HAVING COUNT(i.Issue_ID) >= 2
  ORDER BY Issue_Count DESC;
  ```
* **Examiner Question & Answer:**
  * **Question:** What is the technical difference between `WHERE` and `HAVING`?
  * **Answer:** `WHERE` filters rows before any grouping or aggregate calculation takes place. `HAVING` filters rows *after* the `GROUP BY` aggregation has computed group metrics. In this query, `HAVING COUNT(i.Issue_ID) >= 2` restricts the satisfaction rating report only to personnel who have handled at least two cases.

---

### Concept 5: ACID Transactions & Concurrency Control
* **Where to Show:** Section 4 of `/admin/dbms-demo` and the live Reassignment Modal in `/admin/dashboard`.
* **Code Implementation (`services/issue_service.py`):**
  ```python
  with get_db_connection() as conn:
      try:
          # Step 1: Update the handler and set status to Assigned
          conn.execute(
              "UPDATE ISSUE SET Staff_ID = ?, Status_ID = 2 WHERE Issue_ID = ?",
              (new_staff_id, issue_id)
          )
          # Step 2: Append an audit log of custody transfer
          conn.execute(
              "INSERT INTO REASSIGNMENT_LOG (Issue_ID, Old_Staff_ID, New_Staff_ID, Reason) VALUES (?, ?, ?, ?)",
              (issue_id, old_staff_id, new_staff_id, reason)
          )
          # Step 3: Record action history
          conn.execute(
              "INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description) VALUES (?, ?, ?)",
              (issue_id, new_staff_id, f"Ticket reassigned: {reason}")
          )
          conn.commit()  # Atomicity: All 3 updates commit together
      except Exception:
          conn.rollback()  # Rollback on failure preserves consistency
          raise
  ```
* **Live Step to Demonstrate:**
  1. Go to `http://127.0.0.1:5000/admin/dashboard`.
  2. Find any ticket in the Campus Issues table and click **Reassign**.
  3. Select a new faculty/staff member, provide a mandatory reason, and submit.
  4. Navigate to `/admin/dbms-demo` Section 4 to show that `REASSIGNMENT_LOG` immediately has the new atomic record.

---

### Concept 6: Data Integrity Constraints & 1:1 Cardinality
* **Where to Show:** Section 5 of `/admin/dbms-demo` and file `database/schema.sql`.
* **Key Constraints Enforced:**
  1. **1:1 Cardinality Constraint:**
     * In table `FEEDBACK`: `Issue_ID INT NOT NULL UNIQUE`.
     * The `UNIQUE` constraint guarantees that each resolved grievance can receive at most one student rating.
  2. **Check Constraints:**
     * `Rating BETWEEN 1 AND 5` (verifies feedback scores are bounded).
     * `Year BETWEEN 1 AND 4` (validates student enrollment tier).
     * `Default_SLA_Days > 0` (guarantees positive resolution deadlines).
  3. **Referential Integrity Cascading:**
     * `FOREIGN KEY (Issue_ID) REFERENCES ISSUE(Issue_ID) ON DELETE CASCADE` ensures related actions and logs are cleanly purged if a parent issue is deleted, avoiding orphaned records.
  4. **Connection Pragma:**
     * Every SQLite connection runs `PRAGMA foreign_keys = ON;` in `db.py` to strictly enforce foreign keys.

---

## 3. Recommended 3-Minute Viva Presentation Script

1. **Introduction (30 Seconds):**
   > "Our project is the Student Issue Tracking and Resolution System. It is an operational RDBMS application built with Python Flask and SQLite/MySQL. The primary objective is to centralize grievance resolution under measurable Service Level Agreements (SLAs) while eliminating data duplication through strict 3NF normalization."

2. **Relational Schema & Joins (60 Seconds):**
   > "The schema consists of 8 tables. To prevent anomalies, entities like CATEGORY, STATUS, and STAFF are fully decoupled. On our live demo page, Section 1 shows a 5-table JOIN. We specifically use a LEFT OUTER JOIN for the STAFF table so that new, unassigned complaints remain visible on administrative boards rather than being dropped."

3. **Transactions & Audit (60 Seconds):**
   > "Data consistency is guaranteed through ACID transactions. For instance, when an administrator reassigns a complaint, our service executes multi-statement updates: updating the issue's assigned staff and inserting permanent audit entries into REASSIGNMENT_LOG and ACTION. If any step fails, a full rollback occurs to prevent partial updates."

4. **Views, Aggregation & Constraints (30 Seconds):**
   > "We implemented views such as `v_staff_workload` that aggregate open, in-progress, and resolved cases using GROUP BY. We also use HAVING clauses to calculate average satisfaction ratings for personnel with significant caseloads. Finally, 1:1 relationships are enforced using UNIQUE foreign key constraints on the FEEDBACK table."

---

## 4. Verification Commands

To verify all database tables, views, joins, and transactions programmatically before presenting:

```powershell
# Navigate to the project directory
cd DBMS_PROJECT

# Run the 7-suite automated test suite
python test_app.py

# Launch the web application
python app.py
```

*Access the application at `http://127.0.0.1:5000`.*
