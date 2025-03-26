# File: tests/conftest.py
import os
import pytest
import requests
from dotenv import load_dotenv
import sys

# Add the project root directory to Python's path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def api_url():
    """Get the API URL from environment variables or use default."""
    return os.environ.get("API_URL", "http://localhost:8000/api")

@pytest.fixture(scope="session")
def api_health_check(api_url):
    """Check if the API is healthy before running tests."""
    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code != 200:
            pytest.skip(f"API is not available at {api_url}")
    except requests.exceptions.RequestException:
        pytest.skip(f"API is not available at {api_url}")

# File: tests/.env.example
# API Settings
API_URL="http://localhost:8000/api"
WAIT_TIMEOUT=120
POLL_INTERVAL=5

# File: tests/environment.py
"""Behave environment setup file"""
from behave.model import Scenario
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def before_all(context):
    """Setup before all tests."""
    # Configure the API URL
    context.api_url = os.environ.get("API_URL", "http://localhost:8000/api")
    context.wait_timeout = int(os.environ.get("WAIT_TIMEOUT", 120))
    context.poll_interval = int(os.environ.get("POLL_INTERVAL", 5))
    
    # Check if the API is available
    try:
        response = requests.get(f"{context.api_url}/health")
        response.raise_for_status()
        context.api_available = True
    except Exception:
        context.api_available = False
        print(f"WARNING: API not available at {context.api_url}")

def before_scenario(context, scenario):
    """Setup before each scenario."""
    if not context.api_available:
        scenario.skip(f"API not available at {context.api_url}")
    
    # Clean up any existing test data
    context.transaction_id = None
    context.result = None
    context.scenario_data = None
    context.transaction_text = None
    context.expected_entities = None
    context.expected_risk_keywords = None
    context.min_risk_score = None

def after_scenario(context, scenario):
    """Cleanup after each scenario."""
    # Log results for debugging
    if hasattr(context, 'result') and context.result:
        print(f"\nResults for scenario: {scenario.name}")
        print(f"Transaction ID: {context.transaction_id}")
        print(f"Risk Score: {context.result.get('risk_score')}")
        print(f"Entities: {context.result.get('extracted_entities')}")
        print(f"Evidence: {context.result.get('supporting_evidence')}")