-- EduSQL Test Queries - Erroneous Cases
-- One erroneous query per rule (20 total)
-- Each query is expected to trigger the corresponding rule
-- Run individually through EduSQL: py main.py


-- PHASE 1 - STATIC RULES

-- S1: Aggregate function in WHERE clause (SYN-4)
SELECT * FROM employees
WHERE COUNT(*) > 5;

-- S2: HAVING without GROUP BY (SYN-5)
SELECT dept FROM employees
HAVING COUNT(*) > 2;

-- S3: Column in SELECT missing from GROUP BY (SYN-5)
SELECT dept, name
FROM employees
GROUP BY dept;

-- S4: NULL comparison using = or <> (SYN-6)
SELECT * FROM employees
WHERE salary = NULL;

-- S5: Missing FROM clause (SYN-6)
SELECT name
WHERE salary > 5000
FROM employees;

-- S6: DISTINCT ON without ORDER BY (PG-SYN)
SELECT DISTINCT ON (dept) name, dept
FROM employees;

-- S7: DISTINCT ON ORDER BY mismatch (PG-SYN)
SELECT DISTINCT ON (dept) name, dept
FROM employees
ORDER BY name;

-- S8: Ranking window function missing ORDER BY in OVER (PG-SYN)
SELECT name, ROW_NUMBER() OVER ()
FROM employees;

-- S9: Recursive CTE missing RECURSIVE keyword (PG-SYN)
WITH hierarchy AS (
    SELECT id, dept FROM employees
    UNION ALL
    SELECT e.id, e.dept
    FROM employees e
    JOIN hierarchy h ON e.dept = h.dept
)
SELECT * FROM hierarchy;

-- S10: LATERAL subquery without outer reference (PG-SYN)
SELECT * FROM employees e,
LATERAL (SELECT AVG(salary) FROM employees) sub;


-- PHASE 2 - RUNTIME RULES

-- R1: Column does not exist (SYN-2)
SELECT non_existing_column FROM employees;

-- R2: Relation does not exist (SYN-2)
SELECT non_existing_column FROM empower;

-- R3: Data type mismatch - operator does not exist (SYN-3)
SELECT * FROM employees
WHERE name = 5000;

-- R4: Column must appear in GROUP BY or aggregate (SYN-5)
-- Note: caught by S3 in Phase 1 if static analysis runs first
SELECT dept, salary FROM employees
GROUP BY dept;

-- R5: Aggregate functions not allowed in WHERE (SYN-4)
-- Note: caught by S1 in Phase 1 if static analysis runs first
SELECT dept FROM employees
WHERE COUNT(*) > 1;

-- R6: Syntax error at or near token (SYN-6)
SELECT name, FROM employees;

-- R7: Invalid input syntax for type (SYN-3)
SELECT * FROM employees
WHERE id = 'abc123';

-- R8: Subquery returns more than one row (SYN-6)
SELECT * FROM employees
WHERE salary = (SELECT salary FROM employees);

-- R9: Missing FROM-clause entry for table (SYN-2)
SELECT e.name FROM employees
WHERE departments.dept = employees.dept;

-- R10: DISTINCT ON expressions must match ORDER BY (PG-SYN)
-- Note: caught by S7 in Phase 1 if static analysis runs first
SELECT DISTINCT ON (dept) name, dept
FROM employees
ORDER BY name;
