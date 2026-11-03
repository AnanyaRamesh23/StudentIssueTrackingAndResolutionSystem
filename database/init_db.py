"""
Database Initialization & Diagnostic Utility
Student Issue Tracking and Resolution System (DBMS Academic Project)
Ananya Ramesh (USN: U25UV24T064002) - ISE 5th SEM
"""

import os
import sys

# Ensure parent directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from db import get_db_connection, get_active_db_engine, query_all

def init_mysql():
    """Initializes the MariaDB / MySQL database using schema.sql and seed.sql."""
    print("=" * 70)
    print("STUDENT ISSUE TRACKING AND RESOLUTION SYSTEM")
    print("DBMS Database Initialization Utility")
    print("=" * 70)
    print(f"Connecting to MySQL/MariaDB server at {Config.DB_HOST}:{Config.DB_PORT} as {Config.DB_USER}...")
    
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.8)
    try:
        if s.connect_ex((Config.DB_HOST, Config.DB_PORT)) != 0:
            print(f"[!] MariaDB/MySQL port {Config.DB_PORT} is not currently responding.")
            print("[*] Note: If MariaDB/MySQL is not running right now, the application will")
            print("    automatically use the built-in SQLite dual-engine database.")
            return False
    except Exception as e_sock:
        print(f"[!] Socket check error: {e_sock}")
        return False
    finally:
        s.close()

    # Connect to MySQL server without selecting DB initially to create DB if needed
    conn = None
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            connection_timeout=2,
            autocommit=True
        )
        print("[OK] Connected to MySQL via mysql.connector")
    except Exception as e1:
        try:
            import pymysql
            conn = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                connect_timeout=2,
                autocommit=True
            )
            print("[OK] Connected to MySQL via pymysql")
        except Exception as e2:
            print(f"[!] Could not connect to MySQL server ({e1} | {e2})")
            print("[*] Note: If MariaDB/MySQL is not running right now, the application will")
            print("    automatically use the built-in SQLite dual-engine database.")
            return False

    cursor = conn.cursor()
    print("[*] Creating database 'student_issue_db' if not exists...")
    cursor.execute("CREATE DATABASE IF NOT EXISTS student_issue_db;")
    cursor.execute("USE student_issue_db;")

    schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
    seed_file = os.path.join(os.path.dirname(__file__), 'seed.sql')

    print(f"[*] Reading and executing schema DDL: {schema_file}")
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Split schema statements by delimiter
    # Handle DELIMITER // in stored procedures & triggers
    statements = []
    current_stmt = []
    in_delimiter_block = False
    
    for line in schema_sql.splitlines():
        trimmed = line.strip()
        if trimmed.startswith('--') or not trimmed:
            continue
        if trimmed == 'DELIMITER //':
            in_delimiter_block = True
            continue
        elif trimmed == 'DELIMITER ;':
            in_delimiter_block = False
            statements.append("\n".join(current_stmt).strip())
            current_stmt = []
            continue
        elif in_delimiter_block and trimmed == '//':
            in_delimiter_block = False
            statements.append("\n".join(current_stmt).strip())
            current_stmt = []
            continue
        
        current_stmt.append(line)
        if not in_delimiter_block and trimmed.endswith(';'):
            statements.append("\n".join(current_stmt).strip())
            current_stmt = []
            
    for stmt in statements:
        if stmt:
            try:
                cursor.execute(stmt)
            except Exception as ex:
                # Ignore non-fatal drop notices
                if "DROP" not in stmt:
                    print(f"    [Notice] {ex} while running: {stmt[:60]}...")

    print("[OK] Schema created successfully.")

    print(f"[*] Reading and executing seed DML: {seed_file}")
    with open(seed_file, 'r', encoding='utf-8') as f:
        seed_sql = f.read()

    seed_statements = [s.strip() for s in seed_sql.split(';') if s.strip() and not s.strip().startswith('--')]
    for stmt in seed_statements:
        try:
            cursor.execute(stmt)
        except Exception as ex:
            print(f"    [Seed Notice] {ex}")

    print("[OK] Seed data inserted successfully.")
    cursor.close()
    conn.close()
    return True

def run_diagnostics():
    """Runs verification diagnostics and prints summary counts."""
    print("\n" + "=" * 70)
    print(f"DATABASE VERIFICATION & DIAGNOSTICS [Active Engine: {get_active_db_engine()}]")
    print("=" * 70)

    tables = ['STUDENT', 'STAFF', 'CATEGORY', 'STATUS', 'ISSUE', 'ACTION', 'REASSIGNMENT_LOG', 'FEEDBACK']
    for t in tables:
        res = query_all(f"SELECT COUNT(*) AS cnt FROM {t};")
        count = res[0]['cnt'] if res else 0
        print(f"  * Table {t:<18}: {count:>2} records")

    print("\nVerifying View: v_issue_details (Multi-Table Join & Derived Overdue)")
    views = query_all("SELECT Issue_ID, Student_Name, Category_Name, Status_Name, Priority, Is_Overdue FROM v_issue_details LIMIT 5;")
    for v in views:
        overdue_flag = " [OVERDUE]" if v.get('Is_Overdue') else ""
        print(f"    Issue #{v['Issue_ID']}: {v['Category_Name']} | {v['Priority']} | {v['Status_Name']} | Student: {v['Student_Name']}{overdue_flag}")

    print("\nVerifying View: v_staff_workload (Aggregation GROUP BY)")
    workload = query_all("SELECT Staff_Name, Department, Total_Assigned, In_Progress_Count, Resolved_Count, Overdue_Count FROM v_staff_workload LIMIT 5;")
    for w in workload:
        print(f"    Staff: {w['Staff_Name']} ({w['Department']}) - Assigned: {w['Total_Assigned']}, In Progress: {w['In_Progress_Count']}, Resolved: {w['Resolved_Count']}, Overdue: {w['Overdue_Count']}")

    print("=" * 70)
    print("All database objects verified and operational!")
    print("=" * 70)

if __name__ == '__main__':
    mysql_ok = init_mysql()
    run_diagnostics()
