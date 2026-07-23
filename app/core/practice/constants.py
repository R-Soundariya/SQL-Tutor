"""Selectable options for the Practice Questions page.

Views, Indexes, and Query Optimization are deliberately excluded here -
they don't fit a "write a SELECT, compare the output" loop, and belong to
the dedicated Query Optimizer phase instead.
"""

TOPICS: list[str] = [
    "SELECT / WHERE / ORDER BY",
    "GROUP BY",
    "HAVING",
    "JOINS",
    "Subqueries",
    "CASE",
    "CTE",
    "Window Functions",
    "Date Functions",
    "Ranking",
    "Aggregate Functions",
    "String Functions",
    "NULL Handling",
]

DIFFICULTIES: list[str] = ["Beginner", "Intermediate", "Advanced"]

COMPANIES: list[str] = [
    "Any / Generic",
    "Amazon",
    "Zoho",
    "Tiger Analytics",
    "Accenture",
    "TCS",
    "Capgemini",
]
