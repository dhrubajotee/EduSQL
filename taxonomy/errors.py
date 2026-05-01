from dataclasses import dataclass


@dataclass
class ErrorRule:
    """error rule in EduSQL."""
    rule_id: str           # e.g. 'S1', 'R3'
    category: str          # Taipalus category e.g. 'SYN-4'
    label: str             # Short label e.g. 'Aggregate in WHERE'
    message: str           # Enhanced feedback message for the student
    phase: int             # 1 = static, 2 = runtime


# Static Analysis

S1 = ErrorRule(
    rule_id='S1',
    category='SYN-4',
    label='Aggregate function in WHERE clause',
    message=(
        "Your query uses an aggregate function (such as COUNT, SUM, AVG, MIN, or MAX) "
        "inside a WHERE clause. This is not allowed because the WHERE clause filters "
        "rows before any grouping takes place, so aggregate values are not yet available.\n\n"
        
        "To filter based on aggregate results, you should use a HAVING clause after GROUP BY.\n\n"
        
        "Example fix:\n"
        "  Instead of: WHERE COUNT(*) > 5\n"
        "  Use:        GROUP BY column_name HAVING COUNT(*) > 5"
    ),
    phase=1
)

S2 = ErrorRule(
    rule_id='S2',
    category='SYN-5',
    label='HAVING without GROUP BY',
    message=(
        "You used a HAVING clause without a GROUP BY clause. HAVING is designed "
        "to filter groups created by GROUP BY, so it does not make sense on its "
        "own.\n\n"
        "If you want to filter rows based on a condition, use a WHERE clause. "
        "If you want to filter groups, add a GROUP BY clause first.\n\n"
        "Example fix:\n"
        "  Add GROUP BY before your HAVING clause, or replace HAVING with WHERE."
    ),
    phase=1
)

S3 = ErrorRule(
    rule_id='S3',
    category='SYN-5',
    label='Column in SELECT missing from GROUP BY',
    message=(
        "You have a column in your SELECT clause that is not in your GROUP BY "
        "clause and is not wrapped in an aggregate function.\n\n"
        "When you use GROUP BY, every column in SELECT must either:\n"
        "  1. Appear in the GROUP BY list, or\n"
        "  2. Be wrapped in an aggregate function like COUNT(), AVG(), etc.\n\n"
        "Example fix:\n"
        "  Either add the column to GROUP BY, or wrap it in an aggregate function."
    ),
    phase=1
)

S4 = ErrorRule(
    rule_id='S4',
    category='SYN-6',
    label='NULL comparison using = or <>',
    message=(
        "You compared a value to NULL using = or <>. In SQL, NULL represents an "
        "unknown value, and comparing anything to NULL using = or <> always "
        "returns NULL (not true or false), which means no rows will ever match "
        "your condition.\n\n"
        "To check for NULL values, use IS NULL or IS NOT NULL.\n\n"
        "Example fix:\n"
        "  Instead of: WHERE column = NULL\n"
        "  Use:        WHERE column IS NULL\n\n"
        "  Instead of: WHERE column <> NULL\n"
        "  Use:        WHERE column IS NOT NULL"
    ),
    phase=1
)

S5 = ErrorRule(
    rule_id='S5',
    category='SYN-6',
    label='Missing FROM clause',
    message=(
        "Your query references a table or column but is missing a FROM clause. "
        "The FROM clause tells PostgreSQL which table to retrieve data from. "
        "Without it, PostgreSQL cannot find the data you are asking for.\n\n"
        "Example fix:\n"
        "  Instead of: SELECT name WHERE salary > 5000\n"
        "  Use:        SELECT name FROM employees WHERE salary > 5000"
    ),
    phase=1
)

S6 = ErrorRule(
    rule_id='S6',
    category='PG-SYN',
    label='DISTINCT ON without ORDER BY',
    message=(
        "You used DISTINCT ON without an ORDER BY clause. In PostgreSQL, "
        "DISTINCT ON requires an ORDER BY clause that begins with the same "
        "expression used in DISTINCT ON. Without ORDER BY, PostgreSQL cannot "
        "determine which row to keep from each group, and will raise an error.\n\n"
        "Example fix:\n"
        "  SELECT DISTINCT ON (dept_id) name, dept_id\n"
        "  FROM employees\n"
        "  ORDER BY dept_id;  -- must start with dept_id"
    ),
    phase=1
)

