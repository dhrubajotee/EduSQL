-- EduSQL Test Queries - Erroneous Cases
-- 4 erroneous queries and 3 correct queries per rule
-- Run individually through EduSQL: py main.py


-- PHASE 1 - STATIC RULES

-- S1: Aggregate function in WHERE clause (SYN-4)
-- Error Variant 1
SELECT * FROM employees WHERE COUNT(*) > 5;

-- Error Variant 2
SELECT * FROM employees WHERE SUM(salary) > 50000;

-- Error Variant 3
SELECT e.name, d.name FROM employees e JOIN departments d ON e.dept = d.name WHERE MAX(e.salary) > 8000;

-- Error Variant 4
SELECT * FROM projects WHERE AVG(budget) > 40000;

-- Correct Variant 1
SELECT dept, COUNT(*) FROM employees GROUP BY dept HAVING COUNT(*) > 2;

-- Correct Variant 2
SELECT * FROM employees WHERE salary > (SELECT AVG(salary) FROM employees);

-- Correct Variant 3
SELECT * FROM projects WHERE budget > 40000;



-- S2: HAVING without GROUP BY (SYN-5)

-- Error Variant 1
SELECT dept FROM employees HAVING COUNT(*) > 2;

-- Error Variant 2
SELECT salary FROM employees HAVING salary > 5000;

-- Error Variant 3
SELECT budget FROM projects HAVING budget > 30000;

-- Error Variant 4
SELECT name, dept FROM employees HAVING COUNT(*) > 1;

-- Correct Variant 1
SELECT dept, COUNT(*) FROM employees GROUP BY dept HAVING COUNT(*) > 2;

-- Correct Variant 2
SELECT salary FROM employees WHERE salary > 5000;

-- Correct Variant 3
SELECT dept, SUM(budget) FROM projects GROUP BY dept HAVING SUM(budget) > 40000;



-- S3: Column in SELECT missing from GROUP BY (SYN-5)
-- Error Variant 1
SELECT dept, name FROM employees GROUP BY dept;

-- Error Variant 2
SELECT dept, title FROM projects GROUP BY dept;

-- Error Variant 3
SELECT e.dept, e.name, COUNT(*) FROM employees e JOIN departments d ON e.dept = d.name GROUP BY e.dept;

-- Error Variant 4
SELECT dept, name, salary FROM employees GROUP BY dept;

-- Correct Variant 1
SELECT dept, name FROM employees GROUP BY dept, name;

-- Correct Variant 2
SELECT dept, MAX(salary) FROM employees GROUP BY dept;

-- Correct Variant 3
SELECT dept, COUNT(*), SUM(budget) FROM projects GROUP BY dept;


-- S4: NULL comparison using = or <> (SYN-6)
-- Error Variant 1
SELECT * FROM employees WHERE salary = NULL;

-- Error Variant 2
SELECT * FROM employees WHERE salary <> NULL;

-- Error Variant 3
SELECT e.name, p.title FROM employees e JOIN projects p ON e.dept = p.dept WHERE e.salary = NULL;

-- Error Variant 4
SELECT * FROM projects WHERE budget = NULL;

-- Correct Variant 1
SELECT * FROM employees WHERE salary IS NULL;

-- Correct Variant 2
SELECT * FROM employees WHERE salary IS NOT NULL;

-- Correct Variant 3
SELECT * FROM projects WHERE budget IS NOT NULL;



-- S5: Missing FROM clause (SYN-6)
-- Error Variant 1
SELECT name WHERE salary > 5000 FROM employees;

-- Error Variant 2
SELECT id, name WHERE dept = 'IT';

-- Error Variant 3
SELECT title, budget WHERE budget > 30000;

-- Error Variant 4
SELECT dept WHERE id = 1;

-- Correct Variant 1
SELECT id, name FROM employees WHERE dept = 'IT';

-- Correct Variant 2
SELECT title, budget FROM projects WHERE budget > 30000;

-- Correct Variant 3
SELECT dept FROM employees WHERE id = 1;



-- S6: DISTINCT ON without ORDER BY (PG-SYN)
-- Error Variant 1
SELECT DISTINCT ON (dept) name, dept FROM employees;

-- Error Variant 2
SELECT DISTINCT ON (e.dept) e.name, e.dept FROM employees e JOIN departments d ON e.dept = d.name;

