"""
Issue Service Layer
Encapsulates all SQL business logic, queries, aggregations, views, and transactions.
Student Issue Tracking and Resolution System - DBMS Project
"""

import datetime
from db import query_all, query_one, execute_stmt, get_db_connection

# Status IDs mapping for reference:
# 1: Submitted
# 2: Assigned
# 3: In Progress
# 4: Resolved
# 5: Closed

VALID_TRANSITIONS = {
    1: [2, 3],       # Submitted can move to Assigned or directly to In Progress (if staff begins work)
    2: [3, 4],       # Assigned can move to In Progress or Resolved
    3: [4],          # In Progress moves to Resolved
    4: [5, 3],       # Resolved can be Closed (or reopened to In Progress if student rejects)
    5: []            # Closed is terminal
}

def get_all_categories():
    """Retrieve all issue categories."""
    return query_all("SELECT Category_ID, Category_Name, Default_SLA_Days FROM CATEGORY ORDER BY Category_ID;")

def get_all_statuses():
    """Retrieve all predefined statuses."""
    return query_all("SELECT Status_ID, Status_Name FROM STATUS ORDER BY Status_ID;")

def get_all_staff():
    """Retrieve all staff members."""
    return query_all("SELECT Staff_ID, Name, Email, Department, Role FROM STAFF ORDER BY Name;")

def get_issues(filters=None):
    """
    Retrieve issues based on dynamic filters using the consolidated VIEW v_issue_details.
    Demonstrates: Views, Multi-Table JOINs, Dynamic WHERE Filtering.
    """
    filters = filters or {}
    sql = """
        SELECT 
            Issue_ID, Description, Location, Priority, Date_Submitted, Due_Date,
            Student_ID, Student_Name, Student_Email, Student_Dept, Student_Year,
            Category_ID, Category_Name, Default_SLA_Days,
            Status_ID, Status_Name,
            Staff_ID, Staff_Name, Staff_Dept, Staff_Role,
            Is_Overdue
        FROM v_issue_details
        WHERE 1=1
    """
    params = []

    if filters.get('student_id'):
        sql += " AND Student_ID = %s"
        params.append(filters['student_id'])

    if filters.get('staff_id'):
        sql += " AND Staff_ID = %s"
        params.append(filters['staff_id'])

    if filters.get('category_id'):
        sql += " AND Category_ID = %s"
        params.append(filters['category_id'])

    if filters.get('status_id'):
        sql += " AND Status_ID = %s"
        params.append(filters['status_id'])

    if filters.get('priority'):
        sql += " AND Priority = %s"
        params.append(filters['priority'])

    if filters.get('is_overdue'):
        sql += " AND Is_Overdue = 1"

    if filters.get('search'):
        sql += " AND (Description LIKE %s OR Location LIKE %s OR Student_Name LIKE %s)"
        term = f"%{filters['search']}%"
        params.extend([term, term, term])

    sql += " ORDER BY Date_Submitted DESC;"
    return query_all(sql, params)

def get_issue_by_id(issue_id):
    """
    Retrieve full issue details including its actions, reassignment history, and 1:1 feedback.
    Demonstrates: Primary Key lookups, Multi-table Joins, 1:N and 1:1 relationships.
    """
    issue = query_one("""
        SELECT 
            Issue_ID, Description, Location, Priority, Date_Submitted, Due_Date,
            Student_ID, Student_Name, Student_Email, Student_Dept, Student_Year,
            Category_ID, Category_Name, Default_SLA_Days,
            Status_ID, Status_Name,
            Staff_ID, Staff_Name, Staff_Dept, Staff_Role,
            Is_Overdue
        FROM v_issue_details
        WHERE Issue_ID = %s;
    """, [issue_id])

    if not issue:
        return None

    # Fetch chronological actions taken on this issue (Issue 1 -> N Action, Staff 1 -> N Action)
    actions = query_all("""
        SELECT 
            a.Action_ID, a.Action_Description, a.Action_Date,
            s.Staff_ID, s.Name AS Staff_Name, s.Department AS Staff_Dept, s.Role AS Staff_Role
        FROM ACTION a
        JOIN STAFF s ON a.Staff_ID = s.Staff_ID
        WHERE a.Issue_ID = %s
        ORDER BY a.Action_Date ASC;
    """, [issue_id])

    # Fetch reassignment history (Issue 1 -> N Reassignment_Log)
    reassignments = query_all("""
        SELECT 
            r.Reassign_ID, r.Reassigned_On, r.Reason,
            old_s.Staff_ID AS Old_Staff_ID, old_s.Name AS Old_Staff_Name,
            new_s.Staff_ID AS New_Staff_ID, new_s.Name AS New_Staff_Name
        FROM REASSIGNMENT_LOG r
        LEFT JOIN STAFF old_s ON r.Old_Staff_ID = old_s.Staff_ID
        JOIN STAFF new_s ON r.New_Staff_ID = new_s.Staff_ID
        WHERE r.Issue_ID = %s
        ORDER BY r.Reassigned_On ASC;
    """, [issue_id])

    # Fetch feedback (Issue 1 -> 1 Feedback)
    feedback = query_one("""
        SELECT Feedback_ID, Rating, Comments, Submitted_On
        FROM FEEDBACK
        WHERE Issue_ID = %s;
    """, [issue_id])

    issue['actions'] = actions
    issue['reassignments'] = reassignments
    issue['feedback'] = feedback
    return issue