S7 = ErrorRule(
    rule_id='S7',
    category='PG-SYN',
    label='DISTINCT ON ORDER BY mismatch',
    message=(
        "Your ORDER BY clause does not start with the same expression used in "
        "DISTINCT ON. PostgreSQL requires that the DISTINCT ON expression appears "
        "as the leftmost element of the ORDER BY clause. This is how PostgreSQL "
        "decides which row to keep from each group.\n\n"
        "Example fix:\n"
        "  SELECT DISTINCT ON (dept_id) name, dept_id\n"
        "  FROM employees\n"
        "  ORDER BY dept_id, name;  -- dept_id must come first"
    ),
    phase=1
)

S8 = ErrorRule(
    rule_id='S8',
    category='PG-SYN',
    label='Ranking window function missing ORDER BY in OVER',
    message=(
        "You used a ranking window function (ROW_NUMBER, RANK, DENSE_RANK, "
        "NTILE, or similar) without an ORDER BY inside the OVER clause. "
        "Without ORDER BY, the ranking is arbitrary and non-deterministic, "
        "meaning the results will be unpredictable.\n\n"
        "Example fix:\n"
        "  Instead of: ROW_NUMBER() OVER ()\n"
        "  Use:        ROW_NUMBER() OVER (ORDER BY salary DESC)"
    ),
    phase=1
)

S9 = ErrorRule(
    rule_id='S9',
    category='PG-SYN',
    label='Recursive CTE missing RECURSIVE keyword',
    message=(
        "Your Common Table Expression (CTE) appears to reference its own name, "
        "which means it is recursive. In PostgreSQL, recursive CTEs must be "
        "declared with the RECURSIVE keyword after WITH. Without it, PostgreSQL "
        "treats the self-reference as an undefined table and raises an error.\n\n"
        "Example fix:\n"
        "  Instead of: WITH hierarchy AS (...)\n"
        "  Use:        WITH RECURSIVE hierarchy AS (...)"
    ),
    phase=1
)

S10 = ErrorRule(
    rule_id='S10',
    category='PG-SYN',
    label='LATERAL subquery without outer reference',
    message=(
        "You used the LATERAL keyword with a subquery that does not reference "
        "any column from the preceding tables in the FROM clause. LATERAL is "
        "only meaningful when the subquery needs to access columns from an outer "
        "table expression. If your subquery does not do this, LATERAL is "
        "unnecessary.\n\n"
        "Example of correct LATERAL usage:\n"
        "  SELECT e.name, d.avg_sal\n"
        "  FROM employees e,\n"
        "  LATERAL (SELECT AVG(salary) FROM employees\n"
        "           WHERE dept_id = e.dept_id) d(avg_sal);\n"
        "  -- references e.dept_id from the outer FROM clause"
    ),
    phase=1
)


# Runtime Enhancement

R1 = ErrorRule(
    rule_id='R1',
    category='SYN-2',
    label='Column does not exist',
    message=(
        "PostgreSQL could not find the column you referenced. This usually "
        "happens because of a spelling mistake in the column name, or because "
        "you are referencing a column from the wrong table.\n\n"
        "Things to check:\n"
        "  - Check the spelling of the column name\n"
        "  - Make sure the column exists in the table you are querying\n"
        "  - If using aliases, make sure you are using the alias correctly\n"
        "  - Column names in PostgreSQL are case-sensitive when quoted"
    ),
    phase=2
)

R2 = ErrorRule(
    rule_id='R2',
    category='SYN-2',
    label='Table does not exist',
    message=(
        "PostgreSQL could not find the table you referenced. This usually "
        "happens because of a spelling mistake in the table name, or because "
        "the table is in a different schema.\n\n"
        "Things to check:\n"
        "  - Check the spelling of the table name\n"
        "  - Make sure the table exists in the current database\n"
        "  - If the table is in a specific schema, use schema.table notation\n"
        "  - Table names in PostgreSQL are case-sensitive when quoted"
    ),
    phase=2
)

R3 = ErrorRule(
    rule_id='R3',
    category='SYN-3',
    label='Type mismatch in comparison',
    message=(
        "You tried to compare two values of incompatible data types. Unlike "
        "some other database systems, PostgreSQL does not automatically convert "
        "between types in comparisons. For example, comparing an integer column "
        "to a text value will cause this error.\n\n"
        "Things to check:\n"
        "  - Make sure both sides of your comparison use the same data type\n"
        "  - If comparing a number column to a string, remove the quotes\n"
        "  - If you need to convert a type explicitly, use CAST or ::\n\n"
        "Example fix:\n"
        "  Instead of: WHERE id = '5'\n"
        "  Use:        WHERE id = 5"
    ),
    phase=2
)