-- Error Variant 3
SELECT DISTINCT ON (salary) name, salary FROM employees;

-- Error Variant 4
SELECT DISTINCT ON (dept) title, dept FROM projects;

-- Correct Variant 1
SELECT DISTINCT ON (dept) title, dept FROM projects ORDER BY dept;

-- Correct Variant 2
SELECT DISTINCT ON (e.dept) e.name, e.dept FROM employees e JOIN departments d ON e.dept = d.name ORDER BY e.dept;

-- Correct Variant 3
SELECT DISTINCT ON (salary) name, salary FROM employees ORDER BY salary;



-- S7: DISTINCT ON ORDER BY mismatch (PG-SYN)
-- Error Variant 1
SELECT DISTINCT ON (dept) name, dept FROM employees ORDER BY name;

-- Error Variant 2
SELECT DISTINCT ON (dept) name, dept, salary FROM employees ORDER BY salary;

-- Error Variant 3
SELECT DISTINCT ON (id) id, name FROM employees ORDER BY name;

-- Error Variant 4
SELECT DISTINCT ON (title) title, budget FROM projects ORDER BY budget;

-- Correct Variant 1
SELECT DISTINCT ON (dept) name, dept, salary FROM employees ORDER BY dept, salary DESC;

-- Correct Variant 2
SELECT DISTINCT ON (title) title, budget FROM projects ORDER BY title;

-- Correct Variant 3
SELECT DISTINCT ON (id) id, name FROM employees ORDER BY id;




-- S8: Ranking window function missing ORDER BY in OVER (PG-SYN)
-- Error Variant 1
SELECT name, ROW_NUMBER() OVER () FROM employees;

-- Error Variant 2
SELECT name, RANK() OVER () FROM employees;

-- Error Variant 3
SELECT title, ROW_NUMBER() OVER () FROM projects;

-- Error Variant 4
SELECT name, RANK() OVER () FROM employees;

-- Correct Variant 1
SELECT name, ROW_NUMBER() OVER (ORDER BY salary DESC) FROM employees;

-- Correct Variant 2
SELECT name, dept, RANK() OVER (ORDER BY salary DESC) FROM employees;

-- Correct Variant 3
SELECT title, DENSE_RANK() OVER (ORDER BY budget DESC) FROM projects;


-- S9: Recursive CTE missing RECURSIVE keyword (PG-SYN)
-- Error Variant 1
WITH hierarchy AS (
    SELECT id, dept FROM employees
    UNION ALL
    SELECT e.id, e.dept
    FROM employees e
    JOIN hierarchy h ON e.dept = h.dept
)
SELECT * FROM hierarchy;

-- Error Variant 2
WITH project_chain AS (
    SELECT id, title FROM projects
    UNION ALL
    SELECT p.id, p.title
    FROM projects p
    JOIN project_chain pc ON p.id = pc.id + 1
)
SELECT * FROM project_chain;

-- Error Variant 3
WITH org AS (
    SELECT id, name, dept FROM employees
    UNION ALL
    SELECT e.id, e.name, e.dept
    FROM employees e
    JOIN org o ON e.dept = o.dept
    WHERE e.id <> o.id
)
SELECT * FROM org;
-- Error Variant 4
WITH dept_chain AS (
    SELECT id, dept FROM employees
    UNION ALL
    SELECT e.id, e.dept
    FROM employees e
    JOIN dept_chain dc ON e.id = dc.id + 1
)
SELECT * FROM dept_chain;

-- Correct Variant 1
WITH RECURSIVE dept_chain AS (
    SELECT id, dept FROM employees WHERE id = 1
    UNION ALL
    SELECT e.id, e.dept
    FROM employees e
    JOIN dept_chain dc ON e.id = dc.id + 1
)
SELECT * FROM dept_chain;

-- Correct Variant 2
WITH RECURSIVE project_chain AS (
    SELECT id, title FROM projects WHERE id = 1
    UNION ALL
    SELECT p.id, p.title
    FROM projects p
    JOIN project_chain pc ON p.id = pc.id + 1
)
SELECT * FROM project_chain;

-- Correct Variant 3
WITH dept_summary AS (
    SELECT dept, COUNT(*) AS total
    FROM employees
    GROUP BY dept
)
SELECT * FROM dept_summary;



