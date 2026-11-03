import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'college_dbms_project_ananya_u25uv24t064002_secret_key')
    
    # MariaDB / MySQL Configuration
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'student_issue_db')
    
    # Automatic fallback to local SQLite if MariaDB/MySQL server is not running
    # Set AUTO_FALLBACK_SQLITE=False if you strictly want it to fail when MySQL is unavailable
    AUTO_FALLBACK_SQLITE = os.getenv('AUTO_FALLBACK_SQLITE', 'True').lower() in ('true', '1', 'yes')
    SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'student_issue_db.sqlite')