R4 = ErrorRule(
    rule_id='R4',
    category='SYN-5',
    label='Column must appear in GROUP BY or aggregate',
    message=(
        "You have a column in your SELECT clause that is not in your GROUP BY "
        "clause and is not wrapped in an aggregate function. When you use "
        "GROUP BY, PostgreSQL needs to know how to produce a single value for "
        "each group for every column in SELECT.\n\n"
        "Things to check:\n"
        "  - Add the column to your GROUP BY clause, or\n"
        "  - Wrap the column in an aggregate function like MAX(), MIN(), etc.\n\n"
        "Example fix:\n"
        "  Instead of: SELECT dept, salary FROM employees GROUP BY dept\n"
        "  Use:        SELECT dept, AVG(salary) FROM employees GROUP BY dept"
    ),
    phase=2
)

R5 = ErrorRule(
    rule_id='R5',
    category='SYN-4',
    label='Aggregate function not allowed in WHERE',
    message=(
        "You used an aggregate function inside a WHERE clause. PostgreSQL does "
        "not allow this because WHERE is evaluated before grouping happens, so "
        "there are no aggregated values available at that stage.\n\n"
        "Example fix:\n"
        "  Instead of: WHERE AVG(salary) > 5000\n"
        "  Use:        GROUP BY dept HAVING AVG(salary) > 5000"
    ),
    phase=2
)

R6 = ErrorRule(
    rule_id='R6',
    category='SYN-6',
    label='Syntax error',
    message=(
        "PostgreSQL found a syntax error in your query near the token mentioned "
        "in the error message. This means there is something in your query that "
        "does not follow SQL grammar rules.\n\n"
        "Common causes:\n"
        "  - Missing comma between column names in SELECT\n"
        "  - Missing or extra parenthesis\n"
        "  - Misspelled keyword\n"
        "  - Wrong clause order\n"
        "  - Using a reserved word as a column or table name without quoting it"
    ),
    phase=2
)

R7 = ErrorRule(
    rule_id='R7',
    category='SYN-3',
    label='Data type mismatch',
    message=(
        "You provided a value that does not match the expected data type of "
        "the column. This happens when you compare a column to a value of the "
        "wrong type, for example comparing an integer column to a text string.\n\n"
        "Things to check:\n"
        "  - If the column is a number, remove the quotes around the value\n"
        "  - If the column is a date, use the correct format (e.g. '2024-01-15')\n"
        "  - Make sure the value type matches the column type\n\n"
        "Example fix:\n"
        "  Instead of: WHERE salary = 'hello'\n"
        "  Use:        WHERE salary = 5000"
    ),
    phase=2
)

R8 = ErrorRule(
    rule_id='R8',
    category='SYN-6',
    label='Subquery returns more than one row',
    message=(
        "Your subquery returned more than one row in a context where only a "
        "single value is expected. This commonly happens when you use a subquery "
        "with = in a WHERE clause but the subquery returns multiple rows.\n\n"
        "Things to check:\n"
        "  - If you expect multiple values, use IN instead of =\n"
        "  - If you expect a single value, add a condition to your subquery "
        "to make it return only one row\n\n"
        "Example fix:\n"
        "  Instead of: WHERE salary = (SELECT salary FROM employees)\n"
        "  Use:        WHERE salary IN (SELECT salary FROM employees)"
    ),
    phase=2
)

R9 = ErrorRule(
    rule_id='R9',
    category='SYN-2',
    label='Missing FROM clause entry for table',
    message=(
        "You referenced a table or alias in your query that was not declared "
        "in the FROM clause. PostgreSQL cannot find the source of the columns "
        "you are trying to use.\n\n"
        "Things to check:\n"
        "  - Make sure every table you reference is listed in your FROM clause\n"
        "  - If you used a table alias, make sure it matches what you declared\n"
        "  - If you are using a JOIN, make sure the joined table is included"
    ),
    phase=2
)

R10 = ErrorRule(
    rule_id='R10',
    category='PG-SYN',
    label='DISTINCT ON expressions must match ORDER BY',
    message=(
        "PostgreSQL requires that the expression used in DISTINCT ON also "
        "appears as the leftmost element of the ORDER BY clause. Your ORDER BY "
        "clause either starts with a different expression or is missing entirely.\n\n"
        "Example fix:\n"
        "  SELECT DISTINCT ON (dept_id) name, dept_id\n"
        "  FROM employees\n"
        "  ORDER BY dept_id, name;  -- dept_id must be first in ORDER BY"
    ),
    phase=2
)


STATIC_RULES = [S1, S2, S3, S4, S5, S6, S7, S8, S9, S10]

RUNTIME_RULES = [R1, R2, R3, R4, R5, R6, R7, R8, R9, R10]

ALL_RULES = STATIC_RULES + RUNTIME_RULES


def get_rule(rule_id: str) -> ErrorRule | None:
    """return error rule by its rule_id, or null."""
    for rule in ALL_RULES:
        if rule.rule_id == rule_id:
            return rule
    return None
