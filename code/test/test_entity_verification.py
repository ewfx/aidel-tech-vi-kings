# File: tests/test_entity_verification.py
import pytest
import json
import os
from unittest.mock import patch, MagicMock

# Import the component being tested - adjust the import paths as needed
try:
    from dags.utils.data_enrichment import (
        check_pep_list,
        check_sanctions,
        get_open_corporates_data,
    )
except ImportError:
    # Skip tests if imports fail
    raise ImportError(
        "Could not import the required modules. Ensure the module paths are correct."
    )
    pytest.skip("Could not import the required modules", allow_module_level=True)

# Sample test data
SAMPLE_PEP = "Viktor Yanukovych"
SAMPLE_ORG = "Sberbank of Russia"


@pytest.fixture
def sample_transaction_id():
    return "TEST-UNIT-001"


@pytest.fixture
def mock_response():
    """Create a mock response for API calls."""
    mock = MagicMock()
    mock.status_code = 200
    mock.raise_for_status = MagicMock()
    mock.json = MagicMock(return_value={})
    return mock


@pytest.mark.unit
class TestPEPDetection:
    """Tests for PEP detection functionality."""

    @patch("dags.utils.data_enrichment.open")
    @patch("os.path.exists")
    def test_check_pep_list_positive(
        self, mock_exists, mock_open, sample_transaction_id
    ):
        """Test PEP detection with a known PEP."""
        # Setup mocks
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__iter__.return_value = [
            "name\tposition\tcountry\talias\n",
            f"{SAMPLE_PEP}\tFormer President\tUkraine\tViktor F. Yanukovych\n",
        ]
        mock_open.return_value = mock_file

        # Execute
        result = check_pep_list(SAMPLE_PEP, transaction_id=sample_transaction_id)

        # Assert
        assert result["status"] == "success"
        assert len(result["data"]) > 0
        match = False
        for entry in result["data"]:
            if SAMPLE_PEP in entry.get("name", ""):
                match = True
                break
        assert match, "PEP should be found in the results"

    @patch("dags.utils.data_enrichment.open")
    @patch("os.path.exists")
    def test_check_pep_list_negative(
        self, mock_exists, mock_open, sample_transaction_id
    ):
        """Test PEP detection with a non-PEP."""
        # Setup mocks
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__iter__.return_value = [
            "name\tposition\tcountry\talias\n",
            f"{SAMPLE_PEP}\tFormer President\tUkraine\tViktor F. Yanukovych\n",
        ]
        mock_open.return_value = mock_file

        # Execute
        result = check_pep_list("John Doe", transaction_id=sample_transaction_id)

        # Assert
        assert result["status"] == "success"
        assert len(result["data"]) == 0


@pytest.mark.unit
class TestSanctionsDetection:
    """Tests for sanctions detection functionality."""

    @patch("requests.Session")
    def test_check_sanctions_positive(self, mock_session, sample_transaction_id):
        """Test sanctions detection with a sanctioned entity."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "responses": {
                "q1": {
                    "results": [
                        {
                            "schema": "Company",
                            "id": "123",
                            "caption": SAMPLE_ORG,
                            "score": 0.9,
                            "properties": {"name": SAMPLE_ORG},
                            "datasets": ["OFAC"],
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status = MagicMock()

        mock_session_instance = MagicMock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance

        # Execute
        result = check_sanctions(
            "Company", SAMPLE_ORG, transaction_id=sample_transaction_id
        )

        # Assert
        assert result["status"] == "success"
        assert len(result["data"]) > 0
        assert result["data"][0]["caption"] == SAMPLE_ORG

    @patch("requests.Session")
    def test_check_sanctions_negative(self, mock_session, sample_transaction_id):
        """Test sanctions detection with a non-sanctioned entity."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"responses": {"q1": {"results": []}}}
        mock_response.raise_for_status = MagicMock()

        mock_session_instance = MagicMock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance

        # Execute
        result = check_sanctions(
            "Company", "Clean Company Inc", transaction_id=sample_transaction_id
        )

        # Assert
        assert result["status"] == "success"
        assert len(result["data"]) == 0


@pytest.mark.unit
class TestCorporateRegistry:
    """Tests for corporate registry lookup functionality."""

    @patch("requests.get")
    def test_open_corporates_lookup_positive(
        self, mock_get, mock_response, sample_transaction_id
    ):
        """Test corporate registry lookup with a known entity."""
        # Setup mock
        mock_response.json.return_value = {
            "results": {
                "companies": [
                    {
                        "company": {
                            "name": SAMPLE_ORG,
                            "jurisdiction_code": "ru",
                            "company_number": "12345",
                            "company_type": "Bank",
                            "incorporation_date": "1991-12-22",
                            "registered_address": "Moscow, Russia",
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        # Execute
        result = get_open_corporates_data(
            {"name": SAMPLE_ORG, "jurisdiction": "Russia"},
            transaction_id=sample_transaction_id,
        )

        # Assert
        assert result["status"] == "success"
        assert result["data"]["name"] == SAMPLE_ORG

    @patch("requests.get")
    def test_open_corporates_lookup_negative(
        self, mock_get, mock_response, sample_transaction_id
    ):
        """Test corporate registry lookup with an unknown entity."""
        # Setup mock
        mock_response.json.return_value = {"results": {"companies": []}}
        mock_get.return_value = mock_response

        # Execute
        result = get_open_corporates_data(
            {"name": "Unknown Company", "jurisdiction": "Nowhere"},
            transaction_id=sample_transaction_id,
        )

        # Assert
        assert result["status"] == "no_results"
        assert result["data"] is None
