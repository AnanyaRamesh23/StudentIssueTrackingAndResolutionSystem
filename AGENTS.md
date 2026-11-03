# Database Management Systems Project Report Reference
## Student Issue Tracking and Resolution System

**Repository:** https://github.com/AnanyaRamesh23/StudentIssueTrackingAndResolutionSystem.git  
**Academic Course:** Database Management Systems (DBMS)  
**Architecture:** Relational Schema (3NF), ACID Transactions, Parameterized SQL, Flask MVC  

---

## 1. Introduction and Problem Statement

### 1.1 Problem Statement
In conventional educational institutions, student grievance handling and campus issue management often rely on manual registers, disconnected emails, or informal messaging. This causes critical bottlenecks:
- Lack of centralized accountability and delayed resolution times.
- Absence of structured Service Level Agreements (SLAs).
- High risk of duplicate grievance filing and unmonitored ticket lifecycles.
- Absence of transparent audit trails for staff reassignments and status updates.

### 1.2 Proposed System
The **Student Issue Tracking and Resolution System** is an enterprise-grade Relational Database Management System (RDBMS) paired with an intuitive web application. It enforces strict relational integrity, formalizes SLA tracking, eliminates duplicate issue reporting, logs every administrative action atomically, and aggregates performance analytics across academic and facility departments.

### 1.3 Key Objectives
- **Data Normalization:** Eliminate data redundancy and update anomalies by designing a schema normalized up to 3rd Normal Form (3NF).
- **ACID Compliance:** Execute complex multi-table updates (e.g., ticket reassignment, status progression) within atomic transaction boundaries.
- **Audit Logging:** Maintain append-only histories of administrative actions and staff reassignments.
- **Role-Based Access Control (RBAC):** Provide distinct operational views and privileges for Students, Staff, and Administrators.
- **Security & Integrity:** Prevent SQL injection via 100% parameterized queries and enforce referential integrity with foreign key cascade controls.

---

## 2. System Specifications

### 2.1 Software Specifications
- **Operating System:** Windows 10 / 11, Linux, or macOS
- **RDBMS Engine:** SQLite 3 (Production-grade embedded engine) / MySQL / PostgreSQL compatible
- **Backend Framework:** Python 3.10+ with Flask 3.0+
- **Security Library:** Werkzeug (PBKDF2-SHA256 password hashing)
- **Frontend:** HTML5, CSS3 (Emerald & Dark Green System), Vanilla JavaScript (ES6)
- **Version Control:** Git & GitHub

### 2.2 Hardware Requirements
- **Processor:** 1.6 GHz Dual-Core or higher
- **RAM:** Minimum 2 GB (4 GB recommended)
- **Storage:** 50 MB free disk space for application files and relational storage

---

## 3. Database Design and Architecture

### 3.1 Entity-Relationship Overview
The system models 8 distinct entities with explicit primary-to-foreign key mappings:

```
[STUDENT] (1) --------< (M) [ISSUE] (M) >-------- (1) [CATEGORY]
                             |    |
                             |    +--- (1) >--- (M) [ACTION]
                             |    |
                             |    +--- (1) >--- (M) [REASSIGNMENT_LOG]
                             |    |
                             |    +--- (1) ---- (1) [FEEDBACK]
                             |
                      (M) >--+--< (1) [STAFF]
                             |
                      (M) >--+--< (1) [STATUS]
```

### 3.2 Relational Schema & 3NF Table Definitions

#### 1. STUDENT Table (Reporter Entity)
- **StudentID** (INT, Primary Key, Auto Increment)
- **Name** (VARCHAR(100), NOT NULL)
- **Email** (VARCHAR(100), UNIQUE, NOT NULL)
- **PasswordHash** (VARCHAR(255), NOT NULL)
- **Department** (VARCHAR(50), NOT NULL)
- **Semester** (INT, CHECK 1-8)
- **Phone** (VARCHAR(15))
- **CreatedAt** (DATETIME, DEFAULT CURRENT_TIMESTAMP)
*3NF Compliance:* All attributes depend solely on the primary key `StudentID`. No transitive dependencies exist.

#### 2. STAFF Table (Resolver Entity)
- **StaffID** (INT, Primary Key, Auto Increment)
- **Name** (VARCHAR(100), NOT NULL)
- **Email** (VARCHAR(100), UNIQUE, NOT NULL)
- **PasswordHash** (VARCHAR(255), NOT NULL)
- **Department** (VARCHAR(50), NOT NULL)
- **Role** (VARCHAR(50), NOT NULL)
- **Phone** (VARCHAR(15))
- **CreatedAt** (DATETIME, DEFAULT CURRENT_TIMESTAMP)
*3NF Compliance:* Fully normalized; staff attributes are non-transitively dependent on `StaffID`.

