import re
import psycopg2
from psycopg2 import sql
from taxonomy.errors import R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, ErrorRule
from config import DB_CONFIG


RUNTIME_PATTERNS = [
    # R1 - column does not exist
    (re.compile(r'column .* does not exist', re.IGNORECASE), R1),

    # R2 - relation/table does not exist
    (re.compile(r'relation .* does not exist', re.IGNORECASE), R2),

    # R3 - operator does not exist (type mismatch)
    (re.compile(r'operator does not exist', re.IGNORECASE), R3),

    # R4 - column must appear in GROUP BY or aggregate
    (re.compile(r'must appear in the GROUP BY clause', re.IGNORECASE), R4),

    # R5 - aggregate not allowed in WHERE
    (re.compile(r'aggregate functions are not allowed in WHERE', re.IGNORECASE), R5),

    # R6 - syntax error
    (re.compile(r'syntax error at or near', re.IGNORECASE), R6),

    # R7 - invalid input syntax for type
    (re.compile(r'invalid input syntax for type', re.IGNORECASE), R7),

    # R8 - subquery returns more than one row
    (re.compile(r'more than one row returned by a subquery', re.IGNORECASE), R8),

    # R9 - missing FROM clause entry
    (re.compile(r'missing FROM-clause entry for table', re.IGNORECASE), R9),

    # R10 - DISTINCT ON must match ORDER BY
    (re.compile(r'SELECT DISTINCT ON expressions must match initial ORDER BY expressions', re.IGNORECASE), R10),
]


class RuntimeEnhancer:
    
    def __init__(self):
        self.connection = None

    def _connect(self):
        """Connection to PostgreSQL."""
        self.connection = psycopg2.connect(**DB_CONFIG)
        self.connection.autocommit = False

    def _disconnect(self):
        """Close the PostgreSQL connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute(self, query: str) -> dict:
        """
        Execute a SQL query against PostgreSQL.

        Returns a dict with:
            - success (bool): True if query executed without error
            - rule (ErrorRule | None): matched rule if error found
            - raw_error (str | None): original PostgreSQL error message
            - feedback (str | None): enhanced feedback message
            - rows (list | None): result rows if query succeeded
        """
        try:
            self._connect()
            cursor = self.connection.cursor()

            try:
                cursor.execute(query)
                rows = cursor.fetchall() if cursor.description else []
                self.connection.rollback()  # always rollback to avoid side effects
                return {
                    "success": True,
                    "rule": None,
                    "raw_error": None,
                    "feedback": None,
                    "rows": rows
                }

            except psycopg2.Error as e:
                self.connection.rollback()
                raw_error = str(e).strip()
                matched_rule = self._match_error(raw_error)

                if matched_rule:
                    feedback = self._build_feedback(matched_rule, raw_error)
                else:
                    feedback = None  # no match, will return raw error

                return {
                    "success": False,
                    "rule": matched_rule,
                    "rule_id": matched_rule.rule_id if matched_rule else None,
                    "category": matched_rule.category if matched_rule else None,
                    "label": matched_rule.label if matched_rule else None,
                    "raw_error": raw_error,
                    "feedback": feedback,
                    "rows": None
                    }

        finally:
            self._disconnect()

    def _match_error(self, error_message: str) -> ErrorRule | None:
        
        for pattern, rule in RUNTIME_PATTERNS:
            if pattern.search(error_message):
                return rule
        return None


    def _build_feedback(self, rule: ErrorRule, raw_error: str) -> str:
        message = self._personalise_message(rule, raw_error)
        return (
            f"[{rule.rule_id}] {rule.label}\n"
            f"Taxonomy category: {rule.category}\n"
            f"{'-' * 50}\n"
            f"{message}\n"
            f"{'-' * 50}\n"
            f"Original PostgreSQL error:\n{raw_error}"
        )

    def _personalise_message(self, rule: ErrorRule, raw_error: str) -> str:
        
        if rule.rule_id == "R1":
            match = re.search(r'column "(.*?)" does not exist', raw_error, re.IGNORECASE)
            if match:
                col = match.group(1)
                return (
                    f'PostgreSQL could not find the column "{col}". '
                    f"Check for spelling mistakes, make sure the column belongs to a table "
                    f"in your FROM clause"
                )

        if rule.rule_id == "R2":
            match = re.search(r'relation "(.*?)" does not exist', raw_error, re.IGNORECASE)
            if match:
                table = match.group(1)
                return (
                    f'PostgreSQL could not find a table named "{table}". '
                    f"Check for spelling mistakes and make sure the table exists "
                    f"in the current schema."
                )

        if rule.rule_id == "R6":
            match = re.search(r'syntax error at or near "(.*?)"', raw_error, re.IGNORECASE)
            if match:
                token = match.group(1)
                return (
                    f'PostgreSQL found a syntax error near "{token}". '
                    f"Common causes include an extra or missing comma, an unbalanced "
                    f"parenthesis, a misspelled or misplaced keyword, or incorrect "
                    f"clause order. Review the query structure around this token."
                )

        if rule.rule_id == "R9":
            match = re.search(r'missing FROM-clause entry for table "(.*?)"', raw_error, re.IGNORECASE)
            if match:
                alias = match.group(1)
                return (
                    f'The table or alias "{alias}" was referenced in your query but not '
                    f"declared in the FROM clause. Make sure every table you reference is "
                    f"listed in FROM, and that any alias you use matches what you declared."
                )

        # fallback to static message for all other rules
        return rule.message
