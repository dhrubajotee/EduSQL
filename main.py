from phase1.static_analyzer import StaticAnalyzer
from phase2.runtime_enhancer import RuntimeEnhancer


def run(query: str, verbose: bool = True) -> dict:
    """
    Run a SQL query through the full EduSQL pipeline.

    Returns a dict with:
        - phase (int): which phase caught the error (0 = none, 1 or 2)
        - errors (list): list of error result dicts from Phase 1
        - runtime (dict): result dict from Phase 2
        - feedback (str): final feedback to show the student
    """

    analyzer = StaticAnalyzer()
    enhancer = RuntimeEnhancer()

    # Static Analysis
    static_errors = analyzer.analyze(query)

    if static_errors:
        feedback_parts = []
        for error in static_errors:
            feedback_parts.append(error['feedback'])

        full_feedback = (
            f"EduSQL found {len(static_errors)} {'issue' if len(static_errors) == 1 else 'issues'} in your query "
            f"before execution:\n\n" +
            "\n\n".join(feedback_parts)
        )

        if verbose:
            print("=" * 60)
            print("PHASE 1 - Static Analysis")
            print("=" * 60)
            print(full_feedback)

        return {
            "phase": 1,
            "errors": static_errors,
            "runtime": None,
            "feedback": full_feedback
        }

    # Runtime Enhancement
    runtime_result = enhancer.execute(query)

    if runtime_result['success']:
        rows = runtime_result['rows']
        feedback = f"Query executed successfully. {len(rows)} row(s) returned."

        if verbose:
            print("=" * 60)
            print("Query executed successfully.")
            print("=" * 60)
            if rows:
                for row in rows:
                    print(row)

        return {
            "phase": 0,
            "errors": [],
            "runtime": runtime_result,
            "feedback": feedback
        }

    else:
        if runtime_result['feedback']:
            # enhanced message
            full_feedback = (
                "EduSQL detected an error when executing your query:\n\n" +
                runtime_result['feedback']
            )
        else:
            # No pattern matched and return raw PostgreSQL error
            full_feedback = (
                "Your query failed with the following PostgreSQL error:\n\n" +
                runtime_result['raw_error']
            )

        if verbose:
            print("=" * 60)
            print("PHASE 2 - Runtime Error Enhancement")
            print("=" * 60)
            print(full_feedback)

        return {
            "phase": 2,
            "errors": [],
            "runtime": runtime_result,
            "feedback": full_feedback
        }


def main():
    print("=" * 60)
    print("Welcome to EduSQL")
    print("A PostgreSQL-specific SQL error feedback tool")
    print("=" * 60)
    print("Type your SQL query below.")
    print("Type 'exit' to quit.\n")

    while True:
        print("Enter SQL query (end with semicolon):")
        lines = []
        while True:
            line = input()
            if line.strip().lower() == 'exit':
                print("Goodbye!")
                return
            lines.append(line)
            if line.strip().endswith(';'):
                break

        query = ' '.join(lines)
        print()
        run(query)
        print()


if __name__ == '__main__':
    main()
