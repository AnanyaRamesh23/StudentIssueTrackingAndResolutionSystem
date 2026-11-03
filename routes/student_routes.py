from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from services.issue_service import (
    get_issues, get_issue_by_id, create_issue, submit_feedback,
    get_all_categories, get_all_statuses, get_all_staff
)

student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'student':
            flash('Access restricted to students.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/dashboard')
@student_required
def dashboard():
    student_id = session['user_id']
    issues = get_issues({'student_id': student_id})
    
    total = len(issues)
    submitted = sum(1 for i in issues if i['Status_ID'] == 1)
    assigned = sum(1 for i in issues if i['Status_ID'] == 2)
    in_progress = sum(1 for i in issues if i['Status_ID'] == 3)
    resolved = sum(1 for i in issues if i['Status_ID'] == 4)
    closed = sum(1 for i in issues if i['Status_ID'] == 5)
    overdue = sum(1 for i in issues if i.get('Is_Overdue'))

    return render_template(
        'student_dashboard.html',
        issues=issues[:5], # Recent 5
        stats={
            'total': total,
            'submitted': submitted,
            'assigned': assigned,
            'in_progress': in_progress,
            'resolved': resolved,
            'closed': closed,
            'overdue': overdue
        }
    )

@student_bp.route('/submit-issue', methods=['GET', 'POST'])
@student_bp.route('/submit', methods=['GET', 'POST'])
@student_required
def submit_issue_page():
    if request.method == 'POST':
        student_id = session['user_id']
        category_id = request.form.get('category_id')
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        priority = request.form.get('priority', 'Medium')

        if not category_id or not description or not location or not priority:
            flash('All fields are required to submit an issue.', 'danger')
            return render_template('submit_issue.html', categories=get_all_categories())

        try:
            issue_id = create_issue(
                student_id=student_id,
                category_id=int(category_id),
                description=description,
                location=location,
                priority=priority
            )
            flash(f'Issue #{issue_id} submitted successfully! Our staff will review and act on it according to the category SLA.', 'success')
            return redirect(url_for('student.my_issues'))
        except Exception as e:
            flash(f'Error submitting issue: {e}', 'danger')

    categories = get_all_categories()
    return render_template('submit_issue.html', categories=categories)

@student_bp.route('/my-issues')
@student_required
def my_issues():
    student_id = session['user_id']
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')
    priority_filter = request.args.get('priority')
    search_term = request.args.get('q')

    filters = {'student_id': student_id}
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

    return render_template(
        'my_issues.html',
        issues=issues,
        categories=categories,
        statuses=statuses,
        selected_status=status_filter,
        selected_category=category_filter,
        selected_priority=priority_filter,
        search_query=search_term
    )

@student_bp.route('/issue/<int:issue_id>/feedback', methods=['POST'])
@student_required
def post_feedback(issue_id):
    student_id = session['user_id']
    issue = get_issue_by_id(issue_id)

    if not issue or issue['Student_ID'] != student_id:
        flash('Unauthorized or issue not found.', 'danger')
        return redirect(url_for('student.my_issues'))

    if issue['Status_ID'] not in (4, 5):
        flash('Feedback can only be submitted once the issue has been resolved or closed.', 'warning')
        return redirect(url_for('student.view_issue_details', issue_id=issue_id))

    if issue.get('feedback'):
        flash('Feedback has already been submitted for this issue (1:1 Relationship Enforced).', 'info')
        return redirect(url_for('student.view_issue_details', issue_id=issue_id))

    try:
        rating = int(request.form.get('rating', '5'))
        comments = request.form.get('comments', '').strip()
        submit_feedback(issue_id, rating, comments)
        flash('Thank you! Your feedback has been recorded successfully.', 'success')
    except Exception as e:
        flash(f'Failed to record feedback: {e}', 'danger')

    return redirect(url_for('student.view_issue_details', issue_id=issue_id))

@student_bp.route('/issue/<int:issue_id>')
def view_issue_details(issue_id):
    """View details for an issue (accessible by logged-in users)."""
    if 'user_id' not in session:
        flash('Please log in to view issue details.', 'warning')
        return redirect(url_for('auth.login'))

    issue = get_issue_by_id(issue_id)
    if not issue:
        flash(f'Issue #{issue_id} was not found.', 'danger')
        return redirect(url_for('student.my_issues'))

    # If student, ensure they only view their own issues
    if session.get('user_role') == 'student' and issue['Student_ID'] != session['user_id']:
        flash('You are not authorized to view issues submitted by another student.', 'danger')
        return redirect(url_for('student.my_issues'))

    all_staff = get_all_staff()
    return render_template('issue_details.html', issue=issue, all_staff=all_staff)
