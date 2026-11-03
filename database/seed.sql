-- =============================================================================
-- STUDENT ISSUE TRACKING AND RESOLUTION SYSTEM
-- DBMS Academic Project - Seed Data (MariaDB / MySQL)
-- =============================================================================

USE student_issue_db;

-- Clear any existing seed data safely
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE FEEDBACK;
TRUNCATE TABLE REASSIGNMENT_LOG;
TRUNCATE TABLE ACTION;
TRUNCATE TABLE ISSUE;
TRUNCATE TABLE STATUS;
TRUNCATE TABLE CATEGORY;
TRUNCATE TABLE STAFF;
TRUNCATE TABLE STUDENT;
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- 1. INSERT CATEGORIES
-- Default SLA: Academic (5 days), Administrative (7 days), Technical (3 days), Facilities (4 days)
-- =============================================================================
INSERT INTO CATEGORY (Category_ID, Category_Name, Default_SLA_Days) VALUES
(1, 'Academic', 5),
(2, 'Administrative', 7),
(3, 'Technical', 3),
(4, 'Facilities', 4);

-- =============================================================================
-- 2. INSERT STATUSES
-- Predefined linear lifecycle stages
-- =============================================================================
INSERT INTO STATUS (Status_ID, Status_Name) VALUES
(1, 'Submitted'),
(2, 'Assigned'),
(3, 'In Progress'),
(4, 'Resolved'),
(5, 'Closed');