#### 3. CATEGORY Table (Service Level Agreement Definition)
- **CategoryID** (INT, Primary Key, Auto Increment)
- **CategoryName** (VARCHAR(50), UNIQUE, NOT NULL)
- **SLA_Hours** (INT, NOT NULL) - *Maximum resolution threshold in hours*
- **Description** (TEXT)
*Standard Seeds:* Academic (48h), Infrastructure (24h), Hostel (12h), Administration (72h), IT / Network (8h).

#### 4. STATUS Table (Lifecycle State Machine)
- **StatusID** (INT, Primary Key, Auto Increment)
- **StatusName** (VARCHAR(30), UNIQUE, NOT NULL)
- **Description** (TEXT)
*Standard States:* Open, Under Review, In Progress, Resolved, Closed.

#### 5. ISSUE Table (Central Relational Entity)
- **IssueID** (INT, Primary Key, Auto Increment)
- **Title** (VARCHAR(150), NOT NULL)
- **Description** (TEXT, NOT NULL)
- **CategoryID** (INT, Foreign Key -> CATEGORY.CategoryID)
- **StudentID** (INT, Foreign Key -> STUDENT.StudentID)
- **AssignedStaffID** (INT, Foreign Key -> STAFF.StaffID)
- **StatusID** (INT, Foreign Key -> STATUS.StatusID)
- **Priority** (VARCHAR(10), CHECK Priority IN ('Low', 'Medium', 'High', 'Critical'))
- **CreatedAt** (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- **UpdatedAt** (DATETIME, DEFAULT CURRENT_TIMESTAMP)

#### 6. ACTION Table (Audit Trail of Resolutions)
- **ActionID** (INT, Primary Key, Auto Increment)
- **IssueID** (INT, Foreign Key -> ISSUE.IssueID ON DELETE CASCADE)
- **StaffID** (INT, Foreign Key -> STAFF.StaffID)
- **ActionDescription** (TEXT, NOT NULL)
- **ActionDate** (DATETIME, DEFAULT CURRENT_TIMESTAMP)

#### 7. REASSIGNMENT_LOG Table (Administrative Chain of Custody)
- **LogID** (INT, Primary Key, Auto Increment)
- **IssueID** (INT, Foreign Key -> ISSUE.IssueID ON DELETE CASCADE)
- **OldStaffID** (INT, Foreign Key -> STAFF.StaffID)
- **NewStaffID** (INT, Foreign Key -> STAFF.StaffID)
- **Reason** (TEXT, NOT NULL)
- **Timestamp** (DATETIME, DEFAULT CURRENT_TIMESTAMP)

#### 8. FEEDBACK Table (Post-Resolution Evaluation)
- **FeedbackID** (INT, Primary Key, Auto Increment)
- **IssueID** (INT, UNIQUE, Foreign Key -> ISSUE.IssueID ON DELETE CASCADE)
- **Rating** (INT, CHECK Rating BETWEEN 1 AND 5)
- **Comments** (TEXT)
- **SubmittedAt** (DATETIME, DEFAULT CURRENT_TIMESTAMP)

---

## 4. Normalization Analysis

The database was structured iteratively to eliminate insertion, deletion, and update anomalies:

1. **First Normal Form (1NF):**
   - Every column contains atomic (indivisible) values.
   - Each record possesses a unique identifier (Primary Key).
   - Multi-valued attributes (such as multiple action logs per issue) were split into a separate table (`ACTION`).

2. **Second Normal Form (2NF):**
   - The schema meets 1NF criteria.
   - All non-key attributes are fully functionally dependent on the entire primary key (avoiding partial dependency). Tables using surrogate single-column primary keys inherently satisfy 2NF.

3. **Third Normal Form (3NF):**
   - The schema meets 2NF criteria.
   - No transitive functional dependencies exist ($X \to Y$ and $Y \to Z$ where $Z$ is non-key). Category SLA properties were extracted to `CATEGORY`, and student department data remains isolated to `STUDENT`.

---

## 5. Advanced Relational Views and Queries

### 5.1 View: `v_issue_details`
Combines 5 tables to provide an integrated representation for reporting without redundant JOIN operations in application queries:
```sql
CREATE VIEW IF NOT EXISTS v_issue_details AS
SELECT 
    i.IssueID,
    i.Title,
    i.Description,
    i.Priority,
    c.CategoryName,
    c.SLA_Hours,
    s.StatusName,
    stu.Name AS StudentName,
    stu.Email AS StudentEmail,
    stu.Department AS StudentDepartment,
    stf.Name AS AssignedStaffName,
    stf.Email AS AssignedStaffEmail,
    i.CreatedAt,
    i.UpdatedAt,
    ROUND((JULIANDAY('now') - JULIANDAY(i.CreatedAt)) * 24, 1) AS ElapsedHours,
    CASE 
        WHEN s.StatusName NOT IN ('Resolved', 'Closed') 
             AND ((JULIANDAY('now') - JULIANDAY(i.CreatedAt)) * 24) > c.SLA_Hours 
        THEN 1 ELSE 0 
    END AS IsOverdue
FROM ISSUE i
JOIN CATEGORY c ON i.CategoryID = c.CategoryID
JOIN STATUS s ON i.StatusID = s.StatusID
JOIN STUDENT stu ON i.StudentID = stu.StudentID
LEFT JOIN STAFF stf ON i.AssignedStaffID = stf.StaffID;
```

### 5.2 View: `v_staff_workload`
Aggregates operational workload by department and personnel:
```sql
CREATE VIEW IF NOT EXISTS v_staff_workload AS
SELECT 
    stf.StaffID,
    stf.Name AS StaffName,
    stf.Department,
    COUNT(CASE WHEN s.StatusName = 'In Progress' THEN 1 END) AS InProgressCount,
    COUNT(CASE WHEN s.StatusName = 'Open' THEN 1 END) AS OpenCount,
    COUNT(CASE WHEN s.StatusName = 'Resolved' THEN 1 END) AS ResolvedCount,
    COUNT(i.IssueID) AS TotalAssigned
FROM STAFF stf
LEFT JOIN ISSUE i ON stf.StaffID = i.AssignedStaffID
LEFT JOIN STATUS s ON i.StatusID = s.StatusID
GROUP BY stf.StaffID, stf.Name, stf.Department;
```

---

## 6. ACID Transactions & Concurrency Control

### 6.1 Stored Procedure Simulation: Atomic Issue Reassignment
When an administrator reassigns a staff member to an existing issue, three table updates must occur atomically:
```python
def sp_reassign_issue(issue_id: int, new_staff_id: int, reason: str) -> bool:
    with get_db_connection() as conn:
        try:
            # 1. Fetch current assigned staff
            cur = conn.execute("SELECT AssignedStaffID FROM ISSUE WHERE IssueID = ?", (issue_id,))
            old_staff_id = cur.fetchone()[0]

            # 2. Update issue assignment
            conn.execute(
                "UPDATE ISSUE SET AssignedStaffID = ?, UpdatedAt = CURRENT_TIMESTAMP WHERE IssueID = ?",
                (new_staff_id, issue_id)
            )

            # 3. Log to REASSIGNMENT_LOG
            conn.execute(
                "INSERT INTO REASSIGNMENT_LOG (IssueID, OldStaffID, NewStaffID, Reason) VALUES (?, ?, ?, ?)",
                (issue_id, old_staff_id, new_staff_id, reason)
            )

            # 4. Record action in audit log
            conn.execute(
                "INSERT INTO ACTION (IssueID, StaffID, ActionDescription) VALUES (?, ?, ?)",
                (issue_id, new_staff_id, f"Ticket reassigned: {reason}")
            )

            conn.commit()  # Atomicity: All 3 writes committed together
            return True
        except Exception:
            conn.rollback()  # Rollback on any failure
            raise
```

---

## 7. Automated Testing & Validation

The project includes an automated test harness (`test_app.py`) validating 6 critical dimensions:

1. **Test 1 - Schema & Foreign Key Constraints:** Confirms all 8 relational tables exist and `PRAGMA foreign_keys = ON;` is enforced.
2. **Test 2 - Relational Views:** Confirms both `v_issue_details` and `v_staff_workload` execute without syntax or join errors.
3. **Test 3 - Full Lifecycle & 1:1 Feedback:** Verifies issue submission, assignment, action logging, resolution, and one-to-one feedback constraint.
4. **Test 4 - SLA Breach Computation:** Validates mathematical accuracy of elapsed hours and derived `IsOverdue` flag.
5. **Test 5 - Aggregation with GROUP BY / HAVING:** Validates summary statistics and load thresholds.
6. **Test 6 - Web Tier & Route Security:** Asserts HTTP 200/302 statuses across student, staff, and admin session states.

---

## 8. Quick Verification Commands

```powershell
# 1. Run Automated DBMS Test Suite
python test_app.py

# 2. Start Flask Application
python app.py

# 3. Access in Web Browser
http://127.0.0.1:5000
```

---

## 9. Conclusion

The **Student Issue Tracking and Resolution System** demonstrates a complete, mathematically normalized (3NF) relational database design coupled with practical application controls. By enforcing foreign key constraints, wrapping multi-step workflows in ACID transactions, deploying indexed views for analytical aggregation, and sanitizing all inputs with prepared statements, the project meets both rigorous academic DBMS standards and real-world deployment reliability.
