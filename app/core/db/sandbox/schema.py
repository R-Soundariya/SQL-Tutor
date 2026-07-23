"""Table definitions for the practice sandbox datasets.

Each dataset is a group of plain SQLAlchemy Core tables (not ORM models,
since these are practice data the user queries directly, not domain
entities the app's own business logic manages). They live on their own
MetaData so they're independent of Base (app/core/db/models.py), which is
reserved for the app's own tables (attempts, progress, etc.) added in
later phases.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
)

sandbox_metadata = MetaData()

# --- HR / Employees dataset -------------------------------------------------
# Classic dataset for joins, self-joins (manager_id), GROUP BY/HAVING,
# window functions (salary rank within department), aggregate functions.

hr_departments = Table(
    "hr_departments",
    sandbox_metadata,
    Column("department_id", Integer, primary_key=True),
    Column("department_name", String(100), nullable=False),
    Column("location", String(100), nullable=False),
)

hr_employees = Table(
    "hr_employees",
    sandbox_metadata,
    Column("employee_id", Integer, primary_key=True),
    Column("first_name", String(50), nullable=False),
    Column("last_name", String(50), nullable=False),
    Column("email", String(150), nullable=False),
    Column("hire_date", Date, nullable=False),
    Column("job_title", String(100), nullable=False),
    Column("department_id", Integer, ForeignKey("hr_departments.department_id"), nullable=False),
    Column("manager_id", Integer, ForeignKey("hr_employees.employee_id"), nullable=True),
    Column("salary", Numeric(10, 2), nullable=False),
)

# --- E-commerce dataset ------------------------------------------------------
# Multi-table joins, subqueries, date functions, revenue aggregation.

ecom_customers = Table(
    "ecom_customers",
    sandbox_metadata,
    Column("customer_id", Integer, primary_key=True),
    Column("first_name", String(50), nullable=False),
    Column("last_name", String(50), nullable=False),
    Column("email", String(150), nullable=False),
    Column("country", String(60), nullable=False),
    Column("signup_date", Date, nullable=False),
)

ecom_products = Table(
    "ecom_products",
    sandbox_metadata,
    Column("product_id", Integer, primary_key=True),
    Column("product_name", String(150), nullable=False),
    Column("category", String(80), nullable=False),
    Column("price", Numeric(10, 2), nullable=False),
)

ecom_orders = Table(
    "ecom_orders",
    sandbox_metadata,
    Column("order_id", Integer, primary_key=True),
    Column("customer_id", Integer, ForeignKey("ecom_customers.customer_id"), nullable=False),
    Column("order_date", Date, nullable=False),
    Column("status", String(20), nullable=False),
)

ecom_order_items = Table(
    "ecom_order_items",
    sandbox_metadata,
    Column("order_item_id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("ecom_orders.order_id"), nullable=False),
    Column("product_id", Integer, ForeignKey("ecom_products.product_id"), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("unit_price", Numeric(10, 2), nullable=False),
)

# --- Streaming catalog dataset ------------------------------------------------
# Single wide table: string functions, date functions, CASE, NULL handling
# (duration_minutes is NULL for TV shows, seasons is NULL for movies).
# Titles are fictional to avoid representing real catalog data as factual.

streaming_titles = Table(
    "streaming_titles",
    sandbox_metadata,
    Column("title_id", Integer, primary_key=True),
    Column("title", String(200), nullable=False),
    Column("content_type", String(20), nullable=False),  # 'Movie' | 'TV Show'
    Column("director", String(100), nullable=True),
    Column("primary_country", String(60), nullable=False),
    Column("date_added", Date, nullable=False),
    Column("release_year", Integer, nullable=False),
    Column("rating", String(10), nullable=False),
    Column("duration_minutes", Integer, nullable=True),
    Column("seasons", Integer, nullable=True),
    Column("genre", String(80), nullable=False),
)


@dataclass(frozen=True)
class Dataset:
    """Metadata describing one practice dataset for the Sandbox UI."""

    id: str
    display_name: str
    description: str
    tables: tuple[Table, ...]


DATASETS: dict[str, Dataset] = {
    "hr": Dataset(
        id="hr",
        display_name="HR / Employees",
        description=(
            "Employees, departments, managers, and salaries. Good for joins, "
            "self-joins, GROUP BY/HAVING, and window functions."
        ),
        tables=(hr_departments, hr_employees),
    ),
    "ecommerce": Dataset(
        id="ecommerce",
        display_name="E-commerce Orders",
        description=(
            "Customers, products, orders, and order line items. Good for "
            "multi-table joins, subqueries, and revenue aggregation."
        ),
        tables=(ecom_customers, ecom_products, ecom_orders, ecom_order_items),
    ),
    "streaming": Dataset(
        id="streaming",
        display_name="Streaming Catalog",
        description=(
            "A Netflix-style catalog of fictional titles. Good for string "
            "functions, date functions, CASE expressions, and NULL handling."
        ),
        tables=(streaming_titles,),
    ),
}
