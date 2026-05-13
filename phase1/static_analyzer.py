import sqlglot
from sqlglot import exp
from taxonomy.errors import S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, ErrorRule


# Ranking window functions that require ORDER BY inside OVER(...)
RANKING_FUNCTIONS = {
    'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'NTILE',
    'PERCENT_RANK', 'CUME_DIST'
}

# Expected SQL clause order for S5
CLAUSE_ORDER = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY', 'LIMIT']


class StaticAnalyzer:
    
    def __init__(self):
        pass

    def analyze(self, query: str) -> list[dict]:
        """
        parse the query and run all static detectors.

        returns a list of dicts, each containing:
            - rule (ErrorRule): the matched rule
            - detail (str): optional extra detail about where error was found
            - feedback (str): full formatted feedback message
        """
        results = []

        try:
            # parse
            statements = sqlglot.parse(query, dialect='postgres')
        except Exception as e:
            # if parsing fails completely, return a generic syntax error
            results.append(self._build_result(S5, f"Query could not be parsed: {str(e)}"))
            return results

        if not statements:
            return results

        ast = statements[0]

        # run all detectors in order
        detectors = [
            self._detect_s1,
            self._detect_s2,
            self._detect_s3,
            self._detect_s4,
            self._detect_s5,
            self._detect_s6,
            self._detect_s7,
            self._detect_s8,
            self._detect_s9,
            self._detect_s10,
        ]

        for detector in detectors:
            errors = detector(ast, query)
            results.extend(errors)

        return results

    def _build_result(self, rule: ErrorRule, detail: str = '') -> dict:
        
        feedback = (
            f"[{rule.rule_id}] {rule.label}\n"
            f"Taxonomy category: {rule.category}\n"
            f"{'-' * 50}\n"
            f"{rule.message}"
        )
        if detail:
            feedback += f"\n\nDetail: {detail}"
        return {
            "rule": rule,
            "rule_id": rule.rule_id,
            "category": rule.category,
            "label": rule.label,
            "detail": detail,
            "feedback": feedback
            }

    def _detect_s1(self, ast, query: str) -> list[dict]:
        results = []
        aggregate_types = (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)

        for where_clause in ast.find_all(exp.Where):
            for agg in where_clause.find_all(*aggregate_types):
                # Skip aggregates inside subqueries within WHERE
                parent = agg.parent
                is_inside_subquery = False
                while parent is not None and not isinstance(parent, exp.Where):
                    if isinstance(parent, exp.Subquery):
                        is_inside_subquery = True
                        break
                    parent = parent.parent
                if is_inside_subquery:
                    continue
                results.append(self._build_result(
                    S1,
                    f"Found '{agg.sql()}' inside WHERE clause"
                ))
                break

        return results

    
    # S2 - HAVING without GROUP BY
    def _detect_s2(self, ast, query: str) -> list[dict]:
        results = []

        for select in ast.find_all(exp.Select):
            has_having = select.args.get('having') is not None
            has_group = select.args.get('group') is not None

            if has_having and not has_group:
                results.append(self._build_result(S2))

        return results

    
    # S3 - Column in SELECT missing from GROUP BY
    def _detect_s3(self, ast, query: str) -> list[dict]:
        results = []

        for select in ast.find_all(exp.Select):
            group_node = select.args.get('group')
            if not group_node:
                continue  # no GROUP BY, skip

            # Collect GROUP BY column names
            group_cols = set()
            for expr in group_node.find_all(exp.Column):
                group_cols.add(expr.name.lower())

            # Check SELECT columns
            for expression in select.expressions:
                # Skip aggregated expressions
                if expression.find(exp.AggFunc):
                    continue
                # Check plain columns
                for col in expression.find_all(exp.Column):
                    if col.name.lower() not in group_cols:
                        results.append(self._build_result(
                            S3,
                            f"Column '{col.name}' is in SELECT but not in GROUP BY"
                        ))

        return results

    
    # S4 - NULL comparison using = or <>
    def _detect_s4(self, ast, query: str) -> list[dict]:
        results = []

        for eq in ast.find_all(exp.EQ, exp.NEQ):
            left = eq.left
            right = eq.right
            if isinstance(left, exp.Null) or isinstance(right, exp.Null):
                results.append(self._build_result(
                    S4,
                    f"Found NULL comparison: '{eq.sql()}'"
                ))

        return results

    
    # S5 - Wrong clause order
    def _detect_s5(self, ast, query: str) -> list[dict]:
        results = []

        for select in ast.find_all(exp.Select):
            from_clause = select.args.get('from')
            has_tables = len(list(select.find_all(exp.Table))) > 0

            if from_clause is not None or has_tables:
                continue

            has_where = select.args.get('where') is not None

            has_columns = False
            for expr in select.expressions:
                if expr.find(exp.Column):
                    has_columns = True
                    break

            if has_where or has_columns:
                results.append(self._build_result(
                    S5,
                    "Query references columns or has WHERE clause but no FROM clause"
                ))

        return results

    
    # S6 - DISTINCT ON without ORDER BY
    def _detect_s6(self, ast, query: str) -> list[dict]:
        results = []

        for select in ast.find_all(exp.Select):
            distinct = select.args.get('distinct')
            if distinct is None:
                continue

            # DISTINCT ON has 'on' expressions
            distinct_on = distinct.args.get('on')
            if not distinct_on:
                continue  # plain DISTINCT, not DISTINCT ON

            order = select.args.get('order')
            if order is None:
                distinct_cols = ', '.join(e.sql() for e in distinct_on.expressions)
                results.append(self._build_result(
                    S6,
                    f"DISTINCT ON ({distinct_cols}) has no ORDER BY clause"
                ))

        return results

    
    # S7 - DISTINCT ON ORDER BY mismatch
    def _detect_s7(self, ast, query: str) -> list[dict]:
        results = []

        for select in ast.find_all(exp.Select):
            distinct = select.args.get('distinct')
            if distinct is None:
                continue

            distinct_on = distinct.args.get('on')
            if not distinct_on:
                continue

            order = select.args.get('order')
            if order is None:
                continue  # handled by S6

            # Get DISTINCT ON expressions
            distinct_exprs = [e.sql().lower() for e in distinct_on.expressions]

            # Get ORDER BY expressions (strip ASC/DESC)
            order_exprs = []
            for ordered in order.find_all(exp.Ordered):
                order_exprs.append(ordered.this.sql().lower())

            # Check that ORDER BY starts with DISTINCT ON expressions
            for i, d_expr in enumerate(distinct_exprs):
                if i >= len(order_exprs) or order_exprs[i] != d_expr:
                    results.append(self._build_result(
                        S7,
                        f"DISTINCT ON expression '{d_expr}' not at position {i+1} in ORDER BY"
                    ))
                    break

        return results

    
    # S8 - Ranking window function missing ORDER BY in OVER
    def _detect_s8(self, ast, query: str) -> list[dict]:
        results = []

        for window in ast.find_all(exp.Window):
            func = window.this
            if func is None:
                continue

            func_name = type(func).__name__.upper()

            # Map sqlglot class names to SQL function names
            name_map = {
                'ROWNUMBER': 'ROW_NUMBER',
                'RANK': 'RANK',
                'DENSERANK': 'DENSE_RANK',
                'NTILE': 'NTILE',
                'PERCENTRANK': 'PERCENT_RANK',
                'CUMEDIST': 'CUME_DIST',
            }

            sql_name = name_map.get(func_name, func_name)

            if sql_name not in RANKING_FUNCTIONS:
                continue

            order = window.args.get('order')
            if order is None:
                results.append(self._build_result(
                    S8,
                    f"'{sql_name}() OVER (...)' is missing ORDER BY inside OVER"
                ))

        return results

    
    # S9 - Recursive CTE missing RECURSIVE keyword
    def _detect_s9(self, ast, query: str) -> list[dict]:
        results = []

        query_upper = query.upper()

        # Only check queries with WITH but not WITH RECURSIVE
        if 'WITH' not in query_upper:
            return results
        if 'WITH RECURSIVE' in query_upper:
            return results

        # Find all CTEs
        with_node = ast.find(exp.With)
        if not with_node:
            return results

        for cte in with_node.find_all(exp.CTE):
            cte_name = cte.alias.lower() if cte.alias else None
            if not cte_name:
                continue

            # Check if the CTE body references its own name
            cte_body = cte.this
            if cte_body is None:
                continue

            for table in cte_body.find_all(exp.Table):
                if table.name.lower() == cte_name:
                    results.append(self._build_result(
                        S9,
                        f"CTE '{cte.alias}' references itself but WITH RECURSIVE is missing"
                    ))
                    break

        return results

    
    # S10 - LATERAL subquery without outer reference
    def _detect_s10(self, ast, query: str) -> list[dict]:
        results = []

        if 'LATERAL' not in query.upper():
            return results

        for select in ast.find_all(exp.Select):

            # Check if this SELECT has any LATERAL join
            lateral_joins = [
                join for join in select.find_all(exp.Join)
                if join.find(exp.Lateral)
            ]
            if not lateral_joins:
                continue

            # Collect outer aliases from FROM clause main table
            outer_aliases = set()

            from_clause = select.args.get('from_')
            if from_clause and isinstance(from_clause.this, exp.Table):
                tbl = from_clause.this
                alias = tbl.alias or tbl.name
                if alias:
                    outer_aliases.add(alias.lower())

            # Collect aliases from non-LATERAL joins only
            for join in select.find_all(exp.Join):
                if join.find(exp.Lateral):
                    continue
                for tbl in join.find_all(exp.Table):
                    alias = tbl.alias or tbl.name
                    if alias:
                        outer_aliases.add(alias.lower())

            # For each LATERAL join, check if its SQL references any outer alias
            for join in lateral_joins:
                lateral = join.find(exp.Lateral)
                if not lateral:
                    continue

                # Use SQL text — simpler and more reliable than AST traversal
                lateral_sql = lateral.sql().lower()

                has_outer_ref = any(
                    f"{alias}." in lateral_sql
                    for alias in outer_aliases
                    if alias
                )

                if not has_outer_ref:
                    results.append(self._build_result(
                        S10,
                        "LATERAL subquery does not reference any outer table column"
                    ))

        return results
