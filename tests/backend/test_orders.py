"""
Tests for orders API endpoints.
"""
import pytest


class TestOrdersEndpoints:
    """Test suite for orders-related endpoints."""

    def test_get_orders_by_quarter_filter(self, client):
        """Test that quarter filter returns only orders from that quarter's months.

        Validates filter_by_month() quarter-expansion logic: Q1-2025 must map
        to exactly 2025-01, 2025-02, 2025-03 and nothing else.
        """
        response = client.get("/api/orders?month=Q1-2025")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        q1_months = {"2025-01", "2025-02", "2025-03"}
        for order in data:
            # order_date format: "2025-01-08T10:19:00" → first 7 chars are YYYY-MM
            order_month = order["order_date"][:7]
            assert order_month in q1_months, (
                f"Order {order['order_number']} dated {order['order_date']} "
                f"is outside Q1-2025"
            )

        # Cross-validate: count should equal sum of individual month queries
        jan = client.get("/api/orders?month=2025-01").json()
        feb = client.get("/api/orders?month=2025-02").json()
        mar = client.get("/api/orders?month=2025-03").json()
        assert len(data) == len(jan) + len(feb) + len(mar)

    def test_order_total_value_calculation(self, client):
        """Test that every order's total_value equals sum of item line totals.

        Critical money-path validation: total_value must equal
        sum(quantity * unit_price) across all line items.
        """
        response = client.get("/api/orders")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for order in data:
            assert "total_value" in order
            assert isinstance(order["total_value"], (int, float))
            assert order["total_value"] > 0

            calculated_total = sum(
                item["quantity"] * item["unit_price"]
                for item in order["items"]
            )
            assert abs(order["total_value"] - calculated_total) < 0.01, (
                f"Order {order['order_number']}: total_value={order['total_value']} "
                f"but sum(qty*price)={calculated_total}"
            )

    def test_order_status_values(self, client):
        """Test that all orders have a valid status from the allowed set.

        Validates status field integrity — downstream dashboard logic
        (pending_orders) and filters depend on these exact values.
        """
        response = client.get("/api/orders")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        valid_statuses = {"delivered", "shipped", "processing", "backordered"}
        for order in data:
            assert "status" in order
            assert order["status"].lower() in valid_statuses, (
                f"Order {order['order_number']} has invalid status: {order['status']}"
            )
