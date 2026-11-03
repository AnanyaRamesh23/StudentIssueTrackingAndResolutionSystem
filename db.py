import os
import sys
import sqlite3
import datetime
from config import Config

# Track active engine & availability
ACTIVE_ENGINE = None
_MYSQL_CHECKED = False
_MYSQL_AVAILABLE = False

def check_mysql_status():
    """Checks if MySQL port is open and reachable (cached per process)."""
    global _MYSQL_CHECKED, _MYSQL_AVAILABLE
    if _MYSQL_CHECKED:
        return _MYSQL_AVAILABLE
    
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        if s.connect_ex((Config.DB_HOST, Config.DB_PORT)) == 0:
            _MYSQL_AVAILABLE = True
        else:
            _MYSQL_AVAILABLE = False
    except Exception:
        _MYSQL_AVAILABLE = False
    finally:
        s.close()
    
    _MYSQL_CHECKED = True
    return _MYSQL_AVAILABLE

def get_mysql_connection():
    """Attempt to establish a MariaDB / MySQL connection using mysql.connector or pymysql."""
    if not check_mysql_status():
        return None, "MySQL port not open"

    # 1. Try mysql.connector
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            connection_timeout=2,
            autocommit=False
        )
        return conn, 'mysql.connector'
    except Exception as e_mysql:
        # 2. Try pymysql
        try:
            import pymysql
            import pymysql.cursors
            conn = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                connect_timeout=2,
                autocommit=False,
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn, 'pymysql'
        except Exception as e_pymysql:
            return None, f"MySQL connection failed: {e_mysql} | {e_pymysql}"

