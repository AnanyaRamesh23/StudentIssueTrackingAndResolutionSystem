-- =============================================================================
-- STUDENT ISSUE TRACKING AND RESOLUTION SYSTEM
-- DBMS Academic Project - Relational Database Schema (MariaDB / MySQL)
-- Student: Ananya Ramesh | USN: U25UV24T064002 | ISE 5th SEM
-- Faculty Guide: Dr. Arunalatha J S
-- =============================================================================

CREATE DATABASE IF NOT EXISTS student_issue_db;
USE student_issue_db;

-- Drop dependent objects if recreating
DROP VIEW IF EXISTS v_issue_details;
DROP VIEW IF EXISTS v_staff_workload;
DROP VIEW IF EXISTS v_category_summary;

DROP TRIGGER IF EXISTS trg_set_due_date;
DROP TRIGGER IF EXISTS trg_log_reassignment;

DROP PROCEDURE IF EXISTS sp_reassign_issue;
DROP PROCEDURE IF EXISTS sp_update_status_and_action;
DROP FUNCTION IF EXISTS fn_calculate_sla_status;

DROP TABLE IF EXISTS FEEDBACK;
DROP TABLE IF EXISTS REASSIGNMENT_LOG;
DROP TABLE IF EXISTS ACTION;
DROP TABLE IF EXISTS ISSUE;
DROP TABLE IF EXISTS STATUS;
DROP TABLE IF EXISTS CATEGORY;
DROP TABLE IF EXISTS STAFF;
DROP TABLE IF EXISTS STUDENT;