def create_issue(student_id, category_id, description, location, priority, due_date=None):
    """
    Inserts a new student issue into the database.
    Calculates SLA Due_Date based on Category.Default_SLA_Days if not explicitly provided.
    Prevents duplicate submissions for active issues.
    """
    clean_desc = (description or '').strip()
    clean_loc = (location or '').strip()

    # Prevent duplicate active issue submission by the same student
    existing = query_one("""
        SELECT Issue_ID FROM ISSUE 
        WHERE Student_ID = %s 
          AND Category_ID = %s 
          AND LOWER(TRIM(Location)) = LOWER(TRIM(%s)) 
          AND LOWER(TRIM(Description)) = LOWER(TRIM(%s))
          AND Status_ID IN (1, 2, 3);
    """, [student_id, category_id, clean_loc, clean_desc])

    if existing:
        raise ValueError(f"A ticket (#{existing['Issue_ID']}) is already active for this issue and location. Duplicate submission prevented.")

    if not due_date:
        cat = query_one("SELECT Default_SLA_Days FROM CATEGORY WHERE Category_ID = %s;", [category_id])
        sla_days = cat['Default_SLA_Days'] if cat else 5
        due_date = (datetime.date.today() + datetime.timedelta(days=sla_days)).isoformat()

    res = execute_stmt("""
        INSERT INTO ISSUE (Student_ID, Category_ID, Staff_ID, Status_ID, Description, Date_Submitted, Location, Priority, Due_Date)
        VALUES (%s, %s, NULL, 1, %s, %s, %s, %s, %s);
    """, [student_id, category_id, clean_desc, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), clean_loc, priority, due_date])

    return res['lastrowid']

