# STUDENT ISSUE TRACKING AND RESOLUTION SYSTEM
### Database Management Systems (DBMS) Academic Laboratory Project

**Candidate:** Ananya Ramesh  
**USN:** U25UV24T064002  
**Branch / Semester:** Information Science & Engineering (ISE), 5th Semester  
**Faculty Guide:** Dr. Arunalatha J S  

---

## 1. Project Overview & Purpose

The **Student Issue Tracking and Resolution System** is a complete, full-stack database-driven web application designed to demonstrate core Relational Database Management System (DBMS) concepts in practice. 

Rather than serving as a basic static submission form, the core architecture enforces complete issue lifecycle tracking (`Submitted` → `Assigned` → `In Progress` → `Resolved` → `Closed`), preserves full accountability through historical audit trails (recorded actions and reassignments), maintains 1:1 satisfaction feedback upon resolution, and calculates derived SLA compliance.

### At any point, the system allows knowing:
1. **What the issue is** (Description, Location, Priority)
2. **Which student submitted it** (Foreign key to `STUDENT`)
3. **What category it belongs to** (Academic, Administrative, Technical, Facilities)
4. **Which staff member is responsible** (Foreign key to `STAFF`)
5. **What its current status is** (Submitted, Assigned, In Progress, Resolved, Closed)
6. **What concrete actions have been taken** (`ACTION` audit trail)
7. **Whether it was reassigned, why, and to whom** (`REASSIGNMENT_LOG`)
8. **Whether it has been resolved or is overdue** (Computed SLA condition)
9. **What feedback and rating the student gave** (`FEEDBACK` 1:1 relation)

---

## 2. Technology Stack

- **Frontend:** Pure HTML5, CSS3, Vanilla JavaScript (Zero heavy frameworks like React/Angular/Vue; calm, responsive academic aesthetic).
- **Backend:** Python 3 Flask (modular blueprints: Auth, Student, Staff, Admin).
- **Database:** MariaDB / MySQL (with seamless built-in dual-engine SQLite fallback for zero-friction evaluation).
- **Database Connectivity:** Python MySQL connector (`mysql-connector-python` and `pymysql`).
- **Security:** Parameterized SQL queries (preventing SQL Injection), Werkzeug password hashing, session-based authorization.

---

## 3. Relational Database Schema & Architecture

The database is normalized approximately up to **Third Normal Form (3NF)**. Repeated student names, staff details, category names, and status names are never duplicated within the `ISSUE` table; relational foreign keys and SQL `JOIN`s are used throughout.

```
 ┌──────────────┐ 1        N ┌──────────────┐ N        1 ┌──────────────┐
 │   STUDENT    │───────────<│    ISSUE     │>───────────│   CATEGORY   │
 └──────────────┘            └──────┬───────┘            └──────────────┘
                                    │ N
                                    │ │
                                    │ │ 1
                                    │ ▼
                             ┌──────────────┐
                             │    STATUS    │
                             └──────────────┘
                                    ▲
                                    │ 1
                                    │ │
                                    │ │ N
                                    │ ▼
 ┌──────────────┐ 1        N ┌──────────────┐
 │    STAFF     │───────────<│    ACTION    │
 └──────┬───────┘            └──────────────┘
        │ 1
        │
        │ N
        ▼
 ┌──────────────┐ N        1
 │REASSIGN_LOG  │>───────────┐
 └──────────────┘            │
                             │
 ┌──────────────┐ 1        1 │
 │   FEEDBACK   │───────────<┘
 └──────────────┘
```

### Table Definitions & Constraints

#### 1. `STUDENT`
Stores registered students who report grievances.
- `Student_ID`: `INT PRIMARY KEY`
- `Name`: `VARCHAR(100) NOT NULL`
- `Email`: `VARCHAR(100) UNIQUE NOT NULL`
- `Department`: `VARCHAR(50) NOT NULL`
- `Year`: `INT NOT NULL CHECK (Year BETWEEN 1 AND 4)`
- `Password_Hash`: `VARCHAR(255) NOT NULL`
- `Created_At`: `DATETIME DEFAULT CURRENT_TIMESTAMP`