def get_sqlite_connection():
    """Connect to local SQLite database with custom functions matching MySQL syntax."""
    os.makedirs(os.path.dirname(Config.SQLITE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Register MySQL compatible functions in SQLite
    conn.create_function("CURDATE", 0, lambda: datetime.date.today().isoformat())
    conn.create_function("NOW", 0, lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    conn.create_function("CONCAT", -1, lambda *args: "".join(str(a) for a in args if a is not None))
    conn.create_function("COALESCE", -1, lambda *args: next((a for a in args if a is not None), None))
    
    # Enable foreign keys in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_db_connection():
    """Returns an active database connection. Uses MySQL if available, otherwise SQLite fallback."""
    global ACTIVE_ENGINE
    
    # First, try MySQL / MariaDB
    conn, driver = get_mysql_connection()
    if conn:
        ACTIVE_ENGINE = f"MariaDB/MySQL ({driver})"
        return conn
    
    if Config.AUTO_FALLBACK_SQLITE:
        ACTIVE_ENGINE = "SQLite (Local Dual-Engine Fallback)"
        conn = get_sqlite_connection()
        ensure_sqlite_initialized(conn)
        return conn
    
    raise ConnectionError(f"Could not connect to MariaDB/MySQL on {Config.DB_HOST}:{Config.DB_PORT} and SQLite fallback is disabled.")

def get_active_db_engine():
    global ACTIVE_ENGINE
    if ACTIVE_ENGINE is None:
        try:
            conn = get_db_connection()
            conn.close()
        except Exception:
            pass
    return ACTIVE_ENGINE or "Unknown"

def ensure_sqlite_initialized(conn):
    """Initializes tables, views, and seed data in SQLite if not yet populated."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='STUDENT';")
    if cur.fetchone():
        return  # Already initialized
    
    # Create SQLite schema
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS STUDENT (
        Student_ID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Email TEXT NOT NULL UNIQUE,
        Department TEXT NOT NULL,
        Year INTEGER NOT NULL CHECK (Year BETWEEN 1 AND 4),
        Password_Hash TEXT NOT NULL,
        Created_At DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS STAFF (
        Staff_ID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Email TEXT NOT NULL UNIQUE,
        Department TEXT NOT NULL,
        Role TEXT NOT NULL,
        Password_Hash TEXT NOT NULL,
        Created_At DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS CATEGORY (
        Category_ID INTEGER PRIMARY KEY,
        Category_Name TEXT NOT NULL UNIQUE,
        Default_SLA_Days INTEGER NOT NULL CHECK (Default_SLA_Days > 0)
    );

    CREATE TABLE IF NOT EXISTS STATUS (
        Status_ID INTEGER PRIMARY KEY,
        Status_Name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS ISSUE (
        Issue_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Student_ID INTEGER NOT NULL,
        Category_ID INTEGER NOT NULL,
        Staff_ID INTEGER,
        Status_ID INTEGER NOT NULL DEFAULT 1,
        Description TEXT NOT NULL,
        Date_Submitted DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        Location TEXT NOT NULL,
        Priority TEXT NOT NULL CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
        Due_Date DATE NOT NULL,
        FOREIGN KEY (Student_ID) REFERENCES STUDENT (Student_ID),
        FOREIGN KEY (Category_ID) REFERENCES CATEGORY (Category_ID),
        FOREIGN KEY (Staff_ID) REFERENCES STAFF (Staff_ID),
        FOREIGN KEY (Status_ID) REFERENCES STATUS (Status_ID)
    );

    CREATE TABLE IF NOT EXISTS ACTION (
        Action_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Issue_ID INTEGER NOT NULL,
        Staff_ID INTEGER NOT NULL,
        Action_Description TEXT NOT NULL,
        Action_Date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Issue_ID) REFERENCES ISSUE (Issue_ID) ON DELETE CASCADE,
        FOREIGN KEY (Staff_ID) REFERENCES STAFF (Staff_ID)
    );

    CREATE TABLE IF NOT EXISTS REASSIGNMENT_LOG (
        Reassign_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Issue_ID INTEGER NOT NULL,
        Old_Staff_ID INTEGER,
        New_Staff_ID INTEGER NOT NULL,
        Reassigned_On DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        Reason TEXT NOT NULL,
        FOREIGN KEY (Issue_ID) REFERENCES ISSUE (Issue_ID) ON DELETE CASCADE,
        FOREIGN KEY (Old_Staff_ID) REFERENCES STAFF (Staff_ID),
        FOREIGN KEY (New_Staff_ID) REFERENCES STAFF (Staff_ID)
    );

    CREATE TABLE IF NOT EXISTS FEEDBACK (
        Feedback_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Issue_ID INTEGER NOT NULL UNIQUE,
        Rating INTEGER NOT NULL CHECK (Rating BETWEEN 1 AND 5),
        Comments TEXT,
        Submitted_On DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Issue_ID) REFERENCES ISSUE (Issue_ID) ON DELETE CASCADE
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_issue_status ON ISSUE (Status_ID);
    CREATE INDEX IF NOT EXISTS idx_issue_staff ON ISSUE (Staff_ID);
    CREATE INDEX IF NOT EXISTS idx_issue_category ON ISSUE (Category_ID);
    CREATE INDEX IF NOT EXISTS idx_issue_student ON ISSUE (Student_ID);
    CREATE INDEX IF NOT EXISTS idx_action_issue ON ACTION (Issue_ID);
    CREATE INDEX IF NOT EXISTS idx_reassign_issue ON REASSIGNMENT_LOG (Issue_ID);

    -- Views
    CREATE VIEW IF NOT EXISTS v_issue_details AS
    SELECT 
        i.Issue_ID,
        i.Description,
        i.Location,
        i.Priority,
        i.Date_Submitted,
        i.Due_Date,
        s.Student_ID,
        s.Name AS Student_Name,
        s.Email AS Student_Email,
        s.Department AS Student_Dept,
        s.Year AS Student_Year,
        c.Category_ID,
        c.Category_Name,
        c.Default_SLA_Days,
        st.Status_ID,
        st.Status_Name,
        sf.Staff_ID,
        sf.Name AS Staff_Name,
        sf.Department AS Staff_Dept,
        sf.Role AS Staff_Role,
        CASE 
            WHEN i.Due_Date < date('now') AND st.Status_Name NOT IN ('Resolved', 'Closed') THEN 1 
            ELSE 0 
        END AS Is_Overdue
    FROM ISSUE i
    JOIN STUDENT s ON i.Student_ID = s.Student_ID
    JOIN CATEGORY c ON i.Category_ID = c.Category_ID
    JOIN STATUS st ON i.Status_ID = st.Status_ID
    LEFT JOIN STAFF sf ON i.Staff_ID = sf.Staff_ID;

    CREATE VIEW IF NOT EXISTS v_staff_workload AS
    SELECT 
        sf.Staff_ID,
        sf.Name AS Staff_Name,
        sf.Department,
        sf.Role,
        COUNT(i.Issue_ID) AS Total_Assigned,
        SUM(CASE WHEN st.Status_Name = 'Assigned' THEN 1 ELSE 0 END) AS Assigned_Count,
        SUM(CASE WHEN st.Status_Name = 'In Progress' THEN 1 ELSE 0 END) AS In_Progress_Count,
        SUM(CASE WHEN st.Status_Name = 'Resolved' THEN 1 ELSE 0 END) AS Resolved_Count,
        SUM(CASE WHEN st.Status_Name = 'Closed' THEN 1 ELSE 0 END) AS Closed_Count,
        SUM(CASE WHEN i.Due_Date < date('now') AND st.Status_Name NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS Overdue_Count
    FROM STAFF sf
    LEFT JOIN ISSUE i ON sf.Staff_ID = i.Staff_ID
    LEFT JOIN STATUS st ON i.Status_ID = st.Status_ID
    GROUP BY sf.Staff_ID, sf.Name, sf.Department, sf.Role;

    CREATE VIEW IF NOT EXISTS v_category_summary AS
    SELECT 
        c.Category_ID,
        c.Category_Name,
        c.Default_SLA_Days,
        COUNT(i.Issue_ID) AS Total_Issues,
        SUM(CASE WHEN st.Status_Name IN ('Submitted', 'Assigned', 'In Progress') THEN 1 ELSE 0 END) AS Open_Issues,
        SUM(CASE WHEN st.Status_Name IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS Resolved_Issues
    FROM CATEGORY c
    LEFT JOIN ISSUE i ON c.Category_ID = i.Category_ID
    LEFT JOIN STATUS st ON i.Status_ID = st.Status_ID
    GROUP BY c.Category_ID, c.Category_Name, c.Default_SLA_Days;
    """)

    # Insert Categories
    cur.executemany("INSERT OR IGNORE INTO CATEGORY (Category_ID, Category_Name, Default_SLA_Days) VALUES (?, ?, ?);", [
        (1, 'Academic', 5),
        (2, 'Administrative', 7),
        (3, 'Technical', 3),
        (4, 'Facilities', 4)
    ])

    # Insert Statuses
    cur.executemany("INSERT OR IGNORE INTO STATUS (Status_ID, Status_Name) VALUES (?, ?);", [
        (1, 'Submitted'),
        (2, 'Assigned'),
        (3, 'In Progress'),
        (4, 'Resolved'),
        (5, 'Closed')
    ])

    pwd_hash = 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387'

    # Insert Students
    cur.executemany("INSERT OR IGNORE INTO STUDENT (Student_ID, Name, Email, Department, Year, Password_Hash, Created_At) VALUES (?, ?, ?, ?, ?, ?, ?);", [
        (101, 'Ananya Ramesh', 'ananya@college.edu', 'Information Science & Engg', 3, pwd_hash, '2026-08-01 10:00:00'),
        (102, 'Rohan Sharma', 'rohan.sharma@college.edu', 'Computer Science & Engg', 3, pwd_hash, '2026-08-02 11:30:00'),
        (103, 'Priya Nair', 'priya.nair@college.edu', 'Electronics & Comm Engg', 2, pwd_hash, '2026-08-03 09:15:00'),
        (104, 'Karthik V', 'karthik.v@college.edu', 'Mechanical Engg', 4, pwd_hash, '2026-08-04 14:00:00'),
        (105, 'Sneha Patel', 'sneha.p@college.edu', 'Information Science & Engg', 2, pwd_hash, '2026-08-05 16:45:00'),
        (106, 'Rahul Roy', 'rahul.roy@college.edu', 'Civil Engg', 3, pwd_hash, '2026-08-06 12:10:00'),
        (107, 'Divya M', 'divya.m@college.edu', 'Computer Science & Engg', 4, pwd_hash, '2026-08-07 10:20:00'),
        (108, 'Amit Kumar', 'amit.k@college.edu', 'Electronics & Comm Engg', 1, pwd_hash, '2026-08-08 15:30:00'),
        (109, 'Tanvi Rao', 'tanvi.rao@college.edu', 'Information Science & Engg', 3, pwd_hash, '2026-08-09 13:00:00')
    ])

    # Insert Staff
    cur.executemany("INSERT OR IGNORE INTO STAFF (Staff_ID, Name, Email, Department, Role, Password_Hash, Created_At) VALUES (?, ?, ?, ?, ?, ?, ?);", [
        (201, 'Dr. Suresh Kumar', 'suresh@college.edu', 'Technical / IT', 'System Administrator & Lab Incharge', pwd_hash, '2026-07-01 09:00:00'),
        (202, 'Prof. Sunita Rao', 'sunita@college.edu', 'Academic', 'Academic Coordinator & Associate Prof', pwd_hash, '2026-07-01 09:00:00'),
        (203, 'Mr. Anand Murthy', 'anand@college.edu', 'Facilities', 'Campus Infrastructure Supervisor', pwd_hash, '2026-07-01 09:00:00'),
        (204, 'Mrs. Meena Iyer', 'meena@college.edu', 'Administrative', 'Student Affairs Officer', pwd_hash, '2026-07-01 09:00:00'),
        (205, 'Dr. Rajesh Verma', 'rajesh@college.edu', 'Academic', 'Dean of Academic Affairs', pwd_hash, '2026-07-01 09:00:00')
    ])

    # Insert Issues
    cur.executemany("INSERT OR IGNORE INTO ISSUE (Issue_ID, Student_ID, Category_ID, Staff_ID, Status_ID, Description, Date_Submitted, Location, Priority, Due_Date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", [
        (1, 101, 3, 201, 3, 'Classroom 302 ceiling projector HDMI port damaged; display shows severe pink distortion during lectures.', '2026-09-28 09:30:00', 'Academic Block A, Room 302', 'High', '2026-10-01'),
        (2, 102, 4, 203, 3, 'Hostel Block B 3rd floor water purifier is leaking continuously and pressure is too low for drinking water.', '2026-09-29 11:15:00', 'Hostel Block B, Floor 3', 'High', '2026-10-03'),
        (3, 103, 1, 202, 2, 'Grade sheet discrepancy for 4th Semester DBMS Lab exam marks not updated in college portal after re-evaluation.', '2026-10-01 14:00:00', 'Department Office, ISE Dept', 'High', '2026-10-06'),
        (4, 101, 2, 204, 4, 'Bonafide student certificate request for education loan subsidy pending verification for 10 days.', '2026-09-20 10:00:00', 'Administrative Building Counter 2', 'Medium', '2026-09-27'),
        (5, 104, 3, 201, 5, 'WiFi access points in Central Library 2nd floor disconnecting frequently during peak research hours.', '2026-09-18 16:20:00', 'Central Library, 2nd Floor', 'Medium', '2026-09-21'),
        (6, 105, 4, 203, 2, 'Classroom 405 air conditioner not cooling and producing loud rattling noise during classes.', '2026-10-02 08:45:00', 'Academic Block B, Room 405', 'Medium', '2026-10-06'),
        (7, 106, 1, None, 1, 'Request for elective course change approval from Cloud Computing to Advanced Database Systems.', '2026-10-03 09:10:00', 'Dean Academic Office', 'Low', '2026-10-08'),
        (8, 107, 2, 204, 3, 'Bus pass renewal counter delay and transaction receipt mismatch in student finance counter.', '2026-09-27 13:20:00', 'Finance Office Counter 4', 'Low', '2026-10-04'),
        (9, 108, 3, None, 1, 'Computer Lab 4 Desktop Workstation #12 experiences kernel panic and freeze on Linux boot.', '2026-10-03 11:00:00', 'Computer Lab 4, Desktop 12', 'Critical', '2026-10-06'),
        (10, 109, 4, 203, 5, 'Broken wooden bench and loose desk in Seminar Hall A causing safety concern during guest lectures.', '2026-09-15 15:30:00', 'Seminar Hall A', 'Medium', '2026-09-19'),
        (11, 102, 1, 205, 3, 'Medical leave attendance waiver form submitted on Sept 15th not updated in student attendance tracking portal.', '2026-09-25 10:15:00', 'Academic Affairs Section', 'High', '2026-09-30'),
        (12, 103, 4, 203, 4, 'Sports complex indoor badminton court floodlight fixture fused and flickering continuously.', '2026-09-22 17:00:00', 'Sports Complex Court 2', 'Low', '2026-09-26'),
        (13, 104, 3, 201, 3, 'College ERP and Moodle portal account locked out due to LDAP directory synchronization error.', '2026-09-16 11:45:00', 'Campus IT Data Center', 'High', '2026-09-19'),
        (14, 105, 2, 204, 2, 'Tuition fee refund balance for duplicate semester transaction via netbanking pending accountant signoff.', '2026-10-02 12:00:00', 'Accounts Branch', 'Critical', '2026-10-09')
    ])

    # Insert Actions
    cur.executemany("INSERT OR IGNORE INTO ACTION (Action_ID, Issue_ID, Staff_ID, Action_Description, Action_Date) VALUES (?, ?, ?, ?, ?);", [
        (1, 1, 201, 'Inspected projector in Room 302. Confirmed damaged HDMI connector pin. Replaced HDMI transmitter cable; ordered replacement wall port.', '2026-09-29 14:00:00'),
        (2, 1, 201, 'Installed interim VGA-to-HDMI active converter while new wall panel arrives.', '2026-09-30 16:30:00'),
        (3, 2, 203, 'Plumber inspected 3rd floor RO unit. Identified faulty float valve causing tank overflow. Closed inlet temporarily.', '2026-09-30 10:00:00'),
        (4, 2, 203, 'Installed replacement high-pressure diaphragm valve and sanitized storage chamber.', '2026-10-01 15:45:00'),
        (5, 4, 204, 'Verified student record with registrar office. Signed and stamped bonafide certificate.', '2026-09-25 11:30:00'),
        (6, 4, 204, 'Dispatched digitally signed certificate to student email and handed physical copy at Counter 2.', '2026-09-27 10:15:00'),
        (7, 5, 201, 'Rebooted Cisco Catalyst switch in Library. Replaced faulty Cat6 patch cable on AP-204 and upgraded firmware.', '2026-09-19 14:20:00'),
        (8, 8, 204, 'Checked banking reconciliation log with Canara Bank gateway. Matched transaction UTR number.', '2026-09-28 15:10:00'),
        (9, 10, 203, 'Carpentry team repaired bench frame, replaced broken pine slat, and secured bolts in Seminar Hall A.', '2026-09-18 12:00:00'),
        (10, 12, 203, 'Replaced 150W LED driver unit and ballast for badminton court lighting pole.', '2026-09-25 16:30:00')
    ])

    # Insert Reassignment Logs
    cur.executemany("INSERT OR IGNORE INTO REASSIGNMENT_LOG (Reassign_ID, Issue_ID, Old_Staff_ID, New_Staff_ID, Reassigned_On, Reason) VALUES (?, ?, ?, ?, ?, ?);", [
        (1, 1, 203, 201, '2026-09-28 10:45:00', 'Initially tagged as facility repair, reassigned to IT department as HDMI circuit replacement requires technical staff.'),
        (2, 8, 202, 204, '2026-09-27 14:00:00', 'Transferred from Academic office to Student Affairs / Administrative branch for financial verification.'),
        (3, 11, 202, 205, '2026-09-26 11:30:00', 'Escalated to Dean of Academic Affairs because attendance exemption beyond 10 days requires Dean authorization.'),
        (4, 13, 204, 201, '2026-09-16 12:15:00', 'Forwarded from Administrative office to System Administrator for LDAP server credential reset.')
    ])

    # Insert Feedback
    cur.executemany("INSERT OR IGNORE INTO FEEDBACK (Feedback_ID, Issue_ID, Rating, Comments, Submitted_On) VALUES (?, ?, ?, ?, ?);", [
        (1, 4, 5, 'Bonafide certificate was delivered on time for my loan bank subsidy. Great prompt support from Mrs. Meena Iyer.', '2026-09-28 09:00:00'),
        (2, 5, 4, 'Library WiFi is working stable now without disconnection. Speed is much improved.', '2026-09-22 10:30:00'),
        (3, 10, 5, 'The bench in Seminar Hall was repaired neatly before the guest lecture. Thank you!', '2026-09-20 17:15:00'),
        (4, 12, 4, 'Badminton court floodlight fixed quickly, sports practice resumed.', '2026-09-27 18:40:00')
    ])

    conn.commit()

def query_all(sql, params=None):
    """Execute query and return list of dictionaries."""
    conn = get_db_connection()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)
        adjusted_sql = sql.replace('%s', '?') if is_sqlite else sql
        
        if is_sqlite:
            cur = conn.cursor()
            cur.execute(adjusted_sql, params or ())
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        else:
            # MySQL / MariaDB
            cursor_kwargs = {'dictionary': True} if 'mysql.connector' in str(type(conn)) else {}
            cur = conn.cursor(**cursor_kwargs)
            cur.execute(adjusted_sql, params or ())
            rows = cur.fetchall()
            cur.close()
            return rows
    finally:
        conn.close()

def query_one(sql, params=None):
    """Execute query and return single row dictionary or None."""
    results = query_all(sql, params)
    return results[0] if results else None

def execute_stmt(sql, params=None):
    """Execute INSERT/UPDATE/DELETE statement, return lastrowid and affected rows."""
    conn = get_db_connection()
    try:
        is_sqlite = isinstance(conn, sqlite3.Connection)
        adjusted_sql = sql.replace('%s', '?') if is_sqlite else sql
        
        cur = conn.cursor()
        cur.execute(adjusted_sql, params or ())
        conn.commit()
        last_id = cur.lastrowid
        row_count = cur.rowcount
        cur.close()
        return {'lastrowid': last_id, 'rowcount': row_count}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