-- =============================================================================
-- 1. STUDENT TABLE
-- Stores registered students who submit complaints/issues.
-- Normalization: 3NF (Atomic fields, primary key Student_ID, no transitive deps).
-- =============================================================================
CREATE TABLE STUDENT (
    Student_ID INT NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL,
    Department VARCHAR(50) NOT NULL,
    Year INT NOT NULL,
    Password_Hash VARCHAR(255) NOT NULL,
    Created_At DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_student PRIMARY KEY (Student_ID),
    CONSTRAINT uq_student_email UNIQUE (Email),
    CONSTRAINT chk_student_year CHECK (Year BETWEEN 1 AND 4)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- 2. STAFF TABLE
-- Stores faculty and administrative staff handling student grievances.
-- Normalization: 3NF.
-- =============================================================================
CREATE TABLE STAFF (
    Staff_ID INT NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL,
    Department VARCHAR(50) NOT NULL,
    Role VARCHAR(50) NOT NULL,
    Password_Hash VARCHAR(255) NOT NULL,
    Created_At DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_staff PRIMARY KEY (Staff_ID),
    CONSTRAINT uq_staff_email UNIQUE (Email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- 3. CATEGORY TABLE
-- Lookup table for classifying student issues with Default Service Level Agreement (SLA) in days.
-- Normalization: 3NF.
-- =============================================================================
CREATE TABLE CATEGORY (
    Category_ID INT NOT NULL,
    Category_Name VARCHAR(50) NOT NULL,
    Default_SLA_Days INT NOT NULL,
    CONSTRAINT pk_category PRIMARY KEY (Category_ID),
    CONSTRAINT uq_category_name UNIQUE (Category_Name),
    CONSTRAINT chk_sla_days CHECK (Default_SLA_Days > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- 4. STATUS TABLE
-- Lookup table for predefined issue lifecycle stages:
-- Submitted -> Assigned -> In Progress -> Resolved -> Closed
-- Normalization: 3NF.
-- =============================================================================
CREATE TABLE STATUS (
    Status_ID INT NOT NULL,
    Status_Name VARCHAR(50) NOT NULL,
    CONSTRAINT pk_status PRIMARY KEY (Status_ID),
    CONSTRAINT uq_status_name UNIQUE (Status_Name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- 5. ISSUE TABLE
-- Central entity capturing student grievances, lifecycle state, priority, and assignment.
-- Foreign keys link to Student, Category, Staff, and Status.
-- Normalization: 3NF.
-- =============================================================================
CREATE TABLE ISSUE (
    Issue_ID INT NOT NULL AUTO_INCREMENT,
    Student_ID INT NOT NULL,
    Category_ID INT NOT NULL,
    Staff_ID INT NULL,
    Status_ID INT NOT NULL DEFAULT 1,
    Description TEXT NOT NULL,
    Date_Submitted DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Location VARCHAR(100) NOT NULL,
    Priority VARCHAR(20) NOT NULL,
    Due_Date DATE NOT NULL,
    CONSTRAINT pk_issue PRIMARY KEY (Issue_ID),
    CONSTRAINT fk_issue_student FOREIGN KEY (Student_ID) 
        REFERENCES STUDENT (Student_ID) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_issue_category FOREIGN KEY (Category_ID) 
        REFERENCES CATEGORY (Category_ID) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_issue_staff FOREIGN KEY (Staff_ID) 
        REFERENCES STAFF (Staff_ID) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_issue_status FOREIGN KEY (Status_ID) 
        REFERENCES STATUS (Status_ID) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_issue_priority CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- 6. ACTION TABLE
-- Maintains an audit trail of concrete actions/steps taken by staff to resolve an issue.
-- Relationship: Issue 1 -> N Action, Staff 1 -> N Action.
-- =============================================================================
CREATE TABLE ACTION (
    Action_ID INT NOT NULL AUTO_INCREMENT,
    Issue_ID INT NOT NULL,
    Staff_ID INT NOT NULL,
    Action_Description TEXT NOT NULL,
    Action_Date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_action PRIMARY KEY (Action_ID),
    CONSTRAINT fk_action_issue FOREIGN KEY (Issue_ID) 
        REFERENCES ISSUE (Issue_ID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_action_staff FOREIGN KEY (Staff_ID) 
        REFERENCES STAFF (Staff_ID) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- 7. REASSIGNMENT_LOG TABLE
-- Complete accountability log whenever an issue is reassigned from one staff member to another.
-- Relationship: Issue 1 -> N Reassignment_Log.
-- =============================================================================
CREATE TABLE REASSIGNMENT_LOG (
    Reassign_ID INT NOT NULL AUTO_INCREMENT,
    Issue_ID INT NOT NULL,
    Old_Staff_ID INT NULL,
    New_Staff_ID INT NOT NULL,
    Reassigned_On DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Reason VARCHAR(255) NOT NULL,
    CONSTRAINT pk_reassign PRIMARY KEY (Reassign_ID),
    CONSTRAINT fk_reassign_issue FOREIGN KEY (Issue_ID) 
        REFERENCES ISSUE (Issue_ID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_reassign_old_staff FOREIGN KEY (Old_Staff_ID) 
        REFERENCES STAFF (Staff_ID) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_reassign_new_staff FOREIGN KEY (New_Staff_ID) 
        REFERENCES STAFF (Staff_ID) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- 8. FEEDBACK TABLE
-- Captures student satisfaction rating (1-5) and remarks upon resolution.
-- Relationship: Issue 1 -> 1 Feedback (enforced by UNIQUE constraint on Issue_ID).
-- =============================================================================
CREATE TABLE FEEDBACK (
    Feedback_ID INT NOT NULL AUTO_INCREMENT,
    Issue_ID INT NOT NULL,
    Rating INT NOT NULL,
    Comments TEXT NULL,
    Submitted_On DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_feedback PRIMARY KEY (Feedback_ID),
    CONSTRAINT uq_feedback_issue UNIQUE (Issue_ID),
    CONSTRAINT fk_feedback_issue FOREIGN KEY (Issue_ID) 
        REFERENCES ISSUE (Issue_ID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_feedback_rating CHECK (Rating BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- PERFORMANCE INDEXES
-- Optimize lookup performance for queries, joins, and dashboard filters.
-- =============================================================================
CREATE INDEX idx_issue_status ON ISSUE (Status_ID);
CREATE INDEX idx_issue_staff ON ISSUE (Staff_ID);
CREATE INDEX idx_issue_category ON ISSUE (Category_ID);
CREATE INDEX idx_issue_student ON ISSUE (Student_ID);
CREATE INDEX idx_issue_due_date ON ISSUE (Due_Date);
CREATE INDEX idx_action_issue ON ACTION (Issue_ID);
CREATE INDEX idx_reassign_issue ON REASSIGNMENT_LOG (Issue_ID);

-- =============================================================================
-- DATABASE VIEWS
-- =============================================================================

-- VIEW 1: v_issue_details
-- Consolidated view of all issue attributes combined with Student, Category, Staff,
-- and Status descriptions, plus derived boolean flag Is_Overdue.
CREATE OR REPLACE VIEW v_issue_details AS
SELECT 
    i.Issue_ID,
    i.Description,
    i.Location,
    i.Priority,
    i.Date_Submitted,
    i.Due_Date,
    s.Student_ID,
    s.Name AS Student_Name,
    s.Email AS Student_Email,
    s.Department AS Student_Dept,
    s.Year AS Student_Year,
    c.Category_ID,
    c.Category_Name,
    c.Default_SLA_Days,
    st.Status_ID,
    st.Status_Name,
    sf.Staff_ID,
    sf.Name AS Staff_Name,
    sf.Department AS Staff_Dept,
    sf.Role AS Staff_Role,
    CASE 
        WHEN i.Due_Date < CURDATE() AND st.Status_Name NOT IN ('Resolved', 'Closed') THEN 1 
        ELSE 0 
    END AS Is_Overdue
FROM ISSUE i
JOIN STUDENT s ON i.Student_ID = s.Student_ID
JOIN CATEGORY c ON i.Category_ID = c.Category_ID
JOIN STATUS st ON i.Status_ID = st.Status_ID
LEFT JOIN STAFF sf ON i.Staff_ID = sf.Staff_ID;

-- VIEW 2: v_staff_workload
-- Summarizes assigned, in-progress, resolved, closed, and overdue issues per staff member.
CREATE OR REPLACE VIEW v_staff_workload AS
SELECT 
    sf.Staff_ID,
    sf.Name AS Staff_Name,
    sf.Department,
    sf.Role,
    COUNT(i.Issue_ID) AS Total_Assigned,
    SUM(CASE WHEN st.Status_Name = 'Assigned' THEN 1 ELSE 0 END) AS Assigned_Count,
    SUM(CASE WHEN st.Status_Name = 'In Progress' THEN 1 ELSE 0 END) AS In_Progress_Count,
    SUM(CASE WHEN st.Status_Name = 'Resolved' THEN 1 ELSE 0 END) AS Resolved_Count,
    SUM(CASE WHEN st.Status_Name = 'Closed' THEN 1 ELSE 0 END) AS Closed_Count,
    SUM(CASE WHEN i.Due_Date < CURDATE() AND st.Status_Name NOT IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS Overdue_Count
FROM STAFF sf
LEFT JOIN ISSUE i ON sf.Staff_ID = i.Staff_ID
LEFT JOIN STATUS st ON i.Status_ID = st.Status_ID
GROUP BY sf.Staff_ID, sf.Name, sf.Department, sf.Role;

-- VIEW 3: v_category_summary
-- Summarizes issue counts and resolution percentages across categories.
CREATE OR REPLACE VIEW v_category_summary AS
SELECT 
    c.Category_ID,
    c.Category_Name,
    c.Default_SLA_Days,
    COUNT(i.Issue_ID) AS Total_Issues,
    SUM(CASE WHEN st.Status_Name IN ('Submitted', 'Assigned', 'In Progress') THEN 1 ELSE 0 END) AS Open_Issues,
    SUM(CASE WHEN st.Status_Name IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS Resolved_Issues
FROM CATEGORY c
LEFT JOIN ISSUE i ON c.Category_ID = i.Category_ID
LEFT JOIN STATUS st ON i.Status_ID = st.Status_ID
GROUP BY c.Category_ID, c.Category_Name, c.Default_SLA_Days;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- TRIGGER 1: Automatically compute Due_Date based on Category SLA if not provided
DELIMITER //
CREATE TRIGGER trg_set_due_date
BEFORE INSERT ON ISSUE
FOR EACH ROW
BEGIN
    DECLARE v_sla INT;
    IF NEW.Due_Date IS NULL OR NEW.Due_Date = '0000-00-00' THEN
        SELECT Default_SLA_Days INTO v_sla FROM CATEGORY WHERE Category_ID = NEW.Category_ID;
        IF v_sla IS NULL THEN
            SET v_sla = 5;
        END IF;
        SET NEW.Due_Date = DATE_ADD(CURRENT_DATE(), INTERVAL v_sla DAY);
    END IF;
END;
//
DELIMITER ;

-- TRIGGER 2: Automatically audit staff reassignment when Staff_ID changes
DELIMITER //
CREATE TRIGGER trg_log_reassignment
AFTER UPDATE ON ISSUE
FOR EACH ROW
BEGIN
    -- Check if staff has changed from an existing staff to another staff
    IF OLD.Staff_ID IS NOT NULL 
       AND NEW.Staff_ID IS NOT NULL 
       AND OLD.Staff_ID <> NEW.Staff_ID THEN
        -- Insert audit record if not already recorded within current transaction
        INSERT INTO REASSIGNMENT_LOG (Issue_ID, Old_Staff_ID, New_Staff_ID, Reassigned_On, Reason)
        VALUES (
            NEW.Issue_ID, 
            OLD.Staff_ID, 
            NEW.Staff_ID, 
            NOW(), 
            COALESCE(@reassign_reason, 'Staff reassignment via system update')
        );
    END IF;
END;
//
DELIMITER ;

-- =============================================================================
-- STORED PROCEDURES & FUNCTIONS
-- =============================================================================

-- PROCEDURE 1: Reassign Issue within an explicit ACID Transaction
DELIMITER //
CREATE PROCEDURE sp_reassign_issue (
    IN p_issue_id INT,
    IN p_new_staff_id INT,
    IN p_reason VARCHAR(255)
)
BEGIN
    DECLARE v_old_staff_id INT;
    DECLARE v_status_id INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
        -- Retrieve current staff and status
        SELECT Staff_ID, Status_ID INTO v_old_staff_id, v_status_id 
        FROM ISSUE WHERE Issue_ID = p_issue_id FOR UPDATE;

        -- If issue is currently 'Submitted' (1), move to 'Assigned' (2)
        IF v_status_id = 1 THEN
            SET v_status_id = 2;
        END IF;

        -- Update issue with new staff
        UPDATE ISSUE 
        SET Staff_ID = p_new_staff_id,
            Status_ID = v_status_id
        WHERE Issue_ID = p_issue_id;

        -- Record reassignment log
        INSERT INTO REASSIGNMENT_LOG (Issue_ID, Old_Staff_ID, New_Staff_ID, Reassigned_On, Reason)
        VALUES (p_issue_id, v_old_staff_id, p_new_staff_id, NOW(), p_reason);

        -- Record an action trail entry
        INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date)
        VALUES (p_issue_id, p_new_staff_id, CONCAT('Issue reassigned: ', p_reason), NOW());
    COMMIT;
END;
//
DELIMITER ;

-- PROCEDURE 2: Update Status and log Action within an ACID Transaction
DELIMITER //
CREATE PROCEDURE sp_update_status_and_action (
    IN p_issue_id INT,
    IN p_status_id INT,
    IN p_staff_id INT,
    IN p_action_desc TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
        -- Update the issue status
        UPDATE ISSUE 
        SET Status_ID = p_status_id
        WHERE Issue_ID = p_issue_id;

        -- Insert the action description
        IF p_action_desc IS NOT NULL AND TRIM(p_action_desc) <> '' THEN
            INSERT INTO ACTION (Issue_ID, Staff_ID, Action_Description, Action_Date)
            VALUES (p_issue_id, p_staff_id, p_action_desc, NOW());
        END IF;
    COMMIT;
END;
//
DELIMITER ;

-- FUNCTION 1: Calculate SLA Status
DELIMITER //
CREATE FUNCTION fn_calculate_sla_status (
    p_due_date DATE,
    p_status_id INT
)
RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
    -- Status 4 is Resolved, 5 is Closed
    IF p_status_id IN (4, 5) THEN
        RETURN 'RESOLVED';
    ELSEIF p_due_date < CURDATE() THEN
        RETURN 'OVERDUE';
    ELSEIF p_due_date = CURDATE() THEN
        RETURN 'DUE TODAY';
    ELSE
        RETURN 'ON TRACK';
    END IF;
END;
//
DELIMITER ;