#### 2. `STAFF`
Stores faculty and staff members handling issues.
- `Staff_ID`: `INT PRIMARY KEY`
- `Name`: `VARCHAR(100) NOT NULL`
- `Email`: `VARCHAR(100) UNIQUE NOT NULL`
- `Department`: `VARCHAR(50) NOT NULL`
- `Role`: `VARCHAR(50) NOT NULL`
- `Password_Hash`: `VARCHAR(255) NOT NULL`
- `Created_At`: `DATETIME DEFAULT CURRENT_TIMESTAMP`

#### 3. `CATEGORY`
Lookup table organizing issues with default Service Level Agreement (SLA).
- `Category_ID`: `INT PRIMARY KEY`
- `Category_Name`: `VARCHAR(50) UNIQUE NOT NULL` (*Academic, Administrative, Technical, Facilities*)
- `Default_SLA_Days`: `INT NOT NULL CHECK (Default_SLA_Days > 0)`

#### 4. `STATUS`
Lookup table enforcing the issue lifecycle stages.
- `Status_ID`: `INT PRIMARY KEY`
- `Status_Name`: `VARCHAR(50) UNIQUE NOT NULL` (*1: Submitted, 2: Assigned, 3: In Progress, 4: Resolved, 5: Closed*)

#### 5. `ISSUE`
Central transaction table capturing student complaints.
- `Issue_ID`: `INT PRIMARY KEY AUTO_INCREMENT`
- `Student_ID`: `INT NOT NULL, FK → STUDENT(Student_ID)`
- `Category_ID`: `INT NOT NULL, FK → CATEGORY(Category_ID)`
- `Staff_ID`: `INT NULL, FK → STAFF(Staff_ID)`
- `Status_ID`: `INT NOT NULL DEFAULT 1, FK → STATUS(Status_ID)`
- `Description`: `TEXT NOT NULL`
- `Date_Submitted`: `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `Location`: `VARCHAR(100) NOT NULL`
- `Priority`: `VARCHAR(20) NOT NULL CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical'))`
- `Due_Date`: `DATE NOT NULL`

#### 6. `ACTION`
Audit trail of concrete actions/steps taken by staff.
- `Action_ID`: `INT PRIMARY KEY AUTO_INCREMENT`
- `Issue_ID`: `INT NOT NULL, FK → ISSUE(Issue_ID) ON DELETE CASCADE`
- `Staff_ID`: `INT NOT NULL, FK → STAFF(Staff_ID)`
- `Action_Description`: `TEXT NOT NULL`
- `Action_Date`: `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`

#### 7. `REASSIGNMENT_LOG`
Accountability log tracking staff transfers.
- `Reassign_ID`: `INT PRIMARY KEY AUTO_INCREMENT`
- `Issue_ID`: `INT NOT NULL, FK → ISSUE(Issue_ID) ON DELETE CASCADE`
- `Old_Staff_ID`: `INT NULL, FK → STAFF(Staff_ID) ON DELETE SET NULL`
- `New_Staff_ID`: `INT NOT NULL, FK → STAFF(Staff_ID)`
- `Reassigned_On`: `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`
- `Reason`: `VARCHAR(255) NOT NULL`

#### 8. `FEEDBACK`
Post-resolution student satisfaction rating and remarks.
- `Feedback_ID`: `INT PRIMARY KEY AUTO_INCREMENT`
- `Issue_ID`: `INT NOT NULL UNIQUE, FK → ISSUE(Issue_ID) ON DELETE CASCADE` *(Enforces strict 1:1 relationship)*
- `Rating`: `INT NOT NULL CHECK (Rating BETWEEN 1 AND 5)`
- `Comments`: `TEXT NULL`
- `Submitted_On`: `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`

---

## 4. Entity-Relationship (ER) Explanations

1. **Student 1 : N Issue** — One student can submit multiple issues over time; each issue belongs to exactly one student.
2. **Category 1 : N Issue** — One category classifies many issues; each issue belongs to one category.
3. **Staff 1 : N Issue** — One staff member can be assigned multiple issues; an issue has at most one active responsible staff member.
4. **Status 1 : N Issue** — One status state applies to many issues.
5. **Issue 1 : N Action** — An issue can have multiple recorded actions detailing its resolution progress.
6. **Staff 1 : N Action** — A staff member records multiple actions across various issues.
7. **Issue 1 : N Reassignment_Log** — An issue can be reassigned between staff members multiple times during its lifecycle.
8. **Issue 1 : 1 Feedback** — Once resolved or closed, an issue can receive at most one student rating and feedback comment (`UNIQUE` key on `Issue_ID`).