-- S10: LATERAL subquery without outer reference (PG-SYN)
-- Error Variant 1
SELECT * FROM employees e, LATERAL (SELECT AVG(salary) FROM employees) sub;

-- Error Variant 2
SELECT * FROM departments d, LATERAL (SELECT MAX(budget) FROM projects) sub;

-- Error Variant 3
SELECT * FROM employees e, LATERAL (SELECT COUNT(*) FROM departments) sub;

-- Error Variant 4
SELECT * FROM projects p, LATERAL (SELECT SUM(salary) FROM employees) sub;

-- Correct Variant 1
SELECT e.name, sub.avg_budget FROM employees e,
LATERAL (
    SELECT AVG(budget) AS avg_budget
    FROM projects p
    WHERE p.dept = e.dept
) sub;

-- Correct Variant 2
SELECT d.name, sub.total FROM departments d,
LATERAL (
    SELECT COUNT(*) AS total
    FROM employees e
    WHERE e.dept = d.name
) sub;

-- Correct Variant 3
SELECT p.title, sub.max_sal FROM projects p,
LATERAL (
    SELECT MAX(salary) AS max_sal
    FROM employees e
    WHERE e.dept = p.dept
) sub;



-- PHASE 2 - RUNTIME RULES

-- R1: Column does not exist (SYN-2)
-- Error Variant 1
SELECT student FROM employees;

-- Error Variant 2
SELECT nmae FROM employees;

-- Error Variant 3
SELECT titel FROM projects;

-- Error Variant 4
SELECT name FROM employees WHERE wage > 5000;

-- Correct Variant 1
SELECT name FROM employees;

-- Correct Variant 2
SELECT title FROM projects;

-- Correct Variant 3
SELECT name FROM employees WHERE salary > 5000;



-- R2: Relation does not exist (SYN-2)
-- Error Variant 1
SELECT student FROM empower;

-- Error Variant 2
SELECT * FROM employes;

-- Error Variant 3
SELECT * FROM projet;

-- Error Variant 4
SELECT e.name, d.budget
FROM employees e
JOIN departmens d ON e.dept = d.name;

-- Correct Variant 1
SELECT * FROM employees;

-- Correct Variant 2
SELECT * FROM projects;

-- Correct Variant 3
SELECT e.name, d.budget FROM employees e JOIN departments d ON e.dept = d.name;




-- R3: Data type mismatch - operator does not exist (SYN-3)
-- Error Variant 1
SELECT * FROM employees WHERE name = 5000;

-- Error Variant 2
SELECT * FROM employees WHERE salary = TRUE;

-- Error Variant 3
SELECT * FROM projects WHERE title = 50000;

-- Error Variant 4
SELECT e.name FROM employees e JOIN departments d ON d.name = e.id;

-- Correct Variant 1
SELECT * FROM employees WHERE id = 1;

-- Correct Variant 2
SELECT * FROM projects WHERE title = 'Alpha';

-- Correct Variant 3
SELECT e.name, p.title FROM employees e JOIN projects p ON e.dept = p.dept;




-- R4: Column must appear in GROUP BY or aggregate (SYN-5)
-- Note: caught by S3 in Phase 1 if static analysis runs first
-- Error Variant 1
SELECT dept, salary FROM employees GROUP BY dept;

-- Error Variant 2
SELECT dept, budget FROM projects GROUP BY budget;

-- Error Variant 3
SELECT e.dept, e.name, COUNT(*) FROM employees e JOIN departments d ON e.dept = d.name GROUP BY e.dept;

-- Error Variant 4
SELECT dept, title, SUM(budget) FROM projects GROUP BY title;

-- Correct Variant 1
SELECT dept, MAX(salary) FROM employees GROUP BY dept;

-- Correct Variant 2
SELECT dept, name FROM employees GROUP BY dept, name;

-- Correct Variant 3
SELECT dept, COUNT(*), SUM(budget) FROM projects GROUP BY dept;



-- R5: Aggregate functions not allowed in WHERE (SYN-4)
-- Note: caught by S1 in Phase 1 if static analysis runs first
-- Error Variant 1
SELECT dept FROM employees WHERE COUNT(*) > 1;

-- Error Variant 2
SELECT title FROM projects WHERE AVG(budget) > 40000;

-- Error Variant 3
SELECT e.name, d.name FROM employees e JOIN departments d ON e.dept = d.name WHERE SUM(e.salary) > 50000;

