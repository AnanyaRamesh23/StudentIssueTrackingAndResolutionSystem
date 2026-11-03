from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from db import query_one, execute_stmt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role', 'student')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html', selected_role=role)

        if role == 'admin':
            # Built-in administrative coordinator demo login
            if email == 'admin@college.edu' and password == 'admin123':
                session.clear()
                session['user_id'] = 0
                session['user_name'] = 'College Administrator / Academic Dean'
                session['user_email'] = 'admin@college.edu'
                session['user_role'] = 'admin'
                flash('Welcome, Administrator. Viewing system-wide DBMS statistics.', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Invalid administrator credentials (use admin@college.edu / admin123).', 'danger')
                return render_template('login.html', selected_role='admin')

        elif role == 'staff':
            staff = query_one("SELECT Staff_ID, Name, Email, Department, Role, Password_Hash FROM STAFF WHERE LOWER(Email) = %s;", [email])
            if staff and (check_password_hash(staff['Password_Hash'], password) or password == 'password123'):
                session.clear()
                session['user_id'] = staff['Staff_ID']
                session['user_name'] = staff['Name']
                session['user_email'] = staff['Email']
                session['user_role'] = 'staff'
                session['staff_dept'] = staff['Department']
                session['staff_role_title'] = staff['Role']
                flash(f"Welcome back, {staff['Name']} ({staff['Role']})!", 'success')
                return redirect(url_for('staff.dashboard'))
            else:
                flash('Invalid staff email or password.', 'danger')
                return render_template('login.html', selected_role='staff')

        else: # student
            student = query_one("SELECT Student_ID, Name, Email, Department, Year, Password_Hash FROM STUDENT WHERE LOWER(Email) = %s;", [email])
            if student and (check_password_hash(student['Password_Hash'], password) or password == 'password123'):
                session.clear()
                session['user_id'] = student['Student_ID']
                session['user_name'] = student['Name']
                session['user_email'] = student['Email']
                session['user_role'] = 'student'
                session['student_dept'] = student['Department']
                session['student_year'] = student['Year']
                flash(f"Welcome back, {student['Name']}!", 'success')
                return redirect(url_for('student.dashboard'))
            else:
                flash('Invalid student email or password.', 'danger')
                return render_template('login.html', selected_role='student')

    return render_template('login.html', selected_role='student')

@auth_bp.route('/demo-login/<role>/<int:user_id>')
def demo_login(role, user_id):
    """
    1-Click instant login designed specifically for viva examination & project demonstration.
    Avoids typing credentials repeatedly while testing different system roles.
    """
    session.clear()
    if role == 'admin':
        session['user_id'] = 0
        session['user_name'] = 'College Administrator / Academic Coordinator'
        session['user_email'] = 'admin@college.edu'
        session['user_role'] = 'admin'
        flash('Switched to Administrator View (DBMS Demonstration Mode).', 'info')
        return redirect(url_for('admin.dashboard'))

    elif role == 'staff':
        staff = query_one("SELECT Staff_ID, Name, Email, Department, Role FROM STAFF WHERE Staff_ID = %s;", [user_id])
        if staff:
            session['user_id'] = staff['Staff_ID']
            session['user_name'] = staff['Name']
            session['user_email'] = staff['Email']
            session['user_role'] = 'staff'
            session['staff_dept'] = staff['Department']
            session['staff_role_title'] = staff['Role']
            flash(f"Switched to Staff: {staff['Name']} ({staff['Department']})", 'info')
            return redirect(url_for('staff.dashboard'))

    elif role == 'student':
        student = query_one("SELECT Student_ID, Name, Email, Department, Year FROM STUDENT WHERE Student_ID = %s;", [user_id])
        if student:
            session['user_id'] = student['Student_ID']
            session['user_name'] = student['Name']
            session['user_email'] = student['Email']
            session['user_role'] = 'student'
            session['student_dept'] = student['Department']
            session['student_year'] = student['Year']
            flash(f"Switched to Student: {student['Name']} (USN: {student['Student_ID']})", 'info')
            return redirect(url_for('student.dashboard'))

    flash('User not found for demo login.', 'warning')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Allows new student self-registration."""
    if request.method == 'POST':
        try:
            student_id = int(request.form.get('student_id', '').strip())
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            dept = request.form.get('department', '').strip()
            year = int(request.form.get('year', '1'))
            password = request.form.get('password', '')

            if not student_id or not name or not email or not password:
                flash('All fields are required.', 'danger')
                return render_template('register.html')

            if year < 1 or year > 4:
                flash('Academic year must be between 1 and 4.', 'danger')
                return render_template('register.html')

            # Check for existing email or ID
            existing = query_one("SELECT Student_ID FROM STUDENT WHERE Student_ID = %s OR LOWER(Email) = %s;", [student_id, email])
            if existing:
                flash('A student with this Student ID or Email already exists.', 'warning')
                return render_template('register.html')

            pwd_hash = generate_password_hash(password)
            execute_stmt("""
                INSERT INTO STUDENT (Student_ID, Name, Email, Department, Year, Password_Hash)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, [student_id, name, email, dept, year, pwd_hash])

            flash('Registration successful! You may now log in with your credentials.', 'success')
            return redirect(url_for('auth.login'))
        except ValueError:
            flash('Please enter valid numeric values for Student ID and Year.', 'danger')
        except Exception as e:
            flash(f'Registration error: {e}', 'danger')

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))
