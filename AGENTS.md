# AGENTS.md - Student Issue Tracking and Resolution System

A concise, high-density project review and navigation guide designed for AI agents and human technical reviewers inspecting the **Student Issue Tracking and Resolution System** codebase.

---

## 1. Executive Summary

| Attribute | Specification |
|---|---|
| **Project Title** | Student Issue Tracking and Resolution System |
| **Domain** | Relational Database Management System (RDBMS) / Academic Operations |
| **Stack** | Python 3 (Flask), SQLite 3, Jinja2, HTML5/CSS3 (Emerald & Dark Green Theme), Vanilla JavaScript |
| **Normalization Level** | 3rd Normal Form (3NF) across all entities |
| **Data Integrity** | Foreign Key cascading/referential integrity (`PRAGMA foreign_keys = ON`), Check constraints |
| **Transaction Standard** | ACID-compliant Stored Procedures / multi-statement transactions with atomic commit and rollback |
| **Security Controls** | Parameterized SQL queries (zero string formatting / zero SQL injection), PBKDF2-SHA256 password hashing, Role-Based Access Control (RBAC) |
| **Repository URL** | https://github.com/AnanyaRamesh23/StudentIssueTrackingAndResolutionSystem.git |

---

## 2. System Architecture & Component Mapping

```
DBMS_PROJECT/
├── app.py                      # Application bootstrap, configuration, and blueprint registration
├── config.py                   # Environment configuration, database paths, secret keys
├── db.py                       # Connection manager, execution helpers, ACID transaction wrappers
├── requirements.txt            # Minimal runtime dependencies (Flask, Werkzeug)
├── test_app.py                 # Automated unit and integration test suite (6 suites)
├── AGENTS.md                   # This project review and architecture map
├── README.md                   # Full user and deployment documentation
│
├── database/
│   ├── schema.sql              # DDL: 8 Normalized 3NF tables, constraints, indexes, and views
│   ├── seed.sql                # DML: Production-grade initial dataset across departments
│   ├── init_db.py              # Script to recreate and seed the database idempotently
│   └── student_issue_db.sqlite # Embedded SQLite database file
│
├── routes/
│   ├── auth_routes.py          # Authentication, session establishment, role dispatching
│   ├── student_routes.py       # Issue filing, ticket tracking, student feedback
│   ├── staff_routes.py         # Workload views, status updates, action logging
│   └── admin_routes.py         # Global monitoring, staff reassignment, workload analytics
│
├── services/
│   └── issue_service.py        # Core domain logic, duplicate detection, SLA calculation, ACID procedures
│
├── static/
│   ├── css/
│   │   └── style.css           # Custom Emerald/Dark Green theme (#047857), responsive grid, cards, tables
│   └── js/
│       └── main.js             # Client-side debounce, confirmation modals, form validation
│
└── templates/
    ├── base.html               # Master layout (Dark forest header, navigation, flash alert container)
    ├── login.html              # Role-aware login form
    ├── register.html           # Student registration form
    ├── student_dashboard.html  # Student metrics, quick submission link, recent tickets
    ├── submit_issue.html       # Categorized issue submission form
    ├── my_issues.html          # Paginated/filterable list of student's own issues
    ├── staff_dashboard.html    # Staff workload summary, pending actions, SLA timers
    ├── assigned_issues.html    # List of issues assigned to active staff member
    ├── admin_dashboard.html    # Department-wide workload table, SLA breach monitor, reassignment modal
    ├── issue_details.html      # Comprehensive ticket view with action timeline and feedback form
    └── dbms_demo.html          # Relational schema reference and DBMS design review page
```

---

## 3. Database Design & Relational Schema (3NF)

The schema enforces strict referential integrity across 8 normalized tables:

### 3.1 Entity Relationship Summary

1. **`STUDENT`**:
   - Attributes: `StudentID` (PK), `Name`, `Email` (UNIQUE), `PasswordHash`, `Department`, `Semester`, `Phone`, `CreatedAt`
   - Purpose: Stores student credentials and departmental context.

2. **`STAFF`**:
   - Attributes: `StaffID` (PK), `Name`, `Email` (UNIQUE), `PasswordHash`, `Department`, `Role`, `Phone`, `CreatedAt`
   - Purpose: Stores academic and facility staff members handling assigned issues.

3. **`CATEGORY`**:
   - Attributes: `CategoryID` (PK), `CategoryName` (UNIQUE), `SLA_Hours`, `Description`
   - Purpose: Defines standard service categories (Academic, Infrastructure, Hostel, Administration, IT) with SLA deadlines.

4. **`STATUS`**:
   - Attributes: `StatusID` (PK), `StatusName` (UNIQUE), `Description`
   - Purpose: State machine milestones (`Open`, `Under Review`, `In Progress`, `Resolved`, `Closed`).

5. **`ISSUE`**:
   - Attributes: `IssueID` (PK), `Title`, `Description`, `CategoryID` (FK -> CATEGORY), `StudentID` (FK -> STUDENT), `AssignedStaffID` (FK -> STAFF), `StatusID` (FK -> STATUS), `Priority` (CHECK: Low, Medium, High, Critical), `CreatedAt`, `UpdatedAt`
   - Purpose: Central issue entity linking reporter, resolver, category, and lifecycle state.

