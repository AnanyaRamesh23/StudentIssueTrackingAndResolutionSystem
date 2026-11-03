from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from services.issue_service import (
    get_issues, get_issue_by_id, update_issue_status, add_action,
    reassign_issue, assign_initial_staff, get_all_categories,
    get_all_statuses, get_all_staff
)

staff_bp = Blueprint('staff', __name__)

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') not in ('staff', 'admin'):
            flash('Access restricted to college staff members.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@staff_bp.route('/dashboard')
@staff_required
def dashboard():
    staff_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'

    # Retrieve issues assigned to this staff member (or all if admin)
    assigned_issues = get_issues({'staff_id': staff_id} if not is_admin else {})
    # Also retrieve unassigned issues (Status_ID = 1 Submitted and Staff_ID IS NULL)
    unassigned_issues = get_issues({'status_id': 1})
    unassigned_issues = [i for i in unassigned_issues if not i.get('Staff_ID')]

    total_assigned = len(assigned_issues)
    in_progress = sum(1 for i in assigned_issues if i['Status_ID'] == 3)
    resolved = sum(1 for i in assigned_issues if i['Status_ID'] == 4)
    closed = sum(1 for i in assigned_issues if i['Status_ID'] == 5)
    overdue = sum(1 for i in assigned_issues if i.get('Is_Overdue'))

    return render_template(
        'staff_dashboard.html',
        assigned_issues=assigned_issues[:6],
        unassigned_issues=unassigned_issues[:5],
        stats={
            'total_assigned': total_assigned,
            'in_progress': in_progress,
            'resolved': resolved,
            'closed': closed,
            'overdue': overdue,
            'unassigned_count': len(unassigned_issues)
        }
    )

@staff_bp.route('/assigned-issues')
@staff_required
def assigned_issues():
    staff_id = session['user_id']
    view_scope = request.args.get('scope', 'mine') # 'mine' or 'all'
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')
    priority_filter = request.args.get('priority')
    search_term = request.args.get('q')

    filters = {}
    if view_scope == 'mine' and session.get('user_role') != 'admin':
        filters['staff_id'] = staff_id

    if status_filter:
        filters['status_id'] = status_filter
    if category_filter:
        filters['category_id'] = category_filter
    if priority_filter:
        filters['priority'] = priority_filter
    if search_term:
        filters['search'] = search_term

    issues = get_issues(filters)
    categories = get_all_categories()
    statuses = get_all_statuses()
    all_staff_members = get_all_staff()

    return render_template(
        'assigned_issues.html',
        issues=issues,
        categories=categories,
        statuses=statuses,
        all_staff=all_staff_members,
        selected_scope=view_scope,
        selected_status=status_filter,
        selected_category=category_filter,
        selected_priority=priority_filter,
        search_query=search_term
    )

@staff_bp.route('/claim-issue/<int:issue_id>', methods=['POST'])
@staff_required
def claim_issue(issue_id):
    """Claim an unassigned issue."""
    staff_id = session['user_id']
    try:
        assign_initial_staff(issue_id, staff_id)
        flash(f'Issue #{issue_id} has been assigned to you. Status changed to Assigned.', 'success')
    except Exception as e:
        flash(f'Error claiming issue: {e}', 'danger')
    return redirect(url_for('staff.dashboard'))

@staff_bp.route('/update-status', methods=['POST'])
@staff_required
def update_status():
    """Update issue status and optionally log action inside a transaction."""
    issue_id = int(request.form.get('issue_id'))
    new_status_id = int(request.form.get('status_id'))
    staff_id = session['user_id']
    action_desc = request.form.get('action_description', '').strip()

    try:
        update_issue_status(issue_id, new_status_id, staff_id, action_desc)
        flash(f'Status for Issue #{issue_id} updated successfully.', 'success')
    except Exception as e:
        flash(f'Failed to update status: {e}', 'danger')

    return redirect(url_for('student.view_issue_details', issue_id=issue_id))

@staff_bp.route('/add-action', methods=['POST'])
@staff_required
def post_action():
    """Add a concrete action log entry for an issue."""
    issue_id = int(request.form.get('issue_id'))
    staff_id = session['user_id']
    action_desc = request.form.get('action_description', '').strip()

    if not action_desc:
        flash('Action description is required.', 'danger')
        return redirect(url_for('student.view_issue_details', issue_id=issue_id))

    try:
        add_action(issue_id, staff_id, action_desc)
        flash('Action recorded successfully in the issue audit trail.', 'success')
    except Exception as e:
        flash(f'Error recording action: {e}', 'danger')

    return redirect(url_for('student.view_issue_details', issue_id=issue_id))

@staff_bp.route('/reassign', methods=['POST'])
@staff_required
def post_reassignment():
    """Reassign issue to another staff member with mandatory reason (ACID Transaction)."""
    issue_id = int(request.form.get('issue_id'))
    new_staff_id = int(request.form.get('new_staff_id'))
    reason = request.form.get('reason', '').strip()
    current_staff_id = session['user_id']

    if not reason:
        flash('A clear reason is required for reassigning an issue.', 'danger')
        return redirect(url_for('student.view_issue_details', issue_id=issue_id))

    try:
        reassign_issue(issue_id, new_staff_id, reason, current_staff_id)
        flash(f'Issue #{issue_id} was successfully reassigned to new staff. Audit log created.', 'success')
    except Exception as e:
        flash(f'Failed to reassign issue: {e}', 'danger')

    return redirect(url_for('student.view_issue_details', issue_id=issue_id))
