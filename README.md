# EduSQL

A two-phase PostgreSQL-specific SQL error classification and feedback tool for learners.

EduSQL intercepts SQL errors and translates them into structured, educational feedback based on the [Taipalus taxonomy](https://doi.org/10.1145/3197091.3197104). It combines static analysis before execution with runtime error enhancement after execution, covering errors that PostgreSQL either reports unclearly or does not report at all.

---

## What it does

When a student submits a SQL query, EduSQL runs it through two phases:

**Phase 1 - Static Analysis**
The query is parsed into an Abstract Syntax Tree before execution. Ten detectors check for structural errors such as aggregate functions in WHERE clauses, missing GROUP BY columns, NULL misuse, and PostgreSQL-specific constructs like DISTINCT ON and LATERAL. Errors are reported with their taxonomy category and an explanation written in plain language.

**Phase 2 - Runtime Enhancement**
If no static errors are found, the query is executed against a live PostgreSQL database. Any exception raised by PostgreSQL is matched against known error patterns and replaced with a learner-oriented explanation that names the underlying concept and suggests what to fix.

Both phases map errors to the Taipalus taxonomy (SYN-2 through SYN-6, plus PG-SYN for PostgreSQL-specific constructs).

---

## Requirements

- Python 3.11 or higher
- PostgreSQL (running locally)
- The following Python libraries:
  - `sqlglot`
  - `psycopg2`
  - `sqlparse`

Install dependencies:

```bash
pip install sqlglot psycopg2 sqlparse
```

---

## Database setup

EduSQL requires a PostgreSQL database to exist before Phase 2 can run. Create one and set up a test table:

```sql
CREATE DATABASE thesis_test;

\c thesis_test

CREATE TABLE public.employees (
    id      INTEGER NOT NULL,
    name    CHARACTER VARYING(100),
    dept    CHARACTER VARYING(50),
    salary  INTEGER
);

INSERT INTO public.employees VALUES (1, 'Alice', 'IT', 6000);
INSERT INTO public.employees VALUES (2, 'Bob',   'HR', 4000);
INSERT INTO public.employees VALUES (3, 'Carol', 'IT', 7000);
INSERT INTO public.employees VALUES (4, 'David', 'HR', 3500);
```

---

## Configuration

Edit `config.py` to match your PostgreSQL connection settings:

```python
DB_CONFIG = {
    "dbname":   "thesis_test",
    "user":     "postgres",
    "password": "your_password",
    "host":     "localhost",
    "port":     5432
}
```

---

## Running EduSQL

```bash
py main.py
```

You will see a prompt where you can type or paste a SQL query. End the query with a semicolon and press Enter. Type `exit` to quit.

**Example session:**

```
EduSQL> SELECT * FROM employees WHERE COUNT(*) > 5;

EduSQL found 1 issue(s) in your query before execution:

[S1] Aggregate function in WHERE clause
Taxonomy category: SYN-4
--------------------------------------------------
Your query uses an aggregate function (such as COUNT, SUM, AVG, MIN, or MAX)
inside a WHERE clause. This is not allowed because the WHERE clause filters
rows before any grouping takes place, so aggregate values are not yet available.

To filter based on aggregate results, use a HAVING clause after GROUP BY.

Example fix:
  Instead of: WHERE COUNT(*) > 5
  Use:        GROUP BY column_name HAVING COUNT(*) > 5
```

A second example showing runtime error enhancement — when no static error is found but execution fails:

```
EduSQL> SELECT * FROM employees WHERE salary = 'abc123';

[R7] Data type mismatch
Taxonomy category: SYN-3
--------------------------------------------------
You provided a value that does not match the expected data type of the
column. This happens when you compare a column to a value of the wrong
type, for example comparing an integer column to a text string.
--------------------------------------------------
Original PostgreSQL error:
invalid input syntax for type integer: "abc123"
```

A third example where both phases pass — the query is correct:

```
EduSQL> SELECT dept, COUNT(*) FROM employees GROUP BY dept;

Query executed successfully. No errors detected.
```

---

## Rule coverage

### Phase 1 - Static rules

| Rule | Category | Description |
|------|----------|-------------|
| S1 | SYN-4 | Aggregate function in WHERE clause |
| S2 | SYN-5 | HAVING without GROUP BY |
| S3 | SYN-5 | Column in SELECT missing from GROUP BY |
| S4 | SYN-6 | NULL comparison using = or <> |
| S5 | SYN-6 | Missing FROM clause |
| S6 | PG-SYN | DISTINCT ON without ORDER BY |
| S7 | PG-SYN | DISTINCT ON ORDER BY mismatch |
| S8 | PG-SYN | Ranking window function missing ORDER BY in OVER |
| S9 | PG-SYN | Recursive CTE missing RECURSIVE keyword |
| S10 | PG-SYN | LATERAL subquery without outer reference |

### Phase 2 - Runtime rules

| Rule | Category | Description |
|------|----------|-------------|
| R1 | SYN-2 | Column does not exist |
| R2 | SYN-2 | Relation does not exist |
| R3 | SYN-3 | Operator does not exist (type mismatch) |
| R4 | SYN-5 | Column must appear in GROUP BY or aggregate |
| R5 | SYN-4 | Aggregate functions not allowed in WHERE |
| R6 | SYN-6 | Syntax error at or near token |
| R7 | SYN-3 | Invalid input syntax for type |
| R8 | SYN-6 | Subquery returns more than one row |
| R9 | SYN-2 | Missing FROM-clause entry for table |
| R10 | PG-SYN | DISTINCT ON expressions must match ORDER BY |

---

## Project structure

```
edusql/
├── main.py          # Entry point and command-line interface
├── config.py        # Database connection settings
├── taxonomy/
│   └── errors.py    # All 20 rule definitions as dataclasses
├── phase1/
│   └── static_analyzer.py   # AST-based static detectors
└── phase2/
    └── runtime_enhancer.py  # PostgreSQL error pattern matching
```

---

## Notes

- Every query in Phase 2 is executed inside a transaction that is always rolled back. EduSQL never modifies the database state.
- If a query cannot be parsed by `sqlglot`, a generic parse error is returned and no detectors are executed.
- If no runtime pattern matches, the original PostgreSQL error is returned as a fallback.

---

## Related work

This tool was developed as part of a Master's thesis at the University of Jyväskylä. It extends the taxonomy-based approach of [SQLMentor](https://doi.org/10.1145/3594781.3594789) to PostgreSQL-specific constructs and adds runtime error enhancement, which SQLMentor does not cover.

The Taipalus taxonomy used for error classification is described in:
> Taipalus, T., Siponen, M., & Vartiainen, T. (2018). Errors and complications in SQL query formulation. *ACM Transactions on Computing Education*, 18(3), 1–29.

---

## Author

Dhrubajotee Howlader
Master's in Artificial Intelligence, University of Jyväskylä
