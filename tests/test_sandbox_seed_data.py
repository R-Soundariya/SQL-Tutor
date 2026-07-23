"""Unit tests for seed data generation: determinism and referential integrity."""

from app.core.db.sandbox.seed_data import (
    build_ecommerce_rows,
    build_hr_rows,
    build_streaming_rows,
)


def test_seed_data_is_deterministic() -> None:
    assert build_hr_rows() == build_hr_rows()
    assert build_ecommerce_rows() == build_ecommerce_rows()
    assert build_streaming_rows() == build_streaming_rows()


def test_hr_referential_integrity() -> None:
    data = build_hr_rows()
    department_ids = {d["department_id"] for d in data["hr_departments"]}
    employee_ids = {e["employee_id"] for e in data["hr_employees"]}

    for employee in data["hr_employees"]:
        assert employee["department_id"] in department_ids
        if employee["manager_id"] is not None:
            assert employee["manager_id"] in employee_ids


def test_ecommerce_referential_integrity() -> None:
    data = build_ecommerce_rows()
    customer_ids = {c["customer_id"] for c in data["ecom_customers"]}
    product_ids = {p["product_id"] for p in data["ecom_products"]}
    order_ids = {o["order_id"] for o in data["ecom_orders"]}

    for order in data["ecom_orders"]:
        assert order["customer_id"] in customer_ids

    for item in data["ecom_order_items"]:
        assert item["order_id"] in order_ids
        assert item["product_id"] in product_ids
        assert item["quantity"] >= 1


def test_streaming_null_handling_matches_content_type() -> None:
    data = build_streaming_rows()
    for title in data["streaming_titles"]:
        if title["content_type"] == "Movie":
            assert title["duration_minutes"] is not None
            assert title["seasons"] is None
        else:
            assert title["content_type"] == "TV Show"
            assert title["duration_minutes"] is None
            assert title["seasons"] is not None
