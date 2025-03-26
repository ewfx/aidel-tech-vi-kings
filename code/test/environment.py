# File: tests/environment.py
"""
Behave environment setup file for the AML Risk Assessment tests.
This file contains hooks that are executed at various points during test execution.
"""
import os
import json
import logging
import requests
from behave.model import Scenario, Feature
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def before_all(context):
    """
    Setup executed before any feature or scenario is run.
    """
    # Configure the API URL
    context.api_url = os.environ.get("API_URL", "http://localhost:8000/api")
    context.wait_timeout = int(os.environ.get("WAIT_TIMEOUT", 120))
    context.poll_interval = int(os.environ.get("POLL_INTERVAL", 5))
    
    # Setup test output directory
    context.output_dir = os.environ.get("TEST_OUTPUT_DIR", "test_output")
    if not os.path.exists(context.output_dir):
        os.makedirs(context.output_dir)
    
    # Create a test run ID
    from datetime import datetime
    context.test_run_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Check if the API is available
    try:
        response = requests.get(f"{context.api_url}/health", timeout=5)
        response.raise_for_status()
        context.api_available = True
        logger.info(f"API available at {context.api_url}")
    except Exception as e:
        context.api_available = False
        logger.warning(f"API not available at {context.api_url}: {str(e)}")
        logger.warning("Tests will be skipped if API is required")

def before_feature(context, feature):
    """
    Setup executed before each feature.
    """
    logger.info(f"Starting feature: {feature.name}")
    # Create feature output directory
    feature_dir = os.path.join(context.output_dir, feature.name.replace(' ', '_').lower())
    if not os.path.exists(feature_dir):
        os.makedirs(feature_dir)
    context.feature_dir = feature_dir

def before_scenario(context, scenario):
    """
    Setup executed before each scenario.
    """
    logger.info(f"Starting scenario: {scenario.name}")
    
    # Skip if API is required but not available
    if not context.api_available and scenario.tags.count("requires_api"):
        scenario.skip(f"API not available at {context.api_url}")
        return
    
    # Clean up any existing test data
    context.transaction_id = None
    context.result = None
    context.scenario_data = None
    context.transaction_text = None
    context.expected_entities = None
    context.expected_risk_keywords = None
    context.min_risk_score = None
    
    # Create scenario output directory
    scenario_dir = os.path.join(
        context.feature_dir, 
        scenario.name.replace(' ', '_').lower()
    )
    if not os.path.exists(scenario_dir):
        os.makedirs(scenario_dir)
    context.scenario_dir = scenario_dir

def after_scenario(context, scenario):
    """
    Cleanup executed after each scenario.
    """
    # Save test results if available
    if hasattr(context, 'result') and context.result:
        result_file = os.path.join(context.scenario_dir, "result.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(context.result, f, indent=2)
        
        # Log results for debugging
        logger.info(f"Results for scenario: {scenario.name}")
        logger.info(f"Transaction ID: {context.transaction_id}")
        logger.info(f"Risk Score: {context.result.get('risk_score')}")
        logger.info(f"Entities: {context.result.get('extracted_entities')}")
        logger.info(f"Evidence: {context.result.get('supporting_evidence')}")
    
    # Save original transaction text
    if hasattr(context, 'transaction_text') and context.transaction_text:
        text_file = os.path.join(context.scenario_dir, "transaction.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(context.transaction_text)
    
    # Record final scenario status
    status_file = os.path.join(context.scenario_dir, "status.json")
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump({
            "scenario": scenario.name,
            "status": scenario.status.name,
            "duration": scenario.duration,
            "steps_passed": len([s for s in scenario.steps if s.status == 'passed']),
            "steps_failed": len([s for s in scenario.steps if s.status == 'failed']),
            "steps_skipped": len([s for s in scenario.steps if s.status == 'skipped']),
        }, f, indent=2)

def after_feature(context, feature):
    """
    Cleanup executed after each feature.
    """
    # Summarize feature results
    scenarios_total = len(feature.scenarios)
    scenarios_passed = len([s for s in feature.scenarios if s.status == 'passed'])
    scenarios_failed = len([s for s in feature.scenarios if s.status == 'failed'])
    scenarios_skipped = len([s for s in feature.scenarios if s.status == 'skipped'])
    
    logger.info(f"Feature: {feature.name} completed")
    logger.info(f"Total: {scenarios_total}, Passed: {scenarios_passed}, Failed: {scenarios_failed}, Skipped: {scenarios_skipped}")
    
    # Save feature summary
    summary_file = os.path.join(context.feature_dir, "summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "feature": feature.name,
            "scenarios_total": scenarios_total,
            "scenarios_passed": scenarios_passed,
            "scenarios_failed": scenarios_failed,
            "scenarios_skipped": scenarios_skipped,
            "duration": feature.duration,
        }, f, indent=2)

def after_all(context):
    """
    Cleanup executed after all features and scenarios.
    """
    # Create a test run summary
    if hasattr(context, 'features'):
        features_total = len(context.features)
        features_passed = len([f for f in context.features if all(s.status == 'passed' for s in f.scenarios)])
        scenarios_total = sum(len(f.scenarios) for f in context.features)
        scenarios_passed = sum(len([s for s in f.scenarios if s.status == 'passed']) for f in context.features)
        
        logger.info(f"Test run completed: {context.test_run_id}")
        logger.info(f"Features: {features_passed}/{features_total} passed")
        logger.info(f"Scenarios: {scenarios_passed}/{scenarios_total} passed")
        
        # Save test run summary
        summary_file = os.path.join(context.output_dir, "test_run_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_run_id": context.test_run_id,
                "timestamp": context.test_run_id,
                "features_total": features_total,
                "features_passed": features_passed,
                "scenarios_total": scenarios_total,
                "scenarios_passed": scenarios_passed,
            }, f, indent=2)