-- Error Variant 4
SELECT budget FROM employees WHERE COUNT(*) > 15000;


-- Correct Variant 1
SELECT dept, COUNT(*) FROM employees GROUP BY dept HAVING COUNT(*) > 1;

-- Correct Variant 2
SELECT * FROM employees WHERE salary > (SELECT AVG(salary) FROM employees);

-- Correct Variant 3
SELECT title FROM projects WHERE budget > 40000;




-- R6: Syntax error at or near token (SYN-6)
-- Error Variant 1
SELECT name, FROM employees;

-- Error Variant 2
SELECT name dept FROM employees;

-- Error Variant 3
SELECT id, title, FROM projects;

-- Error Variant 4
SELCT name FROM employees;

-- Correct Variant 1
SELECT name, dept FROM employees;

-- Correct Variant 2
SELECT id, title FROM projects;

-- Correct Variant 3
SELECT name FROM employees;




-- R7: Invalid input syntax for type (SYN-3)
-- Error Variant 1
SELECT * FROM employees WHERE id = 'abc123';

-- Error Variant 2
SELECT * FROM employees WHERE salary = 'high';

-- Error Variant 3
SELECT * FROM projects WHERE budget = 'large';

-- Error Variant 4
SELECT * FROM employees WHERE id + 'one' > 5;


-- Correct Variant 1
SELECT * FROM employees WHERE salary = 6000;

-- Correct Variant 2
SELECT * FROM projects WHERE budget = 50000;

-- Correct Variant 3
SELECT * FROM employees WHERE id + 1 > 5;




-- R8: Subquery returns more than one row (SYN-6)
-- Error Variant 1
SELECT * FROM employees WHERE salary = (SELECT salary FROM employees);

-- Error Variant 2
SELECT * FROM projects WHERE budget = (SELECT budget FROM projects);

-- Error Variant 3
SELECT * FROM employees WHERE dept = (SELECT dept FROM departments);

-- Error Variant 4
SELECT name,
    (SELECT salary FROM employees) AS all_salaries
FROM employees;

-- Correct Variant 1
SELECT * FROM projects WHERE budget = (SELECT MAX(budget) FROM projects LIMIT 1);

-- Correct Variant 2
SELECT * FROM employees WHERE dept IN (SELECT name FROM departments);

-- Correct Variant 3
SELECT name,
    (SELECT MAX(salary) FROM employees) AS max_salary
FROM employees;




-- R9: Missing FROM-clause entry for table (SYN-2)
-- Error Variant 1
SELECT e.name FROM employees WHERE departments.dept = employees.dept;

-- Error Variant 2
SELECT p.title FROM projects WHERE e.dept = 'IT';

-- Error Variant 3
SELECT e.name, p.title FROM employees e WHERE p.dept = e.dept;

-- Error Variant 4
SELECT emp.name FROM employees WHERE emp.salary > 5000;

-- Correct Variant 1
SELECT e.name, p.title FROM employees e JOIN projects p ON e.dept = p.dept WHERE p.dept = 'IT';

-- Correct Variant 2
SELECT e.name, d.budget FROM employees e JOIN departments d ON e.dept = d.name WHERE e.dept = 'IT';

-- Correct Variant 3
SELECT emp.name FROM employees emp WHERE emp.salary > 5000;




-- R10: DISTINCT ON expressions must match ORDER BY (PG-SYN)
-- Note: caught by S7 in Phase 1 if static analysis runs first
-- Error Variant 1
SELECT DISTINCT ON (dept) name, dept FROM employees ORDER BY name;

-- Error Variant 2
SELECT DISTINCT ON (dept) name, dept, salary FROM employees ORDER BY salary;

-- Error Variant 3
SELECT DISTINCT ON (title) title, budget FROM projects ORDER BY budget;

-- Error Variant 4
SELECT DISTINCT ON (e.id) e.name, e.dept, d.budget FROM employees e JOIN departments d ON e.dept = d.name ORDER BY e.dept;

-- Correct Variant 1
SELECT DISTINCT ON (dept) name, dept, salary FROM employees ORDER BY dept, salary DESC;

-- Correct Variant 2
SELECT DISTINCT ON (title) title, budget FROM projects ORDER BY title;

-- Correct Variant 3
SELECT DISTINCT ON (id) id, name FROM employees ORDER BY id;