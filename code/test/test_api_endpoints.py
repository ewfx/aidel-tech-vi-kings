import pytest
import requests


@pytest.mark.api
class TestAPIEndpoints:
    """Tests for the API endpoints."""

    def test_health_endpoint(self, api_url, api_health_check):
        """Test the health check endpoint."""
        response = requests.get(f"{api_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_transaction_submission(self, api_url, api_health_check):
        """Test submitting a transaction."""
        transaction_text = """
        Transaction ID: TEST-API-001
        Date: 2023-09-24 10:00:00
        
        Sender:
        Name: "Test Sender LLC"
        
        Receiver:
        Name: "Test Receiver Inc"
        
        Amount: $100 USD
        """

        response = requests.post(
            f"{api_url}/transaction",
            data=transaction_text,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data or "run_id" in data

    def test_dashboard_stats(self, api_url, api_health_check):
        """Test getting dashboard statistics."""
        response = requests.get(f"{api_url}/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "totalTransactions" in data
        assert "highRiskTransactions" in data
        assert "mediumRiskTransactions" in data
        assert "lowRiskTransactions" in data
        assert "recentTransactions" in data
