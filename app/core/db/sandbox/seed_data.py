"""Deterministic seed data generators for each sandbox dataset.

A fixed random seed is used everywhere so that reloading a dataset always
produces byte-identical rows. This matters beyond Phase 2: later phases
compare a user's query output against a precomputed "expected output" for
each practice question, and that only works if the underlying data never
drifts between loads.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from faker import Faker

SEED = 42


def _new_faker() -> Faker:
    faker = Faker()
    Faker.seed(SEED)
    return faker


def _random_date(rng: random.Random, start: date, end: date) -> date:
    span_days = (end - start).days
    return start + timedelta(days=rng.randint(0, span_days))


# --- HR / Employees ----------------------------------------------------------

_DEPARTMENTS = [
    ("Engineering", "Bengaluru"),
    ("Sales", "Mumbai"),
    ("Marketing", "Delhi"),
    ("Human Resources", "Pune"),
    ("Finance", "Hyderabad"),
    ("Customer Support", "Chennai"),
]

_JOB_TITLES_BY_LEVEL = {
    "manager": ["Department Head", "Senior Manager"],
    "senior": ["Senior Analyst", "Senior Associate", "Team Lead"],
    "junior": ["Analyst", "Associate", "Executive"],
}


def build_hr_rows() -> dict[str, list[dict]]:
    rng = random.Random(SEED)
    faker = _new_faker()

    departments = [
        {"department_id": i + 1, "department_name": name, "location": location}
        for i, (name, location) in enumerate(_DEPARTMENTS)
    ]

    employees: list[dict] = []
    employee_id = 1
    hire_window_start = date(2018, 1, 1)
    hire_window_end = date(2026, 6, 1)

    department_managers: dict[int, int] = {}

    # One manager per department first, so later employees can report to them.
    for dept in departments:
        manager_id = employee_id
        employees.append(
            {
                "employee_id": manager_id,
                "first_name": faker.first_name(),
                "last_name": faker.last_name(),
                "email": f"manager{manager_id}@example.com",
                "hire_date": _random_date(rng, hire_window_start, date(2020, 1, 1)),
                "job_title": rng.choice(_JOB_TITLES_BY_LEVEL["manager"]),
                "department_id": dept["department_id"],
                "manager_id": None,
                "salary": rng.randint(95000, 140000),
            }
        )
        department_managers[dept["department_id"]] = manager_id
        employee_id += 1

    # Remaining staff report to their department's manager.
    for _ in range(34):
        dept = rng.choice(departments)
        level = rng.choices(["senior", "junior"], weights=[0.35, 0.65])[0]
        employees.append(
            {
                "employee_id": employee_id,
                "first_name": faker.first_name(),
                "last_name": faker.last_name(),
                "email": f"employee{employee_id}@example.com",
                "hire_date": _random_date(rng, hire_window_start, hire_window_end),
                "job_title": rng.choice(_JOB_TITLES_BY_LEVEL[level]),
                "department_id": dept["department_id"],
                "manager_id": department_managers[dept["department_id"]],
                "salary": rng.randint(45000, 90000) if level == "junior" else rng.randint(70000, 100000),
            }
        )
        employee_id += 1

    return {"hr_departments": departments, "hr_employees": employees}


# --- E-commerce ---------------------------------------------------------------

_COUNTRIES = ["India", "United States", "United Kingdom", "Germany", "Canada", "Australia", "Singapore"]
_PRODUCT_CATALOG = [
    ("Wireless Mouse", "Electronics", 799.00),
    ("Mechanical Keyboard", "Electronics", 3499.00),
    ("USB-C Hub", "Electronics", 1599.00),
    ("Noise Cancelling Headphones", "Electronics", 6999.00),
    ("Standing Desk", "Furniture", 12999.00),
    ("Ergonomic Chair", "Furniture", 8999.00),
    ("Desk Lamp", "Furniture", 1299.00),
    ("Notebook Set", "Stationery", 249.00),
    ("Fountain Pen", "Stationery", 599.00),
    ("Whiteboard", "Stationery", 1899.00),
    ("Yoga Mat", "Fitness", 899.00),
    ("Dumbbell Set", "Fitness", 2999.00),
    ("Resistance Bands", "Fitness", 499.00),
    ("Water Bottle", "Fitness", 349.00),
    ("Coffee Grinder", "Kitchen", 2199.00),
    ("French Press", "Kitchen", 1099.00),
    ("Air Fryer", "Kitchen", 5499.00),
    ("Blender", "Kitchen", 2799.00),
    ("Backpack", "Accessories", 1799.00),
    ("Travel Mug", "Accessories", 699.00),
]
_ORDER_STATUSES = ["Completed", "Completed", "Completed", "Pending", "Cancelled", "Refunded"]


def build_ecommerce_rows() -> dict[str, list[dict]]:
    rng = random.Random(SEED)
    faker = _new_faker()

    customers = []
    for customer_id in range(1, 31):
        first_name = faker.first_name()
        last_name = faker.last_name()
        customers.append(
            {
                "customer_id": customer_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name.lower()}.{last_name.lower()}{customer_id}@example.com",
                "country": rng.choice(_COUNTRIES),
                "signup_date": _random_date(rng, date(2022, 1, 1), date(2026, 1, 1)),
            }
        )

    products = [
        {"product_id": i + 1, "product_name": name, "category": category, "price": price}
        for i, (name, category, price) in enumerate(_PRODUCT_CATALOG)
    ]

    orders = []
    order_items = []
    order_item_id = 1
    for order_id in range(1, 61):
        customer = rng.choice(customers)
        order_date = _random_date(rng, date(2024, 1, 1), date(2026, 6, 1))
        orders.append(
            {
                "order_id": order_id,
                "customer_id": customer["customer_id"],
                "order_date": order_date,
                "status": rng.choice(_ORDER_STATUSES),
            }
        )

        for _ in range(rng.randint(1, 4)):
            product = rng.choice(products)
            order_items.append(
                {
                    "order_item_id": order_item_id,
                    "order_id": order_id,
                    "product_id": product["product_id"],
                    "quantity": rng.randint(1, 5),
                    "unit_price": product["price"],
                }
            )
            order_item_id += 1

    return {
        "ecom_customers": customers,
        "ecom_products": products,
        "ecom_orders": orders,
        "ecom_order_items": order_items,
    }


# --- Streaming catalog ---------------------------------------------------------

_TITLE_WORDS_A = ["Silent", "Crimson", "Last", "Hidden", "Broken", "Golden", "Quiet", "Distant", "Forgotten", "Endless"]
_TITLE_WORDS_B = ["Harbor", "Horizon", "Signal", "Garden", "Circuit", "Kingdom", "Shadows", "Tide", "Orbit", "Ember"]
_GENRES = ["Drama", "Comedy", "Documentary", "Thriller", "Sci-Fi", "Romance", "Crime", "Animation"]
_RATINGS = ["G", "PG", "PG-13", "R", "TV-MA", "TV-14"]


def build_streaming_rows() -> dict[str, list[dict]]:
    rng = random.Random(SEED)
    faker = _new_faker()

    titles = []
    for title_id in range(1, 41):
        content_type = rng.choice(["Movie", "TV Show"])
        release_year = rng.randint(2005, 2026)
        title_name = f"{rng.choice(_TITLE_WORDS_A)} {rng.choice(_TITLE_WORDS_B)}"
        titles.append(
            {
                "title_id": title_id,
                "title": title_name,
                "content_type": content_type,
                "director": faker.name() if content_type == "Movie" else None,
                "primary_country": rng.choice(_COUNTRIES),
                "date_added": _random_date(rng, date(2021, 1, 1), date(2026, 6, 1)),
                "release_year": release_year,
                "rating": rng.choice(_RATINGS),
                "duration_minutes": rng.randint(80, 160) if content_type == "Movie" else None,
                "seasons": None if content_type == "Movie" else rng.randint(1, 6),
                "genre": rng.choice(_GENRES),
            }
        )

    return {"streaming_titles": titles}


SEED_BUILDERS = {
    "hr": build_hr_rows,
    "ecommerce": build_ecommerce_rows,
    "streaming": build_streaming_rows,
}