6. **`ACTION`**:
   - Attributes: `ActionID` (PK), `IssueID` (FK -> ISSUE), `StaffID` (FK -> STAFF), `ActionDescription`, `ActionDate`
   - Purpose: Append-only audit log of actions taken toward issue resolution.

7. **`REASSIGNMENT_LOG`**:
   - Attributes: `LogID` (PK), `IssueID` (FK -> ISSUE), `OldStaffID` (FK -> STAFF), `NewStaffID` (FK -> STAFF), `Reason`, `Timestamp`
   - Purpose: Tracks the chain of custody when an administrator reassigns a ticket.

8. **`FEEDBACK`**:
   - Attributes: `FeedbackID` (PK), `IssueID` (FK -> ISSUE, UNIQUE), `Rating` (CHECK: 1 to 5), `Comments`, `SubmittedAt`
   - Purpose: Student satisfaction assessment upon issue resolution.

### 3.2 Relational Views

- **`v_issue_details`**:
  Combines `ISSUE`, `STUDENT`, `STAFF`, `CATEGORY`, and `STATUS` to eliminate repetitive application-level multi-table joins.
- **`v_staff_workload`**:
  Aggregates active, in-progress, and resolved issue counts grouped by `STAFF` member and department.

---

## 4. ACID Transaction Implementation

Critical operations are encapsulated in atomic database transactions with rollback guards:

### 4.1 Issue Reassignment (`sp_reassign_issue`)
- **Step 1**: Verify issue existence and current assigned staff member.
- **Step 2**: Update `ISSUE.AssignedStaffID` to new staff ID.
- **Step 3**: Insert audit record into `REASSIGNMENT_LOG`.
- **Step 4**: Insert record into `ACTION` audit log noting reassignment rationale.
- **Atomicity**: Any constraint violation or error triggers a full `ROLLBACK`. Only when all steps succeed is a `COMMIT` executed.

### 4.2 Status Update and Action Logging (`sp_update_status_and_action`)
- **Step 1**: Update `ISSUE.StatusID` and set `UpdatedAt = CURRENT_TIMESTAMP`.
- **Step 2**: Insert detailed operational note into `ACTION` table.
- **Atomicity**: Wrapped in `with get_db_connection() as conn:` transaction context. Failure in logging automatically reverts the status transition.

---

## 5. Security & Query Governance

1. **SQL Injection Defense**:
   - 100% of SQL statements across `db.py` and `services/issue_service.py` use SQLite parameter placeholders (`?`).
   - Zero dynamic SQL string concatenation.
2. **Authentication & Session Isolation**:
   - Passwords hashed using `werkzeug.security.generate_password_hash` (PBKDF2-SHA256 with per-user salt).
   - Route decorators enforce role checks (`@login_required`, `@student_required`, `@staff_required`, `@admin_required`).
3. **Data Integrity Pragma**:
   - Foreign keys are explicitly turned on for every connection (`PRAGMA foreign_keys = ON;`).

---

## 6. Automated Test Suite & Verification

The test harness in `test_app.py` runs 6 structured test suites:

| Suite Name | Scope | Key Assertions |
|---|---|---|
| **Suite 1: Database & Foreign Keys** | Schema integrity | Foreign key pragma enabled, all 8 tables present |
| **Suite 2: Database Views** | Read performance | `v_issue_details` and `v_staff_workload` return valid result sets |
| **Suite 3: Authentication & Security** | Access control | Password verification, unauthorized redirect handling |
| **Suite 4: Issue Lifecycle & Duplicate Check** | Core workflows | Ticket creation, duplicate detection prevents duplicate filing |
| **Suite 5: ACID Transaction Integrity** | Concurrency & Rollback | Atomic reassignment logs both to `REASSIGNMENT_LOG` and `ACTION` |
| **Suite 6: HTTP Route Responses** | Web tier | All endpoints return HTTP 200 / valid redirects |

---

## 7. How to Run & Verify

### 7.1 Environment Setup
```powershell
# Navigate to project directory
cd DBMS_PROJECT

# Install minimal dependencies
pip install -r requirements.txt
```

### 7.2 Run Automated Verification
```powershell
python test_app.py
```
*Expected Result: All 6 test suites pass with 0 errors.*

### 7.3 Start the Web Application
```powershell
python app.py
```
*Access the interface at `http://127.0.0.1:5000`.*

### 7.4 Default Test Accounts

| Role | Email | Password | Department |
|---|---|---|---|
| **Admin** | `admin@college.edu` | `admin123` | Administration |
| **Staff** | `rajesh.kumar@college.edu` | `staff123` | Computer Science |
| **Staff** | `anita.deshmukh@college.edu` | `staff123` | Infrastructure |
| **Student** | `rahul.sharma@college.edu` | `student123` | Computer Science |
| **Student** | `priya.patel@college.edu` | `student123` | Electrical Engineering |

---

## 8. Agent Checklist for Code Review

When inspecting or extending this codebase, verify:
- [x] No raw SQL string interpolation is introduced. Always pass parameters via tuple/dict.
- [x] Foreign key constraints remain enabled on all newly spawned connections.
- [x] Complex multi-table writes are wrapped in an explicit transaction block with `conn.rollback()` on exception.
- [x] The UI styling adheres to the Dark Green and Emerald system defined in `static/css/style.css`.
- [x] Zero emojis are present in templates, logs, or flash messages.
