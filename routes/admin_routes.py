from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from functools import wraps
from services.issue_service import (
    get_dashboard_stats, get_staff_workload, get_staff_workload_having,
    get_issues, get_all_categories, get_all_statuses, get_all_staff
)
from db import query_all, get_active_db_engine

admin_bp = Blueprint('admin', __name__)

def admin_or_staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to view management overview.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@admin_or_staff_required
def dashboard():
    stats = get_dashboard_stats()
    workload = get_staff_workload()
    recent_issues = get_issues({})[:8]
    active_engine = get_active_db_engine()

    return render_template(
        'admin_dashboard.html',
        stats=stats,
        workload=workload,
        recent_issues=recent_issues,
        active_engine=active_engine
    )

@admin_bp.route('/dbms-demo')
@admin_or_staff_required
def dbms_demo():
    """
    Dedicated DBMS Viva & Concepts Demonstration Page.
    Renders live query results, schema normalization proofs, views, triggers, and transactions.
    """
    active_engine = get_active_db_engine()

    # 1. Live Query Demonstration: Multi-Table JOIN
    join_results = query_all("""
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
        ORDER BY i.Issue_ID ASC
        LIMIT 6;
    """)

    # 2. Live Query Demonstration: GROUP BY and HAVING
    having_results = get_staff_workload_having(min_issues=2)

    # 3. Live Query Demonstration: View Inspection (v_staff_workload)
    view_workload = query_all("SELECT * FROM v_staff_workload LIMIT 5;")

    # 4. Live Query Demonstration: Reassignment Audit Log (Audit Trail Integrity)
    reassignment_logs = query_all("""
        SELECT 
            r.Reassign_ID, r.Issue_ID,
            old_s.Name AS Old_Staff,
            new_s.Name AS New_Staff,
            r.Reassigned_On,
            r.Reason
        FROM REASSIGNMENT_LOG r
        LEFT JOIN STAFF old_s ON r.Old_Staff_ID = old_s.Staff_ID
        JOIN STAFF new_s ON r.New_Staff_ID = new_s.Staff_ID
        ORDER BY r.Reassign_ID DESC;
    """)

    # 5. Live Query Demonstration: 1:1 Feedback Relationship
    feedback_ratings = query_all("""
        SELECT 
            f.Feedback_ID, f.Issue_ID, f.Rating, f.Comments, f.Submitted_On,
            s.Name AS Student_Name, sf.Name AS Staff_Name, c.Category_Name
        FROM FEEDBACK f
        JOIN ISSUE i ON f.Issue_ID = i.Issue_ID
        JOIN STUDENT s ON i.Student_ID = s.Student_ID
        JOIN CATEGORY c ON i.Category_ID = c.Category_ID
        LEFT JOIN STAFF sf ON i.Staff_ID = sf.Staff_ID;
    """)

    return render_template(
        'dbms_demo.html',
        active_engine=active_engine,
        join_results=join_results,
        having_results=having_results,
        view_workload=view_workload,
        reassignment_logs=reassignment_logs,
        feedback_ratings=feedback_ratings
    )
