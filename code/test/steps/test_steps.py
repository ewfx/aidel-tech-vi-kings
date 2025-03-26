import os
import json
import requests
import time
from behave import given, when, then, step
from behave.runner import Context
from dotenv import load_dotenv

load_dotenv()

# Configuration - reused from the original steps file
API_URL = os.environ.get("API_URL", "http://localhost:8000/api")
WAIT_TIMEOUT = 120  # Seconds to wait for transaction processing
POLL_INTERVAL = 5  # Seconds between polling attempts


# Helper functions
def submit_transaction(transaction_text):
    """Submit a transaction to the API and return the response."""
    response = requests.post(
        f"{API_URL}/transaction",
        data=transaction_text,
        headers={"Content-Type": "text/plain"},
    )
    return response.json()


def get_transaction_status(transaction_id):
    """Get the status of a transaction."""
    response = requests.get(f"{API_URL}/transaction/{transaction_id}")
    return response.json()


def poll_until_complete(transaction_id, timeout=WAIT_TIMEOUT, interval=POLL_INTERVAL):
    """Poll the transaction status until it's complete or timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = get_transaction_status(transaction_id)
        if result.get("status") in ["completed", "failed", "error"]:
            return result
        time.sleep(interval)
    raise TimeoutError(f"Transaction processing timed out after {timeout} seconds")


def get_entity_data(transaction_id, entity_name, data_source, entity_type="organizations"):
    """Get data for a specific entity from a specific data source."""
    # First, try using the transaction files endpoint to get the path
    response = requests.get(f"{API_URL}/transaction/{transaction_id}/files")
    if response.status_code != 200:
        return None
    
    file_tree = response.json()
    
    # Find the right path based on entity type and data source
    path = None
    for item in file_tree:
        if item.get("name") == "entity_data":
            for child in item.get("children", []):
                if child.get("name") == f"{entity_type}_results":
                    for subchild in child.get("children", []):
                        if subchild.get("name") == data_source:
                            for file in subchild.get("children", []):
                                if entity_name.lower().replace(" ", "_") in file.get("name", "").lower():
                                    path = file.get("path")
                                    break
    
    if not path:
        return None
    
    # Get the file content
    response = requests.get(f"{API_URL}/transaction/{transaction_id}/files/{path}")
    if response.status_code != 200:
        return None
    
    return response.json().get("content")


# Original step definitions (kept for compatibility)
@given("a transaction with the following content")
def step_impl(context):
    """Set up the transaction data from the docstring."""
    context.transaction_text = context.text.strip()

@when("I check previous transaction with id {transaction_id}")
def step_impl(context, transaction_id):
    """Check the status of a previous transaction."""
    context.transaction_id = transaction_id
    context.result = get_transaction_status(transaction_id)
    print(f"Transaction {transaction_id} status: {context.result.get('status')}")
    assert context.result.get("status") == "completed", f"Transaction {transaction_id} not completed yet."
    

@when("I submit the transaction")
def step_impl(context):
    """Submit the transaction to the API."""
    try:
        context.response = submit_transaction(context.transaction_text)
        assert (
            "transaction_id" in context.response or "run_id" in context.response
        ), f"Failed to submit transaction: {context.response}"

        # Store the transaction ID for later use
        if "transaction_id" in context.response:
            context.transaction_id = context.response["transaction_id"]
        else:
            # For Airflow status responses
            context.transaction_id = context.response.get("run_id")

        print(f"Transaction submitted successfully with ID: {context.transaction_id}")
    except Exception as e:
        context.exception = e
        raise


@when("I wait for the transaction to complete")
def step_impl(context):
    """Wait for the transaction processing to complete."""
    try:
        context.result = poll_until_complete(context.transaction_id)
        print(
            f"Transaction processing completed with status: {context.result.get('status')}"
        )
    except Exception as e:
        context.exception = e
        raise


@then('the transaction status should be "{status}"')
def step_impl(context, status):
    """Check if the transaction has the expected status."""
    assert (
        context.result.get("status") == status
    ), f"Expected status '{status}', got '{context.result.get('status')}'"


@then("the risk score should be at least {min_score:f}")
def step_impl(context, min_score):
    """Check if the risk score meets the minimum threshold."""
    actual_score = float(context.result.get("risk_score", 0))
    assert (
        actual_score >= min_score
    ), f"Expected risk score at least {min_score}, got {actual_score}"


@then("the extracted entities should include")
def step_impl(context):
    """Check if all expected entities in the table were extracted."""
    extracted_entities = context.result.get("extracted_entities", [])
    for row in context.table:
        expected_entity = row[0]
        found = any(
            expected_entity.lower() in entity.lower() for entity in extracted_entities
        )
        assert (
            found
        ), f"Expected entity '{expected_entity}' was not found in {extracted_entities}"


@then("the reasoning should include any of")
def step_impl(context):
    """Check if the reasoning mentions the expected keywords in the table."""
    reason = context.result.get("reason", "").lower()
    found_keywords = []
    total_rows = 0

    for row in context.table:
        total_rows += 1
        keyword = row[0]
        if keyword.lower() in reason:
            found_keywords.append(keyword)
    print(f"Found risk keywords: {found_keywords}")
    
    min_keywords = 1
    assert (
        len(found_keywords) >= min_keywords
    ), f"Expected to find at least {min_keywords} risk keywords, found {len(found_keywords)}: {found_keywords}"


@then("the evidence should include any of")
def step_impl(context):
    """Check if the evidence mentions the expected keywords in the table."""
    supporting_evidence = context.result.get("supporting_evidence", [])
    evidence_str = json.dumps(supporting_evidence).lower()
    found_keywords = []
    total_rows = 0

    for row in context.table:
        total_rows += 1
        keyword = row[0]
        if keyword.lower() in evidence_str:
            found_keywords.append(keyword)

    print(f"Found evidence keywords: {found_keywords}")

    min_keywords = 1
    assert (
        len(found_keywords) >= min_keywords
    ), f"Expected to find at least {min_keywords} evidence keywords, found {len(found_keywords)}: {found_keywords}"


# New step definitions for data source verification

@then('the OpenCorporates data should include company information for "{company_name}"')
def step_impl(context, company_name):
    """Check if OpenCorporates data was retrieved for the specified company."""
    # Fetch the data
    opencorp_data = get_entity_data(context.transaction_id, company_name, "opencorporates")
    
    # Parse the data if it's a string
    if isinstance(opencorp_data, str):
        try:
            opencorp_data = json.loads(opencorp_data)
        except:
            pass
    
    # Check if data exists
    assert opencorp_data, f"No OpenCorporates data found for {company_name}"
    
    # Check if it has the expected structure
    assert isinstance(opencorp_data, dict), "OpenCorporates data should be a dictionary"
    
    # Check for required fields
    required_fields = ["name", "company_number"]
    for field in required_fields:
        assert field in opencorp_data, f"OpenCorporates data missing required field: {field}"
    
    print(f"Successfully verified OpenCorporates data for {company_name}")


@then('the OpenCorporates data should show jurisdiction "{jurisdiction}" for "{company_name}"')
def step_impl(context, jurisdiction, company_name):
    """Check if OpenCorporates data shows the expected jurisdiction."""
    # Fetch the data
    opencorp_data = get_entity_data(context.transaction_id, company_name, "opencorporates")
    
    # Parse the data if it's a string
    if isinstance(opencorp_data, str):
        try:
            opencorp_data = json.loads(opencorp_data)
        except:
            pass
    
    # Check if data exists
    assert opencorp_data, f"No OpenCorporates data found for {company_name}"
    
    # Check jurisdiction
    company_jurisdiction = opencorp_data.get("jurisdiction_code", "").lower()
    assert company_jurisdiction == jurisdiction.lower(), f"Expected jurisdiction '{jurisdiction}', got '{company_jurisdiction}'"
    
    print(f"Successfully verified jurisdiction '{jurisdiction}' for {company_name}")


@then('the sanctions data should include matches for "{entity_name}"')
def step_impl(context, entity_name):
    """Check if sanctions data was found for the specified entity."""
    # First try to get from organizations
    sanctions_data = get_entity_data(context.transaction_id, entity_name, "sanctions")
    
    # If not found, try people
    if not sanctions_data:
        sanctions_data = get_entity_data(context.transaction_id, entity_name, "sanctions", "people")
    
    # Parse the data if it's a string
    if isinstance(sanctions_data, str):
        try:
            sanctions_data = json.loads(sanctions_data)
        except:
            pass
    
    # Check if data exists
    assert sanctions_data, f"No sanctions data found for {entity_name}"
    
    # Check if there are actual matches (non-empty list)
    assert len(sanctions_data) > 0, f"No sanctions matches found for {entity_name}"
    
    print(f"Successfully verified sanctions data for {entity_name} with {len(sanctions_data)} matches")


@then('the sanctions data should include "{source}" as a source')
def step_impl(context, source):
    """Check if sanctions data includes the specified source."""
    # We need the entity name to retrieve the data
    # Use the first entity in the latest result that had sanctions
    entities = context.result.get("extracted_entities", [])
    
    found_source = False
    
    # Try each entity
    for entity in entities:
        # Try both organizations and people
        for entity_type in ["organizations", "people"]:
            sanctions_data = get_entity_data(context.transaction_id, entity, "sanctions", entity_type)
            
            # Parse the data if it's a string
            if isinstance(sanctions_data, str):
                try:
                    sanctions_data = json.loads(sanctions_data)
                except:
                    continue
            
            if not sanctions_data:
                continue
                
            # Look for the source in each match
            for match in sanctions_data:
                datasets = match.get("datasets", [])
                if source in datasets:
                    found_source = True
                    break
            
            if found_source:
                break
        
        if found_source:
            break
    
    assert found_source, f"Sanctions source '{source}' not found in any entity's data"
    print(f"Successfully verified sanctions source '{source}'")


@then('the Wikidata data should include entity information for "{entity_name}"')
def step_impl(context, entity_name):
    """Check if Wikidata data was retrieved for the specified entity."""
    # Fetch the data
    wikidata = get_entity_data(context.transaction_id, entity_name, "wikidata")
    
    # Parse the data if it's a string
    if isinstance(wikidata, str):
        try:
            wikidata = json.loads(wikidata)
        except:
            pass
    
    # Check if data exists
    assert wikidata, f"No Wikidata found for {entity_name}"
    
    # Check entity info
    assert "entity_info" in wikidata, "Wikidata missing entity_info"
    
    entity_info = wikidata.get("entity_info", {})
    assert entity_info.get("entity_name") == entity_name, "Entity name mismatch in Wikidata"
    assert "entity_id" in entity_info, "Wikidata missing entity_id"
    
    print(f"Successfully verified Wikidata for {entity_name}")


@then("the Wikidata data should discover associated people")
def step_impl(context):
    """Check if Wikidata data includes discovered associated people."""
    # We need the entity name to retrieve the data
    # Use the first entity in the latest result
    entities = context.result.get("extracted_entities", [])
    
    found_associated_people = False
    
    # Try each entity
    for entity in entities:
        wikidata = get_entity_data(context.transaction_id, entity, "wikidata")
        
        # Parse the data if it's a string
        if isinstance(wikidata, str):
            try:
                wikidata = json.loads(wikidata)
            except:
                continue
        
        if not wikidata:
            continue
            
        # Check for associated people
        associated_people = wikidata.get("associated_people", [])
        if associated_people and len(associated_people) > 0:
            found_associated_people = True
            context.associated_people = associated_people  # Store for later steps
            break
    
    assert found_associated_people, "No associated people discovered in Wikidata"
    print(f"Successfully verified associated people in Wikidata: {len(context.associated_people)} found")


@then('at least one discovered person should have role containing "{role_keyword}"')
def step_impl(context, role_keyword):
    """Check if at least one discovered person has the specified role."""
    # Use the associated people stored in the previous step
    assert hasattr(context, "associated_people"), "No associated people found in previous step"
    
    found_role = False
    for person in context.associated_people:
        role = person.get("role", "").lower()
        if role_keyword.lower() in role:
            found_role = True
            print(f"Found person with role containing '{role_keyword}': {person.get('name')} ({role})")
            break
    
    assert found_role, f"No discovered person with role containing '{role_keyword}'"


@then('the PEP data should include matches for "{person_name}"')
def step_impl(context, person_name):
    """Check if PEP data was found for the specified person."""
    # Fetch the data
    pep_data = get_entity_data(context.transaction_id, person_name, "pep", "people")
    
    # Parse the data if it's a string
    if isinstance(pep_data, str):
        try:
            pep_data = json.loads(pep_data)
        except:
            pass
    
    # Check if data exists
    assert pep_data, f"No PEP data found for {person_name}"
    
    # Check if there are actual matches
    assert len(pep_data) > 0, f"No PEP matches found for {person_name}"
    
    # Store the PEP data for later steps
    if not hasattr(context, "pep_data"):
        context.pep_data = {}
    context.pep_data[person_name] = pep_data
    
    print(f"Successfully verified PEP data for {person_name} with {len(pep_data)} matches")


@then('the PEP data should show "{country}" as country for at least one person')
def step_impl(context, country):
    """Check if at least one PEP has the specified country."""
    # Use the PEP data stored in the previous step
    assert hasattr(context, "pep_data"), "No PEP data found in previous step"
    
    found_country = False
    for person_name, pep_matches in context.pep_data.items():
        for pep in pep_matches:
            pep_country = pep.get("country", "").lower()
            if country.lower() in pep_country:
                found_country = True
                print(f"Found PEP from {country}: {person_name}")
                break
        if found_country:
            break
    
    assert found_country, f"No PEP with country '{country}' found"


@then('the news data should include articles for "{entity_name}"')
def step_impl(context, entity_name):
    """Check if adverse news data was found for the specified entity."""
    # First try to get from organizations
    news_data = get_entity_data(context.transaction_id, entity_name, "news")
    
    # If not found, try people
    if not news_data:
        news_data = get_entity_data(context.transaction_id, entity_name, "news", "people")
    
    # Parse the data if it's a string
    if isinstance(news_data, str):
        try:
            news_data = json.loads(news_data)
        except:
            pass
    
    # Check if data exists
    assert news_data, f"No news data found for {entity_name}"
    
    # Check if there are actual articles
    assert len(news_data) > 0, f"No news articles found for {entity_name}"
    
    # Store the news data for later steps
    context.news_data = news_data
    
    print(f"Successfully verified news data for {entity_name} with {len(news_data)} articles")


@then("at least one news article should have negative sentiment")
def step_impl(context):
    """Check if at least one news article has negative sentiment/tone."""
    # Use the news data stored in the previous step
    assert hasattr(context, "news_data"), "No news data found in previous step"
    
    found_negative = False
    for article in context.news_data:
        tone = article.get("tone", 0)
        # Negative tone is usually represented as a negative number
        if isinstance(tone, (int, float)) and tone < 0:
            found_negative = True
            print(f"Found article with negative tone: {article.get('title')} (tone: {tone})")
            break
    
    assert found_negative, "No news article with negative sentiment found"