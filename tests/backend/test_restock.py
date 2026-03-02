"""
Tests for restock recommendation API endpoints.
"""
import pytest


class TestRestockEndpoints:
    """Test suite for restock recommendation endpoints."""

    def test_restock_recommendations_respect_budget(self, client):
        """Test that restock recommendations never exceed the budget.

        Validates the greedy-fill algorithm's budget invariants:
        - spent + remaining == budget (no money lost or created)
        - spent <= budget (never overspend)
        - each line_total == quantity * unit_cost (line math is correct)
        - sum of line_totals == spent (aggregate matches detail)
        """
        budget = 5000.0
        response = client.get(f"/api/restock/recommendations?budget={budget}")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == budget
        assert data["spent"] <= budget
        assert data["remaining"] >= 0
        assert abs(data["spent"] + data["remaining"] - budget) < 0.01

        recs = data["recommendations"]
        assert isinstance(recs, list)
        assert len(recs) > 0

        line_sum = 0.0
        for rec in recs:
            assert rec["quantity"] > 0
            expected_line = rec["quantity"] * rec["unit_cost"]
            assert abs(rec["line_total"] - expected_line) < 0.01, (
                f"SKU {rec['sku']}: line_total={rec['line_total']} "
                f"but qty*cost={expected_line}"
            )
            line_sum += rec["line_total"]

        assert abs(line_sum - data["spent"]) < 0.01

    def test_restock_recommendations_prioritize_increasing_trend(self, client):
        """Test that recommendations are ordered by trend priority.

        Validates the core sort key: increasing-trend items must appear
        before stable, which must appear before decreasing. This ensures
        a constrained budget is spent on the highest-urgency items first.
        """
        # Use a large budget so all eligible items appear and we can
        # verify the full ordering.
        response = client.get("/api/restock/recommendations?budget=100000")
        assert response.status_code == 200

        recs = response.json()["recommendations"]
        assert len(recs) > 0

        trend_priority = {"increasing": 0, "stable": 1, "decreasing": 2}

        # Every recommendation should have a known trend
        for rec in recs:
            assert rec["trend"] in trend_priority

        # Priorities must be non-decreasing across the list
        priorities = [trend_priority[rec["trend"]] for rec in recs]
        for i in range(len(priorities) - 1):
            assert priorities[i] <= priorities[i + 1], (
                f"Trend priority violated at index {i}: "
                f"{recs[i]['sku']} (trend={recs[i]['trend']}) "
                f"before {recs[i + 1]['sku']} (trend={recs[i + 1]['trend']})"
            )

        # The algorithm should surface at least one increasing-trend item
        # given the test dataset contains them.
        assert "increasing" in {rec["trend"] for rec in recs}
