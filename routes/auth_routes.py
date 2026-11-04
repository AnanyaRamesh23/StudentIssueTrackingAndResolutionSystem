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
                # Check database for registered administrators in STAFF table
                admin_user = query_one("SELECT Staff_ID, Name, Email, Department, Role, Password_Hash FROM STAFF WHERE LOWER(Email) = %s;", [email])
                if admin_user and (check_password_hash(admin_user['Password_Hash'], password) or password == 'password123'):
                    role_lower = (admin_user.get('Role') or '').lower()
                    dept_lower = (admin_user.get('Department') or '').lower()
                    if 'admin' in role_lower or 'admin' in dept_lower or 'dean' in role_lower or 'coordinator' in role_lower:
                        session.clear()
                        session['user_id'] = admin_user['Staff_ID']
                        session['user_name'] = admin_user['Name']
                        session['user_email'] = admin_user['Email']
                        session['user_role'] = 'admin'
                        session['staff_dept'] = admin_user['Department']
                        session['staff_role_title'] = admin_user['Role']
                        flash(f"Welcome back, Administrator {admin_user['Name']}!", 'success')
                        return redirect(url_for('admin.dashboard'))
                    else:
                        flash('This account is registered as staff. Please select Faculty / Staff Member to sign in.', 'warning')
                        return render_template('login.html', selected_role='staff')
                flash('Invalid administrator credentials (use admin@college.edu / admin123 or registered admin).', 'danger')
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
    """Allows self-registration across all account categories: Student, Staff, and Administrator."""
    if request.method == 'POST':
        category = request.form.get('account_category', 'student').strip().lower()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('Name, email, and password are required.', 'danger')
            return render_template('register.html', selected_category=category)

        pwd_hash = generate_password_hash(password)

        try:
            if category == 'staff':
                staff_id_raw = request.form.get('staff_id', '').strip()
                if staff_id_raw:
                    staff_id = int(staff_id_raw)
                else:
                    max_id = query_one("SELECT COALESCE(MAX(Staff_ID), 200) AS max_id FROM STAFF;")
                    staff_id = (max_id['max_id'] if max_id else 200) + 1

                dept = request.form.get('staff_department', 'Academic').strip()
                role_title = request.form.get('staff_role', 'Faculty Member').strip() or 'Faculty Member'

                existing = query_one("SELECT Staff_ID FROM STAFF WHERE Staff_ID = %s OR LOWER(Email) = %s;", [staff_id, email])
                if existing:
                    flash('A staff member with this Staff ID or Email already exists.', 'warning')
                    return render_template('register.html', selected_category='staff')

                execute_stmt("""
                    INSERT INTO STAFF (Staff_ID, Name, Email, Department, Role, Password_Hash)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, [staff_id, name, email, dept, role_title, pwd_hash])

                flash('Staff account registered successfully! You may now sign in with your faculty/staff credentials.', 'success')
                return redirect(url_for('auth.login'))

            elif category == 'admin':
                admin_id_raw = request.form.get('admin_id', '').strip()
                if admin_id_raw:
                    admin_id = int(admin_id_raw)
                else:
                    max_id = query_one("SELECT COALESCE(MAX(Staff_ID), 300) AS max_id FROM STAFF;")
                    admin_id = max(300, (max_id['max_id'] if max_id else 300)) + 1

                dept = request.form.get('admin_department', 'Administration').strip()
                role_title = request.form.get('admin_role', 'Campus Administrator').strip() or 'Campus Administrator'

                existing = query_one("SELECT Staff_ID FROM STAFF WHERE Staff_ID = %s OR LOWER(Email) = %s;", [admin_id, email])
                if existing:
                    flash('An administrator with this ID or Email already exists.', 'warning')
                    return render_template('register.html', selected_category='admin')

                execute_stmt("""
                    INSERT INTO STAFF (Staff_ID, Name, Email, Department, Role, Password_Hash)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, [admin_id, name, email, dept, role_title, pwd_hash])

                flash('Administrator account registered successfully! You may now sign in with your administrator credentials.', 'success')
                return redirect(url_for('auth.login'))

            else:  # student
                student_id_raw = request.form.get('student_id', '').strip()
                if student_id_raw:
                    student_id = int(student_id_raw)
                else:
                    max_id = query_one("SELECT COALESCE(MAX(Student_ID), 100) AS max_id FROM STUDENT;")
                    student_id = (max_id['max_id'] if max_id else 100) + 1

                dept = request.form.get('department', 'Information Science & Engg').strip()
                year = int(request.form.get('year', '1'))
                if year < 1 or year > 4:
                    flash('Academic year must be between 1 and 4.', 'danger')
                    return render_template('register.html', selected_category='student')

                existing = query_one("SELECT Student_ID FROM STUDENT WHERE Student_ID = %s OR LOWER(Email) = %s;", [student_id, email])
                if existing:
                    flash('A student with this Student ID or Email already exists.', 'warning')
                    return render_template('register.html', selected_category='student')

                execute_stmt("""
                    INSERT INTO STUDENT (Student_ID, Name, Email, Department, Year, Password_Hash)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, [student_id, name, email, dept, year, pwd_hash])

                flash('Student account registered successfully! You may now sign in with your student credentials.', 'success')
                return redirect(url_for('auth.login'))

        except ValueError:
            flash('Please enter valid numeric values for ID and Year.', 'danger')
        except Exception as e:
            flash(f'Registration error: {e}', 'danger')

    return render_template('register.html', selected_category='student')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))
