"""Lesson content for Learn SQL.

This is the first batch of topics from the full curriculum (SELECT, GROUP
BY, HAVING, INNER JOIN, LEFT JOIN, CASE, CTE, and ranking window
functions). It establishes the pattern; RIGHT/FULL/SELF JOIN, UNION,
LAG/LEAD, running totals, and date functions follow the same shape and
are added in a follow-up batch.
"""

from __future__ import annotations

from app.core.learning.models import Lesson

LESSONS: list[Lesson] = [
    Lesson(
        id="select_where_order_by",
        title="SELECT, WHERE, and ORDER BY",
        category="Fundamentals",
        difficulty="Beginner",
        explanation=(
            "`SELECT` chooses which columns to return, `WHERE` filters which "
            "rows are included *before* any grouping happens, and `ORDER BY` "
            "sorts the final result set. These three clauses cover the "
            "majority of everyday data-pulling queries."
        ),
        syntax=(
            "SELECT column1, column2\n"
            "FROM table_name\n"
            "WHERE condition\n"
            "ORDER BY column1 [ASC | DESC];"
        ),
        visual_example=(
            "**Before (`hr_employees`, unfiltered):**\n\n"
            "| first_name | salary |\n|---|---|\n| Asha | 62000 |\n| Ravi | 91000 |\n| Meera | 78000 |\n\n"
            "**After `WHERE salary > 70000 ORDER BY salary DESC`:**\n\n"
            "| first_name | salary |\n|---|---|\n| Ravi | 91000 |\n| Meera | 78000 |"
        ),
        dataset_id="hr",
        practice_question=(
            "List the first_name, last_name, job_title, and salary of every "
            "employee earning more than 80000, sorted by salary from "
            "highest to lowest."
        ),
        answer_query=(
            "SELECT first_name, last_name, job_title, salary\n"
            "FROM hr_employees\n"
            "WHERE salary > 80000\n"
            "ORDER BY salary DESC;"
        ),
        business_use_case=(
            "An HR analyst pulling a shortlist of senior earners for a "
            "compensation review — filter first, then sort by what matters most."
        ),
        common_interview_questions=(
            "In what order does SQL logically evaluate FROM, WHERE, SELECT, and ORDER BY?",
            "How does WHERE handle NULL values — does `WHERE salary != 50000` include NULL salaries?",
            "What's the difference between filtering in WHERE versus filtering in HAVING?",
            "Is ORDER BY guaranteed without an explicit clause? Why or why not?",
        ),
    ),
    Lesson(
        id="group_by",
        title="GROUP BY and Aggregate Functions",
        category="Aggregation",
        difficulty="Beginner",
        explanation=(
            "`GROUP BY` collapses rows that share the same value in one or "
            "more columns into a single row per group, so you can apply "
            "aggregate functions (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`) per "
            "group instead of across the whole table."
        ),
        syntax=(
            "SELECT column, AGG_FUNC(other_column)\n"
            "FROM table_name\n"
            "GROUP BY column;"
        ),
        visual_example=(
            "**Rows:** `(dept=Eng, salary=90k)`, `(dept=Eng, salary=70k)`, `(dept=Sales, salary=60k)`\n\n"
            "**`GROUP BY dept` with `AVG(salary)`:**\n\n"
            "| dept | avg_salary |\n|---|---|\n| Eng | 80000 |\n| Sales | 60000 |"
        ),
        dataset_id="hr",
        practice_question=(
            "For each department, find the average salary. Return "
            "department_id and avg_salary, rounded to 2 decimal places."
        ),
        answer_query=(
            "SELECT department_id, ROUND(AVG(salary), 2) AS avg_salary\n"
            "FROM hr_employees\n"
            "GROUP BY department_id;"
        ),
        business_use_case=(
            "Finance comparing average compensation cost across departments "
            "before budget planning season."
        ),
        common_interview_questions=(
            "Why can't you SELECT a column that isn't in GROUP BY or wrapped in an aggregate function?",
            "What's the difference between COUNT(*) and COUNT(column_name)?",
            "How would you get a running count instead of a single grouped count?",
            "What happens if a group contains NULL values in the aggregated column?",
        ),
    ),
    Lesson(
        id="having",
        title="Filtering Groups with HAVING",
        category="Aggregation",
        difficulty="Beginner",
        explanation=(
            "`WHERE` filters individual rows before grouping; `HAVING` "
            "filters *groups* after aggregation. If your condition uses an "
            "aggregate function like `AVG()` or `COUNT()`, it belongs in HAVING."
        ),
        syntax=(
            "SELECT column, AGG_FUNC(other_column)\n"
            "FROM table_name\n"
            "GROUP BY column\n"
            "HAVING AGG_FUNC(other_column) condition;"
        ),
        visual_example=(
            "**Grouped averages:** `Eng = 80000`, `Sales = 60000`, `HR = 55000`\n\n"
            "**`HAVING AVG(salary) > 65000`:**\n\n"
            "| dept | avg_salary |\n|---|---|\n| Eng | 80000 |"
        ),
        dataset_id="hr",
        practice_question=(
            "Find every department where the average salary exceeds 75000. "
            "Return department_id and avg_salary."
        ),
        answer_query=(
            "SELECT department_id, ROUND(AVG(salary), 2) AS avg_salary\n"
            "FROM hr_employees\n"
            "GROUP BY department_id\n"
            "HAVING AVG(salary) > 75000;"
        ),
        business_use_case=(
            "Flagging departments whose average pay has drifted above a "
            "budget threshold, for a leadership review."
        ),
        common_interview_questions=(
            "Can you use HAVING without GROUP BY? What would it mean?",
            "Why does `WHERE AVG(salary) > 75000` fail but `HAVING AVG(salary) > 75000` works?",
            "Can HAVING filter on a column that isn't aggregated?",
            "What's the execution order of WHERE, GROUP BY, and HAVING?",
        ),
    ),
    Lesson(
        id="inner_join",
        title="INNER JOIN",
        category="Joins",
        difficulty="Beginner",
        explanation=(
            "`INNER JOIN` returns only the rows where the join condition "
            "matches in *both* tables. Rows on either side without a match "
            "are dropped from the result entirely."
        ),
        syntax=(
            "SELECT a.column, b.column\n"
            "FROM table_a a\n"
            "INNER JOIN table_b b ON a.key = b.key;"
        ),
        visual_example=(
            "**employees:** `(id=1, dept_id=10)`, `(id=2, dept_id=99)`  \n"
            "**departments:** `(dept_id=10, name=Eng)`\n\n"
            "**INNER JOIN result:** only employee 1 appears — employee 2's "
            "dept_id (99) has no match, so it's excluded."
        ),
        dataset_id="hr",
        practice_question=(
            "List each employee's first_name, last_name, and their "
            "department_name by joining hr_employees to hr_departments."
        ),
        answer_query=(
            "SELECT e.first_name, e.last_name, d.department_name\n"
            "FROM hr_employees e\n"
            "INNER JOIN hr_departments d ON e.department_id = d.department_id;"
        ),
        business_use_case=(
            "Producing a directory report that only makes sense for "
            "employees who are properly assigned to a real department."
        ),
        common_interview_questions=(
            "What's the difference between INNER JOIN and using a comma-separated FROM with a WHERE condition?",
            "What happens to unmatched rows in an INNER JOIN?",
            "Can you INNER JOIN on more than one condition?",
            "How does INNER JOIN performance relate to indexes on the join columns?",
        ),
    ),
    Lesson(
        id="left_join",
        title="LEFT JOIN",
        category="Joins",
        difficulty="Beginner",
        explanation=(
            "`LEFT JOIN` keeps every row from the left table, filling in "
            "`NULL` for columns from the right table when there's no match. "
            "It's the standard way to answer 'find X with no matching Y' questions."
        ),
        syntax=(
            "SELECT a.column, b.column\n"
            "FROM table_a a\n"
            "LEFT JOIN table_b b ON a.key = b.key;"
        ),
        visual_example=(
            "**customers:** `Asha`, `Ravi`  \n**orders:** `(customer=Asha, order_id=101)`\n\n"
            "**LEFT JOIN result:**\n\n"
            "| customer | order_id |\n|---|---|\n| Asha | 101 |\n| Ravi | NULL |"
        ),
        dataset_id="ecommerce",
        practice_question=(
            "List every customer's first_name and last_name along with "
            "order_id, including customers who have never placed an order "
            "(their order_id should be NULL)."
        ),
        answer_query=(
            "SELECT c.first_name, c.last_name, o.order_id\n"
            "FROM ecom_customers c\n"
            "LEFT JOIN ecom_orders o ON c.customer_id = o.customer_id;"
        ),
        business_use_case=(
            "Marketing wants to find signed-up customers who never placed a "
            "first order, to target them with a welcome offer."
        ),
        common_interview_questions=(
            "How would you find only the customers with zero orders using this LEFT JOIN?",
            "What's the difference between LEFT JOIN and RIGHT JOIN?",
            "Why would `WHERE o.status = 'Completed'` after a LEFT JOIN silently turn it into an INNER JOIN?",
            "How do you simulate a FULL JOIN in MySQL, which doesn't support it natively?",
        ),
    ),
    Lesson(
        id="case_expression",
        title="CASE Expressions",
        category="Conditional Logic",
        difficulty="Intermediate",
        explanation=(
            "`CASE` lets you compute a value conditionally, row by row, "
            "directly inside a query — like an inline if/elif/else. It's "
            "commonly used to bucket continuous values into labeled categories."
        ),
        syntax=(
            "SELECT column,\n"
            "  CASE\n"
            "    WHEN condition1 THEN result1\n"
            "    WHEN condition2 THEN result2\n"
            "    ELSE default_result\n"
            "  END AS new_column\n"
            "FROM table_name;"
        ),
        visual_example=(
            "**rating column:** `PG`, `PG-13`, `TV-MA`\n\n"
            "**With CASE:**\n\n"
            "| rating | audience_group |\n|---|---|\n| PG | Family |\n| PG-13 | Teen |\n| TV-MA | Mature |"
        ),
        dataset_id="streaming",
        practice_question=(
            "For each title, show the title, its rating, and a new column "
            "audience_group that is 'Family' when rating is 'G' or 'PG', "
            "'Teen' when rating is 'PG-13' or 'TV-14', and 'Mature' otherwise."
        ),
        answer_query=(
            "SELECT title, rating,\n"
            "  CASE\n"
            "    WHEN rating IN ('G', 'PG') THEN 'Family'\n"
            "    WHEN rating IN ('PG-13', 'TV-14') THEN 'Teen'\n"
            "    ELSE 'Mature'\n"
            "  END AS audience_group\n"
            "FROM streaming_titles;"
        ),
        business_use_case=(
            "A streaming platform building a parental-controls filter that "
            "groups many specific ratings into a few simple audience tiers."
        ),
        common_interview_questions=(
            "What does CASE return if no WHEN condition matches and there's no ELSE?",
            "Can you use a CASE expression inside a WHERE clause? Inside GROUP BY?",
            "What's the difference between a 'simple CASE' and a 'searched CASE'?",
            "How would you use CASE to pivot rows into columns?",
        ),
    ),
    Lesson(
        id="cte",
        title="Common Table Expressions (CTE)",
        category="CTEs & Subqueries",
        difficulty="Intermediate",
        explanation=(
            "A CTE (`WITH ... AS (...)`) defines a named, temporary result "
            "set you can reference later in the same query — useful for "
            "breaking a complex query into readable steps, especially when "
            "you need to reuse an aggregated result."
        ),
        syntax=(
            "WITH cte_name AS (\n"
            "  SELECT column, AGG_FUNC(other_column) AS agg_value\n"
            "  FROM table_name\n"
            "  GROUP BY column\n"
            ")\n"
            "SELECT *\n"
            "FROM cte_name\n"
            "WHERE agg_value condition;"
        ),
        visual_example=(
            "**Step 1 (the CTE):** compute avg_salary per department\n\n"
            "**Step 2:** join employees back to that CTE to compare each "
            "person's salary against their own department's average"
        ),
        dataset_id="hr",
        practice_question=(
            "Using a CTE that calculates each department's average salary, "
            "list the employees (first_name, last_name, salary) who earn "
            "more than their department's average salary."
        ),
        answer_query=(
            "WITH dept_avg AS (\n"
            "  SELECT department_id, AVG(salary) AS avg_salary\n"
            "  FROM hr_employees\n"
            "  GROUP BY department_id\n"
            ")\n"
            "SELECT e.first_name, e.last_name, e.salary\n"
            "FROM hr_employees e\n"
            "JOIN dept_avg d ON e.department_id = d.department_id\n"
            "WHERE e.salary > d.avg_salary;"
        ),
        business_use_case=(
            "Identifying above-average earners within their own team, as a "
            "first pass before a compensation equity review."
        ),
        common_interview_questions=(
            "How is a CTE different from a subquery, in terms of readability and reuse?",
            "Can a CTE reference itself? What is that called, and what's it used for?",
            "Are CTEs materialized (computed once) or can they be inlined by the optimizer?",
            "Can you chain multiple CTEs in one WITH clause?",
        ),
    ),
    Lesson(
        id="ranking_window_functions",
        title="Ranking with ROW_NUMBER, RANK, DENSE_RANK",
        category="Window Functions",
        difficulty="Advanced",
        explanation=(
            "These three window functions assign a rank to each row within "
            "a `PARTITION BY` group, ordered by `ORDER BY` — but they "
            "handle ties differently: `ROW_NUMBER()` always gives unique, "
            "sequential numbers; `RANK()` gives tied rows the same rank and "
            "then skips the next number(s); `DENSE_RANK()` gives tied rows "
            "the same rank with no gap afterward."
        ),
        syntax=(
            "SELECT column,\n"
            "  ROW_NUMBER() OVER (PARTITION BY group_col ORDER BY sort_col DESC) AS row_num,\n"
            "  RANK()       OVER (PARTITION BY group_col ORDER BY sort_col DESC) AS rank_num,\n"
            "  DENSE_RANK() OVER (PARTITION BY group_col ORDER BY sort_col DESC) AS dense_rank_num\n"
            "FROM table_name;"
        ),
        visual_example=(
            "**Salaries in one department, tied at 90000:** 90000, 90000, 85000\n\n"
            "| salary | ROW_NUMBER | RANK | DENSE_RANK |\n|---|---|---|---|\n"
            "| 90000 | 1 | 1 | 1 |\n| 90000 | 2 | 1 | 1 |\n| 85000 | 3 | 3 | 2 |"
        ),
        dataset_id="hr",
        practice_question=(
            "Rank employees by salary within each department (highest "
            "salary = rank 1) using ROW_NUMBER, RANK, and DENSE_RANK side "
            "by side so you can compare how they handle ties."
        ),
        answer_query=(
            "SELECT\n"
            "  department_id,\n"
            "  first_name,\n"
            "  last_name,\n"
            "  salary,\n"
            "  ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) AS row_num,\n"
            "  RANK()       OVER (PARTITION BY department_id ORDER BY salary DESC) AS rank_num,\n"
            "  DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS dense_rank_num\n"
            "FROM hr_employees\n"
            "ORDER BY department_id, salary DESC;"
        ),
        business_use_case=(
            "Identifying the top earner per department for a recognition "
            "program, while correctly handling departments with tied salaries."
        ),
        common_interview_questions=(
            "When would RANK() and DENSE_RANK() produce the same output, and when would they differ?",
            "How would you find the single top-paid employee per department using one of these functions?",
            "What's the difference between PARTITION BY and GROUP BY?",
            "Can you use a window function's result directly in the same query's WHERE clause? Why not?",
        ),
    ),
]

LESSONS_BY_ID: dict[str, Lesson] = {lesson.id: lesson for lesson in LESSONS}

CATEGORIES: list[str] = sorted({lesson.category for lesson in LESSONS})