---

## 5. Normalization Justification (Targeting 3NF)

- **First Normal Form (1NF):** Every field holds atomic values (no comma-separated lists of actions or handlers). Each table contains a primary key.
- **Second Normal Form (2NF):** Satisfies 1NF and contains no partial dependencies. All non-key attributes are fully functionally dependent on the entire primary key (all tables employ single-column PKs).
- **Third Normal Form (3NF):** Satisfies 2NF and contains no transitive functional dependencies ($X \rightarrow Y \rightarrow Z$).
  - Staff names, departments, and roles are stored in `STAFF`, not inside `ISSUE`.
  - Student names and departments are stored in `STUDENT`, not inside `ISSUE`.
  - Category SLA days are stored in `CATEGORY`, not inside `ISSUE`.
  - Actions and Reassignments are split into separate relation tables because their cardinality is independent ($1:N$).

---

## 6. Installation & Setup Instructions

### Prerequisites
- Python 3.9+ installed (`python --version`)
- MariaDB or MySQL installed (Optional for local testing; the app features a dual-engine architecture that connects to MariaDB/MySQL when active, and automatically falls back to local SQLite if MySQL is offline).

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```
*(Or `python -m pip install -r requirements.txt`)*

### Step 2: MariaDB / MySQL Setup
1. Start your MariaDB or MySQL service (e.g., via XAMPP Control Panel, WAMP, or `net start MySQL`).
2. Verify or update connection credentials in `.env` or `config.py`:
   ```ini
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=student_issue_db
   ```
3. Initialize the database schema and sample data:
   ```bash
   python database/init_db.py
   ```
   *This creates `student_issue_db`, imports `schema.sql` (tables, views, triggers, procedures), and seeds `seed.sql`.*

### Step 3: Run the Flask Web Application
```bash
python app.py
```
Open your web browser at: **`http://127.0.0.1:5000`**

### Step 4: Run Automated Tests
```bash
python test_app.py
```
*(Runs comprehensive tests for all 8 tables, views, full issue lifecycle, transaction atomicity, derived overdue logic, and web routes)*.

---

## 7. Test Login Credentials & 1-Click Viva Mode

The application provides **1-Click Instant Demo Login** on the login page (`/login`) so examiners and students never have to manually re-type credentials during a viva presentation.

| Role | Name | Email | Password | Purpose |
|---|---|---|---|---|
| **Student** | Ananya Ramesh | `ananya@college.edu` | `password123` | View my issues, submit new ticket, rate resolved issue |
| **Student** | Rohan Sharma | `rohan.sharma@college.edu` | `password123` | Test second student perspective |
| **Staff (IT)** | Dr. Suresh Kumar | `suresh@college.edu` | `password123` | System Administrator & Lab In-charge |
| **Staff (Facilities)**| Mr. Anand Murthy | `anand@college.edu` | `password123` | Campus Infrastructure Supervisor |
| **Staff (Academic)**| Prof. Sunita Rao | `sunita@college.edu` | `password123` | Academic Coordinator |
| **Administrator** | College Administrator | `admin@college.edu` | `admin123` | System-wide statistics & DBMS Viva Showcase |

---

## 8. DBMS Concepts Demonstrated

### 1. Database Views
- **`v_issue_details`:** Consolidates 5 tables (`ISSUE`, `STUDENT`, `CATEGORY`, `STATUS`, `STAFF`) and calculates the derived boolean column `Is_Overdue`.
  ```sql
  SELECT * FROM v_issue_details WHERE Status_ID = 3;
  ```
- **`v_staff_workload`:** Aggregates total assigned, in-progress, resolved, closed, and overdue issues per staff member.
  ```sql
  SELECT * FROM v_staff_workload ORDER BY Total_Assigned DESC;
  ```