-- =============================================================================
-- 3. INSERT STUDENTS (9 Students)
-- Default password: password123
-- Password hash: scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387
-- =============================================================================
INSERT INTO STUDENT (Student_ID, Name, Email, Department, Year, Password_Hash, Created_At) VALUES
(101, 'Ananya Ramesh', 'ananya@college.edu', 'Information Science & Engg', 3, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-01 10:00:00'),
(102, 'Rohan Sharma', 'rohan.sharma@college.edu', 'Computer Science & Engg', 3, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-02 11:30:00'),
(103, 'Priya Nair', 'priya.nair@college.edu', 'Electronics & Comm Engg', 2, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-03 09:15:00'),
(104, 'Karthik V', 'karthik.v@college.edu', 'Mechanical Engg', 4, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-04 14:00:00'),
(105, 'Sneha Patel', 'sneha.p@college.edu', 'Information Science & Engg', 2, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-05 16:45:00'),
(106, 'Rahul Roy', 'rahul.roy@college.edu', 'Civil Engg', 3, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-06 12:10:00'),
(107, 'Divya M', 'divya.m@college.edu', 'Computer Science & Engg', 4, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-07 10:20:00'),
(108, 'Amit Kumar', 'amit.k@college.edu', 'Electronics & Comm Engg', 1, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-08 15:30:00'),
(109, 'Tanvi Rao', 'tanvi.rao@college.edu', 'Information Science & Engg', 3, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-09 13:00:00'),
(110, 'Nikhil Bhat', 'nikhil.b@college.edu', 'Computer Science & Engg', 2, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-10 11:00:00'),
(111, 'Swathi Krishna', 'swathi.k@college.edu', 'Information Science & Engg', 4, 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-08-11 14:15:00');

-- =============================================================================
-- 4. INSERT STAFF (5 Staff Members)
-- =============================================================================
INSERT INTO STAFF (Staff_ID, Name, Email, Department, Role, Password_Hash, Created_At) VALUES
(201, 'Dr. Suresh Kumar', 'suresh@college.edu', 'Technical / IT', 'System Administrator & Lab Incharge', 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-07-01 09:00:00'),
(202, 'Prof. Sunita Rao', 'sunita@college.edu', 'Academic', 'Academic Coordinator & Associate Prof', 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-07-01 09:00:00'),
(203, 'Mr. Anand Murthy', 'anand@college.edu', 'Facilities', 'Campus Infrastructure Supervisor', 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-07-01 09:00:00'),
(204, 'Mrs. Meena Iyer', 'meena@college.edu', 'Administrative', 'Student Affairs Officer', 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-07-01 09:00:00'),
(205, 'Dr. Rajesh Verma', 'rajesh@college.edu', 'Academic', 'Dean of Academic Affairs', 'scrypt:32768:8:1$FqGeIauAs4wtNyHX$0eeab5e0e5938e3968698e91bbc78fb3d31ded7651b7df1d1b14efd72881a7a42d7baddf8afe80a3b69d79504c94c40d5d15955e1024297fcb3133c1e44c7387', '2026-07-01 09:00:00');

-- =============================================================================
-- 5. INSERT ISSUES (14 Issues across categories, priorities, and statuses)
-- Notice Issue 13 is designed to test the derived Overdue logic!
-- =============================================================================
INSERT INTO ISSUE (Issue_ID, Student_ID, Category_ID, Staff_ID, Status_ID, Description, Date_Submitted, Location, Priority, Due_Date) VALUES
(1, 101, 3, 201, 3, 'Classroom 302 ceiling projector HDMI port damaged; display shows severe pink distortion during lectures.', '2026-09-28 09:30:00', 'Academic Block A, Room 302', 'High', '2026-10-01'),
(2, 102, 4, 203, 3, 'Hostel Block B 3rd floor water purifier is leaking continuously and pressure is too low for drinking water.', '2026-09-29 11:15:00', 'Hostel Block B, Floor 3', 'High', '2026-10-03'),
(3, 103, 1, 202, 2, 'Grade sheet discrepancy for 4th Semester DBMS Lab exam marks not updated in college portal after re-evaluation.', '2026-10-01 14:00:00', 'Department Office, ISE Dept', 'High', '2026-10-06'),
(4, 101, 2, 204, 4, 'Bonafide student certificate request for education loan subsidy pending verification for 10 days.', '2026-09-20 10:00:00', 'Administrative Building Counter 2', 'Medium', '2026-09-27'),
(5, 104, 3, 201, 5, 'WiFi access points in Central Library 2nd floor disconnecting frequently during peak research hours.', '2026-09-18 16:20:00', 'Central Library, 2nd Floor', 'Medium', '2026-09-21'),
(6, 105, 4, 203, 2, 'Classroom 405 air conditioner not cooling and producing loud rattling noise during classes.', '2026-10-02 08:45:00', 'Academic Block B, Room 405', 'Medium', '2026-10-06'),
(7, 106, 1, NULL, 1, 'Request for elective course change approval from Cloud Computing to Advanced Database Systems.', '2026-10-03 09:10:00', 'Dean Academic Office', 'Low', '2026-10-08'),
(8, 107, 2, 204, 3, 'Bus pass renewal counter delay and transaction receipt mismatch in student finance counter.', '2026-09-27 13:20:00', 'Finance Office Counter 4', 'Low', '2026-10-04'),
(9, 108, 3, NULL, 1, 'Computer Lab 4 Desktop Workstation #12 experiences kernel panic and freeze on Linux boot.', '2026-10-03 11:00:00', 'Computer Lab 4, Desktop 12', 'Critical', '2026-10-06'),
(10, 109, 4, 203, 5, 'Broken wooden bench and loose desk in Seminar Hall A causing safety concern during guest lectures.', '2026-09-15 15:30:00', 'Seminar Hall A', 'Medium', '2026-09-19'),
(11, 102, 1, 205, 3, 'Medical leave attendance waiver form submitted on Sept 15th not updated in student attendance tracking portal.', '2026-09-25 10:15:00', 'Academic Affairs Section', 'High', '2026-09-30'),
(12, 103, 4, 203, 4, 'Sports complex indoor badminton court floodlight fixture fused and flickering continuously.', '2026-09-22 17:00:00', 'Sports Complex Court 2', 'Low', '2026-09-26'),
(13, 104, 3, 201, 3, 'College ERP and Moodle portal account locked out due to LDAP directory synchronization error.', '2026-09-16 11:45:00', 'Campus IT Data Center', 'High', '2026-09-19'),
(14, 105, 2, 204, 2, 'Tuition fee refund balance for duplicate semester transaction via netbanking pending accountant signoff.', '2026-10-02 12:00:00', 'Accounts Branch', 'Critical', '2026-10-09');

-- =============================================================================
-- 6. INSERT ACTIONS (10 Recorded Staff Actions)
-- =============================================================================
INSERT INTO ACTION (Action_ID, Issue_ID, Staff_ID, Action_Description, Action_Date) VALUES
(1, 1, 201, 'Inspected projector in Room 302. Confirmed damaged HDMI connector pin. Replaced HDMI transmitter cable; ordered replacement wall port.', '2026-09-29 14:00:00'),
(2, 1, 201, 'Installed interim VGA-to-HDMI active converter while new wall panel arrives.', '2026-09-30 16:30:00'),
(3, 2, 203, 'Plumber inspected 3rd floor RO unit. Identified faulty float valve causing tank overflow. Closed inlet temporarily.', '2026-09-30 10:00:00'),
(4, 2, 203, 'Installed replacement high-pressure diaphragm valve and sanitized storage chamber.', '2026-10-01 15:45:00'),
(5, 4, 204, 'Verified student record with registrar office. Signed and stamped bonafide certificate.', '2026-09-25 11:30:00'),
(6, 4, 204, 'Dispatched digitally signed certificate to student email and handed physical copy at Counter 2.', '2026-09-27 10:15:00'),
(7, 5, 201, 'Rebooted Cisco Catalyst switch in Library. Replaced faulty Cat6 patch cable on AP-204 and upgraded firmware.', '2026-09-19 14:20:00'),
(8, 8, 204, 'Checked banking reconciliation log with Canara Bank gateway. Matched transaction UTR number.', '2026-09-28 15:10:00'),
(9, 10, 203, 'Carpentry team repaired bench frame, replaced broken pine slat, and secured bolts in Seminar Hall A.', '2026-09-18 12:00:00'),
(10, 12, 203, 'Replaced 150W LED driver unit and ballast for badminton court lighting pole.', '2026-09-25 16:30:00');

-- =============================================================================
-- 7. INSERT REASSIGNMENT_LOGS (4 Realistic Staff Handoffs)
-- =============================================================================
INSERT INTO REASSIGNMENT_LOG (Reassign_ID, Issue_ID, Old_Staff_ID, New_Staff_ID, Reassigned_On, Reason) VALUES
(1, 1, 203, 201, '2026-09-28 10:45:00', 'Initially tagged as facility repair, reassigned to IT department as HDMI circuit replacement requires technical staff.'),
(2, 8, 202, 204, '2026-09-27 14:00:00', 'Transferred from Academic office to Student Affairs / Administrative branch for financial verification.'),
(3, 11, 202, 205, '2026-09-26 11:30:00', 'Escalated to Dean of Academic Affairs because attendance exemption beyond 10 days requires Dean authorization.'),
(4, 13, 204, 201, '2026-09-16 12:15:00', 'Forwarded from Administrative office to System Administrator for LDAP server credential reset.');

-- =============================================================================
-- 8. INSERT FEEDBACK (4 Student Feedback entries on Resolved/Closed Issues)
-- =============================================================================
INSERT INTO FEEDBACK (Feedback_ID, Issue_ID, Rating, Comments, Submitted_On) VALUES
(1, 4, 5, 'Bonafide certificate was delivered on time for my loan bank submission. Great prompt support from Mrs. Meena Iyer.', '2026-09-28 09:00:00'),
(2, 5, 4, 'Library WiFi is working stable now without disconnection. Speed is much improved.', '2026-09-22 10:30:00'),
(3, 10, 5, 'The bench in Seminar Hall was repaired neatly before the guest lecture. Thank you!', '2026-09-20 17:15:00'),
(4, 12, 4, 'Badminton court floodlight fixed quickly, sports practice resumed.', '2026-09-27 18:40:00');
