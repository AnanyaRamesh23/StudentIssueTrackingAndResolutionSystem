"""
Automated Test Suite
Student Issue Tracking and Resolution System (DBMS Project)
Verifies: Tables, Constraints, Views, Full Issue Lifecycle, Transactions, Overdue Logic, and Web Endpoints.
"""

import sys
import unittest
import datetime
from app import create_app
from db import query_all, query_one, get_active_db_engine, get_db_connection, execute_stmt
from services.issue_service import (
    create_issue, update_issue_status, add_action,
    reassign_issue, submit_feedback, get_issue_by_id,
    get_dashboard_stats, get_staff_workload_having
)

class DBMSSystemTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        print(f"\n[TEST SUITE] Running against active engine: {get_active_db_engine()}")

    def test_01_database_tables_and_seeds(self):
        """Verify all 8 tables are present and populated with sample data."""
        tables = ['STUDENT', 'STAFF', 'CATEGORY', 'STATUS', 'ISSUE', 'ACTION', 'REASSIGNMENT_LOG', 'FEEDBACK']
        for t in tables:
            res = query_all(f"SELECT COUNT(*) AS cnt FROM {t};")
            self.assertTrue(len(res) > 0, f"Table {t} should return count.")
            self.assertGreater(res[0]['cnt'], 0, f"Table {t} should contain seed records.")
        print("  [OK] Test 1 Passed: All 8 Relational Tables verified with sample records.")

    def test_02_database_views(self):
        """Verify views v_issue_details and v_staff_workload."""
        issues = query_all("SELECT Issue_ID, Student_Name, Category_Name, Status_Name, Is_Overdue FROM v_issue_details;")
        self.assertGreater(len(issues), 0, "View v_issue_details should return records.")
        self.assertIn('Student_Name', issues[0])
        self.assertIn('Category_Name', issues[0])
        self.assertIn('Is_Overdue', issues[0])

        workload = query_all("SELECT Staff_Name, Total_Assigned, In_Progress_Count FROM v_staff_workload;")
        self.assertGreater(len(workload), 0, "View v_staff_workload should return staff workload.")
        print("  [OK] Test 2 Passed: Views v_issue_details and v_staff_workload query successfully.")

    def test_03_issue_lifecycle_workflow(self):
        """
        Verify the complete lifecycle:
        Submitted -> Assigned -> In Progress -> Reassigned (Transaction) -> Resolved -> Feedback (1:1).
        """
        # Step 1: Student 101 submits new Technical issue (Category 3 has 3-day SLA)
        issue_id = create_issue(
            student_id=101,
            category_id=3,
            description="Automated Test: Projector bulb blown in Room 101.",
            location="Room 101",
            priority="High"
        )
        self.assertIsNotNone(issue_id)
        
        issue = get_issue_by_id(issue_id)
        self.assertEqual(issue['Status_ID'], 1, "New issue must be in 'Submitted' status.")
        self.assertIsNotNone(issue['Due_Date'], "SLA Due_Date must be calculated.")

        # Step 2: Assign Staff 201 (Status -> Assigned)
        update_issue_status(issue_id, new_status_id=2, staff_id=201, action_description="Assigned to Dr. Suresh Kumar")
        issue = get_issue_by_id(issue_id)
        self.assertEqual(issue['Status_ID'], 2, "Status must transition to 'Assigned'.")

        # Step 3: Record Action (Status -> In Progress)
        add_action(issue_id, staff_id=201, action_description="Inspected bulb filament; tested socket voltage.")
        issue = get_issue_by_id(issue_id)
        self.assertEqual(issue['Status_ID'], 3, "Adding action to assigned issue should move to 'In Progress'.")
        self.assertGreaterEqual(len(issue['actions']), 1, "Action trail should record entry.")

        # Step 4: Reassign to Staff 203 (ACID Transaction)
        reassign_issue(
            issue_id=issue_id,
            new_staff_id=203,
            reason="Requires facilities ladder and ceiling hoist equipment.",
            current_staff_id=201
        )
        issue = get_issue_by_id(issue_id)
        self.assertEqual(issue['Staff_ID'], 203, "Staff must be updated to new staff.")
        self.assertGreaterEqual(len(issue['reassignments']), 1, "Reassignment log must contain record.")
        self.assertEqual(issue['reassignments'][-1]['Reason'], "Requires facilities ladder and ceiling hoist equipment.")

        # Step 5: Resolve Issue (Status -> Resolved)
        update_issue_status(issue_id, new_status_id=4, staff_id=203, action_description="Replaced projector bulb and calibrated lens.")
        issue = get_issue_by_id(issue_id)
        self.assertEqual(issue['Status_ID'], 4, "Status must be 'Resolved'.")

        # Step 6: Submit 1:1 Student Feedback
        submit_feedback(issue_id, rating=5, comments="Excellent resolution, projector working crystal clear!")
        issue = get_issue_by_id(issue_id)
        self.assertIsNotNone(issue['feedback'], "Feedback must be linked.")
        self.assertEqual(issue['feedback']['Rating'], 5)

        # Step 8: Clean up test issue so automated tests never leave behind duplicate issues
        execute_stmt("DELETE FROM FEEDBACK WHERE Issue_ID = %s;", [issue_id])
        execute_stmt("DELETE FROM REASSIGNMENT_LOG WHERE Issue_ID = %s;", [issue_id])
        execute_stmt("DELETE FROM ACTION WHERE Issue_ID = %s;", [issue_id])
        execute_stmt("DELETE FROM ISSUE WHERE Issue_ID = %s;", [issue_id])

        print("  [OK] Test 3 Passed: Complete Issue Lifecycle, Audit Trails, and 1:1 Feedback verified.")

    def test_04_derived_overdue_logic(self):
        """Verify that issues with Due_Date < CURDATE() and unresolved status are marked overdue."""
        # Issue 13 in seed data has past due date and is In Progress
        issue13 = query_one("SELECT Issue_ID, Due_Date, Status_Name, Is_Overdue FROM v_issue_details WHERE Issue_ID = 13;")
        self.assertIsNotNone(issue13)
        self.assertEqual(issue13['Is_Overdue'], 1, "Issue 13 must be identified as overdue.")
        print("  [OK] Test 4 Passed: Derived Overdue condition accurately identified.")

    def test_05_aggregation_having(self):
        """Verify GROUP BY and HAVING query."""
        results = get_staff_workload_having(min_issues=2)
        self.assertGreater(len(results), 0, "HAVING count >= 2 should return qualifying staff members.")
        for r in results:
            self.assertGreaterEqual(r['Issue_Count'], 2)
        print("  [OK] Test 5 Passed: GROUP BY with HAVING clause verified.")

    def test_06_flask_web_routes(self):
        """Verify all major Flask endpoints and role access."""
        # 1. Login page
        res = self.client.get('/login', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 2. Demo login as student
        res = self.client.get('/auth/demo-login/student/101', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Ananya Ramesh', res.data)

        # 3. Student Submit Issue page
        res = self.client.get('/student/submit-issue')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Issue Category', res.data)

        # 4. View Issue Details
        res = self.client.get('/issue/1', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Issue #1', res.data)

        # 5. Demo login as Staff
        res = self.client.get('/auth/demo-login/staff/201', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Dr. Suresh Kumar', res.data)

        # 6. Admin Dashboard & DBMS Viva Showcase
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Institution Management', res.data)

        res = self.client.get('/admin/dbms-demo')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'DBMS Concepts', res.data)

        print("  [OK] Test 6 Passed: Web endpoints, session routing, and templates verified.")

if __name__ == '__main__':
    unittest.main()
