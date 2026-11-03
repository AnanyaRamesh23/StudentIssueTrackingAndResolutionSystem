"""
Flask Application Entry Point
Student Issue Tracking and Resolution System - DBMS Academic Project
Student: Ananya Ramesh | USN: U25UV24T064002 | ISE 5th SEM
Faculty Guide: Dr. Arunalatha J S
"""

import os
from flask import Flask, redirect, url_for, session
from config import Config
from db import get_active_db_engine

# Import route blueprints
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.staff_routes import staff_bp
from routes.admin_routes import admin_bp

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Also register short alias routes requested in specification
    @app.route('/')
    def index():
        if 'user_id' in session:
            role = session.get('user_role')
            if role == 'student':
                return redirect(url_for('student.dashboard'))
            elif role == 'staff':
                return redirect(url_for('staff.dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin.dashboard'))
        return redirect(url_for('auth.login'))

    @app.route('/login')
    def login_redirect():
        return redirect(url_for('auth.login'))

    @app.route('/submit-issue', methods=['GET', 'POST'])
    def submit_issue_alias():
        return redirect(url_for('student.submit_issue_page'))

    @app.route('/my-issues')
    def my_issues_alias():
        return redirect(url_for('student.my_issues'))

    @app.route('/issue/<int:issue_id>')
    def issue_alias(issue_id):
        return redirect(url_for('student.view_issue_details', issue_id=issue_id))

    @app.route('/issues')
    def issues_alias():
        if session.get('user_role') == 'student':
            return redirect(url_for('student.my_issues'))
        return redirect(url_for('staff.assigned_issues'))

    # Context processors for all Jinja templates
    @app.context_processor
    def inject_global_data():
        return {
            'active_db_engine': get_active_db_engine(),
            'current_year': 2026,
            'project_title': 'Student Issue Tracking & Resolution System',
            'student_name': 'Ananya Ramesh',
            'student_usn': 'U25UV24T064002',
            'student_branch': 'ISE 5th SEM',
            'faculty_guide': 'Dr. Arunalatha J S'
        }

    return app

app = create_app()

if __name__ == '__main__':
    # Print launch banner
    print("=" * 70)
    print("STUDENT ISSUE TRACKING AND RESOLUTION SYSTEM")
    print("DBMS Academic Project - Flask Server Starting")
    print("=" * 70)
    print(f"[*] Active Database Engine: {get_active_db_engine()}")
    print("[*] Access the Web Application at: http://127.0.0.1:5000")
    print("[*] Quick Demo Logins available on the login page!")
    print("=" * 70)
    app.run(host='127.0.0.1', port=5000, debug=True)