### 2. Triggers
- **`trg_set_due_date` (BEFORE INSERT on `ISSUE`):**
  Automatically queries `CATEGORY.Default_SLA_Days` and sets `NEW.Due_Date = DATE_ADD(CURRENT_DATE(), INTERVAL v_sla DAY)` if not provided.
- **`trg_log_reassignment` (AFTER UPDATE on `ISSUE`):**
  Fires when `OLD.Staff_ID <> NEW.Staff_ID` to log the transition into `REASSIGNMENT_LOG`.

### 3. Stored Procedures & ACID Transactions
- **`sp_reassign_issue`:**
  Atomically executes:
  1. `UPDATE ISSUE SET Staff_ID = p_new_staff_id, Status_ID = 2 WHERE Issue_ID = p_issue_id;`
  2. `INSERT INTO REASSIGNMENT_LOG (Issue_ID, Old_Staff_ID, New_Staff_ID, Reassigned_On, Reason) ...;`
  3. `INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date) ...;`
  Inside `START TRANSACTION;` with `COMMIT;` and rollback handler on exception.

### 4. Aggregations (GROUP BY & HAVING)
- **Issues by Category:**
  ```sql
  SELECT c.Category_Name, COUNT(i.Issue_ID) AS Issue_Count
  FROM CATEGORY c
  LEFT JOIN ISSUE i ON c.Category_ID = i.Category_ID
  GROUP BY c.Category_Name;
  ```
- **Staff Performance with HAVING:**
  ```sql
  SELECT sf.Name, COUNT(i.Issue_ID) AS Handled_Issues, ROUND(AVG(f.Rating), 2) AS Avg_Rating
  FROM STAFF sf
  JOIN ISSUE i ON sf.Staff_ID = i.Staff_ID
  LEFT JOIN FEEDBACK f ON i.Issue_ID = f.Issue_ID
  GROUP BY sf.Staff_ID, sf.Name
  HAVING COUNT(i.Issue_ID) >= 2;
  ```

### 5. Derived Overdue Logic
An issue is dynamically identified as overdue when:
$$\text{Due\_Date} < \text{CURRENT\_DATE}() \quad \text{AND} \quad \text{Status\_Name} \notin (\text{'Resolved'}, \text{'Closed'})$$
Overdue is treated as a **derived condition**, not as a redundant static status value.

---

## 9. Project Directory Structure

```
socket/
├── database/
│   ├── schema.sql            # MariaDB / MySQL DDL (Tables, Constraints, Indexes, Views, Triggers, Procedures)
│   ├── seed.sql              # Realistic academic sample data
│   └── init_db.py            # Automated database setup & diagnostic tool
├── routes/
│   ├── auth_routes.py        # Authentication & 1-click viva demo logins
│   ├── student_routes.py     # Student dashboard, submission, my issues, feedback
│   ├── staff_routes.py       # Staff dashboard, status transitions, actions, reassignment
│   └── admin_routes.py       # Institution overview & live DBMS viva showcase
├── services/
│   └── issue_service.py      # Business logic & SQL query abstraction
├── static/
│   ├── css/
│   │   └── style.css         # Academic, clean, responsive styles
│   └── js/
│       └── main.js           # Client-side validation, SLA preview, modal dialogs
├── templates/
│   ├── base.html             # Common layout, header, footer, flashes
│   ├── login.html            # Portal login & 1-click evaluation cards
│   ├── register.html         # Student registration
│   ├── student_dashboard.html# Student dashboard
│   ├── submit_issue.html     # Grievance submission form
│   ├── my_issues.html        # Filterable issue list
│   ├── issue_details.html    # Full lifecycle stepper, timeline, feedback
│   ├── staff_dashboard.html  # Staff dashboard & unassigned queue
│   ├── assigned_issues.html  # Staff issues table with scope toggle
│   ├── admin_dashboard.html  # Institution overview & analytics
│   └── dbms_demo.html        # Dedicated DBMS viva demonstration panel
├── config.py                 # Application configuration & credentials
├── db.py                     # Dual-engine connection manager (MySQL/MariaDB & SQLite)
├── app.py                    # Flask application entry point
├── requirements.txt          # Python package requirements
├── test_app.py               # Automated test suite
└── README.md                 # Complete project documentation
```