def assign_initial_staff(issue_id, staff_id):
    """Assigns an unassigned issue to a staff member and transitions status from Submitted to Assigned."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        is_sqlite = 'sqlite' in str(type(conn)).lower()
        
        # Check current status
        cur.execute("SELECT Status_ID, Staff_ID FROM ISSUE WHERE Issue_ID = ?" if is_sqlite else "SELECT Status_ID, Staff_ID FROM ISSUE WHERE Issue_ID = %s", (issue_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Issue {issue_id} not found.")

        current_status = row[0] if isinstance(row, tuple) else row['Status_ID']
        new_status = 2 if current_status == 1 else current_status

        stmt1 = "UPDATE ISSUE SET Staff_ID = ?, Status_ID = ? WHERE Issue_ID = ?" if is_sqlite else "UPDATE ISSUE SET Staff_ID = %s, Status_ID = %s WHERE Issue_ID = %s"
        cur.execute(stmt1, (staff_id, new_status, issue_id))

        stmt2 = "INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date) VALUES (?, ?, ?, ?)" if is_sqlite else "INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date) VALUES (%s, %s, %s, %s)"
        cur.execute(stmt2, (issue_id, staff_id, "Assigned issue to staff member.", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def update_issue_status(issue_id, new_status_id, staff_id, action_description=None):
    """
    Updates the status of an issue and records the action inside an explicit ACID Transaction.
    Enforces valid issue lifecycle flow: Submitted -> Assigned -> In Progress -> Resolved -> Closed.
    Demonstrates: ACID Transactions, CHECK logic, State transition validation.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        is_sqlite = 'sqlite' in str(type(conn)).lower()
        
        cur.execute("SELECT Status_ID, Staff_ID FROM ISSUE WHERE Issue_ID = ?" if is_sqlite else "SELECT Status_ID, Staff_ID FROM ISSUE WHERE Issue_ID = %s", (issue_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Issue {issue_id} not found.")

        current_status_id = row[0] if isinstance(row, tuple) else row['Status_ID']
        current_staff_id = row[1] if isinstance(row, tuple) else row['Staff_ID']

        # Prevent invalid transitions
        allowed = VALID_TRANSITIONS.get(current_status_id, [])
        if int(new_status_id) not in allowed and int(new_status_id) != current_status_id:
            raise ValueError(f"Invalid status transition from status {current_status_id} to {new_status_id}.")

        # Assign staff if currently unassigned
        assign_staff = staff_id if not current_staff_id else current_staff_id

        # Update Issue Status
        stmt1 = "UPDATE ISSUE SET Status_ID = ?, Staff_ID = ? WHERE Issue_ID = ?" if is_sqlite else "UPDATE ISSUE SET Status_ID = %s, Staff_ID = %s WHERE Issue_ID = %s"
        cur.execute(stmt1, (new_status_id, assign_staff, issue_id))

        # Record action if provided
        if action_description and action_description.strip():
            stmt2 = "INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date) VALUES (?, ?, ?, ?)" if is_sqlite else "INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date) VALUES (%s, %s, %s, %s)"
            cur.execute(stmt2, (issue_id, staff_id, action_description.strip(), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def reassign_issue(issue_id, new_staff_id, reason, current_staff_id):
    """
    Reassigns an issue to another staff member and logs the event in REASSIGNMENT_LOG.
    Demonstrates: Explicit ACID Transaction (Commit/Rollback), Stored Procedure / Multi-table update.
    """
    if not reason or not reason.strip():
        raise ValueError("A valid reassignment reason is required.")

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        is_sqlite = 'sqlite' in str(type(conn)).lower()

        # Step 1: Read current staff
        cur.execute("SELECT Staff_ID, Status_ID FROM ISSUE WHERE Issue_ID = ?" if is_sqlite else "SELECT Staff_ID, Status_ID FROM ISSUE WHERE Issue_ID = %s", (issue_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Issue {issue_id} not found.")

        old_staff_id = row[0] if isinstance(row, tuple) else row['Staff_ID']
        current_status_id = row[1] if isinstance(row, tuple) else row['Status_ID']

        # If issue was Submitted (1), move to Assigned (2)
        new_status_id = 2 if current_status_id == 1 else current_status_id

        # Step 2: Update ISSUE table
        stmt_update = "UPDATE ISSUE SET Staff_ID = ?, Status_ID = ? WHERE Issue_ID = ?" if is_sqlite else "UPDATE ISSUE SET Staff_ID = %s, Status_ID = %s WHERE Issue_ID = %s"
        cur.execute(stmt_update, (new_staff_id, new_status_id, issue_id))

        # Step 3: Insert into REASSIGNMENT_LOG table
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stmt_log = "INSERT INTO REASSIGNMENT_LOG (Issue_ID, Old_Staff_ID, New_Staff_ID, Reassigned_On, Reason) VALUES (?, ?, ?, ?, ?)" if is_sqlite else "INSERT INTO REASSIGNMENT_LOG (Issue_ID, Old_Staff_ID, New_Staff_ID, Reassigned_On, Reason) VALUES (%s, %s, %s, %s, %s)"
        cur.execute(stmt_log, (issue_id, old_staff_id, new_staff_id, now_str, reason.strip()))

        # Step 4: Record into ACTION table for issue timeline audit
        action_note = f"Issue reassigned to staff #{new_staff_id}. Reason: {reason.strip()}"
        stmt_action = "INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date) VALUES (?, ?, ?, ?)" if is_sqlite else "INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date) VALUES (%s, %s, %s, %s)"
        cur.execute(stmt_action, (issue_id, new_staff_id, action_note, now_str))

        # Step 5: Commit transaction
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def add_action(issue_id, staff_id, action_description):
    """
    Appends an action/investigation note to an issue and updates status to In Progress if currently Assigned.
    """
    if not action_description or not action_description.strip():
        raise ValueError("Action description cannot be empty.")

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        is_sqlite = 'sqlite' in str(type(conn)).lower()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert action
        stmt1 = "INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date) VALUES (?, ?, ?, ?)" if is_sqlite else "INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date) VALUES (%s, %s, %s, %s)"
        cur.execute(stmt1, (issue_id, staff_id, action_description.strip(), now_str))

        # If status is Assigned (2), move to In Progress (3)
        stmt2 = "UPDATE ISSUE SET Status_ID = 3 WHERE Issue_ID = ? AND Status_ID = 2" if is_sqlite else "UPDATE ISSUE SET Status_ID = 3 WHERE Issue_ID = %s AND Status_ID = 2"
        cur.execute(stmt2, (issue_id,))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def submit_feedback(issue_id, rating, comments=None):
    """
    Records student feedback for a Resolved or Closed issue.
    Demonstrates: 1:1 Relationship (UNIQUE constraint on Issue_ID), CHECK constraint (Rating 1..5).
    """
    rating = int(rating)
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be an integer between 1 and 5.")

    issue = query_one("SELECT Status_ID FROM ISSUE WHERE Issue_ID = %s;", [issue_id])
    if not issue:
        raise ValueError(f"Issue {issue_id} not found.")

    if issue['Status_ID'] not in (4, 5):
        raise ValueError("Feedback can only be submitted after an issue has been Resolved or Closed.")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return execute_stmt("""
        INSERT INTO FEEDBACK (Issue_ID, Rating, Comments, Submitted_On)
        VALUES (%s, %s, %s, %s);
    """, [issue_id, rating, (comments or '').strip(), now_str])

def get_dashboard_stats():
    """
    Computes system-wide aggregate statistics.
    Demonstrates: COUNT, SUM with CASE, GROUP BY, Aggregate functions.
    """
    # Overview status counts
    counts = query_one("""
        SELECT 
            COUNT(Issue_ID) AS Total,
            SUM(CASE WHEN Status_ID = 1 THEN 1 ELSE 0 END) AS Submitted,
            SUM(CASE WHEN Status_ID = 2 THEN 1 ELSE 0 END) AS Assigned,
            SUM(CASE WHEN Status_ID = 3 THEN 1 ELSE 0 END) AS In_Progress,
            SUM(CASE WHEN Status_ID = 4 THEN 1 ELSE 0 END) AS Resolved,
            SUM(CASE WHEN Status_ID = 5 THEN 1 ELSE 0 END) AS Closed
        FROM ISSUE;
    """)

    # Overdue count (derived condition: Due_Date < CURDATE() and status not in (4, 5))
    overdue = query_one("""
        SELECT COUNT(*) AS Overdue_Count 
        FROM v_issue_details 
        WHERE Is_Overdue = 1;
    """)

    # Breakdown by Category (GROUP BY)
    by_category = query_all("""
        SELECT 
            c.Category_ID,
            c.Category_Name,
            c.Default_SLA_Days,
            COUNT(i.Issue_ID) AS Issue_Count,
            SUM(CASE WHEN i.Status_ID IN (1, 2, 3) THEN 1 ELSE 0 END) AS Active_Count,
            SUM(CASE WHEN i.Status_ID IN (4, 5) THEN 1 ELSE 0 END) AS Completed_Count
        FROM CATEGORY c
        LEFT JOIN ISSUE i ON c.Category_ID = i.Category_ID
        GROUP BY c.Category_ID, c.Category_Name, c.Default_SLA_Days
        ORDER BY Issue_Count DESC;
    """)

    # Breakdown by Priority (GROUP BY)
    by_priority = query_all("""
        SELECT 
            Priority,
            COUNT(Issue_ID) AS Priority_Count
        FROM ISSUE
        GROUP BY Priority
        ORDER BY FIELD(Priority, 'Critical', 'High', 'Medium', 'Low') 
        COLLATE NOCASE;
    """) if 'mysql' in str(type(get_db_connection())).lower() else query_all("""
        SELECT Priority, COUNT(Issue_ID) AS Priority_Count
        FROM ISSUE
        GROUP BY Priority
        ORDER BY CASE Priority
            WHEN 'Critical' THEN 1
            WHEN 'High' THEN 2
            WHEN 'Medium' THEN 3
            WHEN 'Low' THEN 4
            ELSE 5
        END;
    """)

    # Average Feedback Rating
    rating_stats = query_one("""
        SELECT 
            COUNT(Feedback_ID) AS Feedback_Count,
            ROUND(AVG(Rating), 2) AS Average_Rating
        FROM FEEDBACK;
    """)

    return {
        'total': counts['Total'] if counts else 0,
        'submitted': counts['Submitted'] if counts else 0,
        'assigned': counts['Assigned'] if counts else 0,
        'in_progress': counts['In_Progress'] if counts else 0,
        'resolved': counts['Resolved'] if counts else 0,
        'closed': counts['Closed'] if counts else 0,
        'overdue': overdue['Overdue_Count'] if overdue else 0,
        'by_category': by_category,
        'by_priority': by_priority,
        'feedback_count': rating_stats['Feedback_Count'] if rating_stats else 0,
        'average_rating': rating_stats['Average_Rating'] if rating_stats and rating_stats['Average_Rating'] is not None else 'N/A'
    }

def get_staff_workload():
    """
    Demonstrates: Database View v_staff_workload and Aggregation.
    """
    return query_all("""
        SELECT 
            Staff_ID, Staff_Name, Department, Role,
            Total_Assigned, Assigned_Count, In_Progress_Count, Resolved_Count, Closed_Count, Overdue_Count
        FROM v_staff_workload
        ORDER BY Total_Assigned DESC;
    """)

def get_staff_workload_having(min_issues=1):
    """
    Demonstrates: GROUP BY with HAVING clause (filtering aggregated results).
    Returns staff who have handled at least `min_issues`.
    """
    return query_all("""
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
        HAVING COUNT(i.Issue_ID) >= %s
        ORDER BY Issue_Count DESC;
    """, [min_issues])
